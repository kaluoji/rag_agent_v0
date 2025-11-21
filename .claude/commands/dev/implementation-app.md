---
allowed-tools: Task, Bash, Read, Write, Edit, MultiEdit, TodoWrite
description: Build RAG regulatory compliance backend from design specifications using test-driven development
argument-hint: <design-folder-output-path> <app-folder>
---

# RAG Compliance Backend Implementation from Design Specifications

Build production-ready RAG regulatory compliance backend systems from `/design-app` outputs using modern Test-Driven Development (TDD) with comprehensive testing strategies.

## Core Philosophy

This command demonstrates modern backend TDD practices by:

- **Design-First**: All implementation decisions derive from design phase outputs
- **RAG-First**: Prioritize retrieval-augmented generation architecture for regulatory documents
- **Test-First**: Write tests before code (Red → Green → Verify cycles)
- **Compliance-Driven**: Build audit trails, document versioning, and regulatory reporting from the start
- **Multi-Sector**: Design for adaptability across regulated industries

## Prerequisites

This command requires design outputs from `/design-app`:

- `.claude/outputs/design/projects/[project-name]/[timestamp]/IMPLEMENTATION_PLAN.md` - Technical roadmap
- `.claude/outputs/design/projects/[project-name]/[timestamp]/MANIFEST.md` - Requirements registry
- `.claude/outputs/design/projects/[project-name]/[timestamp]/COMPLIANCE_FRAMEWORK.md` - Sector-agnostic compliance guidelines
- postgres-rag-architect outputs (database schemas, vector storage, audit trails)
- rag-strategy-researcher outputs (retrieval methodologies, reranking strategies)
- scraping-strategy-researcher outputs (regulatory source monitoring)
- tech-stack-researcher outputs (technology selections, security requirements)
- architecture-designer outputs (system architecture, microservices design)
- integration-researcher outputs (external integrations, API specifications)

## Arguments

Parse `$ARGUMENTS` to extract the path to:

- <design-folder-output-path> the design folder containing the design outputs. The path should point to a folder like `.claude/outputs/design/projects/[project-name]/[timestamp]/`

- <app-folder> (optional) the folder that the backend should be built in.

The command will automatically read:

- `MANIFEST.md` - Registry of all design agent outputs with requirements traceability
- `IMPLEMENTATION_PLAN.md` - Unified implementation strategy and technical approach
- `COMPLIANCE_FRAMEWORK.md` - Regulatory compliance guidelines and audit requirements
- Reference all related design agent outputs as indexed by the `MANIFEST.md`
- Check if the `app-folder` is specified. Otherwise, create intelligent folder structure for RAG backend

## Usage Example

```bash
# Implement from design folder path
/implement-app .claude/outputs/design/projects/[project-name]/[timestamp]

# Implement with specific backend folder
/implement-app .claude/outputs/design/projects/[project-name]/[timestamp] ./rag-compliance-backend
```

## Modern TDD Workflow for RAG Backend

### Phase 1: Design Analysis & RAG Architecture Setup (10-15 minutes)

**1. Read ALL Design Specifications First**

Before writing any code or tests, thoroughly analyze the design outputs:

**1.1. RAG Architecture Extraction (CRITICAL)**

BEFORE implementation, extract concrete specifications from design outputs:

```typescript
// Extract from design outputs - example structure
interface RAGConfig {
  vectorStore: {
    dimensions: number; // 1536 for OpenAI embeddings
    indexType: string; // "hnsw" for PostgreSQL pgvector
    chunkSize: number; // 1000 tokens for regulatory docs
    overlap: number; // 200 tokens overlap
  };
  retrieval: {
    hybridWeights: {
      vector: number; // 0.7 weight for semantic search
      keyword: number; // 0.2 weight for exact matches
      metadata: number; // 0.1 weight for regulatory metadata
    };
    rerankingModel: string; // Specific model for regulatory ranking
    topK: number; // Initial retrieval count
    finalK: number; // Post-reranking results
  };
}
```

**Pre-Implementation Validation Checklist**:
- [ ] Database schema includes audit trail tables
- [ ] Vector storage configuration specified (dimensions, index type)
- [ ] RAG pipeline architecture defined (ingestion → storage → retrieval → generation)
- [ ] Reranking strategy specified with concrete models/algorithms
- [ ] Scraping targets and frequencies documented
- [ ] API authentication and authorization patterns defined
- [ ] Compliance logging and reporting requirements specified

**Then proceed with design analysis:**

- `MANIFEST.md` - Understand complete project scope and regulatory requirements
- `IMPLEMENTATION_PLAN.md` - Extract technical specifications and architecture decisions
- `postgres-rag-architect/database-schema.md` - Database design and vector storage
- `rag-strategy-researcher/retrieval-methodology.md` - RAG implementation strategy
- `scraping-strategy-researcher/regulatory-sources-analysis.md` - Document ingestion pipeline
- `tech-stack-researcher/technology-selections.md` - Technology stack and dependencies
- `architecture-designer/system-architecture.md` - Microservices and API design
- `integration-researcher/external-integrations.md` - Third-party service integrations

**2. Initialize Backend Project Based on Design Specs**

Let the IMPLEMENTATION_PLAN.md guide setup, not predetermined patterns:

- Check if the target app-folder already exists
- Assess current state if boilerplate exists
- Install dependencies specified in design outputs (FastAPI/Express, PostgreSQL, pgvector, etc.)
- Configure testing framework for backend APIs and RAG pipelines
- Set up environment configuration for Azure OpenAI, Browserbase, etc.

**3. Write Baseline RAG Pipeline Test**

**🔴 RED Phase**: Write the RAG pipeline test based on design requirements:

- Test derives from actual RAG requirements in MANIFEST.md
- Test document ingestion → vector storage → retrieval → generation flow
- Test must fail initially with clear error message

**🟢 GREEN Phase**: Implement minimal RAG pipeline to pass the test:

- Create basic document ingestion endpoint
- Set up vector storage connection
- Implement simple retrieval mechanism
- No extra features or anticipatory code

**✅ VERIFY Phase**: Confirm test passes and basic RAG flow works

### Phase 2: Database & Vector Storage Implementation (15-20 minutes)

**Database Implementation Strategy**

Based on postgres-rag-architect design outputs:

- PostgreSQL with pgvector extension for vector similarity search
- Audit trail tables for compliance tracking
- Document versioning and metadata storage
- User activity logging for regulatory reporting

**🔴 RED Phase - Write Database Tests**

Create tests that verify the database design from postgres-rag-architect specs:

- Database schema creation tests
- Vector storage and similarity search tests
- Audit trail logging tests
- Document versioning tests
- All tests must fail initially with clear schema-not-found errors

**🟢 GREEN Phase - Implement Database Schema**

Using ONLY the design specifications as reference:

- Implement database schema from `database-schema.md`
- Set up pgvector extension and vector indices
- Create audit trail tables and triggers
- Implement document versioning system

**✅ VERIFY Phase - Confirm All Database Tests Pass**

Run the database test suite:
- Schema creation tests pass
- Vector operations work correctly
- Audit trails capture all required events
- Document versioning functions properly

### Phase 3: RAG Pipeline Implementation (25-30 minutes)

**RAG Implementation Strategy**

Using rag-strategy-researcher design outputs:

- Document chunking and preprocessing
- Vector embedding generation (Azure OpenAI)
- Hybrid retrieval (vector + keyword + metadata)
- Reranking for regulatory relevance
- Response generation with source attribution

**🔴 RED Phase - Write RAG Pipeline Tests**

For EACH RAG component from `retrieval-methodology.md`:

- Document ingestion and chunking tests
- Vector embedding and storage tests
- Hybrid retrieval accuracy tests
- Reranking effectiveness tests
- Response generation and citation tests

**🟢 GREEN Phase - Implement RAG Components**

- Implement document preprocessing pipeline
- Set up Azure OpenAI embedding integration
- Build hybrid retrieval system (vector + keyword + metadata)
- Implement reranking algorithm from design specs
- Create response generation with proper source attribution

**✅ VERIFY Phase - RAG Pipeline Validation**

- All RAG component tests pass
- End-to-end document → query → response flow works
- Retrieval accuracy meets design specifications
- Response citations are accurate and traceable

### Phase 4: Regulatory Scraping & Monitoring (15-20 minutes)

**Scraping Implementation Strategy**

Based on scraping-strategy-researcher design outputs:

- Browserbase integration for web scraping
- Regulatory source monitoring (ESMA, EBA, EIOPA, etc.)
- Document change detection and version tracking
- Automated ingestion pipeline for new regulatory documents

**🔴 RED Phase - Write Scraping Tests**

Create tests based on `regulatory-sources-analysis.md`:

- Browserbase connection and scraping tests
- Document change detection tests
- Automated ingestion pipeline tests
- Error handling and retry mechanism tests

**🟢 GREEN Phase - Implement Scraping System**

- Set up Browserbase integration
- Implement scrapers for each regulatory source
- Build change detection and monitoring system
- Create automated document ingestion pipeline

**✅ VERIFY Phase - Scraping System Validation**

- Browserbase integration works correctly
- Can successfully scrape from regulatory sources
- Change detection identifies document updates
- New documents automatically enter RAG pipeline

### Phase 5: API & Integration Implementation (20-25 minutes)

**API Implementation Strategy**

Using architecture-designer and integration-researcher outputs:

- RESTful API for document queries and analysis
- Authentication and authorization system
- Audit logging for all API operations
- Integration endpoints for external systems
- Real-time regulatory update notifications

**🔴 RED Phase - Write API Tests**

Create comprehensive API tests based on design specifications:

- Authentication and authorization tests
- Document query and analysis endpoint tests
- Audit logging verification tests
- Integration endpoint tests
- Performance and rate limiting tests

**🟢 GREEN Phase - Implement API Layer**

- Build REST API with proper authentication
- Implement document query endpoints with RAG integration
- Set up audit logging for compliance
- Create integration endpoints for external systems
- Implement rate limiting and error handling

**✅ VERIFY Phase - API System Validation**

- All API endpoints function correctly
- Authentication and authorization work properly
- Audit trails capture all API operations
- Integration endpoints support external system connectivity
- Performance meets design specifications

### Phase 6: Compliance & Reporting Implementation (15-20 minutes)

**Compliance System Strategy**

Based on COMPLIANCE_FRAMEWORK.md and audit requirements:

- Regulatory reporting generation
- GAP analysis capabilities
- Cross-jurisdictional comparison tools
- Compliance dashboard data APIs
- Export functionality for regulatory reports

**🔴 RED Phase - Write Compliance Tests**

Create tests for compliance features:

- Regulatory report generation tests
- GAP analysis accuracy tests
- Cross-jurisdictional comparison tests
- Export functionality tests
- Audit trail completeness tests

**🟢 GREEN Phase - Implement Compliance Features**

- Build regulatory report generation system
- Implement GAP analysis algorithms
- Create cross-jurisdictional comparison tools
- Set up export functionality (Word, PDF, Excel)
- Ensure comprehensive audit trail coverage

**✅ VERIFY Phase - Compliance System Validation**

- Regulatory reports generate correctly
- GAP analysis produces accurate results
- Cross-jurisdictional comparisons work properly
- Export functionality supports required formats
- Audit trails meet regulatory requirements

## Implementation Strategy

### Modern TDD with RAG-First Approach

The implementation strategy prioritizes RAG architecture and regulatory compliance:

**Core Workflow**:
1. Read design specifications completely before any implementation
2. Write tests before code (Red → Green → Verify for every component)
3. Build RAG pipeline incrementally with full test coverage
4. Ensure compliance and audit requirements are built-in from the start
5. Let design outputs guide ALL implementation decisions

**Testing Philosophy**:
- **Unit Tests**: Individual RAG components and database operations
- **Integration Tests**: End-to-end RAG pipeline and API workflows
- **Compliance Tests**: Audit trail completeness and regulatory reporting
- **Performance Tests**: Vector search speed and API response times

**Design Integration**:
- `MANIFEST.md`: Requirements and coverage tracking
- `IMPLEMENTATION_PLAN.md`: Technical approach and architecture
- `COMPLIANCE_FRAMEWORK.md`: Regulatory requirements and audit trails
- All agent outputs: Specific technical implementations

## Success Metrics

### RAG Implementation Success
✅ Document ingestion pipeline operational
✅ Vector storage and similarity search working
✅ Hybrid retrieval system implemented
✅ Reranking produces relevant results
✅ Response generation includes proper citations

### Compliance Implementation Success
✅ Audit trails capture all required events
✅ Regulatory reporting functions correctly
✅ GAP analysis produces accurate comparisons
✅ Export functionality supports required formats
✅ Multi-sector adaptability demonstrated

### Backend System Success
✅ All API endpoints functional and tested
✅ Authentication and authorization working
✅ Database performance meets requirements
✅ Integration endpoints support external systems
✅ Error handling and monitoring operational

### Production Readiness
✅ All tests passing (unit → integration → compliance)
✅ Performance benchmarks met
✅ Security requirements satisfied
✅ Documentation complete
✅ Ready for deployment

## Design-Driven TDD Rules

### RAG-Specific Implementation Requirements
- **Must** implement exact RAG pipeline from rag-strategy-researcher outputs
- **Must** use database schema from postgres-rag-architect specifications
- **Must** integrate scraping targets from scraping-strategy-researcher analysis
- **Must** follow API patterns from architecture-designer specifications

### Compliance-First Implementation
- **Must** implement audit trails for all operations
- **Must** support regulatory reporting requirements
- **Must** enable multi-sector adaptability
- **Must** maintain document versioning and change tracking

### RED Phase (Test First)
- Write failing tests based on design specifications
- Database tests check schema and vector operations
- RAG tests verify retrieval accuracy and response quality
- API tests validate endpoints and authentication
- Compliance tests ensure audit trail completeness

### GREEN Phase (Minimal Implementation)
- Implement minimal code to pass current test
- Follow design specifications exactly
- Use technology stack from tech-stack-researcher outputs
- No additional features beyond current test requirements

### VERIFY Phase (System Validation)
- Demonstrate RAG pipeline works end-to-end
- Verify compliance requirements are met
- Validate API functionality and performance
- Ensure audit trails capture all necessary events
- Get user approval before proceeding to next component

## Input

- **Design folder path** (required) - Path to design outputs folder containing MANIFEST.md, IMPLEMENTATION_PLAN.md, and COMPLIANCE_FRAMEWORK.md
- **App folder** (optional) - Target folder for backend implementation

The command automatically determines project setup requirements and implementation approach from the design specifications.

## Philosophy

### Modern RAG Backend TDD Principles

1. **Design as Single Source of Truth** - All implementation decisions derive from design outputs
2. **RAG-First Architecture** - Prioritize document retrieval and generation capabilities
3. **Compliance-Driven Development** - Build audit trails and regulatory features from the start
4. **Test Before Code** - Every component follows Red → Green → Verify discipline
5. **Multi-Sector Adaptability** - Ensure system works across regulated industries
6. **No Assumptions** - If it's not in the design, don't implement it
7. **Continuous Validation** - Verify each component meets regulatory and performance requirements

The goal is to demonstrate that modern TDD with RAG-first architecture creates superior regulatory compliance backends by following design specifications exactly, building quality and compliance in from the start, and maintaining comprehensive test coverage throughout the implementation process.