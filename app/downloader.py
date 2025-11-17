# downloader.py
import os
import uuid
from yt_dlp import YoutubeDL
from pathlib import Path
from typing import Tuple
import logging
import re

logger = logging.getLogger("nekoserver")

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(s: str, max_length: int = 150) -> str:
    """
    Sanitize filename while preserving readability.
    Removes problematic characters but keeps spaces, dashes, and common punctuation.
    """
    # Remove invalid filename characters for cross-platform compatibility
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', s)
    # Replace multiple spaces with single space
    s = re.sub(r'\s+', ' ', s)
    # Trim and limit length
    s = s.strip()[:max_length]
    return s


def download_audio_from_url(url: str) -> Tuple[str, str]:
    """
    Downloads audio as mp3 using yt_dlp Python API.
    Filename format: Artist - Title.mp3
    Returns tuple (filepath, filename)
    """
    
    # First, extract info to get the title and uploader
    ydl_opts_info = {
        'quiet': True,
        'no_warnings': True,
    }
    
    with YoutubeDL(ydl_opts_info) as ydl:
        logger.info(f"Extracting info for: {url}")
        info = ydl.extract_info(url, download=False)
        video_title = info.get('title', 'Unknown')
        uploader = info.get('uploader', 'Unknown')
        artist = info.get('artist') or info.get('creator') or uploader
        track = info.get('track') or video_title
        
    logger.info(f"Title: {video_title}")
    logger.info(f"Artist/Channel: {artist}")
    
    # Create clean filename: Artist - Title
    safe_artist = sanitize_filename(artist, max_length=50)
    safe_title = sanitize_filename(track, max_length=80)
    
    # Format: "Artist - Title"
    clean_filename = f"{safe_artist} - {safe_title}"
    
    # Use a temporary name during download, rename after
    temp_id = uuid.uuid4().hex[:8]
    temp_template = str(DOWNLOAD_DIR / f"temp_{temp_id}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": temp_template,
        "quiet": False,
        "no_warnings": False,
        "ignoreerrors": False,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            },
            {
                "key": "FFmpegMetadata",
                "add_metadata": True,
            },
            {
                "key": "EmbedThumbnail",
            },
        ],
        "writethumbnail": True,
        "add_metadata": True,
        "prefer_ffmpeg": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        logger.info(f"Starting download: {clean_filename}")
        ydl.download([url])

    # Find the temp downloaded file
    temp_files = list(DOWNLOAD_DIR.glob(f"temp_{temp_id}*.mp3"))
    
    if not temp_files:
        raise RuntimeError(f"Download failed: no MP3 file produced")

    temp_file = temp_files[0]
    
    # Rename to clean filename
    final_filename = f"{clean_filename}.mp3"
    final_path = DOWNLOAD_DIR / final_filename
    
    # Handle duplicate names
    counter = 1
    while final_path.exists():
        final_filename = f"{clean_filename} ({counter}).mp3"
        final_path = DOWNLOAD_DIR / final_filename
        counter += 1
    
    temp_file.rename(final_path)
    logger.info(f"Renamed to: {final_filename}")

    # Clean up leftover thumbnail files
    for ext in ['.webp', '.jpg', '.png']:
        for thumb in DOWNLOAD_DIR.glob(f"temp_{temp_id}*{ext}"):
            try:
                thumb.unlink()
                logger.debug(f"Cleaned up: {thumb.name}")
            except:
                pass

    return str(final_path), final_filename
