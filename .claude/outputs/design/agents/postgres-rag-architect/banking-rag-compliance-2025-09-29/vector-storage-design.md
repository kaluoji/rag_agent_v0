# Vector Storage Design for Banking RAG Compliance System

## Executive Summary

This document presents an advanced vector storage architecture optimized for regulatory document embeddings in the Banking RAG Compliance System. The design leverages pgvector 0.8.0's latest capabilities, including HNSW indexing, multiple vector types, and iterative scanning for superior performance in complex regulatory scenarios. The architecture supports multi-modal embeddings, sophisticated chunking strategies, and hybrid search capabilities essential for accurate regulatory compliance queries.

## Architecture Overview

The vector storage system implements a multi-layered approach optimized for regulatory document characteristics:

1. **Hierarchical Document Chunking** - Semantic chunking that preserves regulatory structure
2. **Multi-Modal Embeddings** - Dense, sparse, and specialized regulatory embeddings
3. **HNSW Index Optimization** - Configured for regulatory document similarity patterns
4. **Hybrid Search Integration** - Combining semantic and keyword-based retrieval
5. **Performance Monitoring** - Real-time vector search optimization

## Document Chunking Strategy

### 1. Regulatory-Aware Chunking

Regulatory documents have unique structural characteristics that require specialized chunking approaches:

```sql
-- Regulatory document chunk types with specific handling
CREATE TYPE regulatory_chunk_type AS ENUM (
    'article',           -- Legal articles with numbered sections
    'paragraph',         -- Standard paragraphs
    'definition',        -- Regulatory definitions
    'requirement',       -- Compliance requirements
    'procedure',         -- Procedural steps
    'exception',         -- Exceptions and exemptions
    'cross_reference',   -- References to other regulations
    'table',            -- Regulatory tables and matrices
    'appendix',         -- Appendices and annexes
    'schedule',         -- Implementation schedules
    'formula'           -- Mathematical formulas and calculations
);

-- Enhanced document chunks table with regulatory context
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_id UUID REFERENCES document_versions(id),

    -- Chunk identification
    chunk_index INTEGER NOT NULL,
    chunk_type regulatory_chunk_type NOT NULL,
    regulatory_section TEXT, -- e.g., "Article 15.3.a"

    -- Content and metadata
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    token_count INTEGER NOT NULL CHECK (token_count > 0),
    character_count INTEGER NOT NULL CHECK (character_count > 0),

    -- Structural context preservation
    parent_section TEXT,     -- Hierarchical context
    section_depth INTEGER DEFAULT 0,
    preceding_context TEXT,  -- Context from previous chunks
    following_context TEXT,  -- Context from following chunks

    -- Regulatory-specific metadata
    structural_metadata JSONB DEFAULT '{}'::JSONB,
    regulatory_concepts TEXT[],  -- Extracted regulatory concepts
    jurisdiction_scope TEXT[],   -- Applicable jurisdictions
    compliance_topics TEXT[],    -- Compliance subject areas
    effective_date DATE,         -- When this chunk becomes effective

    -- Primary embedding
    content_embedding vector(1536),

    -- Search optimization
    search_vector tsvector,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_document_chunk UNIQUE (document_id, chunk_index),
    CONSTRAINT valid_content_hash CHECK (LENGTH(content_hash) = 64),
    CONSTRAINT valid_section_depth CHECK (section_depth >= 0 AND section_depth <= 10)
);

-- Comments
COMMENT ON TABLE document_chunks IS 'Regulatory document chunks with structural preservation';
COMMENT ON COLUMN document_chunks.regulatory_section IS 'Regulatory section identifier (Article 15.3.a)';
COMMENT ON COLUMN document_chunks.structural_metadata IS 'Headers, footnotes, cross-references, formatting';
COMMENT ON COLUMN document_chunks.regulatory_concepts IS 'Extracted regulatory concepts for enhanced retrieval';
```

### 2. Intelligent Chunking Function

```sql
-- Advanced chunking function for regulatory documents
CREATE OR REPLACE FUNCTION create_regulatory_chunks(
    p_document_id UUID,
    p_content TEXT,
    p_document_type TEXT,
    p_authority_code TEXT
) RETURNS INTEGER AS $$
DECLARE
    chunk_size INTEGER;
    overlap_size INTEGER;
    chunk_count INTEGER := 0;
    chunk_start INTEGER := 1;
    chunk_end INTEGER;
    current_chunk TEXT;
    section_pattern TEXT;
    chunk_type regulatory_chunk_type;
    regulatory_section TEXT;
    parent_section TEXT := '';
    section_depth INTEGER := 0;
BEGIN
    -- Adjust chunk size based on document type and authority
    chunk_size := CASE
        WHEN p_document_type = 'regulation' THEN 800    -- Larger for complex regulations
        WHEN p_document_type = 'guideline' THEN 600     -- Medium for guidelines
        WHEN p_document_type = 'consultation' THEN 500  -- Smaller for consultations
        ELSE 700  -- Default size
    END;

    overlap_size := chunk_size / 10; -- 10% overlap

    -- Authority-specific section patterns
    section_pattern := CASE
        WHEN p_authority_code IN ('ESMA', 'EBA', 'EIOPA') THEN 'Article \d+(\.\d+)*'
        WHEN p_authority_code = 'EC' THEN '(Article|Chapter|Section) \d+'
        WHEN p_authority_code IN ('BOS', 'CNMV') THEN '(Artículo|Sección) \d+'
        ELSE '\d+(\.\d+)*'
    END;

    WHILE chunk_start <= LENGTH(p_content) LOOP
        -- Calculate chunk end with smart boundary detection
        chunk_end := chunk_start + chunk_size;

        -- Adjust to sentence boundary if possible
        IF chunk_end < LENGTH(p_content) THEN
            -- Look for sentence end within next 100 characters
            FOR i IN 0..100 LOOP
                IF SUBSTRING(p_content, chunk_end + i, 1) IN ('.', '!', '?', ';') AND
                   SUBSTRING(p_content, chunk_end + i + 1, 1) = ' ' THEN
                    chunk_end := chunk_end + i + 1;
                    EXIT;
                END IF;
            END LOOP;
        END IF;

        -- Extract chunk content
        current_chunk := SUBSTRING(p_content, chunk_start, chunk_end - chunk_start);

        -- Determine chunk type and regulatory section
        SELECT INTO chunk_type, regulatory_section, parent_section, section_depth
            detect_regulatory_chunk_type(current_chunk, section_pattern);

        -- Insert chunk with enhanced metadata
        INSERT INTO document_chunks (
            document_id,
            chunk_index,
            chunk_type,
            regulatory_section,
            content,
            content_hash,
            token_count,
            character_count,
            parent_section,
            section_depth,
            preceding_context,
            following_context,
            structural_metadata,
            regulatory_concepts,
            search_vector
        ) VALUES (
            p_document_id,
            chunk_count,
            chunk_type,
            regulatory_section,
            current_chunk,
            encode(sha256(current_chunk::bytea), 'hex'),
            estimate_token_count(current_chunk),
            LENGTH(current_chunk),
            parent_section,
            section_depth,
            -- Preceding context (last 200 chars of previous chunk)
            CASE WHEN chunk_start > 200 THEN
                SUBSTRING(p_content, chunk_start - 200, 200)
                ELSE NULL
            END,
            -- Following context (first 200 chars of next chunk)
            CASE WHEN chunk_end + 200 <= LENGTH(p_content) THEN
                SUBSTRING(p_content, chunk_end, 200)
                ELSE NULL
            END,
            extract_structural_metadata(current_chunk),
            extract_regulatory_concepts(current_chunk, p_authority_code),
            to_tsvector('english', current_chunk)
        );

        chunk_count := chunk_count + 1;
        chunk_start := chunk_end - overlap_size;
    END LOOP;

    RETURN chunk_count;
END;
$$ LANGUAGE plpgsql;

-- Helper function to detect regulatory chunk types
CREATE OR REPLACE FUNCTION detect_regulatory_chunk_type(
    content TEXT,
    section_pattern TEXT
) RETURNS RECORD AS $$
DECLARE
    result RECORD;
BEGIN
    -- Initialize result
    SELECT 'paragraph'::regulatory_chunk_type as chunk_type,
           NULL::TEXT as regulatory_section,
           NULL::TEXT as parent_section,
           0 as section_depth
    INTO result;

    -- Detect article/section patterns
    IF content ~* section_pattern THEN
        result.chunk_type := 'article';
        result.regulatory_section := (regexp_matches(content, section_pattern, 'i'))[1];
        result.section_depth := array_length(string_to_array(result.regulatory_section, '.'), 1);
    -- Detect definitions
    ELSIF content ~* '^(Definition|Definitions?|For the purposes?)' THEN
        result.chunk_type := 'definition';
    -- Detect requirements
    ELSIF content ~* '(shall|must|required|mandatory|obliged|ensure)' THEN
        result.chunk_type := 'requirement';
    -- Detect procedures
    ELSIF content ~* '(procedure|process|step|method|way|manner)' THEN
        result.chunk_type := 'procedure';
    -- Detect exceptions
    ELSIF content ~* '(except|however|notwithstanding|provided that|unless)' THEN
        result.chunk_type := 'exception';
    -- Detect tables
    ELSIF content ~* '(table|matrix|schedule|list)' AND content ~ E'\t|\|' THEN
        result.chunk_type := 'table';
    END IF;

    RETURN result;
END;
$$ LANGUAGE plpgsql;
```

## Multi-Modal Embedding Strategy

### 1. Enhanced Embedding Storage

```sql
-- Advanced embedding storage with multiple embedding types
CREATE TABLE chunk_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,

    -- Embedding model information
    embedding_model TEXT NOT NULL,
    model_version TEXT,
    embedding_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Vector dimensions and types
    dimensions INTEGER NOT NULL CHECK (dimensions > 0 AND dimensions <= 2000),

    -- Different embedding types for various use cases
    dense_embedding vector(1536),       -- Primary dense embedding (OpenAI)
    sparse_embedding sparsevec(1000),   -- Sparse embedding for keyword matching
    regulatory_embedding vector(768),    -- Specialized regulatory domain embedding
    multilingual_embedding vector(512), -- Multi-language support

    -- Embedding metadata and quality metrics
    embedding_quality_score FLOAT CHECK (embedding_quality_score >= 0 AND embedding_quality_score <= 1),
    processing_metadata JSONB DEFAULT '{}',

    -- Performance optimization
    embedding_norm FLOAT, -- Pre-computed L2 norm for faster similarity

    CONSTRAINT unique_chunk_model UNIQUE (chunk_id, embedding_model, model_version),
    CONSTRAINT valid_dimensions CHECK (dimensions > 0 AND dimensions <= 2000)
);

-- Indexes for different embedding types
CREATE INDEX CONCURRENTLY idx_chunk_embeddings_dense_hnsw
ON chunk_embeddings USING hnsw (dense_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX CONCURRENTLY idx_chunk_embeddings_regulatory_hnsw
ON chunk_embeddings USING hnsw (regulatory_embedding vector_cosine_ops)
WITH (m = 12, ef_construction = 32);

CREATE INDEX CONCURRENTLY idx_chunk_embeddings_sparse
ON chunk_embeddings USING gin (sparse_embedding);

-- Enable iterative scanning for complex queries
SET hnsw.iterative_scan = ON;
```

### 2. Embedding Generation Pipeline

```sql
-- Embedding generation coordination table
CREATE TABLE embedding_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    chunk_id UUID REFERENCES document_chunks(id),
    job_type TEXT NOT NULL CHECK (job_type IN ('document', 'chunk', 'batch')),

    -- Job configuration
    embedding_models TEXT[] NOT NULL,
    processing_parameters JSONB DEFAULT '{}',

    -- Job status tracking
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'retry')),
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),

    -- Progress tracking
    total_items INTEGER,
    completed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,

    -- Timing and error tracking
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Resource usage
    processing_time_ms BIGINT,
    tokens_processed INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Function to create embeddings for regulatory content
CREATE OR REPLACE FUNCTION generate_chunk_embeddings(
    p_chunk_id UUID,
    p_models TEXT[] DEFAULT ARRAY['openai-ada-002', 'regulatory-bert', 'multilingual']
) RETURNS BOOLEAN AS $$
DECLARE
    chunk_record RECORD;
    model_name TEXT;
    job_id UUID;
BEGIN
    -- Get chunk details
    SELECT dc.*, d.language, d.document_type, ra.code as authority_code
    INTO chunk_record
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    JOIN regulatory_authorities ra ON d.authority_id = ra.id
    WHERE dc.id = p_chunk_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Chunk not found: %', p_chunk_id;
    END IF;

    -- Create embedding job
    INSERT INTO embedding_jobs (
        chunk_id,
        job_type,
        embedding_models,
        total_items,
        processing_parameters
    ) VALUES (
        p_chunk_id,
        'chunk',
        p_models,
        array_length(p_models, 1),
        jsonb_build_object(
            'document_type', chunk_record.document_type,
            'language', chunk_record.language,
            'authority_code', chunk_record.authority_code,
            'chunk_type', chunk_record.chunk_type
        )
    ) RETURNING id INTO job_id;

    -- Process each embedding model
    FOREACH model_name IN ARRAY p_models LOOP
        PERFORM process_single_embedding(p_chunk_id, model_name, job_id, chunk_record);
    END LOOP;

    -- Update job completion
    UPDATE embedding_jobs
    SET status = 'completed',
        completed_at = NOW(),
        completed_items = array_length(p_models, 1)
    WHERE id = job_id;

    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        -- Update job as failed
        UPDATE embedding_jobs
        SET status = 'failed',
            error_message = SQLERRM,
            completed_at = NOW()
        WHERE id = job_id;

        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;
```

## Advanced Vector Search Optimization

### 1. HNSW Index Configuration

```sql
-- Optimized HNSW indexes for different query patterns
-- Primary dense embedding index (high accuracy)
CREATE INDEX CONCURRENTLY idx_chunks_dense_embedding_high_accuracy
ON document_chunks USING hnsw (content_embedding vector_cosine_ops)
WITH (m = 24, ef_construction = 128);

-- Fast similarity index (balanced performance)
CREATE INDEX CONCURRENTLY idx_chunks_dense_embedding_balanced
ON document_chunks USING hnsw (content_embedding vector_l2_ops)
WITH (m = 16, ef_construction = 64);

-- Memory-efficient index for large-scale deployment
CREATE INDEX CONCURRENTLY idx_chunks_dense_embedding_efficient
ON document_chunks USING hnsw (content_embedding vector_ip_ops)
WITH (m = 8, ef_construction = 32);

-- Regulatory-specific indexes with filtering
CREATE INDEX CONCURRENTLY idx_chunks_regulatory_filtered
ON document_chunks USING hnsw (content_embedding vector_cosine_ops)
INCLUDE (document_id, chunk_type, regulatory_section)
WITH (m = 16, ef_construction = 64);

-- Authority-specific partial indexes
CREATE INDEX CONCURRENTLY idx_chunks_esma_documents
ON document_chunks USING hnsw (content_embedding vector_cosine_ops)
WHERE EXISTS (
    SELECT 1 FROM documents d
    JOIN regulatory_authorities ra ON d.authority_id = ra.id
    WHERE d.id = document_chunks.document_id AND ra.code = 'ESMA'
);
```

### 2. Hybrid Search Implementation

```sql
-- Advanced hybrid search function with regulatory context
CREATE OR REPLACE FUNCTION regulatory_hybrid_search(
    query_text TEXT,
    query_embedding vector(1536),
    user_context JSONB DEFAULT '{}',
    search_params JSONB DEFAULT '{}'
) RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    authority_code TEXT,
    regulatory_section TEXT,
    chunk_type regulatory_chunk_type,
    content TEXT,
    similarity_score FLOAT,
    keyword_score FLOAT,
    regulatory_relevance_score FLOAT,
    combined_score FLOAT,
    explanation JSONB
) AS $$
DECLARE
    similarity_threshold FLOAT := COALESCE((search_params->>'similarity_threshold')::FLOAT, 0.75);
    max_results INTEGER := COALESCE((search_params->>'max_results')::INTEGER, 20);
    authority_filter TEXT[] := CASE
        WHEN search_params ? 'authorities' THEN
            ARRAY(SELECT jsonb_array_elements_text(search_params->'authorities'))
        ELSE NULL
    END;
    jurisdiction_filter TEXT := search_params->>'jurisdiction';
    user_role TEXT := user_context->>'role';
    user_language TEXT := COALESCE(user_context->>'language', 'en');
BEGIN
    RETURN QUERY
    WITH vector_search AS (
        -- Vector similarity search with regulatory context
        SELECT
            dc.id as chunk_id,
            dc.document_id,
            ra.code as authority_code,
            dc.regulatory_section,
            dc.chunk_type,
            dc.content,
            (1 - (dc.content_embedding <=> query_embedding)) as similarity_score,
            -- Boost score based on chunk type relevance
            CASE dc.chunk_type
                WHEN 'requirement' THEN 1.2
                WHEN 'definition' THEN 1.1
                WHEN 'article' THEN 1.0
                WHEN 'procedure' THEN 0.9
                ELSE 0.8
            END as type_boost
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        JOIN regulatory_authorities ra ON d.authority_id = ra.id
        WHERE d.status = 'published'
            AND d.language = user_language
            AND (authority_filter IS NULL OR ra.code = ANY(authority_filter))
            AND (jurisdiction_filter IS NULL OR ra.jurisdiction = jurisdiction_filter)
            AND (dc.content_embedding <=> query_embedding) < (1 - similarity_threshold)
        ORDER BY dc.content_embedding <=> query_embedding
        LIMIT max_results * 2
    ),
    keyword_search AS (
        -- Full-text search with regulatory weighting
        SELECT
            dc.id as chunk_id,
            dc.document_id,
            ra.code as authority_code,
            dc.regulatory_section,
            dc.chunk_type,
            dc.content,
            ts_rank_cd(
                dc.search_vector,
                plainto_tsquery(user_language, query_text),
                32 -- Cover density ranking
            ) as keyword_score
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        JOIN regulatory_authorities ra ON d.authority_id = ra.id
        WHERE d.status = 'published'
            AND d.language = user_language
            AND (authority_filter IS NULL OR ra.code = ANY(authority_filter))
            AND (jurisdiction_filter IS NULL OR ra.jurisdiction = jurisdiction_filter)
            AND dc.search_vector @@ plainto_tsquery(user_language, query_text)
        ORDER BY ts_rank_cd(dc.search_vector, plainto_tsquery(user_language, query_text)) DESC
        LIMIT max_results * 2
    ),
    regulatory_relevance AS (
        -- Calculate regulatory relevance based on user role and content
        SELECT
            dc.id as chunk_id,
            CASE user_role
                WHEN 'compliance_officer' THEN
                    CASE WHEN dc.chunk_type IN ('requirement', 'procedure') THEN 1.0
                         WHEN dc.chunk_type = 'exception' THEN 0.9
                         ELSE 0.7 END
                WHEN 'legal_analyst' THEN
                    CASE WHEN dc.chunk_type IN ('definition', 'article') THEN 1.0
                         WHEN dc.chunk_type = 'cross_reference' THEN 0.9
                         ELSE 0.6 END
                WHEN 'risk_manager' THEN
                    CASE WHEN dc.chunk_type = 'requirement' THEN 1.0
                         WHEN dc.chunk_type = 'procedure' THEN 0.8
                         ELSE 0.5 END
                ELSE 0.8
            END as regulatory_relevance_score
        FROM document_chunks dc
    ),
    combined_results AS (
        SELECT
            COALESCE(v.chunk_id, k.chunk_id) as chunk_id,
            COALESCE(v.document_id, k.document_id) as document_id,
            COALESCE(v.authority_code, k.authority_code) as authority_code,
            COALESCE(v.regulatory_section, k.regulatory_section) as regulatory_section,
            COALESCE(v.chunk_type, k.chunk_type) as chunk_type,
            COALESCE(v.content, k.content) as content,
            COALESCE(v.similarity_score * v.type_boost, 0) as similarity_score,
            COALESCE(k.keyword_score, 0) as keyword_score,
            r.regulatory_relevance_score,
            -- Weighted combination of scores
            (
                COALESCE(v.similarity_score * v.type_boost, 0) * 0.5 +
                COALESCE(k.keyword_score, 0) * 0.3 +
                r.regulatory_relevance_score * 0.2
            ) as combined_score,
            jsonb_build_object(
                'vector_score', COALESCE(v.similarity_score, 0),
                'keyword_score', COALESCE(k.keyword_score, 0),
                'type_boost', COALESCE(v.type_boost, 1.0),
                'regulatory_relevance', r.regulatory_relevance_score,
                'search_method', CASE
                    WHEN v.chunk_id IS NOT NULL AND k.chunk_id IS NOT NULL THEN 'hybrid'
                    WHEN v.chunk_id IS NOT NULL THEN 'vector'
                    ELSE 'keyword'
                END
            ) as explanation
        FROM vector_search v
        FULL OUTER JOIN keyword_search k ON v.chunk_id = k.chunk_id
        LEFT JOIN regulatory_relevance r ON COALESCE(v.chunk_id, k.chunk_id) = r.chunk_id
    )
    SELECT
        cr.chunk_id,
        cr.document_id,
        cr.authority_code,
        cr.regulatory_section,
        cr.chunk_type,
        cr.content,
        cr.similarity_score,
        cr.keyword_score,
        cr.regulatory_relevance_score,
        cr.combined_score,
        cr.explanation
    FROM combined_results cr
    ORDER BY cr.combined_score DESC, cr.similarity_score DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;
```

### 3. Query Optimization and Caching

```sql
-- Query result caching for frequent searches
CREATE TABLE vector_search_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash TEXT NOT NULL UNIQUE,
    query_text TEXT,
    query_embedding vector(1536),
    search_parameters JSONB,
    result_chunk_ids UUID[],
    result_scores FLOAT[],
    cache_metadata JSONB DEFAULT '{}',
    hit_count INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '1 hour')
);

-- Index for cache lookup
CREATE INDEX CONCURRENTLY idx_vector_search_cache_hash ON vector_search_cache (query_hash);
CREATE INDEX CONCURRENTLY idx_vector_search_cache_expiry ON vector_search_cache (expires_at);

-- Function to get or create cached search results
CREATE OR REPLACE FUNCTION get_cached_search_results(
    p_query_text TEXT,
    p_query_embedding vector(1536),
    p_search_params JSONB DEFAULT '{}'
) RETURNS TABLE (
    chunk_id UUID,
    similarity_score FLOAT,
    from_cache BOOLEAN
) AS $$
DECLARE
    query_hash_val TEXT;
    cache_record RECORD;
    chunk_ids UUID[];
    scores FLOAT[];
BEGIN
    -- Generate query hash
    query_hash_val := encode(
        sha256(
            (p_query_text || p_query_embedding::TEXT || p_search_params::TEXT)::bytea
        ),
        'hex'
    );

    -- Check cache
    SELECT * INTO cache_record
    FROM vector_search_cache
    WHERE query_hash = query_hash_val
        AND expires_at > NOW();

    IF FOUND THEN
        -- Update cache statistics
        UPDATE vector_search_cache
        SET hit_count = hit_count + 1,
            last_accessed_at = NOW()
        WHERE id = cache_record.id;

        -- Return cached results
        FOR i IN 1..array_length(cache_record.result_chunk_ids, 1) LOOP
            chunk_id := cache_record.result_chunk_ids[i];
            similarity_score := cache_record.result_scores[i];
            from_cache := TRUE;
            RETURN NEXT;
        END LOOP;
    ELSE
        -- Perform actual search and cache results
        SELECT array_agg(hs.chunk_id), array_agg(hs.combined_score)
        INTO chunk_ids, scores
        FROM regulatory_hybrid_search(p_query_text, p_query_embedding, '{}', p_search_params) hs;

        -- Cache the results
        INSERT INTO vector_search_cache (
            query_hash,
            query_text,
            query_embedding,
            search_parameters,
            result_chunk_ids,
            result_scores,
            cache_metadata
        ) VALUES (
            query_hash_val,
            p_query_text,
            p_query_embedding,
            p_search_params,
            chunk_ids,
            scores,
            jsonb_build_object(
                'result_count', array_length(chunk_ids, 1),
                'cached_at', NOW()
            )
        );

        -- Return fresh results
        FOR i IN 1..array_length(chunk_ids, 1) LOOP
            chunk_id := chunk_ids[i];
            similarity_score := scores[i];
            from_cache := FALSE;
            RETURN NEXT;
        END LOOP;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

## Performance Monitoring and Optimization

### 1. Vector Search Performance Metrics

```sql
-- Vector search performance tracking
CREATE TABLE vector_search_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Query identification
    query_hash TEXT,
    user_id UUID REFERENCES auth.users(id),
    search_type TEXT CHECK (search_type IN ('vector', 'hybrid', 'keyword')),

    -- Query parameters
    query_length INTEGER,
    embedding_model TEXT,
    similarity_threshold FLOAT,
    result_limit INTEGER,

    -- Performance metrics
    total_execution_time_ms FLOAT NOT NULL,
    vector_search_time_ms FLOAT,
    keyword_search_time_ms FLOAT,
    result_processing_time_ms FLOAT,

    -- Result quality metrics
    total_results INTEGER,
    avg_similarity_score FLOAT,
    result_diversity_score FLOAT,

    -- Resource usage
    memory_usage_mb FLOAT,
    cpu_time_ms FLOAT,
    index_cache_hits INTEGER,
    index_cache_misses INTEGER,

    -- Query characteristics
    filters_applied JSONB,
    index_used TEXT,
    query_plan_hash TEXT,

    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance analysis
CREATE INDEX CONCURRENTLY idx_vector_search_metrics_execution_time
ON vector_search_metrics (executed_at DESC, total_execution_time_ms DESC);

CREATE INDEX CONCURRENTLY idx_vector_search_metrics_user_performance
ON vector_search_metrics (user_id, executed_at DESC);
```

### 2. Automated Performance Optimization

```sql
-- Index maintenance and optimization
CREATE OR REPLACE FUNCTION optimize_vector_indexes()
RETURNS void AS $$
DECLARE
    index_name TEXT;
    table_name TEXT;
    index_size BIGINT;
    fragmentation_ratio FLOAT;
BEGIN
    -- Monitor HNSW index performance
    FOR index_name, table_name, index_size, fragmentation_ratio IN
        SELECT
            indexname,
            tablename,
            pg_relation_size(indexname::regclass),
            -- Estimate fragmentation based on index size vs table size ratio
            pg_relation_size(indexname::regclass)::FLOAT /
            GREATEST(pg_relation_size(tablename::regclass), 1)
        FROM pg_indexes
        WHERE indexname LIKE 'idx_%_hnsw'
    LOOP
        -- Log index statistics
        INSERT INTO audit_logs (
            action_type,
            resource_type,
            action_details
        ) VALUES (
            'INDEX_MAINTENANCE',
            'HNSW_INDEX',
            jsonb_build_object(
                'index_name', index_name,
                'table_name', table_name,
                'index_size_bytes', index_size,
                'fragmentation_ratio', fragmentation_ratio
            )
        );

        -- Rebuild index if fragmentation is high
        IF fragmentation_ratio > 0.3 THEN
            EXECUTE format('REINDEX INDEX CONCURRENTLY %I', index_name);

            INSERT INTO audit_logs (
                action_type,
                resource_type,
                action_details
            ) VALUES (
                'INDEX_REBUILD',
                'HNSW_INDEX',
                jsonb_build_object(
                    'index_name', index_name,
                    'reason', 'high_fragmentation',
                    'fragmentation_ratio', fragmentation_ratio
                )
            );
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Schedule regular index optimization
SELECT cron.schedule(
    'vector-index-optimization',
    '0 3 * * 0',  -- Weekly on Sunday at 3 AM
    'SELECT optimize_vector_indexes();'
);
```

### 3. Dynamic Query Optimization

```sql
-- Adaptive query optimization based on performance metrics
CREATE OR REPLACE FUNCTION get_optimal_search_strategy(
    p_query_text TEXT,
    p_result_limit INTEGER DEFAULT 10,
    p_user_id UUID DEFAULT NULL
) RETURNS JSONB AS $$
DECLARE
    query_characteristics JSONB;
    historical_performance RECORD;
    optimal_strategy JSONB;
BEGIN
    -- Analyze query characteristics
    query_characteristics := jsonb_build_object(
        'query_length', LENGTH(p_query_text),
        'word_count', array_length(string_to_array(trim(p_query_text), ' '), 1),
        'has_technical_terms', p_query_text ~* '(article|section|regulation|compliance|requirement)',
        'is_question', p_query_text ~* '(what|how|when|where|why|which|\?)',
        'language_detected', detect_language(p_query_text)
    );

    -- Get historical performance for similar queries
    SELECT
        AVG(total_execution_time_ms) as avg_execution_time,
        AVG(avg_similarity_score) as avg_similarity_score,
        AVG(total_results) as avg_results,
        mode() WITHIN GROUP (ORDER BY search_type) as best_search_type
    INTO historical_performance
    FROM vector_search_metrics
    WHERE query_length BETWEEN (query_characteristics->>'query_length')::INTEGER - 10
                            AND (query_characteristics->>'query_length')::INTEGER + 10
        AND executed_at > NOW() - INTERVAL '30 days'
        AND (p_user_id IS NULL OR user_id = p_user_id);

    -- Determine optimal strategy
    optimal_strategy := jsonb_build_object(
        'search_type', COALESCE(historical_performance.best_search_type, 'hybrid'),
        'similarity_threshold',
            CASE
                WHEN (query_characteristics->>'has_technical_terms')::BOOLEAN THEN 0.75
                WHEN (query_characteristics->>'is_question')::BOOLEAN THEN 0.7
                ELSE 0.8
            END,
        'use_cache',
            CASE
                WHEN historical_performance.avg_execution_time > 1000 THEN TRUE
                ELSE FALSE
            END,
        'recommended_limit',
            CASE
                WHEN p_result_limit > 20 AND historical_performance.avg_results < p_result_limit * 0.5 THEN
                    GREATEST(10, historical_performance.avg_results::INTEGER)
                ELSE p_result_limit
            END,
        'performance_prediction', jsonb_build_object(
            'estimated_execution_time_ms', COALESCE(historical_performance.avg_execution_time, 500),
            'expected_results', COALESCE(historical_performance.avg_results, p_result_limit),
            'confidence_score', COALESCE(historical_performance.avg_similarity_score, 0.8)
        )
    );

    RETURN optimal_strategy;
END;
$$ LANGUAGE plpgsql;
```

## Specialized Vector Operations

### 1. Regulatory Concept Clustering

```sql
-- Regulatory concept clustering for improved retrieval
CREATE TABLE regulatory_concept_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_name TEXT NOT NULL,
    authority_code TEXT,
    jurisdiction TEXT,

    -- Cluster representation
    centroid_embedding vector(1536),
    concept_keywords TEXT[],
    representative_chunks UUID[],

    -- Cluster metadata
    cluster_size INTEGER,
    coherence_score FLOAT,
    coverage_score FLOAT,

    -- Regulatory context
    related_regulations TEXT[],
    compliance_topics TEXT[],

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Function to create regulatory concept clusters
CREATE OR REPLACE FUNCTION create_regulatory_clusters(
    p_authority_code TEXT DEFAULT NULL,
    p_min_cluster_size INTEGER DEFAULT 5
) RETURNS INTEGER AS $$
DECLARE
    cluster_count INTEGER := 0;
    chunk_record RECORD;
    cluster_id UUID;
BEGIN
    -- Use K-means clustering on regulatory embeddings
    -- This is a simplified version - in practice, you'd use ML algorithms

    FOR chunk_record IN
        SELECT
            dc.id,
            dc.content_embedding,
            dc.regulatory_concepts,
            dc.compliance_topics,
            ra.code as authority_code
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        JOIN regulatory_authorities ra ON d.authority_id = ra.id
        WHERE (p_authority_code IS NULL OR ra.code = p_authority_code)
            AND dc.content_embedding IS NOT NULL
    LOOP
        -- Assign chunk to nearest cluster or create new cluster
        -- Implementation would include actual clustering algorithm
        cluster_count := cluster_count + 1;
    END LOOP;

    RETURN cluster_count;
END;
$$ LANGUAGE plpgsql;
```

### 2. Multi-Jurisdictional Vector Alignment

```sql
-- Cross-jurisdiction embedding alignment
CREATE TABLE jurisdiction_alignment_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_chunk_id UUID NOT NULL REFERENCES document_chunks(id),
    target_chunk_id UUID NOT NULL REFERENCES document_chunks(id),

    -- Alignment metrics
    semantic_similarity FLOAT NOT NULL,
    regulatory_equivalence FLOAT,
    contextual_alignment FLOAT,

    -- Mapping metadata
    mapping_type TEXT CHECK (mapping_type IN ('equivalent', 'similar', 'related', 'conflicting')),
    confidence_score FLOAT,

    -- Cross-jurisdiction context
    source_jurisdiction TEXT,
    target_jurisdiction TEXT,
    regulatory_domain TEXT,

    -- Verification status
    human_verified BOOLEAN DEFAULT FALSE,
    verification_date TIMESTAMP WITH TIME ZONE,
    verified_by UUID REFERENCES auth.users(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Function to find cross-jurisdictional alignments
CREATE OR REPLACE FUNCTION find_jurisdiction_alignments(
    p_source_jurisdiction TEXT,
    p_target_jurisdiction TEXT,
    p_similarity_threshold FLOAT DEFAULT 0.8
) RETURNS TABLE (
    source_chunk_id UUID,
    target_chunk_id UUID,
    similarity_score FLOAT,
    regulatory_equivalence FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc1.id as source_chunk_id,
        dc2.id as target_chunk_id,
        1 - (dc1.content_embedding <=> dc2.content_embedding) as similarity_score,
        calculate_regulatory_equivalence(dc1.id, dc2.id) as regulatory_equivalence
    FROM document_chunks dc1
    JOIN documents d1 ON dc1.document_id = d1.id
    JOIN regulatory_authorities ra1 ON d1.authority_id = ra1.id
    JOIN document_chunks dc2 ON dc1.chunk_type = dc2.chunk_type
    JOIN documents d2 ON dc2.document_id = d2.id
    JOIN regulatory_authorities ra2 ON d2.authority_id = ra2.id
    WHERE ra1.jurisdiction = p_source_jurisdiction
        AND ra2.jurisdiction = p_target_jurisdiction
        AND dc1.id != dc2.id
        AND (dc1.content_embedding <=> dc2.content_embedding) < (1 - p_similarity_threshold)
    ORDER BY dc1.content_embedding <=> dc2.content_embedding
    LIMIT 1000;
END;
$$ LANGUAGE plpgsql;
```

## Quality Assurance and Validation

### 1. Embedding Quality Metrics

```sql
-- Embedding quality assessment
CREATE TABLE embedding_quality_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    embedding_model TEXT NOT NULL,
    assessment_date DATE DEFAULT CURRENT_DATE,

    -- Quality metrics
    average_similarity_score FLOAT,
    similarity_distribution JSONB,
    clustering_coherence FLOAT,
    retrieval_precision FLOAT,
    retrieval_recall FLOAT,

    -- Regulatory-specific metrics
    regulatory_accuracy FLOAT,
    cross_reference_accuracy FLOAT,
    jurisdiction_consistency FLOAT,

    -- Performance metrics
    embedding_generation_time_ms FLOAT,
    search_performance_ms FLOAT,
    index_build_time_minutes FLOAT,

    -- Sample results for validation
    sample_queries JSONB,
    sample_results JSONB,

    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Function to assess embedding quality
CREATE OR REPLACE FUNCTION assess_embedding_quality(
    p_embedding_model TEXT,
    p_sample_size INTEGER DEFAULT 100
) RETURNS UUID AS $$
DECLARE
    report_id UUID;
    quality_metrics RECORD;
BEGIN
    -- Create quality assessment report
    INSERT INTO embedding_quality_reports (embedding_model, created_by)
    VALUES (p_embedding_model, auth.uid())
    RETURNING id INTO report_id;

    -- Calculate quality metrics
    WITH similarity_stats AS (
        SELECT
            AVG(1 - (ce1.dense_embedding <=> ce2.dense_embedding)) as avg_similarity,
            percentile_disc(0.25) WITHIN GROUP (ORDER BY (1 - (ce1.dense_embedding <=> ce2.dense_embedding))) as q25,
            percentile_disc(0.5) WITHIN GROUP (ORDER BY (1 - (ce1.dense_embedding <=> ce2.dense_embedding))) as median,
            percentile_disc(0.75) WITHIN GROUP (ORDER BY (1 - (ce1.dense_embedding <=> ce2.dense_embedding))) as q75
        FROM chunk_embeddings ce1
        CROSS JOIN LATERAL (
            SELECT dense_embedding
            FROM chunk_embeddings ce2
            WHERE ce2.embedding_model = p_embedding_model
            AND ce2.id != ce1.id
            LIMIT 1
        ) ce2
        WHERE ce1.embedding_model = p_embedding_model
        LIMIT p_sample_size
    )
    SELECT * INTO quality_metrics FROM similarity_stats;

    -- Update report with metrics
    UPDATE embedding_quality_reports
    SET
        average_similarity_score = quality_metrics.avg_similarity,
        similarity_distribution = jsonb_build_object(
            'q25', quality_metrics.q25,
            'median', quality_metrics.median,
            'q75', quality_metrics.q75
        )
    WHERE id = report_id;

    RETURN report_id;
END;
$$ LANGUAGE plpgsql;
```

## Backup and Recovery Strategy

### 1. Vector-Specific Backup Procedures

```sql
-- Vector data backup coordination
CREATE TABLE vector_backup_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backup_type TEXT CHECK (backup_type IN ('full', 'incremental', 'embeddings_only')),

    -- Backup scope
    table_names TEXT[],
    embedding_models TEXT[],
    date_range_start TIMESTAMP WITH TIME ZONE,
    date_range_end TIMESTAMP WITH TIME ZONE,

    -- Backup metadata
    backup_size_bytes BIGINT,
    compression_ratio FLOAT,
    backup_location TEXT,
    verification_status TEXT,

    -- Timing information
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,

    -- Status tracking
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    error_message TEXT
);

-- Function for vector-aware backup
CREATE OR REPLACE FUNCTION create_vector_backup(
    p_backup_type TEXT DEFAULT 'incremental'
) RETURNS UUID AS $$
DECLARE
    backup_job_id UUID;
BEGIN
    INSERT INTO vector_backup_jobs (backup_type)
    VALUES (p_backup_type)
    RETURNING id INTO backup_job_id;

    -- Implementation would include actual backup logic
    -- This is a placeholder for the backup coordination

    RETURN backup_job_id;
END;
$$ LANGUAGE plpgsql;
```

This comprehensive vector storage design provides the foundation for high-performance regulatory document retrieval, supporting the complex requirements of the Banking RAG Compliance System while ensuring optimal search performance and regulatory accuracy.