from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from openai import OpenAI
from fastapi_mcp import FastApiMCP
import uvicorn
from typing import List, Dict
import json

# Load environment variables
load_dotenv()

app = FastAPI(title="OpenAI MCP Server")

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

# In-memory storage for regulations
stored_regulations: List[Dict[str, str]] = []

# Models
class Regulation(BaseModel):
    id: str
    description: str

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

@app.post("/add-regulations", summary="Add regulations")
async def add_regulations(regulations: List[Regulation]):
    global stored_regulations
    for regulation in regulations:
        if regulation.id in [reg["id"] for reg in stored_regulations]:
            raise HTTPException(status_code=400, detail=f"Regulation ID {regulation.id} already exists.")
        stored_regulations.append(regulation.dict())
    return {"status": "success", "added_regulations": regulations}

@app.get("/get-regulations", summary="Get the active list of regulations")
async def get_regulations():
    return stored_regulations

@app.delete("/delete-regulations", summary="Delete regulations")
async def delete_regulations(regulation_id: str):
    global stored_regulations
    stored_regulations = [reg for reg in stored_regulations if reg["id"] != regulation_id]
    return {"status": "success", "deleted_regulation_id": regulation_id}

@app.post("/check-violations", response_model=CheckRegulationsResponse)
async def check_violations(file: UploadFile = File(...)) -> CheckRegulationsResponse:
    if not stored_regulations:
        raise HTTPException(status_code=400, detail="No regulations are currently set.")

    try:
        content = await file.read()
        file_content = content.decode("utf-8")
        file_lines = file_content.splitlines()

        violations: List[Dict] = []

        for regulation in stored_regulations:
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
                "Be specific with the lines of code that are violating the regulation - don't just give wide ranges."
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



class LLMCostEstimate(BaseModel):
    start_line: int
    end_line: int
    model: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost: float
    call_type: str
    description: str

class CheckCostResponse(BaseModel):
    filename: str
    total_lines: int
    llm_calls: List[LLMCostEstimate]
    total_calls: int
    total_estimated_cost: float

@app.post(
    "/check-cost",
    response_model=CheckCostResponse,
    summary="Upload code and analyze LLM API calls for cost estimation",
)
async def check_cost(
    file: UploadFile = File(...),
) -> CheckCostResponse:
    try:
        # Read & split the file
        content = await file.read()
        file_content = content.decode("utf-8")
        file_lines = file_content.splitlines()
        
        
        # Model pricing information (USD per 1000 tokens)
        model_pricing = {
            # OpenAI models
            "gpt-4o": {"input": 5.0, "output": 15.0},
            "gpt-4": {"input": 10.0, "output": 30.0},
            "gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "gpt-4-32k": {"input": 20.0, "output": 60.0},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            "text-embedding-ada-002": {"input": 0.1, "output": 0.0},
            
            # Anthropic models
            "claude-3-opus": {"input": 15.0, "output": 75.0},
            "claude-3-sonnet": {"input": 3.0, "output": 15.0},
            "claude-3-haiku": {"input": 0.25, "output": 1.25},
            "claude-2": {"input": 8.0, "output": 24.0},
            "claude-instant": {"input": 1.63, "output": 5.51},
            
            # Default for unknown models
            "default": {"input": 5.0, "output": 15.0}
        }
        
        # Analyze the file for LLM API calls
        prompt = (

            "You are a JSON-only API. Do not include explanations, markdown, or code blocks.\n\n"
            "Analyze the following code to identify all Large Language Model (LLM) API calls. "
            "Return a JSON object only. No prose, comments, or formatting.\n\n"
            "```python\n"
            f"{file_content}\n"
            "```\n\n"
            "For each LLM API call, provide the following information in a JSON object:\n"
            "1. start_line: The line number where the API call starts (integer)\n"
            "2. end_line: The line number where the API call ends (integer)\n"
            "3. model: The LLM model being used (string, e.g., 'gpt-4', 'claude-3')\n"
            "4. estimated_input_tokens: Estimate the number of input tokens (integer)\n"
            "5. estimated_output_tokens: Estimate the number of output tokens (integer)\n"
            "6. call_type: Type of call (e.g., 'chat', 'completion', 'embedding')\n"
            "7. description: Brief description of what the API call is doing\n\n"
            
            "For token estimation:\n"
            "- For chat/completion calls, estimate based on prompt length and context\n"
            "- For RAG applications, assume 4000 tokens of context per call\n"
            "- For embeddings, count only input tokens\n\n"
            
            "Return a JSON object with this structure:\n"
            "{\n"
            "  \"llm_calls\": [\n"
            "    {\n"
            "      \"start_line\": 10,\n"
            "      \"end_line\": 20,\n"
            "      \"model\": \"gpt-4\",\n"
            "      \"estimated_input_tokens\": 2500,\n"
            "      \"estimated_output_tokens\": 500,\n"
            "      \"call_type\": \"chat\",\n"
            "      \"description\": \"Chat completion call to summarize text\"\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "If no LLM API calls are found, return: {\"llm_calls\": []}"
        )
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000,
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            
            llm_calls = result.get("llm_calls", [])
        except json.JSONDecodeError:
            
            # Fallback if the LLM returns non-JSON
            llm_calls = [{
                "start_line": 1,
                "end_line": len(file_lines),
                "model": "unknown",
                "estimated_input_tokens": 0,
                "estimated_output_tokens": 0,
                "call_type": "unknown",
                "description": "Error parsing model output; manual review required."
            }]
        
        # Calculate cost for each LLM call
        total_cost = 0.0
        for call in llm_calls:
            model = call.get("model", "default")
            input_tokens = call.get("estimated_input_tokens", 0)
            output_tokens = call.get("estimated_output_tokens", 0)
            
            # Get pricing for the model
            pricing = model_pricing.get(model, model_pricing["default"])
            
            # Calculate cost
            input_cost = (input_tokens / 1000) * pricing["input"]
            output_cost = (output_tokens / 1000) * pricing["output"]
            total_call_cost = input_cost + output_cost
            
            # Add cost to the call data
            call["estimated_cost"] = round(total_call_cost, 6)
            total_cost += total_call_cost
        
        # Build the Pydantic response
        return CheckCostResponse(
            filename=file.filename,
            total_lines=len(file_lines),
            llm_calls=[LLMCostEstimate(**call) for call in llm_calls],
            total_calls=len(llm_calls),
            total_estimated_cost=round(total_cost, 6)
        )
    
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=str(e))




# Add the MCP server to your FastAPI app
mcp = FastApiMCP(
    app,
    name="OpenAI MCP Demo",
    description="MCP server for OpenAI API integration",
    # base_url="http://localhost:8000"
)

# Mount the MCP server to your FastAPI app
mcp.mount()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
