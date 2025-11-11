from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import io

# Import all libraries your agent might use
import matplotlib.pyplot as plt
import numpy as np
import scipy
import pandas as pd
import rdkit # <-- Now available!

app = FastAPI()

# This defines the JSON it expects: {"code": "..."}
class CodeRequest(BaseModel):
    code: str

@app.post("/execute-plot")
def execute_plot_code(request: CodeRequest):
    
    # Create a local "sandbox" for the exec() function
    # We pass in all the libraries your agent can use
    local_scope = {
        "plt": plt,
        "np": np,
        "scipy": scipy,
        "pd": pd,
        "io": io,
        "rdkit": rdkit,
        "image_bytes": None  # This is what we'll capture
    }

    try:
        # Execute the agent's code inside the sandbox
        exec(request.code, {}, local_scope)
        
        # Retrieve the 'image_bytes' variable from the sandbox
        image_bytes = local_scope.get("image_bytes")
        
        if image_bytes:
            # Send the raw bytes back as an image
            return Response(content=image_bytes, media_type="image/png")
        else:
            raise HTTPException(status_code=400, detail="Code did not produce 'image_bytes'.")
    
    except Exception as e:
        # If the agent's code fails, send back a clear error
        return HTTPException(status_code=500, detail=f"Code execution failed: {str(e)}")
