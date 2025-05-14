from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from openai import OpenAI
from fastapi_mcp import FastApiMCP
import uvicorn

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