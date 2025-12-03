"""
Utility functions for image handling
"""
import base64
from pathlib import Path
from PIL import Image
from typing import Tuple

def encode_image_to_base64(image_path: str | Path) -> str:
    """
    Encode an image file to base64 string
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded string of the image
    """
    image_path = Path(image_path)
    
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def get_image_mime_type(image_path: str | Path) -> str:
    """
    Get the MIME type of an image
    
    Args:
        image_path: Path to the image file
        
    Returns:
        MIME type string (e.g., 'image/png', 'image/jpeg')
    """
    image_path = Path(image_path)
    suffix = image_path.suffix.lower()
    
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    
    return mime_types.get(suffix, 'image/png')

def validate_image(image_path: str | Path) -> Tuple[bool, str]:
    """
    Validate if an image file is valid and readable
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    image_path = Path(image_path)
    
    if not image_path.exists():
        return False, f"Image not found: {image_path}"
    
    try:
        with Image.open(image_path) as img:
            img.verify()
        return True, ""
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"

def get_image_info(image_path: str | Path) -> dict:
    """
    Get basic information about an image
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with image information
    """
    image_path = Path(image_path)
    
    with Image.open(image_path) as img:
        return {
            "format": img.format,
            "size": img.size,
            "mode": img.mode,
            "width": img.width,
            "height": img.height
        }
