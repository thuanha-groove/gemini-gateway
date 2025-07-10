import requests
from app.domain.image_models import ImageMetadata, ImageUploader, UploadResponse
from enum import Enum
from typing import Optional, Any

class UploadErrorType(Enum):
    """Upload error type enum"""
    NETWORK_ERROR = "network_error"  # Network request error
    AUTH_ERROR = "auth_error"        # Authentication error
    INVALID_FILE = "invalid_file"    # Invalid file
    SERVER_ERROR = "server_error"    # Server error
    PARSE_ERROR = "parse_error"      # Response parsing error
    UNKNOWN = "unknown"              # Unknown error


class UploadError(Exception):
    """Image upload error exception class"""
    
    def __init__(
        self,
        message: str,
        error_type: UploadErrorType = UploadErrorType.UNKNOWN,
        status_code: Optional[int] = None,
        details: Optional[dict] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initializes the upload error exception
        
        Args:
            message: Error message
            error_type: Error type
            status_code: HTTP status code
            details: Detailed error information
            original_error: Original exception
        """
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.details = details or {}
        self.original_error = original_error
        
        # Build the full error message
        full_message = f"[{error_type.value}] {message}"
        if status_code:
            full_message = f"{full_message} (Status: {status_code})"
        if details:
            full_message = f"{full_message} - Details: {details}"
            
        super().__init__(full_message)
    
    @classmethod
    def from_response(cls, response: Any, message: Optional[str] = None) -> "UploadError":
        """
        Creates an error instance from an HTTP response
        
        Args:
            response: HTTP response object
            message: Custom error message
        """
        try:
            error_data = response.json()
            details = error_data.get("data", {})
            return cls(
                message=message or error_data.get("message", "Unknown error"),
                error_type=UploadErrorType.SERVER_ERROR,
                status_code=response.status_code,
                details=details
            )
        except Exception:
            return cls(
                message=message or "Failed to parse error response",
                error_type=UploadErrorType.PARSE_ERROR,
                status_code=response.status_code
            )


class SmMsUploader(ImageUploader):
    API_URL = "https://sm.ms/api/v2/upload"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def upload(self, file: bytes, filename: str) -> UploadResponse:
        try:
            # Prepare request headers
            headers = {
                "Authorization": f"Basic {self.api_key}"
            }
            
            # Prepare file data
            files = {
                "smfile": (filename, file, "image/png")
            }
            
            # Send the request
            response = requests.post(
                self.API_URL,
                headers=headers,
                files=files
            )
            
            # Check response status
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            # Validate if the upload was successful
            if not result.get("success"):
                raise UploadError(result.get("message", "Upload failed"))
                
            # Convert to a unified format
            data = result["data"]
            image_metadata = ImageMetadata(
                width=data["width"],
                height=data["height"],
                filename=data["filename"],
                size=data["size"],
                url=data["url"],
                delete_url=data["delete"]
            )
            
            return UploadResponse(
                success=True,
                code="success",
                message="Upload success",
                data=image_metadata
            )
            
        except requests.RequestException as e:
            # Handle network request related errors
            raise UploadError(f"Upload request failed: {str(e)}")
        except (KeyError, ValueError) as e:
            # Handle response parsing errors
            raise UploadError(f"Invalid response format: {str(e)}")
        except Exception as e:
            # Handle other unexpected errors
            raise UploadError(f"Upload failed: {str(e)}")
    
    
class QiniuUploader(ImageUploader):
    def __init__(self, access_key: str, secret_key: str):
        self.access_key = access_key
        self.secret_key = secret_key
        
    def upload(self, file: bytes, filename: str) -> UploadResponse:
        # Implement the specific upload logic for Qiniu Cloud
        pass
    
    
class PicGoUploader(ImageUploader):
    """Chevereto API Image Uploader"""
    
    def __init__(self, api_key: str, api_url: str = "https://www.picgo.net/api/1/upload"):
        """
        Initializes the Chevereto uploader
        
        Args:
            api_key: Chevereto API key
            api_url: Chevereto API upload address
        """
        self.api_key = api_key
        self.api_url = api_url
        
    def upload(self, file: bytes, filename: str) -> UploadResponse:
        """
        Uploads an image to the Chevereto service
        
        Args:
            file: Image file binary data
            filename: File name
            
        Returns:
            UploadResponse: The upload response object
            
        Raises:
            UploadError: Thrown when the upload fails
        """
        try:
            # Prepare request headers
            headers = {
                "X-API-Key": self.api_key
            }
            
            # Prepare file data
            files = {
                "source": (filename, file)
            }
            
            # Send the request
            response = requests.post(
                self.api_url,
                headers=headers,
                files=files
            )
            
            # Check response status
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            # Validate if the upload was successful
            if result.get("status_code") != 200:
                error_message = "Upload failed"
                if "error" in result:
                    error_message = result["error"].get("message", error_message)
                raise UploadError(
                    message=error_message,
                    error_type=UploadErrorType.SERVER_ERROR,
                    status_code=result.get("status_code"),
                    details=result.get("error")
                )
                
            # Extract image information from the response
            image_data = result.get("image", {})
            
            # Build image metadata
            image_metadata = ImageMetadata(
                width=image_data.get("width", 0),
                height=image_data.get("height", 0),
                filename=image_data.get("filename", filename),
                size=image_data.get("size", 0),
                url=image_data.get("url", ""),
                delete_url=image_data.get("delete_url", None)
            )
            
            return UploadResponse(
                success=True,
                code="success",
                message=result.get("success", {}).get("message", "Upload success"),
                data=image_metadata
            )
            
        except requests.RequestException as e:
            # Handle network request related errors
            raise UploadError(
                message=f"Upload request failed: {str(e)}",
                error_type=UploadErrorType.NETWORK_ERROR,
                original_error=e
            )
        except (KeyError, ValueError, TypeError) as e:
            # Handle response parsing errors
            raise UploadError(
                message=f"Invalid response format: {str(e)}",
                error_type=UploadErrorType.PARSE_ERROR,
                original_error=e
            )
        except UploadError:
            # Re-throw exceptions that are already of type UploadError
            raise
        except Exception as e:
            # Handle other unexpected errors
            raise UploadError(
                message=f"Upload failed: {str(e)}",
                error_type=UploadErrorType.UNKNOWN,
                original_error=e
            )


class CloudFlareImgBedUploader(ImageUploader):
    """CloudFlare ImgBed Uploader"""

    def __init__(self, auth_code: str, api_url: str, upload_folder: str = ""):
        """
        Initializes the CloudFlare ImgBed uploader
        
        Args:
            auth_code: Authentication code
            api_url: Upload API address
            upload_folder: Upload folder path (optional)
        """
        self.auth_code = auth_code
        self.api_url = api_url
        self.upload_folder = upload_folder

    def upload(self, file: bytes, filename: str) -> UploadResponse:
        """
        Uploads an image to CloudFlare ImgBed
        
        Args:
            file: Image file binary data
            filename: File name
            
        Returns:
            UploadResponse: The upload response object
            
        Raises:
            UploadError: Thrown when the upload fails
        """
        try:
            # Prepare request URL parameters
            params = []
            if self.upload_folder:
                params.append(f"uploadFolder={self.upload_folder}")
            if self.auth_code:
                params.append(f"authCode={self.auth_code}")
            params.append("uploadNameType=origin")

            request_url = f"{self.api_url}?{'&'.join(params)}"

            # Prepare file data
            files = {
                "file": (filename, file)
            }
            
            # Send the request
            response = requests.post(
                request_url,
                files=files
            )
            
            # Check response status
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            # Validate the response format
            if not result or not isinstance(result, list) or len(result) == 0:
                raise UploadError(
                    message="Invalid response format",
                    error_type=UploadErrorType.PARSE_ERROR
                )
                
            # Get the file URL
            file_path = result[0].get("src")
            if not file_path:
                raise UploadError(
                    message="Missing file URL in response",
                    error_type=UploadErrorType.PARSE_ERROR
                )
                
            # Build the full URL (if a relative path is returned)
            base_url = self.api_url.split("/upload")[0]
            full_url = file_path if file_path.startswith(("http://", "https://")) else f"{base_url}{file_path}"
                
            # Build image metadata (Note: CloudFlare-ImgBed does not return all metadata, so some fields have default values)
            image_metadata = ImageMetadata(
                width=0,  # CloudFlare-ImgBed does not return width
                height=0,  # CloudFlare-ImgBed does not return height
                filename=filename,
                size=0,  # CloudFlare-ImgBed does not return size
                url=full_url,
                delete_url=None  # CloudFlare-ImgBed does not return a delete URL
            )
            
            return UploadResponse(
                success=True,
                code="success",
                message="Upload success",
                data=image_metadata
            )
            
        except requests.RequestException as e:
            # Handle network request related errors
            raise UploadError(
                message=f"Upload request failed: {str(e)}",
                error_type=UploadErrorType.NETWORK_ERROR,
                original_error=e
            )
        except (KeyError, ValueError, TypeError, IndexError) as e:
            # Handle response parsing errors
            raise UploadError(
                message=f"Invalid response format: {str(e)}",
                error_type=UploadErrorType.PARSE_ERROR,
                original_error=e
            )
        except UploadError:
            # Re-throw exceptions that are already of type UploadError
            raise
        except Exception as e:
            # Handle other unexpected errors
            raise UploadError(
                message=f"Upload failed: {str(e)}",
                error_type=UploadErrorType.UNKNOWN,
                original_error=e
            )
    
class ImageUploaderFactory:
    @staticmethod
    def create(provider: str, **credentials) -> ImageUploader:
        if provider == "smms":
            return SmMsUploader(credentials["api_key"])
        elif provider == "qiniu":
            return QiniuUploader(
                credentials["access_key"], 
                credentials["secret_key"]
            )
        elif provider == "picgo":
            api_url = credentials.get("api_url", "https://www.picgo.net/api/1/upload")
            return PicGoUploader(credentials["api_key"], api_url)
        elif provider == "cloudflare_imgbed":
            return CloudFlareImgBedUploader(
                credentials["auth_code"],
                credentials["base_url"],
                credentials.get("upload_folder", ""),
            )
        raise ValueError(f"Unknown provider: {provider}")