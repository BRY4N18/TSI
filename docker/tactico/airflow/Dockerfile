# Imagen custom de Airflow para el stack `tactico`: agrega pandas/pyarrow
# (no incluidos en la imagen oficial) requeridos por el staging en Parquet
# del pipeline ETL (ver dags/lib/parquet_io.py).
FROM apache/airflow:2.9.3

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
