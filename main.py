from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List
import docx
from pptx import Presentation
from pptx.util import Inches
import io

# Import the CORS middleware
from fastapi.middleware.cors import CORSMiddleware

# --- Pydantic Models ---
class DocxSection(BaseModel):
    header: str
    paragraphs: List[str]

class DocumentContent(BaseModel):
    title: str
    sections: List[DocxSection]

class PptxSlide(BaseModel):
    title: str
    content: List[str]

class PresentationContent(BaseModel):
    title: str
    slides: List[PptxSlide]

# --- FastAPI App ---
app = FastAPI(title="Document Generation Backend")

# ======================= START: THE FIX =======================
# Define the list of allowed origins.
origins = [
    # Your Production Frontend URL
    "https://student-tools-front-end.vercel.app",
    
    # Keep these for local development and testing
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "null",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ======================= END: THE FIX =========================


# --- API Endpoints (No changes needed below this line) ---

@app.post("/api/generate/docx", summary="Generate a .docx file from JSON")
async def generate_docx(content: DocumentContent):
    try:
        document = docx.Document()
        document.add_heading(content.title, level=0)
        for section in content.sections:
            if section.header:
                document.add_heading(section.header, level=1)
            for p_text in section.paragraphs:
                document.add_paragraph(p_text)
            document.add_paragraph()

        doc_buffer = io.BytesIO()
        document.save(doc_buffer)
        doc_buffer.seek(0)
        headers = {'Content-Disposition': f'attachment; filename="{content.title.replace(" ", "_")}.docx"'}
        return StreamingResponse(doc_buffer, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@app.post("/api/generate/pptx", summary="Generate a .pptx file from JSON")
async def generate_pptx(content: PresentationContent):
    try:
        prs = Presentation()
        title_slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_slide_layout)
        slide.shapes.title.text = content.title

        content_slide_layout = prs.slide_layouts[1]
        for slide_data in content.slides:
            slide = prs.slides.add_slide(content_slide_layout)
            slide.shapes.title.text = slide_data.title
            tf = slide.shapes.body.text_frame
            tf.clear()
            for point in slide_data.content:
                p = tf.add_paragraph()
                p.text = point
                p.level = 0

        ppt_buffer = io.BytesIO()
        prs.save(ppt_buffer)
        ppt_buffer.seek(0)
        headers = {'Content-Disposition': f'attachment; filename="{content.title.replace(" ", "_")}.pptx"'}
        return StreamingResponse(ppt_buffer, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")