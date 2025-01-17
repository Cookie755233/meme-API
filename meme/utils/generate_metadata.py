import re
import json
import spacy

from pathlib import Path
from PIL import Image
from rich.console import Console

console = Console()

def extract_keywords(text):
    """Extract keywords from text using spaCy"""
    try:
        # Load English language model
        nlp = spacy.load("en_core_web_sm")
        
        # Clean the text: replace hyphens and underscores with spaces
        clean_text = re.sub(r'[-_]', ' ', text.lower())
        
        # Process the text
        doc = nlp(clean_text)
        
        # Extract keywords (nouns, verbs, and adjectives)
        keywords = set()
        for token in doc:
            # Add base words (lemmas) for relevant parts of speech
            if token.pos_ in ['NOUN', 'VERB', 'ADJ']:
                # Skip common particles and question words
                if token.lemma_ not in {
                    'be', 'are', 'is', 'was', 'were',  # be verbs
                    'why', 'what', 'when', 'where', 'who', 'how',  # question words
                    'the', 'a', 'an',  # articles
                    'this', 'that', 'these', 'those',  # demonstratives
                    'in', 'on', 'at', 'to', 'for', 'of', 'with',  # prepositions
                    'and', 'or', 'but',  # conjunctions
                    'you', 'your', 'my', 'mine', 'their', 'our'  # pronouns
                }:
                    keywords.add(token.lemma_)
            
            # Add the original word if it's different from the lemma and not in stop words
            if token.text != token.lemma_ and token.text not in {
                'are', 'is', 'was', 'were',
                'why', 'what', 'when', 'where', 'who', 'how',
                'the', 'a', 'an',
                'this', 'that', 'these', 'those',
                'in', 'on', 'at', 'to', 'for', 'of', 'with',
                'and', 'or', 'but',
                'you', 'your', 'my', 'mine', 'their', 'our'
            }:
                keywords.add(token.text)
        
        # Add the original words from the filename as well, excluding stop words
        original_words = set(clean_text.split())
        keywords.update({word for word in original_words 
                        if word not in {
                            'are', 'is', 'was', 'were',
                            'why', 'what', 'when', 'where', 'who', 'how',
                            'the', 'a', 'an',
                            'this', 'that', 'these', 'those',
                            'in', 'on', 'at', 'to', 'for', 'of', 'with',
                            'and', 'or', 'but',
                            'you', 'your', 'my', 'mine', 'their', 'our'
                        }})
        
        # Remove common stop words and single characters
        keywords = {k for k in keywords if len(k) > 1}
        
        return sorted(keywords)
    except Exception as e:
        print(f"Warning: Could not extract keywords: {str(e)}")
        return []

def generate_metadata():
    """Generate meme_metadata.json from images in _images directory"""
    
    # Get the root directory (meme-API)
    root_dir = Path(__file__).parent.parent.parent
    images_dir = root_dir / '_images'
    uploaded_dir = images_dir / 'uploaded'
    pending_dir = images_dir / 'pending'
    static_dir = root_dir / 'meme' / 'static'
    
    # Create directories if they don't exist
    uploaded_dir.mkdir(parents=True, exist_ok=True)
    pending_dir.mkdir(parents=True, exist_ok=True)
    
    # Try to load existing metadata
    metadata_file = static_dir / 'meme_metadata.json'
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {"meme_images": {}}
    
    # Process images from both pending and uploaded directories
    image_count = 0
    for directory in [pending_dir, uploaded_dir]:
        for image_file in directory.glob('*'):
            if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                try:
                    with Image.open(image_file) as img:
                        width, height = img.size
                    
                    name = image_file.stem
                    existing_entry = metadata["meme_images"].get(name, {})
                    
                    # Check and update tags
                    existing_tags = existing_entry.get("tags", [])
                    new_tags = extract_keywords(name)
                    
                    if not existing_tags:
                        tags = new_tags
                        console.print(f"[cyan]- {name}:")
                        console.print(f" >> generated tags: {', '.join(tags)}")
                    else:
                        # Add any new extracted tags that don't exist
                        tag_set = set(existing_tags)
                        new_tag_set = set(new_tags)
                        added_tags = new_tag_set - tag_set
                        
                        if added_tags:
                            tag_set.update(added_tags)
                            tags = sorted(tag_set)
                            console.print(f"[cyan]- {name}:")
                            console.print(f" >> added tags: {', '.join(added_tags)}\n")
                        else:
                            tags = existing_tags
                            console.print(f"[yellow]- {name}: no new tags to add")
                    
                    # Create or update entry in metadata
                    metadata["meme_images"][name] = {
                        "file_name": image_file.name,
                        "title": name,
                        "width": width,
                        "height": height,
                        "box_count": existing_entry.get("box_count", 2),
                        "properties": {
                            "type": "image",
                            "format": image_file.suffix[1:],
                            "dimensions": f"{width}x{height}"
                        },
                        "tags": tags,
                        "language": existing_entry.get("language", "en")
                    }
                    image_count += 1
                except Exception as e:
                    console.print(f"[red]Error processing {image_file.name}: {str(e)}")
    
    # Save to meme_metadata.json
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=4)
    
    return image_count

if __name__ == '__main__':
    generate_metadata() 