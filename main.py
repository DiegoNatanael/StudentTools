from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List
import docx
from pptx import Presentation
from pptx.util import Inches
import io
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

# --- CORS Middleware ---
origins = [
    "https://student-tools-front-end.vercel.app",
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

# --- API Endpoints ---

@app.post("/api/generate/docx")
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
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/pptx")
async def generate_pptx(content: PresentationContent):
    try:
        prs = Presentation()
        
        # Title Slide (Layout 0)
        title_slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_slide_layout)
        slide.shapes.title.text = content.title

        # Content Slides (Layout 1)
        content_slide_layout = prs.slide_layouts[1]
        for slide_data in content.slides:
            slide = prs.slides.add_slide(content_slide_layout)
            shapes = slide.shapes
            
            # Set the title of the content slide
            title_shape = shapes.title
            title_shape.text = slide_data.title

            # ======================= START: THE FIX =======================
            # Your research is 100% correct. We access the body placeholder
            # by its index [1], not by a non-existent '.body' attribute.
            body_shape = slide.placeholders[1]
            tf = body_shape.text_frame
            # ======================= END: THE FIX =========================
            
            tf.clear()  # Clear any default text
            for point in slide_data.content:
                p = tf.add_paragraph()
                p.text = point
                p.level = 0  # 0 is the top-level bullet

        # Save the presentation to an in-memory buffer
        ppt_buffer = io.BytesIO()
        prs.save(ppt_buffer)
        ppt_buffer.seek(0)
        
        headers = {
            'Content-Disposition': f'attachment; filename="{content.title.replace(" ", "_")}.pptx"'
        }
        return StreamingResponse(ppt_buffer, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", headers=headers)

    except Exception as e:
        # Pass the specific error message to the frontend for better debugging
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")