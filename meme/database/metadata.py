
import json

from pathlib import Path
from rich.console import Console

console = Console()

def load_metadata():
    """Load metadata from JSON file"""
    try:
        from ..utils.paths import get_paths
        metadata_file = get_paths()['static'] / 'meme_metadata.json'
        
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return {"meme_images": {}}
    except Exception as e:
        console.print(f"[red]Error loading metadata: {str(e)}")
        return {"meme_images": {}}

def save_metadata(metadata):
    """Save metadata to JSON file"""
    try:
        from ..utils.paths import get_paths
        metadata_file = get_paths()['static'] / 'meme_metadata.json'
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4)
        return True
    except Exception as e:
        console.print(f"[red]Error saving metadata: {str(e)}")
        return False 