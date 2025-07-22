# -*- coding: utf-8 -*-
import boto3
import os
from src import config
from boto3.session import Config

def upload_to_s3(local_path,  dni="sin_dni"):
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=config.MINIO_ENDPOINT,
            aws_access_key_id=config.MINIO_ACCESS_KEY,
            aws_secret_access_key=config.MINIO_SECRET_KEY,
            region_name='us-east-1', # Ajusta según tu región de MinIO si es diferente
            config=Config(signature_version='s3v4', s3={'addressing_style': 'path'})
        )

        bucket = config.MINIO_BUCKET
        extension = os.path.splitext(local_path)[1] or ".pdf"
        # Asegurarse que DNI no tenga caracteres inválidos para nombres de archivo S3 si es necesario
        # Por ahora, asumimos que el DNI es un identificador simple.
        filename = f"{dni.replace('.', '').replace(' ', '_')}{extension}" # Limpieza básica del DNI para nombre de archivo

        with open(local_path, "rb") as f:
            s3.upload_fileobj(f, bucket, filename)

        print(f" Subido a MinIO: {filename}")
    except Exception as e:
        print(f" Error al subir a MinIO: {e}")
