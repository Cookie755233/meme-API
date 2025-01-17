
from dotenv import load_dotenv
load_dotenv()

import os

from pathlib import Path
from rich.console import Console

import cloudinary
import cloudinary.uploader
import cloudinary.api

console = Console()

def init_cloudinary():
    """Initialize Cloudinary configuration from .env"""
    try:

        cloudinary_url = os.getenv('CLOUDINARY_URL')
        if not cloudinary_url:
            console.print("[red]Error: CLOUDINARY_URL not found in .env")
            return False
            
        cloudinary.config(secure=True)
        return True
    except Exception as e:
        console.print(f"[red]Error initializing Cloudinary: {str(e)}")
        return False

def upload_image(file_path, name, tags=None, title=None, language='en'):
    """Upload image to Cloudinary with metadata"""
    try:
        with open(file_path, 'rb') as f:
            result = cloudinary.uploader.upload(
                f,
                public_id=f"memes/{name}",
                tags=tags or []
            )

        # Add contextual metadata
        cloudinary.uploader.add_context(
            f"language={language}|caption={title or name}",
            [f"memes/{name}"]
        )
        return True
    except Exception as e:
        console.print(f"[red]Error uploading {name}: {str(e)}")
        return False

def delete_image(name):
    """Delete image from Cloudinary"""
    try:
        cloudinary.uploader.destroy(f"memes/{name}")
        return True
    except Exception as e:
        console.print(f"[red]Error deleting {name}: {str(e)}")
        return False

def list_images(with_metadata=False):
    """List all images in Cloudinary"""
    try:
        return cloudinary.api.resources(
            type="upload",
            prefix="memes/",
            max_results=500,
            tags=with_metadata,
            context=with_metadata
        )
    except Exception as e:
        console.print(f"[red]Error listing images: {str(e)}")
        return None 

def update_image_metadata(name, tags=None, language=None):
    """Update image metadata in Cloudinary"""
    try:
        if tags is not None:
            cloudinary.uploader.replace_tag(tags, [f"memes/{name}"])
        if language is not None:
            cloudinary.uploader.add_context(f"language={language}", [f"memes/{name}"])
        return True
    except Exception as e:
        console.print(f"[red]Error updating metadata for {name}: {str(e)}")
        return False

def search_images(keyword, threshold=60):
    """Search images in Cloudinary"""
    try:
        result = cloudinary.api.resources(
            type="upload",
            prefix="memes/",
            max_results=500,
            tags=True,
            context=True
        )
        return result['resources']
    except Exception as e:
        console.print(f"[red]Error searching images: {str(e)}")
        return [] 