
from pathlib import Path

def get_paths():
    """Get common paths used in the application"""
    root_dir = Path(__file__).parent.parent.parent
    images_dir = root_dir / '_images'
    
    return {
        'root': root_dir,
        'images': images_dir,
        'pending': images_dir / 'pending',
        'uploaded': images_dir / 'uploaded',
        'static': root_dir / 'meme' / 'static'
    } 