import httpx
import re
from typing import Optional

API_URL = 'https://api.z.ai/api/paas/v4/chat/completions  '
MODEL_NAME = 'glm-4.5-flash'

# --- YOUR ORIGINAL PROMPTS DICT (UNCHANGED) ---
PROMPTS = {
    "Flowchart": """
You are a Mermaid.js expert. Generate ONLY valid Mermaid flowchart code.
Start with 'flowchart TD'.

Valid node shapes:
- Rectangle: A[Process]
- Rounded: B(Action)
- Stadium: C([Start/End])
- Diamond: D{{Decision}}
- Circle: E((Point))

CRITICAL: For diamond decision nodes, use DOUBLE curly braces {{text}}

Example:
flowchart TD
    A([Start]) --> B[Get input]
    B --> C{{Valid}}
    C -->|Yes| D[Process]
    C -->|No| E[Error]
    D --> F([End])
    E --> B

Generate a flowchart for: {description}

Rules:
- Use {{double braces}} for diamonds
- Keep text simple, no special characters
- Output ONLY code, no explanations
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

Relationship syntax:
- One to one: ||--||
- One to many: ||--o{{
- Many to one: }}o--||
- Many to many: }}o--o{{

Attributes syntax:
ENTITY {{
    type attributeName
}}

Example:
erDiagram
    CUSTOMER ||--o{{ ORDER : places
    ORDER ||--|{{ LINE-ITEM : contains
    PRODUCT ||--o{{ LINE-ITEM : "ordered in"
    CUSTOMER {{
        int id
        string name
        string email
    }}
    ORDER {{
        int orderID
        date orderDate
    }}

Now generate an ER diagram for:
{description}

RULES:
- Output ONLY raw Mermaid code. No explanations.
- Use crow's foot notation correctly.
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
# --- END OF YOUR ORIGINAL PROMPTS (UNCHANGED) ---


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
    
    # Fix flowchart issues
    if diagram_type == "Flowchart":
        # Convert single braces {text} to double braces {{text}} for diamonds
        # Match {text} that's not already {{text}}
        code = re.sub(r'(?<!\{)\{([^{}]+)\}(?!\})', r'{{\1}}', code)
        
        # Remove quotes from inside any braces
        code = re.sub(r'\{\{([^}]*)"([^"}]*)"([^}]*)\}\}', r'{{\1\2\3}}', code)
        
        # Remove question marks and exclamation marks
        code = re.sub(r'\{\{([^}]*)[?!]([^}]*)\}\}', r'{{\1\2}}', code)
    
    # Fix Gantt chart task IDs
    if diagram_type == "Gantt":
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


# --- NEW: Prompt Scoring & Refinement System ---
async def score_prompt(api_key: str, user_input: str) -> int:
    """Score prompt quality from 0 (very vague) to 10 (detailed and clear)."""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    payload = {
        'model': MODEL_NAME,
        'messages': [
            {"role": "system", "content": "You are a prompt quality evaluator. Respond ONLY with an integer from 0 to 10."},
            {"role": "user", "content": f"Score this prompt for generating an educational diagram: '{user_input}'"}
        ]
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        score_text = data['choices'][0]['message']['content'].strip()
        try:
            return max(0, min(10, int(re.search(r'\d+', score_text).group())))
        except:
            return 3  # default low score if parsing fails


async def refine_prompt(api_key: str, user_input: str) -> str:
    """Rewrite a vague prompt into a detailed, diagram-ready instruction."""
    refinement_prompt = f"""
You are an expert science educator and diagram designer.
Rewrite the following vague user request into a clear, detailed prompt for generating an educational flowchart or mindmap.

Include:
- A definition of the main concept
- Key stages or components
- For each: what happens, what causes it, where it occurs
- If it's a cycle: state that the last step connects back to the first
- Keep language simple and explanatory

User request: "{user_input}"

Rewritten prompt:
"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    payload = {
        'model': MODEL_NAME,
        'messages': [
            {"role": "system", "content": "You are a helpful prompt engineer."},
            {"role": "user", "content": refinement_prompt}
        ]
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        refined = data['choices'][0]['message']['content'].strip()
        # Clean common AI artifacts
        refined = re.sub(r'^["\s]+|["\s]+$', '', refined)
        return refined


async def generate_mermaid_code(api_key: str, diagram_type: str, description: str) -> str:
    if not api_key:
        raise ValueError("User did not provide an API Key.")

    # --- NEW: Prompt Scoring & Refinement Step ---
    user_input = description.strip()
    score = await score_prompt(api_key, user_input)
    
    if score < 6:  # Threshold for "too naive"
        final_description = await refine_prompt(api_key, user_input)
    else:
        final_description = user_input

    base_prompt = PROMPTS.get(diagram_type)
    if not base_prompt:
        raise ValueError(f"Unsupported diagram type: {diagram_type}")
    
    prompt = base_prompt.format(description=final_description.strip())

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