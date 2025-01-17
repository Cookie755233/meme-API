
from rich.console import Console
from pathlib import Path

console = Console()

def validate_image_name(name, metadata):
    """Validate image name exists in metadata"""
    if not name or name not in metadata['meme_images']:
        console.print(f"[red]Error: Image '{name}' not found in metadata")
        return False
    return True

def show_dry_run_message():
    """Show dry run message"""
    console.print("[yellow]DRY RUN: Showing what would change[/yellow]\n")

def show_confirmation_command(command):
    """Show command to execute changes"""
    console.print("\n[cyan]To execute these changes, run:")
    console.print(f"[green]{command}") 

def validate_upload_args(image_name, pending, upload_all):
    """Validate upload command arguments"""
    if not any([image_name, pending, upload_all]):
        console.print("[red]Error: Please specify what to upload:")
        console.print("  • Upload single image: [cyan]meme upload <image_name>")
        console.print("  • Upload pending: [cyan]meme upload --pending")
        console.print("  • Upload all: [cyan]meme upload --all")
        return False
    return True

def validate_delete_args(image_name, delete_all):
    """Validate delete command arguments"""
    if not any([image_name, delete_all]):
        console.print("[red]Error: Please specify what to delete:")
        console.print("  • Delete single image: [cyan]meme delete <image_name>")
        console.print("  • Delete all images: [cyan]meme delete --all")
        return False
    return True 