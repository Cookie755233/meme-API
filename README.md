# Meme API

A RESTful API for managing and serving memes with Cloudinary integration.

## Features
- Upload memes with tags and metadata
- Search memes by tags using fuzzy matching
- Manage meme metadata (tags, language)
- Cloud storage with Cloudinary

## Setup

### Prerequisites
- Python 3.12+
- Cloudinary account

### Installation
1. Clone the repository
```bash
git clone https://github.com/your-repo/meme-api.git
cd meme-api
```
2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
``` 

4. Configure environment variables
```bash
cp .env.example .env
```
Edit .env with your Cloudinary credentials

### Usage

#### Start the API server
```bash
python app.py
```

Server will run on http://localhost:5001

#### API Endpoints

1. Get all memes 
```bash
GET /api/memes
```

2. Search memes by tags
```bash
GET /api/memes/search?q=keyword&threshold=50
```

3. Upload a meme
```bash
POST /api/memes
```

4. Delete a meme
```bash
DELETE /api/memes/{filename}
```

#### CLI Commands

1. Upload memes
```bash
./meme upload "image-name" # Upload specific image
./meme upload --pending # Upload all pending images
./meme upload --all # Re-upload all images
```

2. Manage tags
```bash
./meme tags "image-name" # View tags
./meme tags "image-name" --add "tag1,tag2" # Add tags
./meme tags --push # Push local tags to cloud
```

3. List and search
```bash
./meme list # List all memes
./meme list --details # List with details
./meme search "keyword" # Search memes
```

### Environment Variables
Required environment variables in `.env`:
- `CLOUDINARY_URL`: Cloudinary connection URL