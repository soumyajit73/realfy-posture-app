import sys
import os

# Add the parent folder to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from pose_detection.pose_detector import process_video



app = FastAPI()

# CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    # Save uploaded video to disk temporarily
    temp_path = f"temp_{file.filename}"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run your posture detection
    results = process_video(temp_path)

    # Remove the temp file
    os.remove(temp_path)

    return {"frame_results": results}
