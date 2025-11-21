# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **RAG-based Regulatory Analysis System** for the financial sector (banking, insurance, telecoms). It's a full-stack application that combines a Python FastAPI backend with a React frontend to provide AI-powered regulatory compliance analysis, document generation, and GAP analysis.

The system uses a **multi-agent architecture** where specialized AI agents coordinate to answer regulatory queries and generate formal reports.

## Common Development Commands

### Backend (Python/FastAPI)

**Setup and running:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Testing:**
```bash
cd backend
pytest
pytest tests/test_integration_complete.py -v --tb=short -x  # Run specific test
```

**Important:** The backend requires a `.env` file in the project root with:
- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_KEY`
- `LLM_MODEL` (default: gpt-4.1-2025-04-14)
- `EMBEDDING_MODEL` (default: text-embedding-3-small)

### Frontend (React/Vite)

**Setup and running:**
```bash
cd frontend
npm install
npm run dev  # Development server on port 5173
npm run build  # Production build
npm run lint  # ESLint check
```

**Environment:** Create `.env` in frontend directory:
```
VITE_API_URL=http://localhost:8000
```

### Docker (Full Stack)

```bash
docker-compose up  # Start both backend and frontend
docker-compose stop
docker-compose rm
docker logs <container_name>
```

## High-Level Architecture

### Multi-Agent System

The backend implements a **coordinator pattern** where an orchestrator agent routes queries to specialized agents:

1. **Orchestrator Agent** (`backend/agents/orchestrator_agent.py`):
   - Entry point for all queries
   - Analyzes user intent and selects appropriate agent(s)
   - Can invoke Query Understanding for complex queries
   - Coordinates multi-step workflows

2. **Query Understanding Agent** (`backend/agents/understanding_query.py`):
   - Analyzes query complexity and intent
   - Expands queries with implicit terms
   - Extracts entities and keywords
   - Decomposes complex queries into sub-queries
   - Returns `QueryInfo` object used by other agents

3. **AI Expert Agent** (`backend/agents/ai_expert_v1.py`):
   - Core compliance/regulatory expert
   - Uses RAG with **hybrid retrieval**: vector search + BM25 + cluster expansion + entity-based search
   - Implements **LLM-based reranking** with configurable chunk limits
   - Has `retrieve_relevant_documentation` tool (executes only once per query via hash-based caching)
   - Can perform GAP analysis via `perform_gap_analysis` tool

4. **Report Agent** (`backend/agents/report_agent.py`):
   - Generates formal Word documents (`.docx`) from templates
   - Uses placeholder replacement: `{{RESUMEN_EJECUTIVO}}`, `{{ALCANCE_ANALISIS}}`, etc.
   - Template location: `backend/agents/templates/Template_Regulatory_Report_AgentIA_v0.docx`
   - Output: `backend/output/reports/`

### RAG Pipeline (Retrieval-Augmented Generation)

The retrieval system in `ai_expert_v1.py` uses a **sophisticated multi-stage approach**:

1. **Parallel Retrieval** (executed simultaneously):
   - Vector similarity search (Supabase pgvector)
   - Cluster-based expansion (finds related chunks from same clusters)
   - BM25 lexical search (exact term matching)
   - Entity-based search (if Query Understanding detected specific entities)

2. **Reranking** (configurable):
   - Uses LLM to evaluate top N chunks (default: 35 for evaluation, 22-28 kept)
   - Different limits for normal queries vs. reports
   - Implements diversity to avoid redundancy

3. **Tool State Management**:
   - Each tool execution is tracked via MD5 hash of query
   - Prevents multiple executions of `retrieve_relevant_documentation`
   - Cached results returned if tool already ran for same query

### Database Schema

Uses **Supabase** (PostgreSQL + pgvector):
- Table: `pd_peru` (or similar regulatory table)
- Columns: `id`, `title`, `summary`, `content`, `metadata`, `embedding` (vector)
- RPC functions: `match_pd_peru` (vector search), `match_pd_peru_by_cluster`
- Filtering: Only returns chunks with `status='vigente'` (active regulations)

### Frontend Architecture

Built with React + Material UI + Zustand for state management:

**Key Pages:**
- `MainPage.jsx` - Main chat interface
- `HistorialPage.jsx` - Query history
- `ConsultaHistorialPage.jsx` - Historical query view
- `NovedadesPage.jsx` - News/updates

**Key Components:**
- `ChatInterface.jsx` - Main chat UI with message history
- `DocxViewer.jsx` / `DocxPreviewPanel.jsx` - Document preview and editing
- `RichTextEditor.jsx` - TipTap-based rich text editor for annotations
- `ThemeProvider.jsx` - Custom theme with dark/light mode support

**Communication:**
- REST API via axios
- WebSocket (`/ws/report`) for real-time report generation updates

## Important Patterns and Conventions

### Agent Communication Flow

1. User query → `OrchestratorAgent.process_query()`
2. Orchestrator creates `OrchestratorPlan` with:
   - `primary_agent`: Which agent to use
   - `requires_query_understanding`: Boolean flag
   - `requires_complex_handling`: For multi-step queries
3. If query understanding enabled: Query expanded/decomposed
4. Primary agent executes with context
5. Results returned as `OrchestrationResult`

### Tool Execution Pattern

Tools use RunContext to access dependencies:
```python
@ai_expert.tool
async def my_tool(ctx: RunContext[AIDeps], param: str) -> str:
    # Access Supabase: ctx.deps.supabase
    # Access OpenAI: ctx.deps.openai_client
    return result
```

### Error Handling

- Global exception handler in `app/main.py` catches all errors
- Structured error responses with traceback in development
- WebSocket disconnections handled gracefully
- Tool failures fall back to default behavior

### Configuration Management

All configuration centralized in `backend/app/core/config.py`:
- Uses `pydantic-settings` for .env loading
- `BASE_DIR` points to project root
- Paths constructed using `os.path.join(BASE_DIR, ...)`

### Document Generation

When generating reports:
1. Orchestrator detects report intent
2. Calls AI Expert to get analysis content
3. Passes analysis to Report Agent
4. Report Agent loads template, generates sections via LLM
5. Replaces placeholders in template
6. Saves to `backend/output/reports/`
7. Returns file path for download

## Key Dependencies

**Backend:**
- `pydantic-ai` - AI agent framework (not pydantic_core)
- `supabase` - Vector database client
- `openai` - OpenAI API (uses AsyncOpenAI)
- `python-docx` - Word document generation
- `rank-bm25` - BM25 lexical search
- `logfire` - Optional logging/monitoring

**Frontend:**
- `@mui/material` - UI components
- `axios` - HTTP client
- `zustand` - State management
- `mammoth` - DOCX preview in browser
- `@tiptap/react` - Rich text editor
- `socket.io-client` - WebSocket client

## Testing Notes

- Integration tests in `backend/tests/`
- Test files should mirror structure of `backend/` directory
- Use `pytest-asyncio` for async tests
- Use `pytest-mockito` for mocking

## Platform-Specific Notes

**Windows Development:**
- The codebase is currently developed on Windows (MINGW64)
- Path separators handled via `os.path.join()`
- Virtual environment activation: `venv\Scripts\activate`

## Important Files to Check When Debugging

**Query not working?**
1. Check `orchestrator_agent.py` - routing logic
2. Check `ai_expert_v1.py` - retrieval and RAG pipeline
3. Check Supabase RPC function `match_pd_peru` - vector search
4. Check `.env` - API keys and configuration

**Report generation failing?**
1. Verify template exists: `backend/agents/templates/Template_Regulatory_Report_AgentIA_v0.docx`
2. Check `report_agent.py` - placeholder mapping
3. Check output directory: `backend/output/reports/` (created automatically)
4. Check DOCX library compatibility

**Frontend not connecting?**
1. Check CORS settings in `app/main.py` (default: localhost:5173)
2. Verify `VITE_API_URL` in frontend `.env`
3. Check WebSocket endpoint: `/ws/report`

## Code Style Guidelines

- Python: Follow PEP 8, use type hints
- Async/await: All agent operations are async
- Logging: Use `logging` module, not print statements
- Error messages: Include context and traceback in development
- Docstrings: Required for all public functions/tools
- Frontend: ESLint configuration in `frontend/.eslintrc.js`
