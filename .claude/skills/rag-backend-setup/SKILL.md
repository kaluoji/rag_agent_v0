---
name: rag-backend-setup
description: Sets up the Python FastAPI backend environment from scratch. Installs virtual environment, dependencies, and validates configuration. Use for initial project setup or when setting up the backend on a new machine.
---

# RAG Backend Setup

## Instructions

When the user needs to setup the backend:

1. **Create Python virtual environment**
   - Navigate to `backend/` directory
   - Create venv: `python -m venv venv`
   - Activate on Windows: `venv\Scripts\activate`
   - Activate on macOS/Linux: `source venv/bin/activate`

2. **Install dependencies**
   - Run: `pip install -r requirements.txt`
   - Wait for all packages to install
   - Verify critical packages: pydantic-ai, supabase, openai, python-docx, rank-bm25

3. **Setup .env file**
   - Create `backend/.env` with:
     ```
     OPENAI_API_KEY=your_api_key_here
     SUPABASE_URL=your_url_here
     SUPABASE_KEY=your_key_here
     SUPABASE_SERVICE_KEY=your_service_key_here
     LLM_MODEL=gpt-4.1-2025-04-14
     EMBEDDING_MODEL=text-embedding-3-small
     ```
   - Remind user to add actual API keys

4. **Validate installation**
   - Try importing key modules
   - Check Python version (3.10+)
   - Verify all dependencies are installed

5. **Ready for development**
   - Provide command to run backend: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Examples

- "Setup the backend"
- "I want to prepare the development environment"
- "Help me install backend dependencies"
- "Configure the FastAPI backend"
