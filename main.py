from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List
import docx
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
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
    style: str = "formal"  # New: default to 'formal'

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

        # === STYLE CONFIGURATION ===
        style_config = {
            "formal": {
                "font_name": "Times New Roman",
                "title_size": 20,
                "header_size": 14,
                "body_size": 12,
                "header_color": RGBColor(0, 51, 102),  # Dark blue
                "title_color": RGBColor(0, 51, 102),
                "line_spacing": 1.15,
                "after_paragraph_space": Pt(6),
                "before_paragraph_space": Pt(6),
                "header_underline": True,
            },
            "modern": {
                "font_name": "Calibri",
                "title_size": 18,
                "header_size": 13,
                "body_size": 11,
                "header_color": RGBColor(70, 70, 70),
                "title_color": RGBColor(70, 70, 70),
                "line_spacing": 1.0,
                "after_paragraph_space": Pt(4),
                "before_paragraph_space": Pt(4),
                "header_underline": False,
            },
            "academic": {
                "font_name": "Georgia",
                "title_size": 22,
                "header_size": 16,
                "body_size": 12,
                "header_color": RGBColor(0, 0, 0),
                "title_color": RGBColor(0, 0, 0),
                "line_spacing": 1.5,
                "after_paragraph_space": Pt(12),
                "before_paragraph_space": Pt(12),
                "header_underline": False,
            }
        }

        config = style_config.get(content.style, style_config["formal"])

        # Set default font for entire document
        style = document.styles['Normal']
        font = style.font
        font.name = config["font_name"]
        font.size = Pt(config["body_size"])
        font.color.rgb = RGBColor(0, 0, 0)

        # === ADD TITLE ===
        title = document.add_heading(content.title, level=0)
        title_run = title.runs[0]
        title_run.font.size = Pt(config["title_size"])
        title_run.font.color.rgb = config["title_color"]
        title_run.font.bold = True
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # === ADD SECTIONS ===
        for section in content.sections:
            if section.header:
                header = document.add_heading(section.header, level=1)
                header_run = header.runs[0]
                header_run.font.size = Pt(config["header_size"])
                header_run.font.color.rgb = config["header_color"]
                header_run.font.bold = True
                if config["header_underline"]:
                    header_run.font.underline = True

            for p_text in section.paragraphs:
                p = document.add_paragraph(p_text)
                p.paragraph_format.space_after = config["after_paragraph_space"]
                p.paragraph_format.space_before = config["before_paragraph_space"]
                p.paragraph_format.line_spacing = config["line_spacing"]

            # Add space between sections
            document.add_paragraph()  # empty para for spacing

        # === SET PAGE MARGINS ===
        sections = document.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1.25)
            section.right_margin = Inches(1.25)

        # === SAVE TO BUFFER ===
        doc_buffer = io.BytesIO()
        document.save(doc_buffer)
        doc_buffer.seek(0)
        filename = f"{content.title.replace(' ', '_')}.docx"
        headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
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
