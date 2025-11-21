---
name: rag-env-validator
description: Validates RAG project environment configuration by checking .env file, Supabase connection, OpenAI API key, and required template files. Use when debugging connection issues or setting up the project for the first time.
---

# RAG Environment Validator

## Instructions

When the user asks to validate the environment, debug connection issues, or verify setup:

1. **Check .env file existence**
   - Verify `backend/.env` exists
   - Show which required variables are present/missing

2. **Verify required environment variables**
   - OPENAI_API_KEY
   - SUPABASE_URL
   - SUPABASE_KEY
   - SUPABASE_SERVICE_KEY
   - LLM_MODEL (default: gpt-4.1-2025-04-14)
   - EMBEDDING_MODEL (default: text-embedding-3-small)

3. **Test API connections**
   - Try OpenAI API call with the key
   - Try Supabase connection with credentials

4. **Verify template files**
   - Check if `backend/agents/templates/Template_Regulatory_Report_AgentIA_v0.docx` exists

5. **Check database accessibility**
   - Verify Supabase table `pd_peru` is accessible
   - Check RPC functions: `match_pd_peru`, `match_pd_peru_by_cluster`

6. **Provide clear diagnosis**
   - Report what's working and what's not
   - Suggest fixes for any issues found

## Examples

- "Validate my environment setup"
- "I'm getting connection errors, can you debug them?"
- "Check if everything is configured correctly"
- "Verify Supabase and OpenAI connections"
