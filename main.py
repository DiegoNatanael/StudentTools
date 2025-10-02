# main.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional
# IMPORT FOR CORS:
from fastapi.middleware.cors import CORSMiddleware 

# Only import the necessary generator
from mermaid_generator import generate_mermaid_code 

app = FastAPI(title="AI Studio Backend Services")

# --- CORS MIDDLEWARE FIX ---
# This allows your local file/server (e.g., http://127.0.0.1:5500) to communicate with 
# your remote Render backend.
# IMPORTANT: "*" allows ALL origins.
origins = ["*"] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------

# --- Diagram Generator Model (BYOK) ---
class DiagramRequest(BaseModel):
    api_key: str = Field(..., description="The user's external AI API Key.")
    diagram_type: str = Field(..., description="The type of diagram to generate (e.g., Flowchart).")
    description: str = Field(..., description="The user's description of the diagram content.")
    use_icons: bool = Field(False, description="Whether to use icons (Mindmap specific).")


# --- API Endpoints ---

# --- Static Files Serving ---
app.mount("/static", StaticFiles(directory=".", html=True), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serves the main frontend application file (index.html)."""
    try:
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found.")

# --- FINAL CORS FIX: Explicit OPTIONS Route for Preflight ---
@app.options("/api/generate/diagram")
async def options_diagram():
    """
    Handles the CORS preflight request. The CORSMiddleware will attach 
    the necessary headers to this response.
    """
    # Return a minimal 200 OK response
    return Response(status_code=200)

# --- NEW: Mermaid Diagram Generator Endpoint (BYOK) ---
@app.post("/api/generate/diagram", summary="Generate Mermaid.js Code via AI (BYOK)")
async def generate_diagram_endpoint(request: DiagramRequest):
    """
    Receives diagram details AND user's API Key, calls the AI securely, 
    and returns the code.
    """
    if not request.api_key or not request.diagram_type or not request.description:
        raise HTTPException(status_code=400, detail="Missing API Key, diagram type, or description.")
        
    try:
        mermaid_code = await generate_mermaid_code(
            api_key=request.api_key, 
            diagram_type=request.diagram_type, 
            description=request.description
        )
        return {"mermaid_code": mermaid_code}
        
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"AI Service Error: {e}")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Authentication Error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")