from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from openai import OpenAI
from fastapi_mcp import FastApiMCP
import uvicorn
from typing import List, Dict, Any, Optional
import json

# Load environment variables
load_dotenv()

app = FastAPI(title="OpenAI MCP API")

# Initialize OpenAI client

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PromptRequest(BaseModel):
    prompt: str
    model: str = "gpt-3.5-turbo"  # Default model
    temperature: float = 0.7
    max_tokens: int = 1000

@app.post("/mcp")
async def process_prompt(request: PromptRequest):
    try:
        print(request)
        # Call OpenAI API
        response = client.chat.completions.create(
            model=request.model,
            messages=[
                {"role": "user", "content": request.prompt}
            ],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return {
            "response": response.choices[0].message.content,
            "model": request.model,
            "usage": response.usage
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RegulationViolation(BaseModel):
    start_line: int
    end_line: int
    regulation_id: str
    description: str
    severity: str = "medium"

class CheckRegulationsResponse(BaseModel):
    filename: str
    total_lines: int
    violations: List[RegulationViolation]
    total_violations: int

@app.post(
    "/check-regulations",
    response_model=CheckRegulationsResponse,
    summary="Upload code and check it against a set of regulations",
)
async def check_regulations(
    file: UploadFile = File(...),
    regulations: str = Form(...),
) -> CheckRegulationsResponse:
    try:
        # Read & split the file
        content = await file.read()
        file_content = content.decode("utf-8")
        file_lines = file_content.splitlines()
        
        # Parse the JSON string of regulations
        regulations_list: List[Dict[str, str]] = json.loads(regulations)
        
        violations: List[Dict] = []
        for regulation in regulations_list:
            reg_id = regulation.get("id", "unknown")
            reg_description = regulation.get("description", "No description")
            
            prompt = (
                f"Analyze the following code for violations of regulation {reg_id!r}:\n"
                f"{reg_description}\n\n"
                "```python\n"
                f"{file_content}\n"
                "```\n\n"
                "Return ONLY valid JSON in the form:\n"
                '{ "violations": [ '
                '{ "start_line": int, "end_line": int, '
                '"description": str, "severity": "low"|"medium"|"high" } '
                '] }\n'
                "If there are no violations, return: { \"violations\": [] }"
                "Be specific with the lines of code that are violating the regulation - dont just give wide ranges"
            )
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000,
            )
            
            try:
                result = json.loads(response.choices[0].message.content)
                reg_violations = result.get("violations", [])
            except json.JSONDecodeError:
                # fallback if the LLM returns non‑JSON
                reg_violations = [{
                    "start_line": 1,
                    "end_line": len(file_lines),
                    "description": "Error parsing model output; manual review required.",
                    "severity": "medium",
                }]
            
            # annotate with regulation_id
            for v in reg_violations:
                v["regulation_id"] = reg_id
            violations.extend(reg_violations)
        
        # Build the Pydantic response
        return CheckRegulationsResponse(
            filename=file.filename,
            total_lines=len(file_lines),
            violations=[RegulationViolation(**v) for v in violations],
            total_violations=len(violations),
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add the MCP server to your FastAPI app
mcp = FastApiMCP(
    app,
    name="OpenAI MCP API",
    description="MCP server for OpenAI API integration",
    # base_url="http://localhost:8000"
)

# Mount the MCP server to your FastAPI app
mcp.mount()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 