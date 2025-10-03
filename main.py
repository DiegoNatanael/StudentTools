from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List
import docx
from pptx import Presentation
from pptx.util import Inches
import io

# --- Pydantic Models: Define the structure we expect from the AI ---

class DocxSection(BaseModel):
    header: str = Field(..., description="The heading of the section.")
    paragraphs: List[str] = Field(..., description="A list of paragraphs in this section.")

class DocumentContent(BaseModel):
    title: str = Field(..., description="The main title of the document.")
    sections: List[DocxSection] = Field(..., description="A list of sections in the document.")

class PptxSlide(BaseModel):
    title: str = Field(..., description="The title of the slide.")
    content: List[str] = Field(..., description="A list of bullet points for the slide content.")

class PresentationContent(BaseModel):
    title: str = Field(..., description="The main title of the presentation (for the title slide).")
    slides: List[PptxSlide] = Field(..., description="A list of content slides.")

# --- FastAPI App ---
app = FastAPI(title="Document Generation Backend")

# --- API Endpoints ---

@app.post("/api/generate/docx", summary="Generate a .docx file from JSON")
async def generate_docx(content: DocumentContent):
    """
    Receives structured JSON content and generates a .docx file in memory.
    """
    try:
        document = docx.Document()
        document.add_heading(content.title, level=0)

        for section in content.sections:
            if section.header:
                document.add_heading(section.header, level=1)
            for p_text in section.paragraphs:
                document.add_paragraph(p_text)
            document.add_paragraph() # Add a little space between sections

        # Save the document to an in-memory buffer
        doc_buffer = io.BytesIO()
        document.save(doc_buffer)
        doc_buffer.seek(0)

        # Define headers for file download
        headers = {
            'Content-Disposition': f'attachment; filename="{content.title.replace(" ", "_")}.docx"'
        }

        # Return the file as a streaming response
        return StreamingResponse(doc_buffer, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers=headers)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while generating the DOCX file: {e}")


@app.post("/api/generate/pptx", summary="Generate a .pptx file from JSON")
async def generate_pptx(content: PresentationContent):
    """
    Receives structured JSON content and generates a .pptx file in memory.
    """
    try:
        prs = Presentation()
        
        # Title slide
        title_slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_slide_layout)
        title = slide.shapes.title
        title.text = content.title

        # Content slides
        content_slide_layout = prs.slide_layouts[1]
        for slide_data in content.slides:
            slide = prs.slides.add_slide(content_slide_layout)
            title = slide.shapes.title
            body = slide.shapes.body
            title.text = slide_data.title
            
            # Add bullet points
            tf = body.text_frame
            tf.clear() # Clear existing text
            for point in slide_data.content:
                p = tf.add_paragraph()
                p.text = point
                p.level = 0

        # Save presentation to an in-memory buffer
        ppt_buffer = io.BytesIO()
        prs.save(ppt_buffer)
        ppt_buffer.seek(0)
        
        headers = {
            'Content-Disposition': f'attachment; filename="{content.title.replace(" ", "_")}.pptx"'
        }

        return StreamingResponse(ppt_buffer, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", headers=headers)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while generating the PPTX file: {e}")