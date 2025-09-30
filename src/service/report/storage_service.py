import boto3
from botocore.exceptions import ClientError
import logging
from datetime import datetime, timezone
import os

# Archivo para futuras mejoras, para manejar los archivos en S3 en almacenamiento

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        self.bucket_name = os.getenv("S3_BUCKET_NAME")

    async def upload_file(self, file_content: bytes, user_rfc: str, operation: str, format_type: str) -> str:
        """
        Sube un archivo a S3 y devuelve la URL.

        Args:
            file_content: Contenido del archivo (bytes).
            user_rfc: RFC del usuario para organizar el archivo.
            operation: Operación que generó el archivo (e.g., predefined_join).
            format_type: Formato del archivo (json, xml, csv, excel, pdf).

        Returns:
            URL del archivo en S3.
        """
        try:
            file_key = f"reports/{user_rfc}/{operation}/{datetime.now(timezone.utc).isoformat()}.{format_type}"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content
            )
            file_url = f"https://{self.bucket_name}.s3.amazonaws.com/{file_key}"
            logger.info(f"Archivo subido a S3: {file_url}")
            return file_url
        except ClientError as e:
            logger.error(f"Error subiendo archivo a S3: {str(e)}")
            raise Exception(f"Failed to upload to S3: {str(e)}")

    async def get_file(self, file_url: str) -> bytes:
        """
        Recupera un archivo de S3.

        Args:
            file_url: URL del archivo en S3.

        Returns:
            Contenido del archivo (bytes).
        """
        try:
            file_key = file_url.replace(f"https://{self.bucket_name}.s3.amazonaws.com/", "")
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
            return response["Body"].read()
        except ClientError as e:
            logger.error(f"Error recuperando archivo de S3: {str(e)}")
            raise Exception(f"Failed to retrieve file from S3: {str(e)}")