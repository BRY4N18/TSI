from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from django.test import RequestFactory

from apps.ventas_crm.authentication import DemoSessionAuthentication
from apps.ventas_crm.demo_tokens import format_iso_expiracion, issue_demo_session_token

pytestmark = pytest.mark.unit


def test_demo_session_authentication_ok():
    # Arrange
    iso = format_iso_expiracion(datetime.now(timezone.utc) + timedelta(minutes=10))
    token = issue_demo_session_token(idprospecto=7, demo_expiracion_iso=iso)
    django_request = RequestFactory().post("/x", HTTP_AUTHORIZATION=f"Bearer {token}")
    # Act
    user, auth = DemoSessionAuthentication().authenticate(django_request)
    # Assert
    assert user.idprospecto == 7
    assert user.is_demo_session is True
    assert auth == token
