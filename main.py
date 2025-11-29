from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import io
import os
import uuid  # For unique file names
import time # For unique file names

# Import all libraries your agent might use
import matplotlib.pyplot as plt
import numpy as np
import scipy
import pandas as pd
import rdkit

app = FastAPI()

# ⚠️ CRITICAL: This is the folder path where Render's Persistent Disk will be mounted.
# You MUST configure a Persistent Disk in Render with this Mount Path.
IMAGE_STORAGE_PATH = "/var/data/images"

# Ensure the directory exists when the app starts
os.makedirs(IMAGE_STORAGE_PATH, exist_ok=True)


# This defines the JSON it expects: {"code": "..."}
class CodeRequest(BaseModel):
    code: str


# --- ENDPOINT 1: Executes Code and Returns URL ---
@app.post("/execute-plot")
def execute_plot_code(request: CodeRequest):

    # Create a local "sandbox" for the exec() function
    local_scope = {
        "plt": plt,
        "np": np,
        "scipy": scipy,
        "pd": pd,
        "io": io,
        "rdkit": rdkit,
        "image_bytes": None
    }

    try:
        exec(request.code, {}, local_scope)
        image_bytes = local_scope.get("image_bytes")

        if image_bytes:
            # 1. Generate a unique filename
            unique_filename = f"{uuid.uuid4().hex}-{int(time.time())}.png"
            file_path = os.path.join(IMAGE_STORAGE_PATH, unique_filename)

            # 2. Save the image to the persistent disk
            with open(file_path, "wb") as f:
                f.write(image_bytes)

            # 3. Construct the public download URL
            # Note: You MUST replace YOUR_SERVICE_URL with your actual Render URL
            # The 'https://' is hardcoded here, so be sure to update it later.
            download_url = f"https://YOUR_SERVICE_URL.onrender.com/download/{unique_filename}"

            # 4. Return the URL as a JSON response
            return JSONResponse(
                content={"download_url": download_url},
                status_code=200
            )

        else:
            raise HTTPException(status_code=400, detail="Code did not produce 'image_bytes'.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code execution failed: {str(e)}")


# --- ENDPOINT 2: Serves the Downloaded File ---
@app.get("/download/{filename}")
def get_image_file(filename: str):
    
    file_path = os.path.join(IMAGE_STORAGE_PATH, filename)
    
    # 1. Check if the file exists on the disk
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found or has been deleted.")

    # 2. Return the file using FileResponse
    # The Content-Disposition header forces the browser to download it.
    return FileResponse(
        file_path, 
        media_type="image/png", 
        filename=filename,
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )
    
    # Optional: You may add logic here to delete the file after a short delay 
    # to prevent the disk from filling up, but that requires more complex async tasks.
