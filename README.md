# 🎵 NekoMusic Server

FastAPI backend that downloads YouTube audio as clean MP3 files using yt-dlp.

## Features

✅ Queue system for concurrent downloads  
✅ Clean filenames: `Artist - Title.mp3`  
✅ Real-time progress tracking  
✅ RESTful API with Swagger docs  
✅ Docker deployment ready  
✅ Auto-embed metadata & thumbnails  

## Quick Start

### Using Docker (Recommended)

```
# Clone the repo
cd server

# Start the server
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

Server runs at `http://localhost:8982`

### Manual Setup

```
# Install dependencies
pip install -r app/requirements.txt

# Run server
cd app
uvicorn main:app --host 0.0.0.0 --port 8982
```

## API Endpoints

### Health Check
```
GET /
```

### Download Audio
```
POST /download
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=..."
}
```

**Response:**
```
{
  "job_id": "abc-123",
  "status": "queued",
  "message": "Download started"
}
```

### Get Queue Status
```
GET /queue
```

### Get Job Status
```
GET /queue/{job_id}
```

### Get Download History
```
GET /history
```

## Configuration

### docker-compose.yml

```
services:
  nekoserver:
    ports:
      - "8982:8982"
    volumes:
      - /path/to/music:/app/downloads  # Your music folder
    environment:
      - PORT=8982
```

Change the volume mount to your music storage location.

## Project Structure

```
server/
├── app/
│   ├── main.py           # FastAPI app + queue system
│   ├── downloader.py     # yt-dlp wrapper
│   └── requirements.txt  # Python dependencies
├── Dockerfile
└── docker-compose.yml
```

## Tech Stack

- **FastAPI** - Modern Python web framework
- **yt-dlp** - YouTube download engine
- **FFmpeg** - Audio conversion
- **Uvicorn** - ASGI server
- **Docker** - Containerization

## Download Format

Files are saved as:
```
Artist - Title.mp3
```

Examples:
- `Rick Astley - Never Gonna Give You Up.mp3`
- `Lofi Girl - lofi hip hop radio.mp3`

Metadata and thumbnails are auto-embedded.

## Development

```
# Install dependencies
pip install -r app/requirements.txt

# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8982

# API docs
open http://localhost:8982/docs
```

## Requirements

- Python 3.11+
- FFmpeg
- Docker (optional)

## License

MIT

## Author

Built with 🎵 by Denizuh