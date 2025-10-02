# mermaid_generator.py

import httpx
import re
from typing import Optional

API_URL = 'https://api.z.ai/api/paas/v4/chat/completions'
MODEL_NAME = 'glm-4.5-flash'

PROMPTS = {
    "Flowchart": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid flowchart code.
CRITICAL: The code MUST start with 'flowchart TD'.

Use these node types and syntax precisely:
- Rectangle: A["Process text"]
- Diamond: B{"Decision text"}
- Circle / Start/End: C(("Start or End"))
- Trapezoid / Input: D[/Input text\\]
- Inverse Trapezoid / Output: E[\Output text/]

Example:
flowchart TD
    A(("Start")) --> B{"Is user valid?"}
    B -->|"Yes"| C["Show dashboard"]
    B -->|"No"| D[/Redirect to login page\\]
    D --> A
    C --> F(("End"))

Now generate a complete flowchart for:
{description}

RULES:
- Output ONLY the raw Mermaid code.
- DO NOT include markdown like ```mermaid or explanations.
- Ensure every node has a unique ID (e.g., A, B, C1).
""",

    "Sequence Diagram": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid sequence diagram code.
The code must start with 'sequenceDiagram'.

Example:
sequenceDiagram
    participant User
    participant App
    User->>App: Login Request
    App-->>User: Authentication Success

Now generate a sequence diagram for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Define participants before using them.
""",

    "Class Diagram": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid class diagram code.
The code must start with 'classDiagram'.

Example:
classDiagram
    class Animal {
        +String name
        +makeSound()
    }
    Animal <|-- Dog

Now generate a class diagram for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Use +, -, # for visibility.
""",

    "State Diagram": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid state diagram code.
The code must start with 'stateDiagram-v2'.

Example:
stateDiagram-v2
    [*] --> Active
    Active --> Inactive : Deactivate
    Inactive --> Active : Activate

Now generate a state diagram for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Use [*] for start/end states.
""",

    "ER Diagram": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid ER diagram code.
The code must start with 'erDiagram'.

Example:
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains

Now generate an ER diagram for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Use crow's foot notation.
""",

    "User Journey": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid user journey code.
The code must start with 'journey'.

Example:
journey
    title User Login Flow
    section Authentication
      Enter credentials: 5: User
      Submit form: 3: User

Now generate a user journey for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Include 'title' and 'section' headers.
""",

    "Gantt": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid Gantt chart code.
The code must start with 'gantt'.

Example:
gantt
    dateFormat YYYY-MM-DD
    section Project Planning
    Task A :a1, 2025-10-01, 5d
    Task B :after a1, 3d

Now generate a Gantt chart for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Always include 'dateFormat'.
""",

    "Pie Chart": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid pie chart code.
The code must start with 'pie'.

Example:
pie showData
    title Pets adopted by volunteers
    "Dogs" : 386
    "Cats" : 85

Now generate a pie chart for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Labels must be in double quotes.
""",

    "Quadrant Chart": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid quadrant chart code.
The code must start with 'quadrantChart'.

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

Now generate a quadrant chart for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Define x-axis, y-axis, and all quadrants.
""",

    "Timeline": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid timeline code.
The code must start with 'timeline'.

Example:
timeline
    title Project Timeline
    2025-01 : Kickoff
    2025-02 : Design phase

Now generate a timeline for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Use YYYY-MM or YYYY-MM-DD for dates.
""",

    "Sankey": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid Sankey diagram code.
The code must start with 'sankey-beta'.

Example:
sankey-beta
    A --> 10 B
    A --> 20 C
    B --> 5 D

Now generate a Sankey diagram for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Format is Source --> value Target.
""",

    "XY Chart": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid XY chart code.
The code must start with 'xychart-beta'.

Example:
xychart-beta
    title Sales vs Profit
    x-axis "Sales"
    y-axis "Profit"
    series "2024"
    series "2025"

Now generate an XY chart for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Define title, x-axis, y-axis, and series.
""",

    "Block Diagram": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid block diagram code.
The code must start with 'block-beta'.

Example:
block-beta
    Columns 2
    ItemA
    ItemB
    ItemC

Now generate a block diagram for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Start with 'Columns N'.
""",

    "Kanban": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid Kanban board code.
The code must start with 'kanban'.

Example:
kanban
    section To Do
      Task 1
      Task 2
    section In Progress
      Task 3

Now generate a Kanban board for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Use 'section' headers for columns.
""",

    "GitGraph": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid git graph code.
The code must start with 'gitGraph'.

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

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Use commands: commit, branch, checkout, merge.
""",

    "Mindmap": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid mindmap code.
The code must start with 'mindmap'. DO NOT use ::icon() syntax.

Example:
mindmap
    root((Project))
        Planning
            Goals
            Timeline
        Execution

Now generate a mindmap for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Indent with 4 spaces per level.
- DO NOT use ::icon() syntax.
""",
}

def extract_mermaid_code(text: str) -> str:
    """
    Finds and extracts the first valid Mermaid code block from a string.
    Handles markdown code fences and introductory text from the AI.
    """
    text = text.strip()
    
    # First, try to find a markdown block
    match = re.search(r"```(?:mermaid)?\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # If no markdown, find the first line that starts with a valid keyword
    lines = text.split('\n')
    valid_starts = (
        "flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram",
        "erDiagram", "journey", "gantt", "pie", "quadrantChart", "mindmap",
        "timeline", "gitGraph", "sankey-beta", "xychart-beta", "block-beta", "kanban"
    )
    
    start_index = -1
    for i, line in enumerate(lines):
        # Use strip() to handle potential leading whitespace
        if line.strip().startswith(valid_starts):
            start_index = i
            break
            
    if start_index != -1:
        # Rejoin the lines from the start of the found code
        return '\n'.join(lines[start_index:]).strip()

    # If no valid code is found at all, raise an error.
    raise ValueError(f"Could not find a valid Mermaid diagram in the AI response. Got: {repr(text[:200])}")


async def generate_mermaid_code(api_key: str, diagram_type: str, description: str) -> str:
    if not api_key:
        raise ValueError("User did not provide an API Key.")

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
            {"role": "system", "content": "You are a Mermaid.js expert. You output ONLY raw, valid Mermaid code without any extra text, explanations, or markdown fences."},
            {"role": "user", "content": prompt}
        ]
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            # Ensure we safely access the content, providing a default empty string
            ai_response = data.get('choices', [{}]).get('message', {}).get('content', '')

            if not ai_response.strip():
                raise ValueError("Empty response from AI model.")

            # Use the new, robust extraction function
            return extract_mermaid_code(ai_response)

        except ValueError as e:
            # This catches parsing errors from extract_mermaid_code
            raise ConnectionError(f"AI returned invalid or incomplete Mermaid code. Details: {e}")
        except Exception as e:
            # This catches network errors or other API failures
            raise ConnectionError(f"AI API communication failed: {e}")