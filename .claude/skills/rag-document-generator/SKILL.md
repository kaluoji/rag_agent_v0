---
name: rag-document-generator
description: Generates formal regulatory report documents in Word format (.docx) from templates and analysis content. Use when creating formal reports, performing GAP analysis reports, or generating compliance documentation.
---

# RAG Document Generator

## Instructions

When the user wants to generate reports or documents:

1. **Verify setup**
   - Check that template exists: `backend/agents/templates/Template_Regulatory_Report_AgentIA_v0.docx`
   - Verify backend is running and accessible
   - Check output directory will be created: `backend/output/reports/`

2. **Understand document generation flow**
   - User query detected as report request
   - Orchestrator routes to AI Expert for analysis
   - AI Expert performs RAG retrieval and analysis
   - Report Agent receives analysis content
   - Report Agent loads template
   - LLM generates content for each section
   - Template placeholders replaced:
     - {{RESUMEN_EJECUTIVO}} → Executive summary
     - {{ALCANCE_ANALISIS}} → Analysis scope
     - {{HALLAZGOS_PRINCIPALES}} → Key findings
     - {{RECOMENDACIONES}} → Recommendations
     - {{REFERENCIAS}} → References

3. **Support different document types**
   - Regulatory compliance reports
   - GAP analysis reports
   - Risk assessment documents
   - Documentation analysis reports

4. **Guide document generation**
   - Help user understand what type of report they need
   - Assist with defining regulatory scope/requirements
   - Help structure the analysis
   - Execute the generation process

5. **Handle output**
   - Show where document will be saved
   - Confirm successful generation
   - Provide download instructions
   - Explain how to preview/edit the document

6. **Troubleshoot issues**
   - Template not found → Check file path
   - Generation errors → Check API connectivity
   - Placeholder issues → Check report_agent.py mapping
   - Formatting problems → Suggest post-generation edits

## Examples

- "Generate a regulatory compliance report"
- "Create a GAP analysis document"
- "I need a formal report for this regulation"
- "Generate documentation for GDPR compliance"
- "Create a compliance assessment report"
- "Help me prepare a regulatory analysis document"
