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
        config_style = content.style
        
        # Set default font
        style = document.styles['Normal']
        
        # === FORMAL STYLE: Corporate/Business Report ===
        if config_style == "formal":
            style.font.name = "Times New Roman"
            style.font.size = Pt(12)
            
            # Add professional header with border
            title = document.add_heading(content.title, level=0)
            title_run = title.runs[0]
            title_run.font.size = Pt(18)
            title_run.font.color.rgb = RGBColor(0, 51, 102)
            title_run.font.bold = True
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Add horizontal line after title
            p = document.add_paragraph()
            p.paragraph_format.border_top.color = RGBColor(0, 51, 102)
            p.paragraph_format.border_top.width = Pt(2)
            
            for section in content.sections:
                # Section headers with underline
                if section.header:
                    header = document.add_heading(section.header, level=1)
                    header_run = header.runs[0]
                    header_run.font.size = Pt(14)
                    header_run.font.color.rgb = RGBColor(0, 51, 102)
                    header_run.font.bold = True
                    header_run.font.underline = True
                
                # Bullet points for formal sections
                for p_text in section.paragraphs:
                    p = document.add_paragraph(p_text, style='List Bullet')
                    p.paragraph_format.left_indent = Inches(0.25)
                    p.paragraph_format.space_after = Pt(6)
                    p.paragraph_format.line_spacing = 1.15
                
                document.add_paragraph()  # Space between sections
            
            # Set narrow margins
            for section in document.sections:
                section.top_margin = Inches(1)
                section.bottom_margin = Inches(1)
                section.left_margin = Inches(1)
                section.right_margin = Inches(1)
        
        # === ACADEMIC STYLE: Scholarly Paper ===
        elif config_style == "academic":
            style.font.name = "Georgia"
            style.font.size = Pt(12)
            
            # Centered title with larger font
            title = document.add_heading(content.title, level=0)
            title_run = title.runs[0]
            title_run.font.size = Pt(16)
            title_run.font.color.rgb = RGBColor(0, 0, 0)
            title_run.font.bold = True
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            title.paragraph_format.space_after = Pt(24)
            
            # Add author placeholder (common in academic papers)
            author = document.add_paragraph("Academic Research Paper")
            author.alignment = WD_ALIGN_PARAGRAPH.CENTER
            author.paragraph_format.space_after = Pt(24)
            author_run = author.runs[0]
            author_run.font.size = Pt(11)
            author_run.font.italic = True
            
            for section in content.sections:
                # Bold, left-aligned section headers
                if section.header:
                    header = document.add_paragraph(section.header)
                    header_run = header.runs[0]
                    header_run.font.size = Pt(14)
                    header_run.font.bold = True
                    header.paragraph_format.space_before = Pt(18)
                    header.paragraph_format.space_after = Pt(12)
                
                # Justified paragraphs with first-line indent
                for p_text in section.paragraphs:
                    p = document.add_paragraph(p_text)
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    p.paragraph_format.first_line_indent = Inches(0.5)
                    p.paragraph_format.space_after = Pt(12)
                    p.paragraph_format.line_spacing = 2.0  # Double-spaced
            
            # Wide margins (typical for academic papers)
            for section in document.sections:
                section.top_margin = Inches(1)
                section.bottom_margin = Inches(1)
                section.left_margin = Inches(1.5)
                section.right_margin = Inches(1.5)
        
        # === MODERN STYLE: Clean & Minimal ===
        elif config_style == "modern":
            style.font.name = "Calibri"
            style.font.size = Pt(11)
            
            # Large, bold title with colored accent
            title = document.add_heading(content.title, level=0)
            title_run = title.runs[0]
            title_run.font.size = Pt(22)
            title_run.font.color.rgb = RGBColor(41, 128, 185)  # Modern blue
            title_run.font.bold = True
            title.alignment = WD_ALIGN_PARAGRAPH.LEFT
            title.paragraph_format.space_after = Pt(18)
            
            for section in content.sections:
                # Colored section headers with larger spacing
                if section.header:
                    header = document.add_paragraph(section.header)
                    header_run = header.runs[0]
                    header_run.font.size = Pt(15)
                    header_run.font.color.rgb = RGBColor(52, 73, 94)  # Dark gray
                    header_run.font.bold = True
                    header.paragraph_format.space_before = Pt(14)
                    header.paragraph_format.space_after = Pt(8)
                
                # Short paragraphs with minimal spacing
                for p_text in section.paragraphs:
                    p = document.add_paragraph(p_text)
                    p.paragraph_format.space_after = Pt(8)
                    p.paragraph_format.line_spacing = 1.3
                
                document.add_paragraph()  # Minimal section spacing
            
            # Narrow, modern margins
            for section in document.sections:
                section.top_margin = Inches(0.75)
                section.bottom_margin = Inches(0.75)
                section.left_margin = Inches(1)
                section.right_margin = Inches(1)
        
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
