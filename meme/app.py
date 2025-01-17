from doctest import debug
import json
import os

import cloudinary
import cloudinary.uploader
import cloudinary.api

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from fuzzywuzzy import fuzz

# Load environment variables
load_dotenv()

cloudinary_url = os.getenv('CLOUDINARY_URL')
if cloudinary_url:
    # Parse cloudinary URL
    parts = cloudinary_url.replace('cloudinary://', '').split('@')
    if len(parts) == 2:
        credentials, cloud_name = parts
        api_key, api_secret = credentials.split(':')
        
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
else:
    print("Warning: CLOUDINARY_URL not found in environment variables")

app = Flask(__name__)
CORS(app)

STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')

@app.route('/api/memes', methods=['GET'])
def get_memes():
    """Get all memes"""
    try:
        # Get all resources from Cloudinary with tags and context
        result = cloudinary.api.resources(
            type="upload",
            prefix="memes/",
            max_results=500,
            tags=True,
            context=True
        )
        
        if not result['resources']:
            return jsonify({'memes': []})

        memes = []
        for resource in result['resources']:
            name = resource['public_id'].replace('memes/', '')
            context = resource.get('context', {}).get('custom', {})
            
            memes.append({
                'name': name,
                'url': resource['secure_url'],
                'width': resource.get('width', 0),
                'height': resource.get('height', 0),
                'tags': resource.get('tags', []),
                'language': context.get('language', 'en'),
                'title': context.get('caption', name)
            })
        
        return jsonify({'memes': memes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/memes/<filename>', methods=['POST'])
def upload_meme(filename):
    """Upload a new meme"""
    try:
        # Get properties from metadata if they exist
        with open(os.path.join(STATIC_DIR, 'meme_metadata.json'), 'r') as f:
            metadata = json.load(f)
        
        meme_properties = metadata['meme_images'].get(filename, {})
        
        # Get the file from request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file.filename:
            return jsonify({'error': 'No file selected'}), 400
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file,
            public_id=f"memes/{filename}",
            tags=['meme']
        )
        
        # Update meme_metadata.json if not already present
        if filename not in metadata['meme_images']:
            metadata['meme_images'][filename] = {
                'file_name': file.filename,
                'width': result['width'],
                'height': result['height'],
                'keywords': meme_properties.get('keywords', []),
                'language': meme_properties.get('language', 'en'),
                'properties': {
                    'type': 'image',
                    'format': file.filename.split('.')[-1],
                    'dimensions': f"{result['width']}x{result['height']}"
                }
            }
            
            with open(os.path.join(STATIC_DIR, 'meme_metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=4)
        
        return jsonify({
            'success': True,
            'url': result['secure_url'],
            'public_id': result['public_id']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/memes/<filename>', methods=['DELETE'])
def delete_meme(filename):
    """Delete a meme"""
    try:
        # Remove from metadata
        with open(os.path.join(STATIC_DIR, 'meme_metadata.json'), 'r') as f:
            metadata = json.load(f)
        
        # Remove all instances of the meme
        for alias, data in list(metadata['meme_images'].items()):
            if alias == filename:
                del metadata['meme_images'][alias]
        
        with open(os.path.join(STATIC_DIR, 'meme_metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=4)
        
        # Delete from Cloudinary
        try:
            cloudinary.uploader.destroy(f"memes/{filename}")
        except Exception as e:
            # If file doesn't exist in Cloudinary, just log the error
            print(f"Warning: Could not delete from Cloudinary: {str(e)}")
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/memes/search', methods=['GET'])
def search_memes():
    """Search memes by matching query against tags using Levenshtein distance"""
    try:
        query = request.args.get('q', '').lower()
        threshold = int(request.args.get('threshold', 75))
        
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400

        # Get all resources from Cloudinary with tags
        result = cloudinary.api.resources(
            type="upload",
            prefix="memes/",
            max_results=500,
            tags=True,
            context=True
        )
        
        if not result['resources']:
            return jsonify({'memes': []})
            

        # Search through memes
        matches = []
        for resource in result['resources']:
            name = resource['public_id'].replace('memes/', '')
            tags = resource.get('tags', [])
            context = resource.get('context', {}).get('custom', {})
            
            # Check each tag for matches
            best_score = 0
            for tag in tags:
                # First check for exact substring match
                if query in tag.lower():
                    best_score = 100
                    break
                # If no exact match, use Levenshtein
                score = fuzz.ratio(query, tag.lower())
                best_score = max(best_score, score)
            
            if best_score >= threshold:
                matches.append({
                    'name': name,
                    'url': resource['secure_url'],
                    'width': resource.get('width', 0),
                    'height': resource.get('height', 0),
                    'tags': tags,
                    'language': context.get('language', 'en'),
                    'title': context.get('caption', name),
                    'score': best_score
                })
        
        # Sort by score
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return jsonify({
            'memes': matches,
            'query': query,
            'threshold': threshold,
            'total_matches': len(matches)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )