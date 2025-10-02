# mermaid_generator.py

import httpx
import re
from typing import Optional

API_URL = 'https://api.z.ai/api/paas/v4/chat/completions'
MODEL_NAME = 'glm-4.5-flash'

PROMPTS = {
    "Flowchart": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid flowchart code.
ALWAYS start with 'flowchart TD' (or 'flowchart LR' if horizontal flow is implied).
Use proper node syntax with double quotes for labels that contain spaces:
- ["Text"] = rectangle (process)
- {"Text"} = diamond (decision)
- (("Text")) = circle (start/stop)
- [/"Text"\\] = trapezoid (manual input)
- [\\"Text"/] = inverted trapezoid (manual output)
- [(("Text"))] = subroutine
- ["Text"] = document
- [("Database")] = cylinder

Example of a complete flowchart:
flowchart TD
    A(("Start")) --> B{"Is user logged in?"}
    B -->|"Yes"| C["Show Dashboard"]
    B -->|"No"| D[/"Enter Credentials"\\]
    D --> E["Validate"]
    E --> B
    C --> F((("End")))

Now generate a flowchart for:
{description}

RULES:
- Output ONLY raw Mermaid code — no markdown, no explanations
- Every node must have an ID (e.g., A, B, Step1)
- Use double quotes around labels if they contain spaces or special characters
- Never output just a single word like 'Decision'
- Always include the 'flowchart TD' header
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

RULES:
- Output ONLY raw Mermaid code
- No markdown, no explanations
- Start with 'sequenceDiagram'
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

RULES:
- Output ONLY raw Mermaid code
- Use UML visibility (+, -, #, ~)
- Include relationships if implied
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

RULES:
- Output ONLY raw Mermaid code
- Use [*] for start, [*] for end
- Transitions use colon syntax: A --> B : label
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

RULES:
- Output ONLY raw Mermaid code
- Use crow's foot notation (||, }|, o{, etc.)
- Entity names in ALL CAPS preferred
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

RULES:
- Output ONLY raw Mermaid code
- Include 'title' and 'section'
- Format: "Task name: score: actor"
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

RULES:
- Output ONLY raw Mermaid code
- Always include 'dateFormat'
- Use IDs (a1, b1) for task references
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

RULES:
- Output ONLY raw Mermaid code
- Labels in double quotes
- Values must be positive numbers
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

RULES:
- Output ONLY raw Mermaid code
- Define x-axis, y-axis, and all 4 quadrants
- Data points as [x, y] with quoted labels
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

RULES:
- Output ONLY raw Mermaid code
- Dates in YYYY-MM or YYYY-MM-DD format
- Use colon to separate date and event
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

RULES:
- Output ONLY raw Mermaid code
- Format: Source --> value Target
- Values must be numbers
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

RULES:
- Output ONLY raw Mermaid code
- Define title, x-axis, y-axis
- Use 'series "Label" [values...]'
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

RULES:
- Output ONLY raw Mermaid code
- Start with 'Columns N' (N = number of columns)
- One item per line
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

RULES:
- Output ONLY raw Mermaid code
- Use 'section SectionName' headers
- Tasks as indented lines under sections
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

RULES:
- Output ONLY raw Mermaid code
- Use commands: commit, branch, checkout, merge
- No quotes or extra syntax
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

RULES:
- Output ONLY raw Mermaid code
- Indent with 4 spaces per level
- DO NOT use ::icon() or any icon syntax
- Use ((root)) for central node if needed
""",
}

def extract_mermaid_code(text: str) -> str:
    text = text.strip()
    
    # Remove markdown code blocks
    if text.startswith("```"):
        lines = text.split("\n")
        in_mermaid = False
        code_lines = []
        for line in lines:
            if line.startswith("```mermaid"):
                in_mermaid = True
                continue
            elif line.startswith("```"):
                if in_mermaid:
                    break
                else:
                    continue
            elif in_mermaid:
                code_lines.append(line)
        if code_lines:
            text = "\n".join(code_lines).strip()
    
    # ✅ CRITICAL: Only accept if it starts with a valid Mermaid keyword
    valid_starts = (
        "flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram",
        "erDiagram", "journey", "gantt", "pie", "quadrantChart", "mindmap",
        "timeline", "gitGraph", "sankey-beta", "xychart-beta", "block-beta", "kanban"
    )
    
    if text and any(text.lstrip().startswith(kw) for kw in valid_starts):
        return text
    
    # ❌ If it's just "Text" or "Decision", reject it
    raise ValueError(f"Invalid Mermaid code: does not start with a valid diagram keyword. Got: {repr(text)}")


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

            # 🔥 LOG THE RAW AI RESPONSE (for debugging)
            print(f"AI RAW RESPONSE for {diagram_type}:")
            print(repr(ai_response))  # This shows quotes, newlines, etc.

            mermaid_code = extract_mermaid_code(ai_response)

            if not mermaid_code:
                raise ValueError("No valid Mermaid code extracted from AI response.")

            return mermaid_code

        except Exception as e:
            # 🔥 Include the raw response in the error
            raise ConnectionError(f"AI API failed. Raw response: {ai_response}. Error: {e}")
            raise ConnectionError(f"AI API communication failed: {e}")