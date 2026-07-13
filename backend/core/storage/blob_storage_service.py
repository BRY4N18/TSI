"""Azure Blob Storage adapter for evidencia fotográfica."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import BinaryIO
from urllib.parse import urlparse

from django.conf import settings

ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/jpg"})
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
DEFAULT_CONTAINER_NAME = "evidencia-fotos"


class BlobTooLargeError(Exception):
    """Raised when uploaded file exceeds size limit."""


class BlobUploadError(Exception):
    """Raised when blob upload fails."""


class BlobStorageService:
    def __init__(self, *, base_path: Path | None = None):
        self._local_only = base_path is not None
        self.base_path = base_path or Path(
            getattr(settings, "BLOB_STORAGE_LOCAL_PATH", settings.BASE_DIR / "blob_storage")
        )
        self.container = getattr(settings, "BLOB_CONTAINER_EVIDENCIA", DEFAULT_CONTAINER_NAME)
        self._blob_service_client = None

    def validate_file(self, content: bytes, content_type: str) -> None:
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise BlobTooLargeError("Archivo excede 10 MB")
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError("Tipo de archivo no permitido; use JPEG o PNG")

    def build_blob_path(self, idaccidente: str, file_key: str, extension: str = "jpg") -> str:
        return f"{idaccidente}/{file_key}.{extension}"

    def upload(
        self,
        *,
        idaccidente: str,
        file_key: str,
        content: bytes | BinaryIO,
        content_type: str,
    ) -> str:
        if isinstance(content, (bytes, bytearray)):
            data = bytes(content)
        else:
            data = content.read()

        self.validate_file(data, content_type)

        extension = "png" if "png" in content_type else "jpg"
        blob_path = self.build_blob_path(idaccidente, file_key, extension)

        if self._should_use_azure():
            return self._upload_azure(blob_path, data, content_type)
        return self._upload_local(blob_path, data)

    def _should_use_azure(self) -> bool:
        if self._local_only:
            return False
        backend = getattr(settings, "BLOB_STORAGE_BACKEND", "local")
        if backend == "azure":
            return True
        if backend == "local":
            return False
        return bool(
            getattr(settings, "AZURE_ACCOUNT_NAME", "")
            and getattr(settings, "AZURE_ACCOUNT_KEY", "")
        )

    def _get_azure_client(self):
        if self._blob_service_client is not None:
            return self._blob_service_client

        from azure.storage.blob import BlobServiceClient

        connection_string = getattr(settings, "AZURE_BLOB_CONNECTION_STRING", "")
        account_name = getattr(settings, "AZURE_ACCOUNT_NAME", "")
        account_key = getattr(settings, "AZURE_ACCOUNT_KEY", "")

        if account_name and account_key:
            self._blob_service_client = BlobServiceClient(
                account_url=f"https://{account_name}.blob.core.windows.net",
                credential=account_key,
            )
        elif connection_string:
            self._blob_service_client = BlobServiceClient.from_connection_string(
                connection_string
            )
        else:
            raise BlobUploadError("Azure Blob no configurado (falta cuenta/clave o connection string)")

        return self._blob_service_client

    def _upload_azure(self, blob_path: str, data: bytes, content_type: str) -> str:
        from azure.core.exceptions import AzureError
        from azure.storage.blob import ContentSettings

        try:
            client = self._get_azure_client()
            blob_client = client.get_blob_client(container=self.container, blob=blob_path)
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type),
            )
            return blob_client.url
        except AzureError as exc:
            raise BlobUploadError("Error al subir archivo a Azure Blob") from exc

    def _upload_local(self, blob_path: str, data: bytes) -> str:
        target = self.base_path / self.container / blob_path
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        except OSError as exc:
            raise BlobUploadError("Error al subir archivo a almacenamiento") from exc

        base_url = getattr(
            settings,
            "BLOB_STORAGE_BASE_URL",
            f"https://tsi-blob.local/{self.container}",
        )
        return f"{base_url.rstrip('/')}/{blob_path}"

    def sign_read_url(self, url: str, *, ttl_minutes: int = 15) -> str:
        """Adjunta un SAS token de solo lectura de corta duración a una URL de blob.

        La evidencia fotográfica no puede exponerse sin control de acceso
        (constitution: Additional Constraints). El contenedor es privado por
        defecto, así que sin este token el navegador recibe 403 al pedir la
        URL directamente. El token nunca se persiste, se genera al vuelo en
        cada consulta ya autorizada por el permiso de la vista.
        """
        if not self._should_use_azure():
            return url

        account_name = getattr(settings, "AZURE_ACCOUNT_NAME", "")
        account_key = getattr(settings, "AZURE_ACCOUNT_KEY", "")
        if not account_name or not account_key:
            return url

        parsed = urlparse(url)
        expected_host = f"{account_name}.blob.core.windows.net"
        if parsed.netloc != expected_host:
            return url

        parts = parsed.path.lstrip("/").split("/", 1)
        if len(parts) != 2:
            return url
        container, blob_name = parts

        from azure.storage.blob import BlobSasPermissions, generate_blob_sas

        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(UTC) + timedelta(minutes=ttl_minutes),
        )
        return f"{url}?{sas_token}"

    @staticmethod
    def generate_file_key() -> str:
        return str(uuid.uuid4())
