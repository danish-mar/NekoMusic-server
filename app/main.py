# main.py
import os
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from downloader import download_audio_from_url, DOWNLOAD_DIR
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging
from typing import Dict, List
from datetime import datetime
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nekoserver")

app = FastAPI(title="NekoMusic Server")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Incoming: {request.method} {request.url}")
    response = await call_next(request)
    logger.debug(f"Response: {response.status_code}")
    return response

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(DOWNLOAD_DIR)), name="static")

# Queue system
download_queue: Dict[str, dict] = {}
download_history: List[dict] = []

class DownloadRequest(BaseModel):
    url: str

@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "NekoMusic Server",
        "version": "1.0"
    }

@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return JSONResponse(content={})

@app.post("/download")
async def download_endpoint(req: DownloadRequest, background_tasks: BackgroundTasks):
    """Add download to queue"""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="No url provided")

    job_id = str(uuid.uuid4())
    
    # Add to queue
    download_queue[job_id] = {
        "id": job_id,
        "url": url,
        "status": "queued",
        "progress": 0,
        "title": None,
        "artist": None,
        "filename": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
        "completed_at": None
    }
    
    logger.info(f"Job {job_id} queued: {url}")
    
    # Start download in background
    background_tasks.add_task(process_download, job_id, url)
    
    return JSONResponse({
        "job_id": job_id,
        "status": "queued",
        "message": "Download started"
    })

async def process_download(job_id: str, url: str):
    """Process download in background"""
    try:
        # Update status
        download_queue[job_id]["status"] = "downloading"
        download_queue[job_id]["progress"] = 10
        
        logger.info(f"Job {job_id} downloading...")
        
        # Run download (blocking, so we use thread executor)
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(download_audio_from_url, url)
            filepath, filename = future.result()
        
        # Update with result
        download_queue[job_id]["status"] = "completed"
        download_queue[job_id]["progress"] = 100
        download_queue[job_id]["filename"] = filename
        download_queue[job_id]["file_url"] = f"/static/{filename}"
        download_queue[job_id]["completed_at"] = datetime.now().isoformat()
        
        # Extract title and artist from filename
        if " - " in filename:
            parts = filename.replace(".mp3", "").split(" - ", 1)
            download_queue[job_id]["artist"] = parts[0]
            download_queue[job_id]["title"] = parts[1]
        else:
            download_queue[job_id]["title"] = filename.replace(".mp3", "")
        
        logger.info(f"Job {job_id} completed: {filename}")
        
        # Add to history
        download_history.insert(0, download_queue[job_id].copy())
        if len(download_history) > 50:
            download_history.pop()
        
    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        download_queue[job_id]["status"] = "failed"
        download_queue[job_id]["error"] = str(e)

@app.get("/queue")
async def get_queue():
    """Get current queue status"""
    return {
        "queue": list(download_queue.values()),
        "count": len(download_queue)
    }

@app.get("/queue/{job_id}")
async def get_job_status(job_id: str):
    """Get specific job status"""
    if job_id not in download_queue:
        raise HTTPException(status_code=404, detail="Job not found")
    return download_queue[job_id]

@app.get("/history")
async def get_history():
    """Get download history"""
    return {
        "history": download_history[:20],  # Last 20
        "count": len(download_history)
    }

@app.delete("/queue/{job_id}")
async def cancel_job(job_id: str):
    """Cancel/remove job from queue"""
    if job_id in download_queue:
        del download_queue[job_id]
        return {"status": "cancelled", "job_id": job_id}
    raise HTTPException(status_code=404, detail="Job not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8982, log_level="info")
