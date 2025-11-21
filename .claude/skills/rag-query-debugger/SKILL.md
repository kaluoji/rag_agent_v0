---
name: rag-query-debugger
description: Debugs and troubleshoots failing queries by checking configuration, testing connections, and executing debug queries. Use when a query fails or returns unexpected results to diagnose the issue.
---

# RAG Query Debugger

## Instructions

When the user has issues with query execution or results:

1. **Check project configuration**
   - Verify `.env` file has all required keys
   - Confirm OPENAI_API_KEY and SUPABASE credentials are valid
   - Check that LLM_MODEL and EMBEDDING_MODEL are set

2. **Test connections**
   - Test OpenAI API connectivity
   - Test Supabase connection
   - Verify database tables are accessible
   - Check RPC functions: `match_pd_peru`, `match_pd_peru_by_cluster`

3. **Examine orchestrator flow**
   - Check `backend/agents/orchestrator_agent.py`
   - Verify routing logic for agent selection
   - Check if query understanding is being triggered

4. **Debug AI Expert agent**
   - Review `backend/agents/ai_expert_v1.py`
   - Check retrieval pipeline:
     - Vector similarity search
     - BM25 lexical search
     - Cluster-based expansion
     - Entity-based search
   - Verify reranking logic
   - Check tool state caching via MD5 hash

5. **Test with sample query**
   - Execute a simple test query
   - Show results from each retrieval stage
   - Display final ranked results
   - Show LLM response

6. **Diagnose issues**
   - No results returned → Check Supabase table and RPC functions
   - Poor quality results → Check reranking or retrieval parameters
   - Timeout → Check API rate limits and network
   - Agent selection wrong → Check orchestrator logic
   - Missing context → Check query understanding decomposition

7. **Provide solutions**
   - Clear explanation of what's failing
   - Step-by-step fix recommendations
   - Links to relevant code sections

## Examples

- "Debug my query, it's not working"
- "Why is the RAG system returning bad results?"
- "Check the retrieval pipeline"
- "The orchestrator is routing to the wrong agent"
- "Verify the database connection"
