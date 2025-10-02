# mermaid_generator.py

import httpx
import re
from typing import Optional

API_URL = 'https://api.z.ai/api/paas/v4/chat/completions'
MODEL_NAME = 'glm-4.5-flash'


def build_diagram_prompt(diagram_type: str, description: str) -> str:
    """Instructs the AI model to generate Mermaid.js code."""
    diagram_instructions = {
        'Flowchart': 'Create a flowchart using "graph TD" syntax.',
        'Sequence Diagram': 'Create a sequence diagram using "sequenceDiagram" syntax.',
        'Mindmap': 'Create a mind map using "mindmap" syntax. DO NOT use any ::icon() syntax.',
        'Class Diagram': 'Create a class diagram using "classDiagram" syntax.',
        'State Diagram': 'Create a state diagram using "stateDiagram-v2" syntax.',
        'ER Diagram': 'Create an entity relationship diagram using "erDiagram" syntax.',
        'User Journey': 'Create a user journey diagram using "journey" syntax.',
        'Gantt': 'Create a Gantt chart using "gantt" syntax.',
        'Pie Chart': 'Create a pie chart using "pie" syntax.',
        'Quadrant Chart': 'Create a quadrant chart using "quadrantChart" syntax.',
        'Timeline': 'Create a timeline using "timeline" syntax.',
        'Sankey': 'Create a Sankey diagram using "sankey-beta" syntax.',
        'XY Chart': 'Create an XY chart using "xychart-beta" syntax.',
        'Block Diagram': 'Create a block diagram using "block-beta" syntax.',
        'Kanban': 'Create a Kanban board using "kanban" syntax.',
        'GitGraph': 'Create a git graph using "gitGraph" syntax.',
    }

    instruction = diagram_instructions.get(diagram_type, 'Create a diagram')
    
    return f"""You are a Mermaid.js expert. {instruction}

Based on this description: "{description}"

IMPORTANT: 
- Output ONLY the raw Mermaid.js code
- No markdown code blocks
- No explanations
- Start directly with the diagram type keyword"""

def extract_mermaid_code(text: str) -> str:
    """Extracts raw Mermaid code from a potentially markdown-wrapped response."""
    match = re.search(r"```mermaid\n([\s\S]*?)\n```", text)
    if match:
        return match.group(1).strip()
    
    diagram_keywords = r"^(mindmap|graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|journey|gantt|pie|gitGraph|C4Context|timeline|sankey-beta|xychart-beta|block-beta|packet-beta|kanban|quadrantChart)"
    direct_match = re.search(diagram_keywords + r"[\s\S]*", text)
    return direct_match.group(0).strip() if direct_match else text.strip()


async def generate_mermaid_code(api_key: str, diagram_type: str, description: str) -> str:
    """Calls the AI API to generate Mermaid.js code."""
    if not api_key:
        raise ValueError("User did not provide an API Key.")

    prompt = build_diagram_prompt(diagram_type, description)
    
    headers = {
        'Content-Type': 'application/json', 
        'Authorization': f'Bearer {api_key}' 
    }
    payload = {
        'model': MODEL_NAME,
        'messages': [{'role': 'user', 'content': prompt}]
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            ai_response = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()

            if not ai_response:
                raise ValueError("Empty response from AI model.")

            return extract_mermaid_code(ai_response)

        except Exception as e:
            # Re-raise as a ConnectionError to be caught by the FastAPI endpoint
            raise ConnectionError(f"AI API communication failed: {e}")