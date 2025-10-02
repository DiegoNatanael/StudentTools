# mermaid_generator.py

import httpx
import re
from typing import Optional

API_URL = 'https://api.z.ai/api/paas/v4/chat/completions'
MODEL_NAME = 'glm-4.5-flash'

PROMPTS = {
    "Flowchart": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid flowchart code.
Use 'flowchart TD' as the header.
Example:
flowchart TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]

Now generate a flowchart for:
{description}
""",

    "Sequence Diagram": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid sequence diagram code.
Use 'sequenceDiagram' as the header.
Example:
sequenceDiagram
    participant User
    participant App
    User->>App: Login
    App-->>User: Success

Now generate a sequence diagram for:
{description}
""",

    "Class Diagram": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid class diagram code.
Use 'classDiagram' as the header.
Example:
classDiagram
    class Animal {
        +String name
        +int age
        +makeSound()
    }
    Animal <|-- Dog

Now generate a class diagram for:
{description}
""",

    "State Diagram": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid state diagram code.
Use 'stateDiagram-v2' as the header.
Example:
stateDiagram-v2
    [*] --> Active
    Active --> Inactive : Deactivate
    Inactive --> Active : Activate

Now generate a state diagram for:
{description}
""",

    "ER Diagram": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid ER diagram code.
Use 'erDiagram' as the header.
Example:
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains

Now generate an ER diagram for:
{description}
""",

    "User Journey": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid user journey code.
Use 'journey' as the header.
Example:
journey
    title User Login Flow
    section Authentication
      Enter credentials: 5: User
      Submit form: 3: User
      Validate: 4: System

Now generate a user journey for:
{description}
""",

    "Gantt": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid Gantt chart code.
Use 'gantt' as the header. Include 'dateFormat YYYY-MM-DD'.
Example:
gantt
    dateFormat YYYY-MM-DD
    section Project
    Task A :a1, 2025-10-01, 5d
    Task B :after a1, 3d

Now generate a Gantt chart for:
{description}
""",

    "Pie Chart": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid pie chart code.
Use 'pie' as the header. Labels must be in quotes, followed by colon and number.
Example:
pie
    "Dogs" : 386
    "Cats" : 85
    "Rats" : 15

Now generate a pie chart for:
{description}
""",

    "Quadrant Chart": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid quadrant chart code.
Use 'quadrantChart' as the header.
Example:
quadrantChart
    title Market Analysis
    x-axis Low Reach --> High Reach
    y-axis Low Engagement --> High Engagement
    quadrant-1 We should expand
    quadrant-2 Need to promote
    quadrant-3 Re-evaluate
    quadrant-4 May be improved
    "Product A": [0.7, 0.8]
    "Product B": [0.3, 0.4]

Now generate a quadrant chart for:
{description}
""",

    "Timeline": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid timeline code.
Use 'timeline' as the header.
Example:
timeline
    title Project Timeline
    2025-01 : Kickoff
    2025-02 : Design phase
    2025-03 : Development

Now generate a timeline for:
{description}
""",

    "Sankey": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid Sankey diagram code.
Use 'sankey-beta' as the header.
Example:
sankey-beta
    A --> 10 B
    A --> 20 C
    B --> 5 D
    C --> 15 D

Now generate a Sankey diagram for:
{description}
""",

    "XY Chart": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid XY chart code.
Use 'xychart-beta' as the header.
Example:
xychart-beta
    title Sales vs Profit
    x-axis Sales
    y-axis Profit
    series "2024" [10, 20, 30, 40]
    series "2025" [15, 25, 35, 45]

Now generate an XY chart for:
{description}
""",

    "Block Diagram": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid block diagram code.
Use 'block-beta' as the header.
Example:
block-beta
    Columns 2
    Item A
    Item B
    Item C
    Item D

Now generate a block diagram for:
{description}
""",

    "Kanban": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid Kanban board code.
Use 'kanban' as the header.
Example:
kanban
    section To Do
      Task 1
      Task 2
    section In Progress
      Task 3
    section Done
      Task 4

Now generate a Kanban board for:
{description}
""",

    "GitGraph": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid git graph code.
Use 'gitGraph' as the header.
Example:
gitGraph
    commit
    branch feature
    checkout feature
    commit
    checkout main
    merge feature

Now generate a git graph for:
{description}
""",

    "Mindmap": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid mindmap code.
Use 'mindmap' as the header. DO NOT use ::icon() syntax.
Example:
mindmap
    root((Project))
        Planning
            Goals
            Timeline
        Execution
            Tasks
            Resources

Now generate a mindmap for:
{description}
""",
}

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
    if not api_key:
        raise ValueError("User did not provide an API Key.")

    # Get the correct prompt
    base_prompt = PROMPTS.get(diagram_type)
    if not base_prompt:
        raise ValueError(f"Unsupported diagram type: {diagram_type}")
    
    prompt = base_prompt.format(description=description.strip())

    headers = {
        'Content-Type': 'application/json', 
        'Authorization': f'Bearer {api_key}' 
    }
    payload = {
        'model': MODEL_NAME,
        'messages': [
            {"role": "system", "content": "You output ONLY raw Mermaid code. No explanations, no markdown, no extra text."},
            {"role": "user", "content": prompt}
        ]
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
            raise ConnectionError(f"AI API communication failed: {e}")