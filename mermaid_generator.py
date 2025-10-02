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

Use these node types WITHOUT quotes inside brackets:
- Rectangle: A[Process step here]
- Diamond: B{Is this valid}
- Circle: C((Start))
- Rounded: D(Action)

Example:
flowchart TD
    A((Start)) --> B{Is user valid}
    B -->|Yes| C[Show dashboard]
    B -->|No| D[Redirect to login]
    D --> A
    C --> F((End))

Now generate a flowchart for: {description}

CRITICAL RULES:
- NO quotes inside node text: WRONG {{"text"}}, CORRECT {{text}}
- NO special characters like ? ! inside curly braces
- Use simple text only
- Output ONLY raw Mermaid code
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
The code must start with 'gantt' and include 'dateFormat YYYY-MM-DD'.

Example:
gantt
    dateFormat YYYY-MM-DD
    title Project Schedule
    section Phase 1
    Task A :a1, 2025-01-01, 5d
    Task B :a2, after a1, 3d
    section Phase 2
    Task C :a3, after a2, 4d

Now generate a Gantt chart for: {description}

CRITICAL RULES:
- Every task MUST have a unique ID like :a1, :a2, :a3
- Use 'after taskID' or specific dates
- NO spaces in task IDs
- Output ONLY raw Mermaid code
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
    Product A: [0.7, 0.8]

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
    Budget,Marketing,1000
    Budget,Development,2000
    Marketing,Online Ads,600

Now generate a Sankey diagram for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Format is Source,Target,Value
""",

    "XY Chart": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid XY chart code.
The code must start with 'xychart-beta'.

Example:
xychart-beta
    title Sales Trend
    x-axis [Jan, Feb, Mar, Apr, May]
    y-axis "Revenue" 0 --> 100
    line [20, 45, 60, 55, 80]

Now generate an XY chart for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Define title, x-axis, y-axis, and data.
""",

    "Block Diagram": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid block diagram code.
The code must start with 'block-beta'.

Example:
block-beta
    columns 3
    Frontend Backend Database
    API["API Layer"]
    Frontend --> API
    API --> Backend

Now generate a block diagram for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Define columns first.
""",

    "Kanban": """
You are a Mermaid.js v11+ expert. Generate ONLY valid Mermaid Kanban board code.
The code must start with 'kanban'.

Example:
kanban
    Todo
        Task 1
        Task 2
    In Progress
        Task 3

Now generate a Kanban board for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Use column names followed by indented tasks.
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
- Indent with 2 spaces per level.
- DO NOT use ::icon() syntax.
""",
}

def extract_mermaid_code(text: str) -> str:
    """
    Finds and extracts the first valid Mermaid code block from a string.
    """
    text = text.strip()
    
    # Try markdown block first
    match = re.search(r"```(?:mermaid)?\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Find line starting with valid keyword
    lines = text.split('\n')
    valid_starts = (
        "flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram",
        "erDiagram", "journey", "gantt", "pie", "quadrantChart", "mindmap",
        "timeline", "gitGraph", "sankey-beta", "xychart-beta", "block-beta", "kanban"
    )
    
    start_index = -1
    for i, line in enumerate(lines):
        if line.strip().startswith(valid_starts):
            start_index = i
            break
            
    if start_index != -1:
        return '\n'.join(lines[start_index:]).strip()

    raise ValueError(f"Could not find valid Mermaid diagram. Got: {repr(text[:200])}")


def sanitize_mermaid_code(code: str, diagram_type: str) -> str:
    """
    Clean up common Mermaid syntax errors that AIs make.
    """
    # Remove any remaining markdown fences
    code = re.sub(r"```(?:mermaid)?", "", code).strip()
    
    # Fix flowchart issues: remove quotes inside curly braces and brackets
    if diagram_type == "Flowchart":
        # Remove quotes from decision nodes: {"text"} -> {text}
        code = re.sub(r'\{([^}]*)"([^"}]*)"\}', r'{\1\2}', code)
        code = re.sub(r'\{([^}]*)"([^"}]*)"\}', r'{\1\2}', code)  # Run twice for nested
        
        # Remove question marks and special chars from decision nodes
        code = re.sub(r'\{([^}]*)\?\}', r'{\1}', code)
        code = re.sub(r'\{([^}]*)!\}', r'{\1}', code)
    
    # Fix Gantt chart task IDs
    if diagram_type == "Gantt":
        # Replace invalid 'after taskName' with valid IDs
        lines = code.split('\n')
        fixed_lines = []
        task_counter = 1
        
        for line in lines:
            # If it's a task line without proper ID, add one
            if ':' in line and 'section' not in line.lower() and not re.search(r':[a-zA-Z0-9_]+,', line):
                # Add task ID after the colon
                line = re.sub(r':(\s*)((?:after|des|active)\s+[^,]+|[\d-]+)', rf':task{task_counter}, \2', line)
                task_counter += 1
            fixed_lines.append(line)
        
        code = '\n'.join(fixed_lines)
    
    # Remove any trailing explanatory text
    lines = code.split('\n')
    clean_lines = []
    for line in lines:
        # Stop if we hit explanatory text
        if line.strip().lower().startswith(('note:', 'explanation:', 'this diagram', 'the above')):
            break
        clean_lines.append(line)
    
    return '\n'.join(clean_lines).strip()



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
            {"role": "system", "content": "You are a Mermaid.js expert. Output ONLY raw, valid Mermaid code without any extra text or markdown fences."},
            {"role": "user", "content": prompt}
        ]
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            
            # FIX: Properly access the nested structure
            choices = data.get('choices', [])
            if not choices:
                raise ValueError("API returned no choices")
            
            message = choices[0].get('message', {})
            ai_response = message.get('content', '').strip()

            if not ai_response:
                raise ValueError("Empty response from AI model.")

            mermaid_code = extract_mermaid_code(ai_response)
            
            # Sanitize the code to fix common AI mistakes
            mermaid_code = sanitize_mermaid_code(mermaid_code, diagram_type)
            
            return mermaid_code

        except ValueError as e:
            raise ConnectionError(f"AI returned invalid Mermaid code: {e}")
        except Exception as e:
            raise ConnectionError(f"AI API failed: {e}")