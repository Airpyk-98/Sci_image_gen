from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import io
import os
import uuid
import time

# Import libraries
import matplotlib.pyplot as plt
import numpy as np
import scipy
import pandas as pd
import rdkit

app = FastAPI()

# 1. SETUP STORAGE (Matches your Render Disk Mount Path)
IMAGE_STORAGE_PATH = "/var/data/images"
# Ensure the directory exists
os.makedirs(IMAGE_STORAGE_PATH, exist_ok=True)

class CodeRequest(BaseModel):
    code: str

# --- ENDPOINT 1: EXECUTE & SAVE ---
@app.post("/execute-plot")
def execute_plot_code(request: CodeRequest):

    # Define the sandbox environment
    local_scope = {
        "plt": plt, "np": np, "scipy": scipy, "pd": pd, "io": io, "rdkit": rdkit, "image_bytes": None
    }

    try:
        # Execute the generated code
        exec(request.code, {}, local_scope)
        image_bytes = local_scope.get("image_bytes")

        if image_bytes:
            # A. Generate a unique filename
            filename = f"{uuid.uuid4().hex}_{int(time.time())}.png"
            file_path = os.path.join(IMAGE_STORAGE_PATH, filename)

            # B. Save the image to the Render Persistent Disk
            with open(file_path, "wb") as f:
                f.write(image_bytes)

            # C. Create the Direct Public URL
            # I HAVE INSERTED YOUR URL HERE:
            base_url = "https://my-n8n-python-worker.onrender.com"
            direct_url = f"{base_url}/images/{filename}"

            # D. Return the URL in JSON format
            return JSONResponse(content={"url": direct_url}, status_code=200)

        else:
            raise HTTPException(status_code=400, detail="Code ran but 'image_bytes' was None.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution Error: {str(e)}")


# --- ENDPOINT 2: SERVE IMAGE (FOR GOOGLE DOCS) ---
@app.get("/images/{filename}")
def get_image(filename: str):
    file_path = os.path.join(IMAGE_STORAGE_PATH, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")

    # CRITICAL: Return the file natively (No 'Attachment' headers)
    # This allows Google Docs to render it inline.
    return FileResponse(file_path, media_type="image/png")
