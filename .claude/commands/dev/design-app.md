---
allowed-tools: Task, Read, Write, TodoWrite
description: Design RAG-powered regulatory compliance system architecture from PRD with multi-sector adaptability
argument-hint: <prd-file-path>
---

# RAG Regulatory Compliance System Design Command

Create a comprehensive RAG system design with test-first specifications for regulatory compliance across multiple sectors, based on a Product Requirements Document (PRD).

## Usage Examples

Analyze PRD file referenced from `$ARGUMENTS`. It may be passed directly as text, or as a file reference, or with parameters.
```bash
# Design from PRD file
/design-app --prd=docs/projects/compliance-rag/prd.md

# Design with specific regulatory focus
/design-app --prd=projects/compliance/prd.md --sector=healthcare

# Design with custom output location
/design-app --prd=specs/regulatory-system.md --output=designs/compliance-rag
PRD-Driven Design Philosophy
The command analyzes a Product Requirements Document to create a complete RAG regulatory compliance system:

PRD Analysis: Extract compliance features, regulatory requirements, and technical specifications
Multi-Sector Adaptability: Design for healthcare, finance, manufacturing, and other regulated industries
RAG-First Architecture: Focus on retrieval-augmented generation for regulatory document analysis
Compliance-Driven Design: Ensure audit trails, document versioning, and regulatory reporting capabilities

Workflow (Orchestrator-Managed Sequential then Parallel Coordination)
Following orchestrator-initialized workflow with structured project setup and validation:
Phase 1: Orchestrator Initialization (Sequential - Project Setup)
Agent: orchestrator
Output: .claude/outputs/design/projects/[project-name]/[timestamp]/
Purpose:

Analyze PRD and confirm regulatory compliance scope
Generate consistent project name and timestamp
Create initial MANIFEST.md with requirements baseline
Establish sector-agnostic compliance framework

Phase 2: UI Design Foundation (Sequential - Foundation Required)
Agent: ui-designer
Output: .claude/outputs/design/agents/ui-designer/[project-name]-[timestamp]/
Purpose:

Read PRD and create compliance-focused wireframes
Design regulatory dashboard interfaces
Create document analysis and reporting workflows
Plan multi-role user interfaces (compliance officers, analysts, auditors)

Phase 3: Parallel Core Architecture Design
Executed Simultaneously after Phase 2 completion:
You MUST execute all Phase 3 agents in parallel using multiple Task tool calls in a single message.
bash- postgres-rag-architect → Database design for regulatory documents, vector storage, audit trails
- rag-strategy-researcher → RAG methodologies, reranking, hybrid retrieval for compliance documents  
- scraping-strategy-researcher → Regulatory source scraping, official document monitoring
- tech-stack-researcher → Technology selection for compliance, security, and scalability
- architecture-designer → Overall system architecture, microservices, compliance workflows
Phase 4: Integration Research (Sequential - Requires Core Architecture)
Agent: integration-researcher
Output: .claude/outputs/design/agents/integration-researcher/[project-name]-[timestamp]/
Purpose:

Design integration patterns with external compliance systems
Plan API strategies for regulatory data feeds
Define webhook patterns for real-time regulatory updates
Specify authentication and authorization for multi-sector compliance

Phase 5: Orchestrator Synthesis (Sequential - Requires All Inputs)
Agent: orchestrator
Output: .claude/outputs/design/projects/[project-name]/[timestamp]/
Purpose: Synthesize all agent outputs into coherent implementation plan
Input: All agent outputs from Phases 2-4 + initial MANIFEST from Phase 1
Validates:

✓ All PRD requirements have corresponding design outputs
✓ UI wireframes cover all compliance workflows
✓ RAG architecture addresses all document analysis requirements
✓ Database design supports audit trails and regulatory reporting
✓ Scraping strategies cover all specified regulatory sources
✓ Integration patterns support multi-sector adaptability
✓ Cross-agent consistency and compliance requirements
Output:
MANIFEST.md - Final registry linking all agent outputs with requirements traceability
IMPLEMENTATION_PLAN.md - Single source of truth for implementation
COMPLIANCE_FRAMEWORK.md - Sector-agnostic compliance guidelines

Output Structure
Phase 1 (Orchestrator Initialization):
.claude/outputs/design/projects/[project-name]/[timestamp]/
└── MANIFEST.md                   # Initial requirements baseline and agent registry
Phase 2 (Sequential - UI Foundation):
.claude/outputs/design/agents/
└── ui-designer/[project-name]-[timestamp]/
    ├── compliance-wireframes.md
    ├── regulatory-dashboard-design.md
    └── workflow-specifications.md
Phase 3 (Parallel Execution):
.claude/outputs/design/agents/
├── postgres-rag-architect/[project-name]-[timestamp]/
│   ├── database-schema.md
│   ├── vector-storage-design.md
│   └── audit-trail-specifications.md
├── rag-strategy-researcher/[project-name]-[timestamp]/
│   ├── retrieval-methodology.md
│   ├── reranking-strategies.md
│   └── hybrid-search-design.md
├── scraping-strategy-researcher/[project-name]-[timestamp]/
│   ├── regulatory-sources-analysis.md
│   ├── scraping-methodologies.md
│   └── monitoring-strategies.md
├── tech-stack-researcher/[project-name]-[timestamp]/
│   ├── technology-selections.md
│   ├── security-requirements.md
│   └── scalability-analysis.md
└── architecture-designer/[project-name]-[timestamp]/
    ├── system-architecture.md
    ├── microservices-design.md
    └── compliance-workflows.md
Phase 4 (Sequential - Integration Research):
.claude/outputs/design/agents/
└── integration-researcher/[project-name]-[timestamp]/
    ├── external-integrations.md
    ├── api-specifications.md
    └── authentication-patterns.md
Phase 5 (Sequential - Final Synthesis):
.claude/outputs/design/projects/[project-name]/[timestamp]/
├── MANIFEST.md                   # Complete registry with requirements traceability
├── IMPLEMENTATION_PLAN.md        # Unified implementation plan
└── COMPLIANCE_FRAMEWORK.md       # Sector-agnostic compliance guidelines
Critical Implementation Pattern for Phase 3
Parallel Execution Requirements:
bash# CORRECT: Five Task tool calls in single message for parallel execution
<invoke name="Task">
  # postgres-rag-architect task
</invoke>
<invoke name="Task">
  # rag-strategy-researcher task
</invoke>
<invoke name="Task">
  # scraping-strategy-researcher task
</invoke>
<invoke name="Task">
  # tech-stack-researcher task
</invoke>
<invoke name="Task">
  # architecture-designer task
</invoke>

# INCORRECT: Sequential Task calls (not parallel)
Multi-Sector Compliance Design
The design ensures adaptability across regulated industries:

Healthcare: HIPAA, FDA, medical device regulations
Financial Services: SOX, Basel III, MiFID II, Dodd-Frank
Manufacturing: ISO standards, environmental regulations
Energy: NERC, environmental compliance
Generic Framework: Extensible for any regulatory environment

RAG-Specific Design Requirements
The design optimizes for regulatory document analysis:

Document Ingestion: Multi-format support (PDF, Word, HTML, XML)
Vector Storage: Optimized for regulatory text chunking and retrieval
Hybrid Search: Vector similarity + keyword + metadata filtering
Reranking: Regulatory relevance scoring and compliance prioritization
Audit Trails: Complete document lineage and analysis history
Version Control: Regulatory document change tracking

Input Parameters

--prd: Path to PRD file (required)
--sector: Specific regulatory sector focus (optional)
--output: Custom output directory (optional)
--compliance-level: Regulatory compliance level (standard, enhanced, enterprise)

Success Criteria
A complete design includes outputs from all phases:

✓ Phase 1: Project setup & initial MANIFEST (orchestrator initialization)
✓ Phase 2: Compliance UI wireframes & workflows (ui-designer)
✓ Phase 3: Core architecture components (5 parallel agents)
✓ Phase 4: Integration patterns & external systems (integration-researcher)
✓ Phase 5: Complete MANIFEST + unified plans (orchestrator synthesis)

Integration with Implementation
Output feeds directly into:

/implement-app for backend RAG implementation
/implement-fullstack-app for complete system implementation
Regulatory compliance validation and testing
Multi-sector deployment strategies