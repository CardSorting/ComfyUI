"""
Backblaze B2 Storage Module for ComfyUI Modal
S3-compatible storage for generated images
"""

import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BackblazeB2Storage:
    """
    Backblaze B2 storage handler using S3-compatible API
    """
    
    def __init__(self):
        """Initialize B2 storage with environment variables"""
        self.enabled = os.environ.get('USE_BACKBLAZE_B2', 'false').lower() == 'true'
        
        if not self.enabled:
            logger.info("Backblaze B2 storage is disabled")
            return
        
        # Load B2 credentials from environment
        self.endpoint = os.environ.get('B2_ENDPOINT', '')
        self.region = os.environ.get('B2_REGION', '')
        self.bucket = os.environ.get('B2_BUCKET', '')
        self.key_id = os.environ.get('B2_KEY_ID', '')
        self.app_key = os.environ.get('B2_APP_KEY', '')
        self.public_url = os.environ.get('B2_PUBLIC_URL', '')
        
        # Validate configuration
        if not all([self.endpoint, self.bucket, self.key_id, self.app_key]):
            logger.error("Backblaze B2 is enabled but configuration is incomplete")
            self.enabled = False
            return
        
        # Initialize S3 client for B2
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=self.endpoint,
                aws_access_key_id=self.key_id,
                aws_secret_access_key=self.app_key,
                region_name=self.region,
            )
            logger.info(f"✅ Backblaze B2 storage initialized: {self.bucket}")
        except Exception as e:
            logger.error(f"Failed to initialize B2 client: {e}")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if B2 storage is enabled and configured"""
        return self.enabled
    
    def upload_file(
        self, 
        file_path: str, 
        object_name: Optional[str] = None,
        folder: str = "generations",
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Upload a file to Backblaze B2
        
        Args:
            file_path: Path to the file to upload
            object_name: S3 object name. If not specified, file_path basename is used
            folder: Folder/prefix in the bucket (default: "generations")
            metadata: Optional metadata to attach to the file
            
        Returns:
            Dict with upload info including URL, or None if failed
        """
        if not self.enabled:
            logger.warning("B2 upload attempted but storage is not enabled")
            return None
        
        # Determine object name
        if object_name is None:
            object_name = os.path.basename(file_path)
        
        # Add folder prefix and date-based organization
        now = datetime.utcnow()
        date_path = f"{now.year}/{now.month:02d}/{now.day:02d}"
        s3_key = f"{folder}/{date_path}/{object_name}"
        
        # Prepare upload parameters
        extra_args = {
            'ContentType': self._get_content_type(file_path),
            'ContentDisposition': 'inline',
            'CacheControl': 'max-age=604800, public',  # 1 week cache
        }
        
        # Add metadata if provided
        if metadata:
            extra_args['Metadata'] = metadata
        
        try:
            # Upload file
            logger.info(f"📤 Uploading to B2: {s3_key}")
            self.s3_client.upload_file(
                file_path,
                self.bucket,
                s3_key,
                ExtraArgs=extra_args
            )
            
            # Generate public URL
            if self.public_url:
                # Use the friendly B2 public URL
                public_url = f"{self.public_url.rstrip('/')}/{s3_key}"
            else:
                # Fallback to S3-compatible URL format
                public_url = f"{self.endpoint}/{self.bucket}/{s3_key}"
            
            file_size = os.path.getsize(file_path)
            
            logger.info(f"✅ Uploaded to B2: {object_name} ({file_size / 1024:.1f} KB)")
            
            return {
                "status": "success",
                "url": public_url,
                "bucket": self.bucket,
                "key": s3_key,
                "filename": object_name,
                "size": file_size,
                "content_type": extra_args['ContentType']
            }
            
        except ClientError as e:
            logger.error(f"❌ B2 upload failed: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error during B2 upload: {e}")
            return None
    
    def _get_content_type(self, file_path: str) -> str:
        """Determine content type from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        content_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
        }
        
        return content_types.get(ext, 'application/octet-stream')
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from Backblaze B2
        
        Args:
            s3_key: The S3 key/path of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)
            logger.info(f"🗑️  Deleted from B2: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete from B2: {e}")
            return False
    
    def list_files(self, prefix: str = "generations/") -> list:
        """
        List files in B2 bucket with given prefix
        
        Args:
            prefix: S3 prefix to filter files
            
        Returns:
            List of file objects
        """
        if not self.enabled:
            return []
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            
            return response.get('Contents', [])
        except ClientError as e:
            logger.error(f"Failed to list B2 files: {e}")
            return []
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about B2 storage configuration"""
        return {
            "enabled": self.enabled,
            "bucket": self.bucket if self.enabled else None,
            "region": self.region if self.enabled else None,
            "endpoint": self.endpoint if self.enabled else None,
            "public_url": self.public_url if self.enabled else None,
        }

