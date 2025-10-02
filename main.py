# main.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware 

# Only import the necessary generator
from mermaid_generator import generate_mermaid_code 

app = FastAPI(title="AI Studio Backend Services")

# --- CORRECT CORS MIDDLEWARE CONFIGURATION ---

origins = [
    "https://student-tools-front-end.vercel.app",
    "https://www.student-tools-front-end.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,  # ← Must be False with specific origins
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------------------------

# --- Diagram Generator Model (BYOK) ---
class DiagramRequest(BaseModel):
    api_key: str = Field(..., description="The user's external AI API Key.")
    diagram_type: str = Field(..., description="The type of diagram to generate (e.g., Flowchart).")
    description: str = Field(..., description="The user's description of the diagram content.")
    use_icons: bool = Field(False, description="Whether to use icons (Mindmap specific).")


# --- API Endpoints ---

# --- Static Files Serving (optional, since frontend is on Vercel) ---
# You can remove this if you're only using Vercel for frontend
app.mount("/static", StaticFiles(directory=".", html=True), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serves the main frontend application file (index.html)."""
    try:
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found.")

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