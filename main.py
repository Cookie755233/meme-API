
import shutil

import click

from fuzzywuzzy import fuzz
from rich.console import Console
from rich.table import Table

from meme.database.cloudinary import (
    init_cloudinary,
    upload_image,
    delete_image,
    list_images,
    search_images,
    update_image_metadata
)
from meme.database.metadata import load_metadata, save_metadata
from meme.utils.cli import (
    validate_image_name,
    show_dry_run_message,
    show_confirmation_command,
    validate_upload_args,
    validate_delete_args
)
from meme.utils.paths import get_paths
from meme.utils.generate_metadata import generate_metadata as gen_metadata

console = Console()

@click.group()
def cli_group():
    """Meme management CLI"""
    pass

@cli_group.command()
@click.argument('image_name', required=False)
@click.option('--pending', is_flag=True, help='Upload pending images only')
@click.option('--all', 'upload_all', is_flag=True, help='Re-upload all images')
@click.option('--dryrun', is_flag=True, help='Preview what would happen without making changes')
def upload(image_name, pending, upload_all, dryrun):
    """Upload images to Cloudinary"""
    if not init_cloudinary():
        return

    if not validate_upload_args(image_name, pending, upload_all):
        return

    if dryrun:
        show_dry_run_message()

    app_paths = get_paths()
    meta = load_metadata()

    if image_name:
        # Find image in either pending or uploaded directory
        image_file = None
        for dir_path in [app_paths['pending'], app_paths['uploaded']]:
            for ext in ['.jpg', '.jpeg', '.png', '.gif']:
                potential_file = dir_path / f"{image_name}{ext}"
                if potential_file.exists():
                    image_file = potential_file
                    break
            if image_file:
                break

        if not image_file:
            console.print(f"[red]Error: Image {image_name} not found")
            return

        # Upload single image
        console.print(f"Processing [cyan]{image_name}[/cyan]")
        if dryrun:
            console.print(f"[yellow]Would upload: {image_file}")
            if image_file.parent == app_paths['pending']:
                console.print(f"[yellow]Would move to: {app_paths['uploaded'] / image_file.name}")
        else:
            meme_data = meta['meme_images'].get(image_name, {})
            if upload_image(
                image_file,
                image_name,
                tags=meme_data.get('tags', []),
                title=meme_data.get('title', image_name),
                language=meme_data.get('language', 'en')
            ):
                console.print(f"[green]>> Successfully uploaded {image_name}")
                if image_file.parent == app_paths['pending']:
                    shutil.move(str(image_file), str(app_paths['uploaded'] / image_file.name))

    elif pending or upload_all:
        source_dir = app_paths['pending'] if pending else app_paths['uploaded']
        images = [f for f in source_dir.iterdir() 
                 if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']]
        
        if not images:
            console.print("[yellow]No images found to process")
            return

        for img in images:
            console.print(f"Processing [cyan]{img.stem}[/cyan]")
            if dryrun:
                console.print(f"[yellow]Would upload: {img}")
                if pending:
                    console.print(f"[yellow]Would move to: {app_paths['uploaded'] / img.name}")
            else:
                meme_data = meta['meme_images'].get(img.stem, {})
                if upload_image(
                    img,
                    img.stem,
                    tags=meme_data.get('tags', []),
                    title=meme_data.get('title', img.stem),
                    language=meme_data.get('language', 'en')
                ):
                    if pending:
                        shutil.move(str(img), str(app_paths['uploaded'] / img.name))
                    console.print(f"[green]>> Successfully uploaded {img.stem}")

@cli_group.command()
@click.argument('image_name', required=False)
@click.option('--all', 'delete_all', is_flag=True, help='Delete all images')
@click.option('--confirm', is_flag=True, help='Actually execute the changes (default is dry-run)')
def delete(image_name, delete_all, confirm):
    """Delete images from Cloudinary"""
    if not init_cloudinary():
        return

    if not validate_delete_args(image_name, delete_all):
        return

    if not confirm:
        show_dry_run_message()

    meta = load_metadata()

    if image_name:
        console.print(f"[cyan]Processing {image_name}...")
        if confirm:
            if delete_image(image_name):
                console.print(f"[green]Successfully deleted {image_name}")
        else:
            console.print(f"[yellow]Would delete: {image_name}")
            show_confirmation_command(f"meme delete {image_name} --confirm")

    elif delete_all:
        meme_count = len(meta['meme_images'])
        if confirm:
            with console.status("[cyan]Deleting all images..."):
                for name in meta['meme_images'].keys():
                    delete_image(name)
                console.print(f"[green]Successfully deleted {meme_count} images")
        else:
            console.print(f"[yellow]Would delete {meme_count} images:")
            for name in meta['meme_images'].keys():
                console.print(f"[yellow] • {name}")
            show_confirmation_command("meme delete --all --confirm")

@cli_group.command()
@click.option('--details', is_flag=True, help='Show detailed information')
def list(details):
    """List all memes in Cloudinary"""
    if not init_cloudinary():
        return

    result = list_images(with_metadata=details)
    if not result or not result.get('resources'):
        console.print("[yellow]No memes found in cloud")
        return

    for resource in result['resources']:
        name = resource['public_id'].replace('memes/', '')
        if details:
            tags = resource.get('tags', [])
            context = resource.get('context', {}).get('custom', {})
            
            console.print(f"[cyan]• {name}")
            console.print(f"  [blue]Dimensions: {resource.get('width', 'N/A')}x{resource.get('height', 'N/A')}")
            console.print(f"  [yellow]Tags: {', '.join(tags)}")
            console.print(f"  [magenta]Language: {context.get('language', 'en')}")
            console.print(f"  [green]URL: {resource['secure_url']}")
            console.print()
        else:
            console.print(f"[cyan]• {name}")

@cli_group.command()
@click.argument('keyword', required=True)
@click.option('--threshold', default=60, help='Match threshold (0-100)', type=int)
def search(keyword, threshold):
    """Search memes in Cloudinary by keyword"""
    if not init_cloudinary():
        return
    
    resources = search_images(keyword, threshold)
    if not resources:
        console.print(f"[yellow]No memes found matching '{keyword}'")
        return

    table = Table(title=f"Search Results for '{keyword}'")
    table.add_column("Name", style="cyan")
    table.add_column("Match Score", style="green")
    table.add_column("Tags", style="yellow")
    table.add_column("URL", style="blue")
    
    results = []
    for resource in resources:
        name = resource['public_id'].replace('memes/', '')
        tags = resource.get('tags', [])
        
        score = max([fuzz.partial_ratio(keyword.lower(), name.lower())] +
                   [fuzz.partial_ratio(keyword.lower(), tag.lower()) for tag in tags])
        
        if score >= threshold:
            results.append({
                'name': name,
                'score': score,
                'tags': tags,
                'url': resource['secure_url']
            })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    
    if results:
        for result in results:
            table.add_row(
                result['name'],
                f"{result['score']}%",
                ", ".join(result['tags']),
                result['url']
            )
        console.print(table)
    else:
        console.print(f"[yellow]No memes found matching '{keyword}'")

@cli_group.command(name='meta')
@click.argument('name', required=False)
@click.option('--add', help='Add tags (comma-separated)', type=str)
@click.option('--push', is_flag=True, help='Push local metadata to cloud')
@click.option('--generate', is_flag=True, help='Generate metadata from images')
@click.option('--overwrite', is_flag=True, help='Overwrite existing metadata when generating')
@click.option('--confirm', is_flag=True, help='Actually execute the changes (default is dry-run)')
def manage_metadata(name, add, push, generate, overwrite, confirm):
    """Manage tags and metadata for memes"""
    if not init_cloudinary():
        return

    try:
        if generate:
            if not confirm:
                show_dry_run_message()

            app_paths = get_paths()
            metadata_file = app_paths['static'] / 'meme_metadata.json'
            
            if overwrite and metadata_file.exists():
                if confirm:
                    metadata_file.unlink()
                    console.print("[yellow]Overwrite flag used, deleted existing metadata")
                else:
                    console.print("[yellow]Would delete existing metadata file and regenerate from scratch")

            console.print("[cyan]Analyzing images...")
            
            if confirm:
                image_count = gen_metadata()
                if image_count == 0:
                    console.print("[yellow]No images found in _images directories")
                    return
                console.print(f"[green]Successfully processed {image_count} images")
            else:
                # Preview image count
                app_paths = get_paths()
                pending_count = len([f for f in app_paths['pending'].glob('*')
                                  if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']])
                uploaded_count = len([f for f in app_paths['uploaded'].glob('*')
                                   if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']])
                
                console.print(f"[yellow]Would process {pending_count + uploaded_count} images:")
                console.print(f"[yellow] • {pending_count} from pending directory")
                console.print(f"[yellow] • {uploaded_count} from uploaded directory")
                
                if overwrite:
                    console.print("[yellow]Would regenerate all metadata from scratch")
                else:
                    console.print("[yellow]Would append/update metadata for new images")

                show_confirmation_command(
                    f"meme meta --generate{' --overwrite' if overwrite else ''} --confirm"
                )
            return

        if push:
            resources = list_images(with_metadata=True)
            if not resources:
                return

            meta = load_metadata()
            cloud_files = {r['public_id'].replace('memes/', ''): r for r in resources['resources']}
            
            if not confirm:
                show_dry_run_message()
            
            updated_count = skipped_count = 0
            for meme_name in cloud_files:
                if meme_name in meta['meme_images']:
                    try:
                        meme_data = meta['meme_images'][meme_name]
                        cloud_data = cloud_files[meme_name]
                        
                        cloud_tags = set(cloud_data.get('tags', []))
                        local_tags = set(meme_data['tags'])
                        
                        cloud_context = cloud_data.get('context', {}).get('custom', {})
                        cloud_language = cloud_context.get('language')
                        local_language = meme_data.get('language', 'en')
                        
                        changes_needed = []
                        if cloud_tags != local_tags:
                            changes_needed.append(f"update tags: {', '.join(local_tags)}")
                        if cloud_language != local_language:
                            changes_needed.append(f"update language: {local_language}")
                        
                        if changes_needed:
                            updated_count += 1
                            console.print(f"[cyan]{meme_name}:[/]\n >> {'\n >> '.join(changes_needed)}")
                            
                            if confirm:
                                update_image_metadata(
                                    meme_name,
                                    tags=list(local_tags),
                                    language=local_language
                                )
                        else:
                            skipped_count += 1
                            console.print(f"[yellow]Skipped {meme_name}: already in sync")
                            
                    except Exception as e:
                        console.print(f"[red]Failed to process {meme_name}: {str(e)}")
            
            console.print(f"\n[cyan]{'Metadata push complete:' if confirm else 'Dry run summary:'}")
            console.print(f"[{'green' if confirm else 'yellow'}]• {'Updated' if confirm else 'Would update'} {updated_count} memes")
            console.print(f"[yellow]• Skipped {skipped_count} memes (already in sync)")
            
            if not confirm:
                show_confirmation_command("meme meta --push --confirm")
            return

        if name:
            meta = load_metadata()
            name = name.strip('"').strip("'")
            
            if not validate_image_name(name, meta):
                return

            if add:
                current_tags = meta['meme_images'][name].get('tags', [])
                if not isinstance(current_tags, list):
                    current_tags = []

                tag_set = set(current_tags)
                new_tags = {k.strip() for k in add.split(',') if k.strip()}
                
                if not confirm:
                    show_dry_run_message()
                    console.print(f"[cyan]Would add tags to {name}:")
                    console.print(f"[yellow]>> {', '.join(new_tags)}")
                    show_confirmation_command(f"meme meta {name} --add \"{','.join(new_tags)}\" --confirm")
                else:
                    tag_set.update(new_tags)
                    meta['meme_images'][name]['tags'] = sorted(tag_set)
                    save_metadata(meta)
                    console.print(f"[green]Added tags to {name}: {', '.join(new_tags)}")
                return

            # Display current tags
            console.print(f"[cyan]Current tags for {name}:")
            console.print(f">> {', '.join(sorted(meta['meme_images'][name].get('tags', [])))}")

    except Exception as e:
        console.print(f"[red]Error managing metadata: {str(e)}")

if __name__ == '__main__':
    cli_group() 