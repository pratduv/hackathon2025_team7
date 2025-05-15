## 🚀 Quick Start

### 1. Install Requirements

```bash
pip install -r requirements.txt
```

### 2. Start the MCP Server

Make sure you have the MCP FastAPI server running locally on port `8000`.

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Launch the Streamlit UI

```bash
streamlit run regulation_manager.py
```