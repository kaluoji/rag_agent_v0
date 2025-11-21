---
allowed-tools: Task, Bash, Read, Write, Edit, MultiEdit, TodoWrite
description: Build complete RAG regulatory compliance fullstack application from design specifications using test-driven development
argument-hint: <design-folder-output-path> <app-folder>
---

# Full-Stack RAG Compliance System Implementation from Design Specifications

Build production-ready full-stack RAG regulatory compliance systems from `/design-app` outputs using modern Test-Driven Development (TDD) with comprehensive frontend, backend, and integration testing strategies.

## Core Philosophy

This command demonstrates modern full-stack TDD practices by:

- **Design-First**: All implementation decisions derive from design phase outputs
- **RAG-First**: Prioritize retrieval-augmented generation architecture for regulatory documents
- **Full-Stack-First**: Build complete working system with all components integrated
- **Test-First**: Write tests before code (Red → Green → Verify cycles)
- **Compliance-Driven**: Build audit trails, document versioning, and regulatory reporting from the start
- **Production-Ready**: Include authentication, monitoring, testing, and deployment
- **Multi-Sector**: Design for adaptability across healthcare, finance, manufacturing, and other regulated industries

## Prerequisites

### Required Design Outputs

This command requires design outputs from `/design-app`:

- `.claude/outputs/design/projects/[project-name]/[timestamp]/IMPLEMENTATION_PLAN.md` - Technical roadmap
- `.claude/outputs/design/projects/[project-name]/[timestamp]/MANIFEST.md` - Requirements registry
- `.claude/outputs/design/projects/[project-name]/[timestamp]/COMPLIANCE_FRAMEWORK.md` - Sector-agnostic compliance guidelines
- ui-designer outputs (wireframes, component hierarchy, user flows)
- postgres-rag-architect outputs (database schemas, vector storage, audit trails)
- rag-strategy-researcher outputs (retrieval methodologies, reranking strategies)
- scraping-strategy-researcher outputs (regulatory source monitoring)
- tech-stack-researcher outputs (technology selections, security requirements)
- architecture-designer outputs (system architecture, microservices design)
- integration-researcher outputs (external integrations, API specifications)

### Required Technology Stack

Based on IMPLEMENTATION_PLAN.md and tech-stack-researcher outputs:

**Backend Requirements:**
- Python 3.11+ with pip/poetry
- FastAPI framework
- PostgreSQL 15+ with pgvector extension installed
- Azure OpenAI API access (GPT-4 and text-embedding-3-large)

**Frontend Requirements:**
- Node.js 18+ with npm/yarn
- React.js 18+ with TypeScript
- Next.js 14+ (if specified in design)

**External Services:**
- Browserbase account and API credentials
- Azure cloud account (or alternative from design)

**Development Tools:**
- Docker and Docker Compose
- Git
- pytest (Python testing)
- Playwright (E2E testing)

### Required Agents

This command works with the following Claude Code agents:
- `python-rag-specialist`: Backend Python/FastAPI implementation
- `rag-pipeline-specialist`: RAG retrieval and reranking
- `postgres-specialist`: Database design and optimization
- `node-ts-specialist`: Frontend React/TypeScript
- `stagehand`: DevOps and operational tasks

## Arguments

Parse `$ARGUMENTS` to extract the path to:

- <design-folder-output-path> the design folder containing the design outputs. The path should point to a folder like `.claude/outputs/design/projects/[project-name]/[timestamp]/`

- <app-folder> (optional) the folder that the fullstack application should be built in.

The command will automatically read:

- `MANIFEST.md` - Registry of all design agent outputs with requirements traceability
- `IMPLEMENTATION_PLAN.md` - Unified implementation strategy and technical approach
- `COMPLIANCE_FRAMEWORK.md` - Regulatory compliance guidelines and audit requirements
- Reference all related design agent outputs as indexed by the `MANIFEST.md`
- Check if the `app-folder` is specified. Otherwise, create intelligent folder structure for fullstack application

## Usage Patterns

### Pattern 1: Orchestrated Implementation (Recommended)

For complex RAG compliance systems, use the project-orchestrator:
```bash
/task project-orchestrator "Orchestrate fullstack RAG compliance implementation

Project Context:
- Design Outputs: [design-folder-path]
- Application Folder: [app-folder] (or auto-create)
- Project Type: Banking RAG regulatory compliance system
- Technology Stack: Python FastAPI + React TypeScript + PostgreSQL + pgvector
- Implementation Phases: 0 through 8 (per IMPLEMENTATION_PLAN.md)

Orchestration Protocol:
1. Read design outputs:
   - IMPLEMENTATION_PLAN.md → Complete roadmap
   - MANIFEST.md → Requirements traceability
   - COMPLIANCE_FRAMEWORK.md → Compliance requirements
   - All agent design outputs → Technical specifications

2. Execute Implementation Phases sequentially:
   Phase 0: Setup (stagehand)
   Phase 1: Analysis (orchestrator direct)
   Phase 2: Database (postgres-specialist)
   Phase 2.5: Backend API (python-rag-specialist)
   Phase 3: RAG Pipeline (rag-pipeline-specialist + python-rag-specialist)
   Phase 4: Frontend (node-ts-specialist)
   Phase 5: Scraping (python-rag-specialist + stagehand)
   Phase 6: Compliance (node-ts-specialist + python-rag-specialist)
   Phase 7: Production (stagehand + python-rag-specialist)
   Phase 8: Integration (node-ts-specialist + stagehand)

3. For each phase:
   - Delegate to appropriate specialist agent(s)
   - Provide design context from relevant .md files
   - Ensure TDD cycle (RED → GREEN → VERIFY)
   - Validate integration before advancing
   - Update progress tracker

4. Validation gates:
   - All phase tests must pass
   - Design specifications must be met
   - Integration points must work
   - No blocking issues for next phase

Available Specialist Agents:
- postgres-specialist: Database, pgvector, migrations
- python-rag-specialist: FastAPI, RAG orchestration
- rag-pipeline-specialist: Document processing, retrieval, reranking
- node-ts-specialist: React frontend, UI components
- stagehand: DevOps, infrastructure, operations"
Pattern 2: Direct Execution (For Simple Projects or Manual Control)
For direct implementation without orchestration:
bash# Execute specific phase directly
/implement-fullstack-app [design-path] [app-folder] --phase=2
This pattern allows manual control but requires you to:

Manually coordinate between agents
Track phase dependencies yourself
Validate integration points manually

Recommendation: Use Pattern 1 (Orchestrated) for fullstack RAG systems.
Implementation Phase Specifications
The following phases define WHAT needs to be implemented and HOW to validate it.
The orchestrator uses these specifications to delegate tasks to specialist agents.
Phase 0: Technology Validation & Bootstrap (10-15 min)
Agent: stagehand
Design Inputs: tech-stack-researcher/technology-selections.md
Deliverables:

Verified: Python 3.11+, PostgreSQL 15+, Node 18+, pgvector extension
Created: Project structure (backend/, frontend/, database/, tests/)
Installed: All dependencies from design specs
Configured: Environment variables template

Validation: pytest --collect-only and npm test --version succeed
Orchestrator Delegation Example:
bash/task stagehand "Phase 0: Bootstrap RAG compliance project

Design Context:
- Read: tech-stack-researcher/technology-selections.md
- Extract: Required technologies, versions, dependencies

Tasks:
1. Verify technology stack:
   - Python 3.11+ installed
   - PostgreSQL 15+ with pgvector extension
   - Node.js 18+ with npm
   - Docker available
   
2. Create project structure:
   backend/
   ├── api/
   ├── rag/
   ├── database/
   ├── tests/
   └── requirements.txt
   
   frontend/
   ├── components/
   ├── pages/
   ├── tests/
   └── package.json
   
   database/
   └── migrations/
   
   infrastructure/
   └── docker-compose.yml

3. Install dependencies:
   - Backend: fastapi, uvicorn, sqlalchemy, alembic, psycopg2-binary, openai
   - Frontend: react, typescript, next, playwright

4. Create .env.template with required variables

Validation:
- Run: pytest --collect-only (should not error)
- Run: npm test --version (should show version)
- Verify: All folders created
- Verify: Git initialized with .gitignore"
Phase 1: Design Analysis & Configuration (15-20 min)
Agent: orchestrator (direct analysis)
Design Inputs: ALL design outputs
Deliverables:

Extracted: Complete architecture configuration
Mapped: Design files → Implementation components
Created: Agent assignment plan for phases 2-8

Validation: Architecture config complete, dependencies identified
Orchestrator Actions (you perform these directly):

Read IMPLEMENTATION_PLAN.md and extract phase dependencies
Read MANIFEST.md to understand requirements coverage
Map design outputs to implementation phases:

database-schema.md → Phase 2 (postgres-specialist)
retrieval-methodology.md → Phase 3 (rag-pipeline-specialist)
compliance-wireframes.md → Phase 4 (node-ts-specialist)


Create phase execution plan with validation checkpoints
Extract technology configuration for agent context

Phase 2: Database Foundation (20-25 min)
Agent: postgres-specialist
Design Inputs:

database-schema.md (complete schema)
vector-storage-design.md (pgvector optimization)
audit-trail-specifications.md (compliance logging)

TDD Cycle:
python# 🔴 RED Phase - Tests (postgres-specialist creates these first)
# tests/test_database_schema.py

def test_database_connection():
    """Test PostgreSQL connection established"""
    assert engine.connect() is not None

def test_pgvector_extension_installed():
    """Test pgvector extension is available"""
    result = session.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
    assert result.fetchone() is not None

def test_regulatory_document_schema():
    """Test regulatory_documents table exists with correct columns"""
    assert table_exists('regulatory_documents')
    assert column_exists('regulatory_documents', 'id')
    assert column_exists('regulatory_documents', 'authority')
    assert column_exists('regulatory_documents', 'content')

def test_vector_storage_with_hnsw_index():
    """Test document_chunks table with vector column and HNSW index"""
    assert table_exists('document_chunks')
    assert column_exists('document_chunks', 'embedding')
    assert index_exists('document_chunks_embedding_idx', index_type='hnsw')

def test_audit_trail_triggers():
    """Test audit_logs table and triggers capture user actions"""
    # Insert test record
    # Verify audit_logs captured the action
    assert audit_log_exists_for_action('INSERT', 'regulatory_documents')
Implementation Tasks:

Alembic migration environment setup
All tables per database-schema.md:

users, roles, permissions (authentication)
regulatory_authorities, documents (content)
document_chunks with vector columns (RAG storage)
embeddings table (dimension: 1536)
audit_logs (compliance tracking)


pgvector extension installation
HNSW indexes for vector similarity search
Audit trail triggers for all data modifications
Foreign key relationships and constraints
Helper functions for vector operations

Validation:
bashpytest tests/test_database_schema.py -v  # All tests pass
psql -c "SELECT * FROM pg_extension WHERE extname='vector';"  # Returns row
psql -c "\d document_chunks"  # Shows embedding vector column
Orchestrator Delegation Example:
bash/task postgres-specialist "Phase 2: Implement Database Foundation

Design Context:
Read these files from design outputs:
- database-schema.md → Complete schema definition with all tables
- vector-storage-design.md → pgvector optimization strategies
- audit-trail-specifications.md → Compliance logging requirements

Your Implementation Tasks:
1. Create Alembic migration environment:
   - Initialize: alembic init database/migrations
   - Configure: database connection in alembic.ini
   - Create first migration: alembic revision --autogenerate -m 'initial_schema'

2. Implement all tables from database-schema.md:
   - Authentication: users, roles, permissions
   - Content: regulatory_authorities, documents
   - RAG: document_chunks with vector(1536) column
   - Compliance: audit_logs with triggers

3. Install and configure pgvector:
   - CREATE EXTENSION vector;
   - Add vector columns to document_chunks and embeddings tables
   - Create HNSW indexes for fast similarity search

4. Implement audit trail system:
   - Create audit_logs table
   - Add triggers to capture INSERT/UPDATE/DELETE on critical tables
   - Include user_id, timestamp, action, table_name in logs

5. Add constraints and relationships:
   - Foreign keys between tables
   - Check constraints for data validation
   - Unique constraints where appropriate

TDD Requirement:
- Create tests/test_database_schema.py FIRST (RED phase)
- Implement schema to make tests pass (GREEN phase)
- Validate all tests pass (VERIFY phase)

Success Criteria:
✓ pytest tests/test_database_schema.py -v shows all passing
✓ pgvector extension installed and queryable
✓ All tables exist with correct columns
✓ HNSW indexes created on vector columns
✓ Audit triggers capture user actions
✓ Alembic migrations tracked in alembic_version table

Output Expected:
- database/migrations/ folder with migration files
- tests/test_database_schema.py with comprehensive tests
- All tables operational in PostgreSQL
- Documentation: database/README.md explaining schema"
Phase 2.5: Backend API Foundation (20-25 min)
Agent: python-rag-specialist
Dependencies: Phase 2 complete
Design Inputs:

system-architecture.md (API architecture)
authentication-patterns.md (JWT, OAuth)
api-specifications.md (endpoint definitions)

TDD Cycle:
python# 🔴 RED Phase
# tests/test_api_endpoints.py

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check_endpoint():
    """Test API health endpoint returns 200"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_authentication_required():
    """Test endpoints require authentication"""
    response = client.get("/api/documents")
    assert response.status_code == 401

def test_user_registration():
    """Test user registration flow"""
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "securepass123"
    })
    assert response.status_code == 201

def test_jwt_token_generation():
    """Test JWT token generation on login"""
    # Register user first
    # Login and verify JWT token returned
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "securepass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_document_upload_endpoint():
    """Test document upload API with authentication"""
    token = get_test_token()
    response = client.post(
        "/api/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.pdf", b"PDF content", "application/pdf")}
    )
    assert response.status_code == 201
Implementation Tasks:

FastAPI application setup:

Main app with CORS middleware
Router organization by domain (auth, documents, rag)
Exception handlers for common errors


Authentication system:

JWT token generation and validation
Password hashing with bcrypt
Login/register endpoints
Protected route decorator


Database integration:

SQLAlchemy models matching schema
Database session management
Connection pooling configuration


Basic CRUD endpoints:

User management (create, read, update)
Document management (upload, list, retrieve)
Regulatory authority management


API documentation:

Swagger/OpenAPI automatic generation
Endpoint descriptions and examples


Logging and error handling:

Structured logging with correlation IDs
Error response standardization
Request/response logging for audit



Validation:
bashpytest tests/test_api_endpoints.py -v  # All tests pass
uvicorn backend.main:app --reload  # Server starts
curl http://localhost:8000/health  # Returns {"status": "healthy"}
curl http://localhost:8000/docs  # Swagger UI accessible
Orchestrator Delegation Example:
bash/task python-rag-specialist "Phase 2.5: Implement Backend API Foundation

Design Context:
Read these files from design outputs:
- system-architecture.md → API structure and patterns
- authentication-patterns.md → JWT implementation details
- api-specifications.md → Endpoint definitions

Your Implementation Tasks:
1. Create FastAPI application (backend/main.py):
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   
   app = FastAPI(title='RAG Compliance API')
   app.add_middleware(CORSMiddleware, allow_origins=['*'])

2. Implement authentication (backend/api/auth.py):
   - User registration endpoint: POST /api/auth/register
   - Login endpoint: POST /api/auth/login (returns JWT)
   - Token validation middleware
   - Password hashing with bcrypt

3. Setup database connection (backend/database/connection.py):
   - SQLAlchemy engine with connection pooling
   - Session management with context manager
   - Models matching Phase 2 schema

4. Create CRUD endpoints (backend/api/documents.py):
   - POST /api/documents (upload document)
   - GET /api/documents (list documents)
   - GET /api/documents/{id} (retrieve document)
   - Protected with JWT authentication

5. Add health check (backend/api/health.py):
   - GET /health → Check database connection
   - Return status and timestamp

6. Setup logging (backend/utils/logging.py):
   - Structured logging with JSON format
   - Correlation ID for request tracing
   - Log all API requests and responses

TDD Requirement:
- Write tests/test_api_endpoints.py FIRST (RED phase)
- Implement API to make tests pass (GREEN phase)  
- Start server and validate manually (VERIFY phase)

Success Criteria:
✓ All tests in tests/test_api_endpoints.py pass
✓ Server starts without errors: uvicorn backend.main:app
✓ Health check returns 200: curl localhost:8000/health
✓ Swagger docs accessible: curl localhost:8000/docs
✓ JWT authentication works end-to-end
✓ Database queries execute successfully

Output Expected:
- backend/main.py (FastAPI app)
- backend/api/ (auth, documents, health routers)
- backend/database/connection.py (DB setup)
- tests/test_api_endpoints.py (comprehensive tests)
- backend/README.md (API documentation)"
Phase 3: RAG Pipeline Core Implementation (35-40 min)
Agents: rag-pipeline-specialist, python-rag-specialist
Dependencies: Phase 2.5 complete
Design Inputs:

retrieval-methodology.md (chunking, embedding, retrieval)
reranking-strategies.md (cross-encoder, scoring)
hybrid-search-design.md (vector+keyword+metadata fusion)

Sub-Phase 3.1: Document Processing (15 min)
Agent: rag-pipeline-specialist
TDD Cycle:
python# 🔴 RED Phase
# tests/test_document_processing.py

def test_pdf_parsing():
    """Test PDF document parsing extracts text correctly"""
    doc = load_test_document("test_regulation.pdf")
    processor = DocumentProcessor()
    parsed = processor.parse(doc)
    assert parsed.text is not None
    assert len(parsed.text) > 0
    assert parsed.metadata['format'] == 'pdf'

def test_hierarchical_chunking():
    """Test chunking strategy from retrieval-methodology.md"""
    text = load_long_regulatory_text()  # 50+ pages
    chunker = HierarchicalChunker(
        min_chunk_size=200,
        max_chunk_size=1000,
        overlap=100
    )
    chunks = chunker.chunk(text)
    assert len(chunks) > 0
    assert all(200 <= len(c.text) <= 1000 for c in chunks)
    assert chunks[1].text[:100] == chunks[0].text[-100:]  # Overlap verified

def test_metadata_extraction():
    """Test regulatory metadata extraction"""
    doc = load_test_document("eba_guideline.pdf")
    metadata = extract_metadata(doc)
    assert metadata['authority'] == 'EBA'
    assert metadata['document_type'] in ['guideline', 'regulation', 'directive']
    assert 'effective_date' in metadata
    assert 'title' in metadata
Implementation Tasks:

Document parsers supporting PDF, HTML, XML
Hierarchical chunking algorithm:

Adaptive sizing based on content structure
Semantic boundary detection (section headers, paragraphs)
Configurable overlap for context preservation


Metadata extraction:

Authority identification
Document type classification
Date extraction (publication, effective dates)
Title and section structure


Text cleaning and normalization
Document structure preservation

Deliverables: DocumentProcessor, HierarchicalChunker, MetadataExtractor classes
Validation: All tests in tests/test_document_processing.py pass
Sub-Phase 3.2: Embeddings & Vector Storage (10 min)
Agent: python-rag-specialist
TDD Cycle:
python# 🔴 RED Phase
# tests/test_embeddings.py

def test_azure_openai_embedding():
    """Test Azure OpenAI embedding generation"""
    generator = EmbeddingGenerator(model="text-embedding-3-large")
    text = "Test regulatory text about capital requirements"
    embedding = generator.generate(text)
    assert len(embedding) == 1536  # Correct dimensions
    assert all(isinstance(x, float) for x in embedding)
    assert -1.0 <= embedding[0] <= 1.0  # Normalized values

def test_batch_embedding_generation():
    """Test batch embedding with rate limiting"""
    generator = EmbeddingGenerator()
    texts = ["Text 1", "Text 2", "Text 3"]
    embeddings = generator.generate_batch(texts, batch_size=2)
    assert len(embeddings) == 3
    assert all(len(e) == 1536 for e in embeddings)

def test_vector_storage():
    """Test pgvector storage and retrieval"""
    store = VectorStore()
    embedding = [0.1] * 1536
    chunk_id = store.store_embedding(
        chunk_id="test-123",
        embedding=embedding,
        metadata={"authority": "EBA", "document_id": "doc-1"}
    )
    assert chunk_id is not None
    
    # Verify stored
    retrieved = store.get_embedding("test-123")
    assert retrieved is not None
    assert len(retrieved) == 1536

def test_similarity_search():
    """Test vector similarity search with pgvector"""
    store = VectorStore()
    query_embedding = [0.1] * 1536
    results = store.similarity_search(
        query_embedding,
        top_k=10,
        filter={"authority": "EBA"}
    )
    assert len(results) <= 10
    assert all(r.similarity_score > 0 for r in results)
    assert results[0].similarity_score >= results[-1].similarity_score  # Ordered
Implementation Tasks:

Azure OpenAI client setup:

API key management
Model configuration (text-embedding-3-large)
Error handling and retries


Embedding generation:

Single text embedding
Batch processing with rate limiting
Caching for common queries


Vector storage operations:

Store embeddings in pgvector
Retrieve by chunk ID
Bulk insert optimization


Similarity search:

HNSW index utilization
Metadata filtering
Top-K retrieval
Distance/similarity scoring



Deliverables: EmbeddingGenerator, VectorStore classes
Validation: All tests in tests/test_embeddings.py pass
Sub-Phase 3.3: Hybrid Retrieval System (10 min)
Agent: rag-pipeline-specialist
TDD Cycle:
python# 🔴 RED Phase
# tests/test_retrieval.py

def test_vector_search():
    """Test vector similarity search component"""
    retriever = HybridRetriever()
    results = retriever.vector_search(
        query="capital requirements for banks",
        top_k=20
    )
    assert len(results) == 20
    assert all(hasattr(r, 'chunk_id') for r in results)
    assert all(hasattr(r, 'similarity_score') for r in results)

def test_keyword_search_bm25():
    """Test BM25 keyword search component"""
    retriever = HybridRetriever()
    results = retriever.keyword_search(
        query="CRD IV capital requirements",
        top_k=20
    )
    assert len(results) > 0
    assert all(hasattr(r, 'bm25_score') for r in results)

def test_metadata_filtering():
    """Test metadata-based filtering"""
    retriever = HybridRetriever()
    results = retriever.search_with_filters(
        query="capital requirements",
        filters={"authority": "EBA", "document_type": "regulation"},
        top_k=10
    )
    assert all(r.metadata['authority'] == 'EBA' for r in results)

def test_hybrid_fusion():
    """Test hybrid search fusion from hybrid-search-design.md"""
    retriever = HybridRetriever()
    results = retriever.hybrid_search(
        query="What are the capital requirements for banks?",
        vector_weight=0.7,  # from design specs
        keyword_weight=0.3,
        top_k=10
    )
    assert len(results) == 10
    assert all(hasattr(r, 'fused_score') for r in results)
    # Verify ranking by fused score
    scores = [r.fused_score for r in results]
    assert scores == sorted(scores, reverse=True)
Implementation Tasks:

Vector search using pgvector similarity
BM25 keyword search implementation (using rank-bm25 library)
Metadata filtering layer
Score fusion algorithm:

Reciprocal Rank Fusion (RRF) or weighted combination
Configurable weights per search type


Authority-specific ranking boost
Query preprocessing and expansion

Deliverables: HybridRetriever class with multiple search strategies
Validation: All tests in tests/test_retrieval.py pass
Sub-Phase 3.4: Reranking & Response Generation (10 min)
Agents: rag-pipeline-specialist + python-rag-specialist
TDD Cycle:
python# 🔴 RED Phase
# tests/test_reranking.py

def test_cross_encoder_reranking():
    """Test reranking from reranking-strategies.md"""
    reranker = CrossEncoderReranker(model="cross-encoder/ms-marco-MiniLM-L-12-v2")
    query = "capital requirements for banks"
    documents = get_test_documents(20)
    reranked = reranker.rerank(query, documents, top_k=5)
    
    assert len(reranked) == 5
    # Scores should be in descending order
    assert all(reranked[i].score >= reranked[i+1].score for i in range(4))
    # Top result should be highly relevant
    assert reranked[0].score > 0.5

def test_regulatory_scoring():
    """Test regulatory relevance scoring"""
    scorer = RegulatoryScorer()
    documents = get_test_documents(10)
    scored = scorer.score(
        query="capital requirements",
        documents=documents,
        preferred_authorities=["EBA", "ECB"]
    )
    # EBA/ECB documents should be boosted
    assert scored[0].metadata['authority'] in ["EBA", "ECB"]

def test_response_generation_with_citations():
    """Test RAG response generation with citations"""
    generator = ResponseGenerator()
    query = "What are the CRD IV capital requirements?"
    context_docs = get_relevant_documents()
    
    response = generator.generate(
        query=query,
        context=context_docs,
        include_citations=True
    )
    
    assert response.answer is not None
    assert len(response.answer) > 100  # Substantive response
    assert len(response.citations) > 0
    
    # Verify citations appear in answer
    for citation in response.citations:
        assert citation.source in response.answer or f"[{citation.index}]" in response.answer

def test_rag_api_endpoint():
    """Test complete RAG pipeline via API"""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    token = get_test_token()
    
    response = client.post(
        "/api/rag/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "What are the capital requirements for banks?"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert len(data["citations"]) > 0
Implementation Tasks:
rag-pipeline-specialist:

Cross-encoder reranker:

Load pre-trained cross-encoder model
Query-document relevance scoring
Top-K selection after reranking


Regulatory scoring algorithm:

Authority preference weighting
Document recency boost
Document type prioritization



python-rag-specialist:
3. Azure OpenAI GPT-4 integration:

Prompt engineering for regulatory context
Context window management
Response streaming support


Citation extraction and formatting:

Source attribution in response
Citation numbering and linking
Snippet extraction from sources


RAG API endpoint (POST /api/rag/query):

Query validation
Pipeline orchestration
Response formatting
Audit logging


Query result caching:

Cache common queries
TTL configuration
Cache invalidation on document updates



Deliverables:

CrossEncoderReranker class
RegulatoryScorer class
ResponseGenerator class
POST /api/rag/query endpoint

Phase 3 Complete Validation:
bashpytest tests/test_rag_pipeline.py -v  # All RAG tests pass
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "What are capital requirements?"}' \
# Returns response with answer and citations

# Verify latency requirement
time curl -X POST http://localhost:8000/api/rag/query ... 
# Should complete in < 2 seconds
Orchestrator Delegation Example for Phase 3:
bash# Sub-phase 3.1
/task rag-pipeline-specialist "Phase 3.1: Document Processing Pipeline

Design Context:
- Read: retrieval-methodology.md (sections on chunking and preprocessing)

Tasks:
1. Implement document parsers (PDF, HTML, XML)
2. Create HierarchicalChunker with adaptive sizing (200-1000 chars, 100 overlap)
3. Build metadata extraction (authority, type, dates)
4. Add text cleaning and normalization

TDD: Create tests/test_document_processing.py first
Success: All tests pass, chunks properly sized"

# Sub-phase 3.2
/task python-rag-specialist "Phase 3.2: Embeddings & Vector Storage

Design Context:
- Read: retrieval-methodology.md (embedding section)
- Read: vector-storage-design.md (pgvector operations)

Tasks:
1. Azure OpenAI client for text-embedding-3-large
2. Batch embedding generation with rate limiting
3. VectorStore class with pgvector operations
4. Similarity search with HNSW indexes

TDD: Create tests/test_embeddings.py first
Success: Embeddings generate, store, and search correctly"

# Sub-phase 3.3
/task rag-pipeline-specialist "Phase 3.3: Hybrid Retrieval

Design Context:
- Read: hybrid-search-design.md (complete fusion strategy)

Tasks:
1. Vector search component
2. BM25 keyword search
3. Metadata filtering
4. RRF score fusion (vector_weight=0.7, keyword_weight=0.3)

TDD: Create tests/test_retrieval.py first
Success: Hybrid search returns relevant results"

# Sub-phase 3.4 (requires both agents)
/task rag-pipeline-specialist "Phase 3.4a: Reranking Components

Design Context:
- Read: reranking-strategies.md (cross-encoder and regulatory scoring)

Tasks:
1. CrossEncoderReranker with pre-trained model
2. RegulatoryScorer with authority preference weighting

TDD: Create tests/test_reranking.py
Success: Reranking improves result quality"

/task python-rag-specialist "Phase 3.4b: Response Generation & API

Design Context:
- Read: reranking-strategies.md (response generation)
- Read: api-specifications.md (RAG endpoint definition)

Tasks:
1. ResponseGenerator with Azure OpenAI GPT-4
2. Citation extraction and formatting
3. POST /api/rag/query endpoint
4. Query result caching

TDD: Add API tests to tests/test_reranking.py
Success: Complete RAG pipeline works via API, latency < 2s"
Phase 4: Frontend Implementation (30-35 min)
Agent: node-ts-specialist
Dependencies: Phase 3 complete (backend API available)
Design Inputs:

compliance-wireframes.md (UI layouts)
regulatory-dashboard-design.md (dashboard specs)
workflow-specifications.md (user flows)

Sub-Phase 4.1: Authentication UI (10 min)
TDD Cycle:
typescript// 🔴 RED Phase (Playwright)
// tests/auth.spec.ts

import { test, expect } from '@playwright/test';

test('user can access login page', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByRole('heading', { name: 'Login' })).toBeVisible();
  await expect(page.getByLabel('Email')).toBeVisible();
  await expect(page.getByLabel('Password')).toBeVisible();
});

test('user can register', async ({ page }) => {
  await page.goto('/register');
  await page.fill('[name=email]', 'test@example.com');
  await page.fill('[name=password]', 'SecurePass123!');
  await page.fill('[name=confirmPassword]', 'SecurePass123!');
  await page.click('[type=submit]');
  
  await expect(page).toHaveURL('/dashboard');
});

test('authentication flow works', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name=email]', 'test@example.com');
  await page.fill('[name=password]', 'password123');
  await page.click('[type=submit]');
  
  await expect(page).toHaveURL('/dashboard');
});

test('protected routes require authentication', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page).toHaveURL('/login');
});

test('logout clears session', async ({ page }) => {
  await loginAsUser(page);
  await page.click('[data-testid=logout-button]');
  await expect(page).toHaveURL('/login');
  
  // Try accessing protected route
  await page.goto('/dashboard');
  await expect(page).toHaveURL('/login');
});
Implementation Tasks:

Next.js 14 setup with App Router and TypeScript
Authentication pages:

Login page with form validation
Register page with password strength indicator
Forgot password flow


JWT token management:

Store in httpOnly cookies or localStorage
Auto-refresh on expiry
Logout functionality


Protected route wrapper component
API client with authentication headers
Tailwind CSS setup (or UI library from design specs)

Deliverables: Login/Register pages, auth context, protected routes
Validation: Playwright tests pass, authentication flow works
Sub-Phase 4.2: RAG Query Interface (10 min)
TDD Cycle:
typescript// 🔴 RED Phase
// tests/query.spec.ts

test('user can submit compliance query', async ({ page }) => {
  await loginAsUser(page);
  await page.goto('/query');
  
  const queryInput = page.getByTestId('query-input');
  await expect(queryInput).toBeVisible();
  
  await queryInput.fill('What are the capital requirements for banks under CRD IV?');
  await page.click('[data-testid=submit-query]');
  
  // Wait for loading indicator
  await expect(page.getByTestId('loading-indicator')).toBeVisible();
  
  // Wait for RAG response
  await page.waitForSelector('[data-testid=rag-response]', { timeout: 5000 });
  const response = await page.textContent('[data-testid=rag-response]');
  expect(response).toBeTruthy();
  expect(response.length).toBeGreaterThan(100);
});

test('response includes citations', async ({ page }) => {
  await loginAsUser(page);
  await submitQuery(page, 'What are capital requirements?');
  
  await page.waitForSelector('[data-testid=rag-response]');
  
  // Verify citations are shown
  const citations = await page.locator('[data-testid=citation]').count();
  expect(citations).toBeGreaterThan(0);
  
  // Click first citation
  await page.click('[data-testid=citation]:first-child');
  
  // Verify citation details modal appears
  await expect(page.getByTestId('citation-modal')).toBeVisible();
});

test('query history is saved', async ({ page }) => {
  await loginAsUser(page);
  await submitQuery(page, 'Test query 1');
  await submitQuery(page, 'Test query 2');
  
  // Check history sidebar
  const historyItems = await page.locator('[data-testid=history-item]').count();
  expect(historyItems).toBe(2);
});

test('follow-up questions appear', async ({ page }) => {
  await loginAsUser(page);
  await submitQuery(page, 'What are capital requirements?');
  
  await page.waitForSelector('[data-testid=rag-response]');
  
  // Check for suggested follow-up questions
  const suggestions = await page.locator('[data-testid=follow-up-question]').count();
  expect(suggestions).toBeGreaterThan(0);
});
Implementation Tasks:

Query input component:

Textarea with auto-resize
Character counter
Submit on Cmd/Ctrl+Enter


Loading states:

Skeleton loaders during RAG processing
Progress indicator


Response display:

Markdown rendering for formatted text
Syntax highlighting for code blocks


Citation cards:

Source document information
Excerpt highlighting
Click to view full document


Follow-up question suggestions:

Generate based on response
One-click to submit


Query history sidebar:

Recent queries list
Click to reload previous query/response


API integration:

Connect to POST /api/rag/query
Error handling
Retry logic



Deliverables: Complete query interface with history and citations
Validation: Users can query RAG system and see responses with citations
Sub-Phase 4.3: Dashboard & Document Management (10 min)
TDD Cycle:
typescript// 🔴 RED Phase
// tests/dashboard.spec.ts

test('dashboard shows regulatory metrics', async ({ page }) => {
  await loginAsUser(page);
  await page.goto('/dashboard');
  
  // From regulatory-dashboard-design.md
  await expect(page.getByText('Total Documents')).toBeVisible();
  await expect(page.getByText('Recent Updates')).toBeVisible();
  await expect(page.getByText('Query Analytics')).toBeVisible();
  
  // Verify metrics have values
  const totalDocs = await page.textContent('[data-testid=total-documents]');
  expect(parseInt(totalDocs)).toBeGreaterThan(0);
});

test('dashboard shows recent regulatory updates', async ({ page }) => {
  await loginAsUser(page);
  await page.goto('/dashboard');
  
  const updates = await page.locator('[data-testid=recent-update]').count();
  expect(updates).toBeGreaterThan(0);
  
  // Verify update has date and authority
  await expect(page.getByTestId('recent-update').first()).toContainText('EBA');
});

test('user can upload regulatory document', async ({ page }) => {
  await loginAsUser(page);
  await page.goto('/documents');
  
  // Test drag-and-drop area
  await expect(page.getByText('Drag and drop files here')).toBeVisible();
  
  const fileInput = await page.locator('input[type=file]');
  await fileInput.setInputFiles('test-regulation.pdf');
  
  await page.click('[data-testid=upload-button]');
  
  await expect(page.getByText('Document uploaded successfully')).toBeVisible();
});

test('user can filter documents by authority', async ({ page }) => {
  await loginAsUser(page);
  await page.goto('/documents');
  
  // Apply EBA filter
  await page.click('[data-testid=filter-authority]');
  await page.click('[data-value=EBA]');
  
  // Verify only EBA documents shown
  const documents = await page.locator('[data-testid=document-item]').all();
  for (const doc of documents) {
    const authority = await doc.getAttribute('data-authority');
    expect(authority).toBe('EBA');
  }
});

test('document detail view shows metadata', async ({ page }) => {
  await loginAsUser(page);
  await page.goto('/documents');
  
  await page.click('[data-testid=document-item]:first-child');
  
  // Verify detail view
  await expect(page.getByTestId('document-detail')).toBeVisible();
  await expect(page.getByText('Authority:')).toBeVisible();
  await expect(page.getByText('Document Type:')).toBeVisible();
  await expect(page.getByText('Effective Date:')).toBeVisible();
});

test('query analytics chart displays', async ({ page }) => {
  await loginAsUser(page);
  await page.goto('/dashboard');
  
  await expect(page.getByTestId('query-analytics-chart')).toBeVisible();
  
  // Verify chart has data points
  const dataPoints = await page.locator('[data-testid=chart-data-point]').count();
  expect(dataPoints).toBeGreaterThan(0);
});
Implementation Tasks:

Dashboard with regulatory metrics:

Total documents count
Documents by authority (pie/bar chart)
Recent updates timeline
Query analytics (queries per day, top queries)


Document upload interface:

Drag-and-drop zone
File input fallback
Upload progress indicator
Multi-file support


Document list with search and filtering:

Search by title/content
Filter by authority (EBA, ESMA, EIOPA, etc.)
Filter by document type
Sort by date, relevance


Document detail view:

Metadata display
Content preview
Download button
Related documents


Recent updates timeline:

Chronological list
Authority badges
Change type indicators


Charts for analytics:

Use recharts or similar library
Queries over time (line chart)
Top authorities (pie chart)
Response time trends



Deliverables: Complete dashboard and document management UI
Validation: Dashboard displays correctly, document upload works
Phase 4 Complete Validation:
bashnpm run test:e2e  # All Playwright tests pass
npm run dev  # Frontend starts on localhost:3000
# Manual testing: Login → Upload document → Submit query → View dashboard
Orchestrator Delegation Example for Phase 4:
bash/task node-ts-specialist "Phase 4: Complete Frontend Implementation

Design Context:
- Read: compliance-wireframes.md (all UI layouts)
- Read: regulatory-dashboard-design.md (dashboard specifications)
- Read: workflow-specifications.md (user flows)

Implementation Phases (do sequentially):

Phase 4.1 - Authentication UI (10 min):
1. Next.js 14 with App Router, TypeScript, Tailwind CSS
2. Login page (email, password, remember me)
3. Register page (email, password, confirm password)
4. JWT token management (localStorage + httpOnly cookies)
5. Protected route wrapper component
6. API client with auth headers

Tests: tests/auth.spec.ts (Playwright)
Validation: Users can register, login, logout

Phase 4.2 - Query Interface (10 min):
1. Query input with auto-resize textarea
2. Loading states with skeleton loaders
3. Response display with markdown rendering
4. Citation cards with source info
5. Follow-up question suggestions
6. Query history sidebar

Tests: tests/query.spec.ts
Validation: Users can submit queries and see responses with citations

Phase 4.3 - Dashboard & Documents (10 min):
1. Dashboard with metrics cards:
   - Total documents, recent updates, query analytics
2. Document upload with drag-and-drop
3. Document list with filters (authority, type, date)
4. Document detail view with metadata
5. Charts using recharts (queries over time, documents by authority)

Tests: tests/dashboard.spec.ts
Validation: Dashboard displays, document upload works

TDD Protocol:
- Write Playwright tests FIRST for each sub-phase (RED)
- Implement components to pass tests (GREEN)
- Run npm run test:e2e and manual testing (VERIFY)

Technology Stack:
- Next.js 14 with App Router
- React 18 with TypeScript
- Tailwind CSS for styling
- Playwright for E2E testing
- Recharts for data visualization
- Axios for API calls

Success Criteria:
✓ All Playwright tests pass
✓ Authentication flow works end-to-end
✓ Query interface successfully calls RAG API
✓ Dashboard displays regulatory metrics
✓ Document upload and management functional
✓ Mobile responsive (test on 375px width)
✓ Accessible (ARIA labels, keyboard navigation)

Output Expected:
- frontend/app/ (Next.js pages and layouts)
- frontend/components/ (reusable React components)
- frontend/lib/ (API client, utilities)
- tests/ (Playwright E2E tests)
- frontend/README.md (setup and running instructions)"
Phase 5: Regulatory Scraping & Monitoring (20-25 min)
Agents: python-rag-specialist, stagehand
Dependencies: Phase 3 complete (document ingestion pipeline ready)
Design Inputs:

regulatory-sources-analysis.md (EBA, ESMA, EIOPA, ECB, Bank of Spain, CNMV, BIS)
scraping-methodologies.md (Browserbase patterns, parsing strategies)
monitoring-strategies.md (change detection, notifications)

TDD Cycle:
python# 🔴 RED Phase
# tests/test_scraping.py

def test_browserbase_connection():
    """Test Browserbase integration"""
    scraper = BrowserbaseScraper()
    assert scraper.connect() is True
    assert scraper.browser is not None

def test_scrape_eba_website():
    """Test scraping from EBA regulatory source"""
    scraper = EBAScraper()
    documents = scraper.scrape_recent_documents(days=30)
    
    assert len(documents) > 0
    assert all(d.authority == 'EBA' for d in documents)
    assert all(d.url is not None for d in documents)
    assert all(d.title is not None for d in documents)

def test_document_change_detection():
    """Test change detection for regulatory documents"""
    detector = ChangeDetector()
    
    # Simulate existing document
    old_doc = create_test_document(content="Old content", checksum="abc123")
    new_doc = create_test_document(content="Updated content", checksum="def456")
    
    changes = detector.detect_changes(old_doc, new_doc)
    assert changes.is_changed is True
    assert changes.change_type in ['content', 'metadata', 'new']

def test_automated_ingestion_pipeline():
    """Test automated document ingestion after scraping"""
    scraper = EBAScraper()
    documents = scraper.scrape_recent_documents(days=7)
    
    pipeline = IngestionPipeline()
    results = pipeline.ingest_batch(documents)
    
    assert len(results) == len(documents)
    assert all(r.status == 'success' for r in results)
    
    # Verify documents in database
    for doc in documents:
        assert document_exists_in_db(doc.url)

def test_scraping_error_handling():
    """Test error handling for failed scraping attempts"""
    scraper = BrokenScraper()  # Simulates failures
    
    with pytest.raises(ScrapingError):
        scraper.scrape_recent_documents()
    
    # Verify error logged to database
    errors = get_scraping_errors(scraper.source_id)
    assert len(errors) > 0
Implementation Tasks:
python-rag-specialist:

Browserbase integration:

API client setup
Session management
Browser automation for JavaScript-heavy sites


Scrapers for each regulatory source:

EBA: Guidelines, regulations, opinions
ESMA: Technical standards, Q&As
EIOPA: Guidelines, opinions, decisions
ECB: Regulations, guidelines, opinions
Bank of Spain: Circulars, communications
CNMV: Circulars, guidelines
BIS: Standards, consultations


Document parsing and metadata extraction:

Title, date, document type
Authority identification
URL and PDF extraction


Change detection system:

Content hashing for change detection
Version tracking in database
Diff generation for changes



stagehand:
5. Scheduled scraping jobs:

Cron jobs or scheduled tasks
Daily scraping for each source
Error notification and retry logic


Admin interface for scraping management:

View scraping status
Manual trigger scraping
Configure scraping frequency
View scraping logs and errors



Deliverables:

Browserbase integration
Scrapers for 7 regulatory sources
Change detection system
Automated ingestion pipeline
Admin interface

Validation: Successfully scrapes from at least one regulatory source, new documents automatically ingested
Orchestrator Delegation Example:
bash/task python-rag-specialist "Phase 5: Regulatory Scraping Integration

Design Context:
- Read: regulatory-sources-analysis.md (all 7 sources)
- Read: scraping-methodologies.md (Browserbase patterns)
- Read: monitoring-strategies.md (change detection)

Tasks:
1. Browserbase integration:
   - Setup API client with credentials
   - Create session manager
   - Implement browser automation helpers

2. Implement scrapers (at least EBA, ESMA, ECB):
   from scrapers.base import BaseScraper
   
   class EBAScraper(BaseScraper):
       def scrape_recent_documents(self, days=30):
           # Navigate to EBA website
           # Extract document list
           # Parse metadata
           # Return Document objects

3. Change detection system:
   - Hash document content for comparison
   - Store document versions in database
   - Generate diff for changed documents

4. Automated ingestion pipeline:
   - Connect to Phase 3 document processing
   - Process scraped documents through RAG pipeline
   - Store in database with proper metadata

TDD: Create tests/test_scraping.py first
Success: Can scrape from EBA, detect changes, auto-ingest"

/task stagehand "Phase 5: Scraping Automation & Admin UI

Tasks:
1. Setup scheduled jobs:
   - Daily scraping cron jobs
   - Error notification on failures
   - Retry logic with exponential backoff

2. Create admin interface (backend/api/admin/scraping.py):
   - GET /api/admin/scraping/status (view all scrapers)
   - POST /api/admin/scraping/trigger (manual scraping)
   - GET /api/admin/scraping/logs (view scraping history)

Success: Scrapers run daily, admin can monitor and trigger"
Phase 6: Compliance & Reporting Features (25-30 min)
Agents: node-ts-specialist, python-rag-specialist
Dependencies: Phase 4 and 5 complete
Design Inputs:

COMPLIANCE_FRAMEWORK.md (compliance requirements, reporting specs)
workflow-specifications.md (compliance workflows)

TDD Cycle:
typescript// 🔴 RED Phase
// tests/compliance.spec.ts

test('user can generate regulatory report', async ({ page }) => {
  await loginAsUser(page);
  await page.goto('/reports');
  
  await page.click('[data-testid=new-report]');
  await page.selectOption('[name=authority]', 'EBA');
  await page.selectOption('[name=reportType]', 'compliance-summary');
  await page.click('[data-testid=generate-report]');
  
  await expect(page.getByText('Report generated successfully')).toBeVisible();
  
  // Verify report appears in list
  await expect(page.getByTestId('report-item')).toBeVisible();
});

test('GAP analysis interface works', async ({ page }) => {
  await loginAsUser(page);
  await page.goto('/gap-analysis');
  
  await expect(page.getByText('GAP Analysis')).toBeVisible();
  
  // Select requirements to analyze
  await page.click('[data-testid=requirement-selector]');
  await page.click('[data-value=crd-iv-capital]');
  
  await page.click('[data-testid=run-analysis]');
  
  // Wait for analysis results
  await page.waitForSelector('[data-testid=gap-result]');
  
  const gaps = await page.locator('[data-testid=gap-item]').count();
  expect(gaps).toBeGreaterThan(0);
});

test('export report to PDF', async ({ page }) => {
  await loginAsUser(page);
  await page.goto('/reports/123');
  
  const downloadPromise = page.waitForEvent('download');
  await page.click('[data-testid=export-pdf]');
  const download = await downloadPromise;
  
  expect(download.suggestedFilename()).toContain('.pdf');
  expect(download.suggestedFilename()).toContain('compliance-report');
});

test('export report to Word', async ({ page }) => {
  await loginAsUser(page);
  await page.goto('/reports/123');
  
  const downloadPromise = page.waitForEvent('download');
  await page.click('[data-testid=export-word]');
  const download = await downloadPromise;
  
  expect(download.suggestedFilename()).toContain('.docx');
});

test('export report to Excel', async ({ page }) => {
  await loginAsUser(page);
  await page.goto('/reports/123');
  
  const downloadPromise = page.waitForEvent('download');
  await page.click('[data-testid=export-excel]');
  const download = await downloadPromise;
  
  expect(download.suggestedFilename()).toContain('.xlsx');
});

test('audit trail shows user actions', async ({ page }) => {
  await loginAsUser(page);
  
  // Perform some actions
  await page.goto('/documents');
  await uploadDocument(page, 'test.pdf');
  await page.goto('/query');
  await submitQuery(page, 'test query');
  
  // View audit trail
  await page.goto('/audit-trail');
  
  const auditEntries = await page.locator('[data-testid=audit-entry]').count();
  expect(auditEntries).toBeGreaterThanOrEqual(2);
  
  // Verify actions are logged
  await expect(page.getByText('Document uploaded')).toBeVisible();
  await expect(page.getByText('Query submitted')).toBeVisible();
});

test('cross-jurisdictional comparison works', async ({ page }) => {
  await loginAsUser(page);
  await page.goto('/comparison');
  
  // Select jurisdictions
  await page.click('[data-testid=jurisdiction-selector]');
  await page.check('[data-value=EU]');
  await page.check('[data-value=US]');
  await page.check('[data-value=UK]');
  
  await page.click('[data-testid=compare]');
  
  // Verify comparison table
  await expect(page.getByTestId('comparison-table')).toBeVisible();
  
  const jurisdictions = await page.locator('[data-testid=jurisdiction-column]').count();
  expect(jurisdictions).toBe(3);
});
Implementation Tasks:
node-ts-specialist (Frontend):

Regulatory report generation interface:

Report type selector (compliance summary, GAP analysis, audit report)
Authority/jurisdiction selector
Date range picker
Generate button with loading state


GAP analysis interface:

Requirement selector (multi-select)
Current compliance status input
Run analysis button
Visual gap display (charts, tables)
Gap details with recommendations


Report viewing interface:

Report metadata display
Section navigation
Export options (PDF, Word, Excel)
Share and collaborate features


Cross-jurisdictional comparison:

Jurisdiction selector
Requirement category selector
Side-by-side comparison table
Highlight differences


Audit trail interface:

Chronological activity list
Filter by user, action type, date
Search functionality
Export audit logs



python-rag-specialist (Backend):
6. Report generation API:

POST /api/reports/generate
Report template system
Data aggregation from RAG queries
Report storage in database


GAP analysis engine:

POST /api/compliance/gap-analysis
Requirement parsing from regulations
Current state assessment
Gap identification algorithm
Recommendation generation


Export functionality:

PDF generation (using reportlab or weasyprint)
Word generation (using python-docx)
Excel generation (using openpyxl)
File download endpoints


Audit trail API:

GET /api/audit-trail
Filter and search capabilities
Pagination for large datasets
Export audit logs



Deliverables:

Report generation UI and API
GAP analysis interface and engine
Export functionality (PDF, Word, Excel)
Audit trail viewing interface
Cross-jurisdictional comparison tool

Validation: Reports generate correctly through UI, exports work, audit trail shows complete activity history
Orchestrator Delegation Example:
bash/task node-ts-specialist "Phase 6a: Compliance Frontend Features

Design Context:
- Read: COMPLIANCE_FRAMEWORK.md (reporting requirements)
- Read: workflow-specifications.md (compliance workflows)

Tasks:
1. Report generation interface (frontend/app/reports/page.tsx)
2. GAP analysis interface (frontend/app/gap-analysis/page.tsx)
3. Report viewing with export buttons
4. Cross-jurisdictional comparison table
5. Audit trail interface with filters

Tests: tests/compliance.spec.ts (Playwright)
Success: All compliance UI tests pass"

/task python-rag-specialist "Phase 6b: Compliance Backend APIs

Design Context:
- Read: COMPLIANCE_FRAMEWORK.md (complete)

Tasks:
1. POST /api/reports/generate (report generation)
2. POST /api/compliance/gap-analysis (GAP analysis engine)
3. Export endpoints (PDF, Word, Excel):
   - GET /api/reports/{id}/export/pdf
   - GET /api/reports/{id}/export/word
   - GET /api/reports/{id}/export/excel
4. GET /api/audit-trail (with filters)

Libraries: reportlab, python-docx, openpyxl
Success: Reports generate, exports work, API tests pass"
Phase 7: Production Readiness (20-25 min)
Agents: stagehand, python-rag-specialist
Dependencies: All previous phases complete
Design Inputs:

security-requirements.md (security hardening)
scalability-analysis.md (performance optimization)

TDD Cycle:
python# 🔴 RED Phase
# tests/test_production.py

def test_security_headers():
    """Test security headers are configured"""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    assert response.headers.get('X-Frame-Options') == 'DENY'
    assert response.headers.get('Strict-Transport-Security') is not None
    assert 'X-Powered-By' not in response.headers

def test_rate_limiting():
    """Test API rate limiting"""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    
    # Make 100 requests rapidly
    for i in range(100):
        response = client.get("/api/documents")
    
    # 101st request should be rate limited
    response = client.get("/api/documents")
    assert response.status_code == 429  # Too Many Requests

def test_csrf_protection():
    """Test CSRF protection is enabled"""
    # Test POST request without CSRF token fails
    # Test POST request with valid CSRF token succeeds
    pass

def test_backup_procedures():
    """Test database backup and recovery"""
    # Trigger backup
    # Verify backup file created
    # Restore from backup
    # Verify data integrity
    pass

def test_performance_benchmarks():
    """Test system meets performance requirements"""
    import time
    
    start = time.time()
    response = client.post("/api/rag/query", json={"query": "test"})
    duration = time.time() - start
    
    assert duration < 2.0  # Sub-2-second response time
    assert response.status_code == 200

def test_monitoring_endpoints():
    """Test monitoring and health check endpoints"""
    response = client.get("/metrics")
    assert response.status_code == 200
    
    # Verify Prometheus metrics format
    metrics_text = response.text
    assert "http_requests_total" in metrics_text

def test_ssl_tls_configuration():
    """Test SSL/TLS is properly configured"""
    # Verify TLS 1.3 minimum
    # Test certificate validity
    # Verify HTTPS redirect from HTTP
    pass


Implementation Tasks:
stagehand:

Environment configuration:

Production environment variables
Secrets management (Azure Key Vault or similar)
Multi-environment config (dev, staging, prod)


Security hardening:

Security headers middleware (Helmet.js equivalent)
HTTPS enforcement
CORS configuration (restrictive for production)
Rate limiting (slowapi or similar)
CSRF protection


Monitoring and logging:

Application Performance Monitoring setup (Azure Monitor, Datadog, or New Relic)
Centralized logging (ELK stack or Azure Log Analytics)
Error tracking (Sentry or similar)
Prometheus metrics export


CI/CD pipeline:

GitHub Actions or Azure DevOps pipeline
Automated testing on PR
Security scanning (Snyk, Dependabot)
Automated deployment to staging
Manual approval for production


Infrastructure as Code:

Docker compose for local development
Kubernetes manifests or Azure Container Apps
Terraform for cloud resources


Backup and disaster recovery:

Automated daily database backups
Backup retention policy (30 days)
Documented recovery procedures
Tested restore process



python-rag-specialist:
7. Performance optimization:

Database query optimization
Connection pooling tuning
Caching strategy (Redis for API responses)
CDN setup for static assets


Load balancing:

Configure load balancer
Health check endpoints
Graceful shutdown handling



Deliverables:

Production environment configuration
Security hardening implemented
Monitoring and alerting operational
CI/CD pipeline functional
Backup and recovery procedures tested

Validation: Security tests pass, deployment pipeline works, system handles load
Orchestrator Delegation Example:
bash/task stagehand "Phase 7: Production Infrastructure & Security

Design Context:
- Read: security-requirements.md (complete security framework)
- Read: scalability-analysis.md (performance requirements)

Tasks:
1. Security hardening:
   - Add security headers middleware
   - Configure rate limiting (100 req/min per IP)
   - Setup CSRF protection
   - HTTPS enforcement

2. Monitoring setup:
   - Azure Monitor or similar APM
   - Prometheus metrics export at /metrics
   - Error tracking with Sentry
   - Log aggregation

3. CI/CD pipeline (GitHub Actions):
   - Run tests on every PR
   - Security scanning with Snyk
   - Deploy to staging on merge to main
   - Manual approval for production

4. Backup automation:
   - Daily PostgreSQL backups
   - Backup to Azure Blob Storage
   - 30-day retention
   - Test restore procedure

5. Infrastructure as Code:
   - Docker compose for local dev
   - Kubernetes manifests for production
   - Terraform for Azure resources

Tests: tests/test_production.py
Success: All security tests pass, deployment works"

/task python-rag-specialist "Phase 7: Performance Optimization

Design Context:
- Read: scalability-analysis.md (performance targets)

Tasks:
1. Database optimization:
   - Add connection pooling (SQLAlchemy pool_size=20)
   - Optimize slow queries (use EXPLAIN ANALYZE)
   - Add database indexes where needed

2. Caching layer:
   - Setup Redis for response caching
   - Cache RAG query results (TTL: 1 hour)
   - Cache document embeddings

3. API optimization:
   - Add response compression (gzip)
   - Optimize serialization
   - Async database queries where possible

Success: RAG queries complete in <2s, API handles 100 req/s"
Phase 8: Final Integration & Testing (15-20 min)
Agents: node-ts-specialist, stagehand
Dependencies: All previous phases complete
TDD Cycle:
typescript// 🔴 RED Phase
// tests/integration.spec.ts

test('complete user journey - registration to report generation', async ({ page }) => {
  // 1. Register new user
  await page.goto('/register');
  const testEmail = `test-${Date.now()}@example.com`;
  await page.fill('[name=email]', testEmail);
  await page.fill('[name=password]', 'SecurePass123!');
  await page.fill('[name=confirmPassword]', 'SecurePass123!');
  await page.click('[type=submit]');
  
  // 2. Should redirect to dashboard
  await expect(page).toHaveURL('/dashboard');
  
  // 3. Upload a document
  await page.goto('/documents');
  const fileInput = await page.locator('input[type=file]');
  await fileInput.setInputFiles('test-data/eba-regulation.pdf');
  await page.click('[data-testid=upload-button]');
  await expect(page.getByText('Document uploaded successfully')).toBeVisible();
  
  // 4. Wait for document processing
  await page.waitForTimeout(3000);
  
  // 5. Submit a compliance query
  await page.goto('/query');
  await page.fill('[data-testid=query-input]', 'What are the capital requirements in this document?');
  await page.click('[data-testid=submit-query]');
  await page.waitForSelector('[data-testid=rag-response]', { timeout: 5000 });
  
  // 6. Verify response has citations
  const citations = await page.locator('[data-testid=citation]').count();
  expect(citations).toBeGreaterThan(0);
  
  // 7. Generate a compliance report
  await page.goto('/reports');
  await page.click('[data-testid=new-report]');
  await page.selectOption('[name=authority]', 'EBA');
  await page.click('[data-testid=generate-report]');
  await expect(page.getByText('Report generated successfully')).toBeVisible();
  
  // 8. Export report
  const downloadPromise = page.waitForEvent('download');
  await page.click('[data-testid=export-pdf]');
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain('.pdf');
});

test('concurrent users can query simultaneously', async ({ browser }) => {
  const context1 = await browser.newContext();
  const context2 = await browser.newContext();
  const context3 = await browser.newContext();
  
  const page1 = await context1.newPage();
  const page2 = await context2.newPage();
  const page3 = await context3.newPage();
  
  // Login all users
  await Promise.all([
    loginAsUser(page1, 'user1@example.com'),
    loginAsUser(page2, 'user2@example.com'),
    loginAsUser(page3, 'user3@example.com')
  ]);
  
  // All submit queries simultaneously
  await Promise.all([
    submitQuery(page1, 'Query from user 1'),
    submitQuery(page2, 'Query from user 2'),
    submitQuery(page3, 'Query from user 3')
  ]);
  
  // All should receive responses
  await Promise.all([
    page1.waitForSelector('[data-testid=rag-response]'),
    page2.waitForSelector('[data-testid=rag-response]'),
    page3.waitForSelector('[data-testid=rag-response]')
  ]);
  
  // Verify each got their own response
  const response1 = await page1.textContent('[data-testid=rag-response]');
  const response2 = await page2.textContent('[data-testid=rag-response]');
  const response3 = await page3.textContent('[data-testid=rag-response]');
  
  expect(response1).toBeTruthy();
  expect(response2).toBeTruthy();
  expect(response3).toBeTruthy();
});

test('mobile responsive design', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
  
  await loginAsUser(page);
  await page.goto('/dashboard');
  
  // Verify mobile navigation works
  await expect(page.getByTestId('mobile-menu-button')).toBeVisible();
  await page.click('[data-testid=mobile-menu-button]');
  await expect(page.getByTestId('mobile-nav')).toBeVisible();
  
  // Test query interface on mobile
  await page.goto('/query');
  await expect(page.getByTestId('query-input')).toBeVisible();
  
  // Submit query on mobile
  await page.fill('[data-testid=query-input]', 'test query');
  await page.click('[data-testid=submit-query]');
  await page.waitForSelector('[data-testid=rag-response]');
});

test('cross-browser compatibility', async ({ browserName }) => {
  console.log(`Testing on ${browserName}`);
  // Test will run on Chromium, Firefox, and WebKit
  // Basic functionality should work across all browsers
});

test('performance under load', async ({ page }) => {
  const startTime = Date.now();
  
  await loginAsUser(page);
  await page.goto('/query');
  await page.fill('[data-testid=query-input]', 'What are capital requirements?');
  await page.click('[data-testid=submit-query]');
  await page.waitForSelector('[data-testid=rag-response]');
  
  const endTime = Date.now();
  const duration = endTime - startTime;
  
  expect(duration).toBeLessThan(5000); // Complete flow in under 5 seconds
});

test('error handling and recovery', async ({ page }) => {
  await loginAsUser(page);
  
  // Test network error handling
  await page.route('**/api/rag/query', route => route.abort());
  
  await page.goto('/query');
  await page.fill('[data-testid=query-input]', 'test query');
  await page.click('[data-testid=submit-query]');
  
  // Should show error message
  await expect(page.getByText(/error|failed/i)).toBeVisible();
  
  // Should allow retry
  await expect(page.getByTestId('retry-button')).toBeVisible();
});

test('accessibility compliance', async ({ page }) => {
  await loginAsUser(page);
  await page.goto('/dashboard');
  
  // Test keyboard navigation
  await page.keyboard.press('Tab');
  const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
  expect(focusedElement).toBeTruthy();
  
  // Test screen reader labels (ARIA)
  const buttons = await page.locator('button').all();
  for (const button of buttons) {
    const ariaLabel = await button.getAttribute('aria-label');
    const text = await button.textContent();
    expect(ariaLabel || text).toBeTruthy();
  }
});
Implementation Tasks:
node-ts-specialist:

Final UI polish:

Loading states consistency
Error message clarity
Success feedback
Mobile responsive adjustments


Accessibility improvements:

ARIA labels on all interactive elements
Keyboard navigation support
Focus indicators
Screen reader testing


Error handling:

Network error recovery
Retry mechanisms
User-friendly error messages
Offline mode handling



stagehand:
4. Load testing:

Apache JMeter or Locust setup
Simulate 100+ concurrent users
Identify bottlenecks
Generate performance report


Security testing:

OWASP ZAP security scan
Penetration testing checklist
Vulnerability assessment
Security report generation


Documentation:

User guide
API documentation
Deployment guide
Troubleshooting guide



Deliverables:

Complete integration tests passing
Load testing report
Security assessment report
Production documentation
System ready for users

Validation: All tests pass, system handles load, documentation complete
Orchestrator Delegation Example:
bash/task node-ts-specialist "Phase 8: Final Integration & Polish

Tasks:
1. Write comprehensive integration tests (tests/integration.spec.ts):
   - Complete user journey test
   - Concurrent user test
   - Mobile responsive test
   - Accessibility test

2. Final UI improvements:
   - Consistent loading states
   - Clear error messages with retry
   - Success feedback animations
   - Mobile responsive fixes

3. Accessibility:
   - Add ARIA labels to all buttons
   - Keyboard navigation support
   - Focus indicators
   - Test with screen reader

Success: All Playwright tests pass, mobile works, accessible"

/task stagehand "Phase 8: Load Testing & Documentation

Tasks:
1. Load testing with Locust:
   - Simulate 100 concurrent users
   - Test RAG query endpoint
   - Test document upload
   - Generate performance report

2. Security scanning:
   - Run OWASP ZAP automated scan
   - Review security report
   - Fix critical vulnerabilities

3. Create documentation:
   - docs/USER_GUIDE.md (how to use the system)
   - docs/API_DOCUMENTATION.md (API reference)
   - docs/DEPLOYMENT.md (deployment instructions)
   - docs/TROUBLESHOOTING.md (common issues)

Success: Load tests pass (100 users), documentation complete"
Phase 8 Complete Validation:
bash# Run all tests
npm run test:e2e  # All Playwright tests pass
pytest tests/ -v  # All backend tests pass

# Load testing
locust -f tests/load_test.py --users 100 --spawn-rate 10
# Verify: No errors, response time < 2s, throughput > 50 req/s

# Security scan
docker run -t owasp/zap2docker-stable zap-baseline.py -t http://localhost:8000
# Verify: No high-severity vulnerabilities

# Manual validation
# 1. Complete user journey works end-to-end
# 2. System handles multiple concurrent users
# 3. Mobile interface is responsive
# 4. Accessibility standards met
# 5. Documentation is clear and complete

Implementation Strategy
Modern Full-Stack TDD with RAG-First Approach
The implementation strategy prioritizes complete system integration and regulatory compliance:
Core Workflow:

Read design specifications completely before any implementation
Write tests before code (Red → Green → Verify for every component)
Build frontend and backend incrementally with full integration testing
Ensure compliance and audit requirements are built-in from the start
Implement complete user workflows with real-time testing
Let design outputs guide ALL implementation decisions

Testing Philosophy:

Unit Tests: Individual components (frontend and backend)
Integration Tests: API endpoints and database operations
End-to-End Tests: Complete user workflows with Playwright
Compliance Tests: Audit trail completeness and regulatory reporting
Performance Tests: System load and response times
Security Tests: Authentication, authorization, and data protection

Design Integration:

MANIFEST.md: Requirements and coverage tracking
IMPLEMENTATION_PLAN.md: Technical approach and architecture
COMPLIANCE_FRAMEWORK.md: Regulatory requirements and audit trails
ui-designer outputs: Frontend specifications and user experience
All other agent outputs: Specific technical implementations

Success Metrics
Full-Stack Implementation Success
✅ Complete user authentication and authorization system
✅ Document upload, processing, and management system
✅ RAG query interface with real-time responses
✅ Regulatory dashboard with compliance monitoring
✅ Report generation and export functionality
✅ Admin interface for system management
RAG Implementation Success
✅ Document ingestion pipeline operational
✅ Vector storage and similarity search working
✅ Hybrid retrieval system implemented
✅ Reranking produces relevant results
✅ Response generation includes proper citations
✅ Real-time query processing through web interface
Compliance Implementation Success
✅ Audit trails capture all required events
✅ Regulatory reporting functions correctly through UI
✅ GAP analysis produces accurate visual comparisons
✅ Export functionality supports required formats
✅ Multi-sector adaptability demonstrated
✅ Cross-jurisdictional comparison tools operational
Production Readiness Success
✅ All tests passing (unit → integration → end-to-end)
✅ Security hardening implemented
✅ Performance benchmarks met
✅ Monitoring and alerting operational
✅ Backup and recovery procedures tested
✅ Deployment pipeline functional
✅ Ready for production users
Design-Driven Full-Stack TDD Rules
Full-Stack Integration Requirements

Must implement complete user workflows from ui-designer specifications
Must integrate frontend with backend through API layer
Must implement exact RAG pipeline from rag-strategy-researcher outputs
Must use database schema from postgres-rag-architect specifications
Must integrate scraping targets from scraping-strategy-researcher analysis
Must follow API patterns from architecture-designer specifications

Compliance-First Implementation

Must implement audit trails for all user operations
Must support regulatory reporting through user interface
Must enable multi-sector adaptability in UI
Must maintain document versioning and change tracking
Must provide export functionality for compliance reports

RED Phase (Test First)

Write failing tests based on design specifications
Frontend tests check UI components and user workflows
Backend tests verify API endpoints and database operations
Integration tests validate complete system workflows
Compliance tests ensure audit trail completeness
Performance tests validate system under load

GREEN Phase (Minimal Implementation)

Implement minimal code to pass current test
Follow design specifications exactly
Use technology stack from tech-stack-researcher outputs
Integrate frontend and backend components properly
No additional features beyond current test requirements

VERIFY Phase (System Validation)

Demonstrate complete user workflow works end-to-end
Verify compliance requirements are met in UI
Validate API functionality and performance
Ensure audit trails capture all necessary user events
Test system with multiple concurrent users
Get user approval before proceeding to next component


For Orchestrator: Phase Execution Protocol
When orchestrating these phases:

Read Phase Specification Above: Understand deliverables and validation
Extract Design Context: Get relevant .md files for the phase
Delegate to Agent: Use Task tool with complete context
Monitor TDD Cycle: Ensure RED → GREEN → VERIFY happens
Validate Completion: Run validation commands, check tests pass
Update Tracker: Mark phase complete before advancing
Handle Failures: If validation fails, retry or reassign

Example Delegation Pattern:
bash/task [agent-name] "Implement Phase X: [Phase Name]

Context: RAG compliance system [component] from design outputs
Design Files to Read:
- [specific-design-file.md] (sections: [relevant sections])
- [another-file.md] (focus on: [specific areas])

Your Tasks:
[Copy implementation tasks from Phase X specification above]

TDD Requirement:
- Phase: [RED/GREEN/VERIFY]
- Create test file: tests/test_[component].py
- Implement to pass tests
- Validate with: [specific validation commands]

Success Criteria:
[Copy validation section from Phase X above]

Output Expected:
- [Specific files/endpoints/components]
- [Documentation requirements]
- [Integration points]

Technology Stack:
[Relevant technologies from tech-stack-researcher]"

Orchestrator Quick Reference
Agent Capabilities Matrix
AgentDatabaseBackendRAG PipelineFrontendDevOpspostgres-specialist✓✓✓----python-rag-specialist✓✓✓✓✓✓--rag-pipeline-specialist-✓✓✓✓--node-ts-specialist---✓✓✓-stagehand----✓✓✓
Design File → Agent Mapping
database-schema.md → postgres-specialist
vector-storage-design.md → postgres-specialist
audit-trail-specifications.md → postgres-specialist

system-architecture.md → python-rag-specialist
api-specifications.md → python-rag-specialist
authentication-patterns.md → python-rag-specialist

retrieval-methodology.md → rag-pipeline-specialist
reranking-strategies.md → rag-pipeline-specialist
hybrid-search-design.md → rag-pipeline-specialist

compliance-wireframes.md → node-ts-specialist
regulatory-dashboard-design.md → node-ts-specialist
workflow-specifications.md → node-ts-specialist

scraping-methodologies.md → python-rag-specialist
regulatory-sources-analysis.md → python-rag-specialist

security-requirements.md → stagehand
scalability-analysis.md → stagehand
technology-selections.md → stagehand

COMPLIANCE_FRAMEWORK.md → multiple agents (compliance features)
IMPLEMENTATION_PLAN.md → orchestrator (overall strategy)
MANIFEST.md → orchestrator (requirements tracking)
Phase Dependencies Map
Phase 0 (Setup) → No dependencies
Phase 1 (Analysis) → Phase 0 complete
Phase 2 (Database) → Phase 1 complete
Phase 2.5 (Backend API) → Phase 2 complete
Phase 3 (RAG Pipeline) → Phase 2.5 complete
Phase 4 (Frontend) → Phase 3 complete
Phase 5 (Scraping) → Phase 3 complete
Phase 6 (Compliance) → Phase 4 and 5 complete
Phase 7 (Production) → All previous phases complete
Phase 8 (Integration) → Phase 7 complete
Critical Success Factors

Sequential Phase Execution: Never skip ahead, dependencies matter
Design Fidelity: Implementations must match design specs exactly
TDD Discipline: Tests before code, every single time
Integration Validation: Verify connections between phases work
Progress Tracking: Always know current phase status
Clear Delegation: Provide complete context to specialist agents
Validation Gates: Don't advance until all criteria met
Documentation: Keep docs updated as implementation progresses

Progress Tracking Template
✅ Phase 0: Setup Complete (2024-01-15 10:30)
✅ Phase 1: Analysis Complete (2024-01-15 11:00)
✅ Phase 2: Database Complete (2024-01-15 12:30)
🔄 Phase 2.5: Backend API (postgres-specialist working...)
⏸️ Phase 3: RAG Pipeline (waiting on Phase 2.5)
⏸️ Phase 4: Frontend (waiting on Phase 3)
⏸️ Phase 5: Scraping (waiting on Phase 3)
⏸️ Phase 6: Compliance (waiting on Phase 4, 5)
⏸️ Phase 7: Production (waiting on Phase 6)
⏸️ Phase 8: Integration (waiting on Phase 7)

Philosophy
Modern Full-Stack RAG TDD Principles

Design as Single Source of Truth - All implementation decisions derive from design outputs
Full-Stack Integration First - Prioritize complete user workflows over isolated components
RAG-First Architecture - Build document retrieval and generation capabilities into user experience
Compliance-Driven Development - Build audit trails and regulatory features into UI/UX
Test Before Code - Every component follows Red → Green → Verify discipline
Multi-Sector Adaptability - Ensure system works across regulated industries in UI
Production-Ready from Start - Build security, monitoring, and deployment from beginning
No Assumptions - If it's not in the design, don't implement it
Continuous User Validation - Test complete workflows with real user scenarios

The goal is to demonstrate that modern full-stack TDD with RAG-first architecture creates superior regulatory compliance applications by following design specifications exactly, building quality and compliance in from the start, integrating frontend and backend seamlessly, and maintaining comprehensive test coverage throughout the entire system.