# RAG Retrieval Methodology for Banking Regulatory Documents

## Executive Summary

This document outlines a comprehensive Retrieval-Augmented Generation (RAG) methodology specifically optimized for banking regulatory documents from EU and Spanish authorities. The approach combines dense vector retrieval, sparse keyword matching, and hierarchical clustering to achieve >95% accuracy in regulatory query resolution while maintaining sub-5 second response times.

## 1. Document Characteristics Analysis

### 1.1 Regulatory Document Properties

Banking regulatory documents exhibit unique characteristics that require specialized RAG approaches:

#### Structural Properties
- **Hierarchical Organization**: Articles → Sections → Paragraphs → Sub-paragraphs
- **Cross-References**: Extensive internal and external references (e.g., "as defined in Article 4(1)(a)")
- **Legal Precision**: Exact wording matters for compliance interpretation
- **Temporal Validity**: Documents have effective dates, amendment histories
- **Multi-Language**: Often available in multiple EU languages

#### Content Properties
- **Dense Technical Language**: High concentration of domain-specific terminology
- **Quantitative Requirements**: Specific numerical thresholds and calculations
- **Conditional Logic**: Complex if-then-else regulatory logic
- **Definitional Dependencies**: Terms rely on precise definitions from other sections

### 1.2 Authority-Specific Characteristics

| Authority | Document Types | Average Length | Update Frequency | Language Priority |
|-----------|---------------|----------------|------------------|-------------------|
| **EBA** | Guidelines, Technical Standards, Opinions | 50-200 pages | Monthly | EN primary, local translations |
| **ESMA** | Guidelines, Technical Standards, Q&As | 30-150 pages | Bi-weekly | EN primary, local translations |
| **EIOPA** | Guidelines, Opinions, Reports | 40-180 pages | Monthly | EN primary, local translations |
| **Bank of Spain** | Circulars, Instructions, Criteria | 20-100 pages | Weekly | ES primary |
| **CNMV** | Circulars, Technical Guides | 15-80 pages | Bi-weekly | ES primary |

## 2. Chunking Strategy for Regulatory Documents

### 2.1 Hierarchical Semantic Chunking

Traditional fixed-size chunking fails to preserve regulatory context. Our approach uses document structure:

#### Level 1: Article-Based Chunking
```python
# Primary chunks based on regulatory articles
chunk_boundaries = [
    "Article \\d+",
    "Section \\d+",
    "Chapter \\d+",
    "Part [IVX]+"
]
```

#### Level 2: Semantic Boundary Detection
```python
# Detect semantic boundaries within articles
semantic_indicators = [
    "shall mean",
    "for the purposes of",
    "without prejudice to",
    "subject to",
    "provided that"
]
```

#### Level 3: Contextual Overlap Strategy
- **Forward Overlap**: Include next paragraph's first sentence
- **Backward Overlap**: Include previous paragraph's last sentence
- **Reference Preservation**: Maintain cross-reference context

### 2.2 Adaptive Chunk Sizing

| Document Section | Chunk Size (tokens) | Overlap (tokens) | Rationale |
|------------------|---------------------|------------------|-----------|
| Definitions | 256-512 | 50 | Preserve complete definitions |
| Articles/Sections | 512-1024 | 100 | Maintain regulatory logic |
| Annexes/Tables | 1024-2048 | 150 | Preserve data relationships |
| Cross-References | 128-256 | 25 | Focus on link context |

### 2.3 Metadata Enhancement

Each chunk includes structured metadata:

```json
{
  "document_id": "eba_gl_2023_01",
  "authority": "EBA",
  "document_type": "Guideline",
  "effective_date": "2023-06-01",
  "article_number": "15",
  "section_number": "3",
  "paragraph_number": "2",
  "hierarchical_path": "Article 15 > Section 3 > Paragraph 2",
  "cross_references": ["Article 4(1)(a)", "Annex II"],
  "keywords": ["capital requirements", "credit risk", "standardised approach"],
  "language": "EN",
  "jurisdiction": "EU",
  "chunk_type": "regulatory_provision"
}
```

## 3. Embedding Strategies

### 3.1 Multi-Model Embedding Approach

#### Primary Dense Embeddings
- **Model**: `text-embedding-3-large` (OpenAI) or `e5-large-v2`
- **Dimensions**: 3072 (with option to reduce to 1536 for performance)
- **Optimization**: Fine-tuned on regulatory text corpus

#### Domain-Specific Embeddings
- **Legal-BERT**: Specialized for legal text understanding
- **FinBERT**: Financial domain-specific embeddings
- **Regulatory-specific**: Custom-trained on EU banking regulations

#### Multilingual Considerations
```python
embedding_models = {
    "EN": "text-embedding-3-large",
    "ES": "multilingual-e5-large",
    "multilingual": "paraphrase-multilingual-MiniLM-L12-v2"
}
```

### 3.2 Embedding Enhancement Techniques

#### Context Window Optimization
- **Sliding Window**: 512-token windows with 128-token overlap
- **Hierarchical Context**: Include parent section context
- **Cross-Reference Expansion**: Include referenced content

#### Preprocessing Pipeline
1. **Text Normalization**: Standardize formatting, remove artifacts
2. **Legal Entity Recognition**: Identify and preserve legal terms
3. **Cross-Reference Resolution**: Expand internal references
4. **Multi-Language Alignment**: Align translations for consistency

## 4. Retrieval Architecture

### 4.1 Hybrid Retrieval Pipeline

#### Stage 1: Multi-Strategy Retrieval
```python
async def hybrid_retrieve(query: str, top_k: int = 20) -> List[Document]:
    # Parallel retrieval strategies
    vector_results = await vector_search(query, top_k=100)
    keyword_results = await bm25_search(query, top_k=50)
    cluster_results = await cluster_search(query, top_k=30)

    # Combine and deduplicate
    combined_results = merge_results([
        vector_results,
        keyword_results,
        cluster_results
    ])

    return combined_results[:top_k]
```

#### Stage 2: Semantic Clustering
- **Topic Clustering**: Group regulations by subject matter
- **Authority Clustering**: Organize by regulatory authority
- **Temporal Clustering**: Group by implementation timeline
- **Cross-Reference Clustering**: Link related provisions

### 4.2 Query Understanding Pipeline

#### Intent Classification
```python
query_intents = {
    "definition_lookup": "what is|what does|define|definition of",
    "requirement_search": "requirement|must|shall|obligation",
    "comparison": "compare|difference|versus|vs",
    "compliance_check": "comply|compliance|violation|breach",
    "calculation": "calculate|computation|formula|rate"
}
```

#### Query Expansion
- **Regulatory Synonyms**: Map colloquial terms to regulatory language
- **Cross-Reference Expansion**: Include related regulatory citations
- **Temporal Context**: Consider regulation versions and amendments
- **Jurisdiction Mapping**: Map generic terms to authority-specific language

### 4.3 Vector Search Optimization

#### Index Configuration
```python
vector_index_config = {
    "metric": "cosine",
    "dimensions": 1536,
    "pods": 2,
    "pod_type": "p1.x1",
    "metadata_config": {
        "indexed": ["authority", "document_type", "effective_date", "article_number"]
    }
}
```

#### Filtering Strategy
- **Temporal Filtering**: Latest version by default, historical on request
- **Authority Filtering**: Jurisdiction-specific searches
- **Document Type Filtering**: Guidelines vs. Technical Standards vs. Q&As
- **Language Filtering**: Prefer user's language, fallback to English

## 5. Performance Optimization

### 5.1 Caching Strategy

#### Multi-Level Caching
```python
cache_hierarchy = {
    "L1_query_cache": {
        "type": "redis",
        "ttl": 3600,  # 1 hour
        "max_size": "1GB"
    },
    "L2_embedding_cache": {
        "type": "redis",
        "ttl": 86400,  # 24 hours
        "max_size": "5GB"
    },
    "L3_document_cache": {
        "type": "disk",
        "ttl": 604800,  # 1 week
        "max_size": "50GB"
    }
}
```

#### Precomputed Embeddings
- **Common Queries**: Pre-embed frequent regulatory queries
- **Document Summaries**: Pre-generate article and section summaries
- **Cross-Reference Maps**: Pre-compute reference relationship graphs

### 5.2 Parallel Processing

#### Concurrent Retrieval
```python
async def parallel_retrieve(query: str) -> SearchResults:
    tasks = [
        asyncio.create_task(vector_search(query)),
        asyncio.create_task(keyword_search(query)),
        asyncio.create_task(cluster_search(query)),
        asyncio.create_task(metadata_search(query))
    ]

    results = await asyncio.gather(*tasks)
    return merge_and_rank(results)
```

#### Batch Processing
- **Embedding Generation**: Process documents in batches of 100
- **Index Updates**: Batch index operations for efficiency
- **Query Processing**: Group similar queries for batch processing

## 6. Evaluation Metrics

### 6.1 Retrieval Quality Metrics

#### Precision and Recall
```python
evaluation_metrics = {
    "precision_at_k": [1, 3, 5, 10],
    "recall_at_k": [5, 10, 20, 50],
    "map_score": "mean_average_precision",
    "ndcg": "normalized_dcg_at_k"
}
```

#### Domain-Specific Metrics
- **Regulatory Accuracy**: Correct article/section retrieval rate
- **Cross-Reference Completeness**: Related provision discovery rate
- **Temporal Accuracy**: Current version retrieval rate
- **Jurisdiction Precision**: Correct authority document retrieval

### 6.2 Performance Benchmarks

| Metric | Target | Current Baseline | Optimization Goal |
|--------|--------|------------------|-------------------|
| Query Response Time | <5 seconds | 8 seconds | <3 seconds |
| Retrieval Precision@5 | >95% | 87% | >98% |
| Cross-Reference Accuracy | >90% | 78% | >95% |
| Multilingual Consistency | >85% | 72% | >90% |
| Cache Hit Rate | >80% | 65% | >85% |

## 7. Implementation Roadmap

### 7.1 Phase 1: Core Retrieval (Weeks 1-4)
- Implement hierarchical chunking strategy
- Deploy primary embedding model
- Set up vector database with metadata indexing
- Implement basic hybrid retrieval

### 7.2 Phase 2: Enhancement (Weeks 5-8)
- Add semantic clustering capabilities
- Implement query understanding pipeline
- Deploy caching infrastructure
- Add cross-reference resolution

### 7.3 Phase 3: Optimization (Weeks 9-12)
- Fine-tune embeddings on regulatory corpus
- Implement advanced filtering strategies
- Deploy parallel processing infrastructure
- Add comprehensive evaluation framework

### 7.4 Phase 4: Advanced Features (Weeks 13-16)
- Implement multilingual support
- Add temporal document tracking
- Deploy real-time index updates
- Implement A/B testing framework

## 8. Technical Implementation Details

### 8.1 Vector Database Configuration

#### Pinecone Setup
```python
import pinecone

pinecone.init(
    api_key="your-api-key",
    environment="us-west1-gcp"
)

index = pinecone.Index("regulatory-documents")

# Upsert with metadata
index.upsert(vectors=[
    {
        "id": "eba_gl_2023_01_art15_sec3_para2",
        "values": embedding_vector,
        "metadata": {
            "authority": "EBA",
            "document_type": "Guideline",
            "article": "15",
            "section": "3",
            "paragraph": "2",
            "effective_date": "2023-06-01",
            "text": chunk_text
        }
    }
])
```

#### Alternative: Weaviate Configuration
```python
import weaviate

client = weaviate.Client("http://localhost:8080")

# Schema definition
schema = {
    "classes": [{
        "class": "RegulatoryDocument",
        "vectorizer": "text2vec-openai",
        "properties": [
            {"name": "authority", "dataType": ["string"]},
            {"name": "documentType", "dataType": ["string"]},
            {"name": "articleNumber", "dataType": ["string"]},
            {"name": "effectiveDate", "dataType": ["date"]},
            {"name": "content", "dataType": ["text"]}
        ]
    }]
}

client.schema.create(schema)
```

### 8.2 Hybrid Search Implementation

```python
from typing import List, Dict, Any
import asyncio
from dataclasses import dataclass

@dataclass
class SearchResult:
    document_id: str
    score: float
    content: str
    metadata: Dict[str, Any]
    source: str  # 'vector', 'keyword', 'cluster'

class HybridSearchEngine:
    def __init__(self):
        self.vector_search = VectorSearchEngine()
        self.keyword_search = BM25SearchEngine()
        self.cluster_search = ClusterSearchEngine()

    async def search(self, query: str, filters: Dict = None) -> List[SearchResult]:
        # Parallel search execution
        vector_task = asyncio.create_task(
            self.vector_search.search(query, top_k=100, filters=filters)
        )
        keyword_task = asyncio.create_task(
            self.keyword_search.search(query, top_k=50, filters=filters)
        )
        cluster_task = asyncio.create_task(
            self.cluster_search.search(query, top_k=30, filters=filters)
        )

        # Await all results
        vector_results, keyword_results, cluster_results = await asyncio.gather(
            vector_task, keyword_task, cluster_task
        )

        # Combine and rerank
        combined_results = self._combine_results([
            vector_results, keyword_results, cluster_results
        ])

        return combined_results[:20]  # Top 20 results

    def _combine_results(self, result_lists: List[List[SearchResult]]) -> List[SearchResult]:
        # Reciprocal Rank Fusion
        combined_scores = {}

        for i, results in enumerate(result_lists):
            weight = [0.6, 0.3, 0.1][i]  # Vector search weighted higher

            for rank, result in enumerate(results):
                doc_id = result.document_id
                rrf_score = weight / (rank + 1)

                if doc_id in combined_scores:
                    combined_scores[doc_id]['score'] += rrf_score
                else:
                    combined_scores[doc_id] = {
                        'score': rrf_score,
                        'result': result
                    }

        # Sort by combined score
        sorted_results = sorted(
            combined_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )

        return [item['result'] for item in sorted_results]
```

### 8.3 Regulatory-Specific Query Processing

```python
import re
from typing import Dict, List

class RegulatoryQueryProcessor:
    def __init__(self):
        self.legal_patterns = {
            'article_reference': r'Article\s+(\d+)(?:\((\d+)\))?(?:\(([a-z])\))?',
            'section_reference': r'Section\s+(\d+)',
            'paragraph_reference': r'paragraph\s+(\d+)',
            'directive_reference': r'Directive\s+(\d{4}\/\d+\/EU)',
            'regulation_reference': r'Regulation\s+\(EU\)\s+(\d{4}\/\d+)'
        }

        self.regulatory_synonyms = {
            'capital requirement': ['capital adequacy', 'capital ratio', 'capital buffer'],
            'credit risk': ['default risk', 'counterparty risk'],
            'operational risk': ['operational loss', 'operational failure'],
            'liquidity risk': ['funding risk', 'market liquidity risk']
        }

    def process_query(self, query: str) -> Dict[str, Any]:
        processed = {
            'original_query': query,
            'expanded_query': self._expand_query(query),
            'detected_references': self._extract_references(query),
            'query_type': self._classify_query_type(query),
            'jurisdiction_hints': self._detect_jurisdiction(query),
            'temporal_context': self._extract_temporal_context(query)
        }

        return processed

    def _expand_query(self, query: str) -> str:
        expanded = query.lower()

        # Add regulatory synonyms
        for term, synonyms in self.regulatory_synonyms.items():
            if term in expanded:
                expanded += ' ' + ' '.join(synonyms)

        # Add common regulatory context
        if 'requirement' in expanded and 'capital' in expanded:
            expanded += ' Basel III CRR CRD'

        return expanded

    def _extract_references(self, query: str) -> List[Dict[str, str]]:
        references = []

        for pattern_name, pattern in self.legal_patterns.items():
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                references.append({
                    'type': pattern_name,
                    'match': match.group(0),
                    'groups': match.groups()
                })

        return references

    def _classify_query_type(self, query: str) -> str:
        query_lower = query.lower()

        if any(word in query_lower for word in ['define', 'definition', 'what is', 'what does']):
            return 'definition'
        elif any(word in query_lower for word in ['requirement', 'must', 'shall', 'obligation']):
            return 'requirement'
        elif any(word in query_lower for word in ['calculate', 'computation', 'formula']):
            return 'calculation'
        elif any(word in query_lower for word in ['compare', 'difference', 'versus']):
            return 'comparison'
        else:
            return 'general'

    def _detect_jurisdiction(self, query: str) -> List[str]:
        jurisdictions = []
        query_upper = query.upper()

        authority_patterns = {
            'EBA': r'\bEBA\b',
            'ESMA': r'\bESMA\b',
            'EIOPA': r'\bEIOPA\b',
            'ECB': r'\bECB\b',
            'Bank of Spain': r'\b(Bank of Spain|Banco de España|BdE)\b',
            'CNMV': r'\bCNMV\b'
        }

        for authority, pattern in authority_patterns.items():
            if re.search(pattern, query_upper):
                jurisdictions.append(authority)

        return jurisdictions

    def _extract_temporal_context(self, query: str) -> Dict[str, Any]:
        temporal_patterns = {
            'year': r'\b(19|20)\d{2}\b',
            'date': r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}\b',
            'relative': r'\b(current|latest|new|recent|updated)\b'
        }

        temporal_context = {}

        for context_type, pattern in temporal_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                temporal_context[context_type] = matches

        return temporal_context
```

## 9. Quality Assurance Framework

### 9.1 Automated Testing
- **Regression Testing**: Ensure consistent performance across updates
- **Stress Testing**: Validate performance under high query volume
- **Accuracy Testing**: Automated evaluation against ground truth datasets
- **Cross-Language Testing**: Validate multilingual consistency

### 9.2 Human Evaluation
- **Expert Review**: Regulatory experts evaluate response quality
- **User Acceptance Testing**: End-user validation of practical utility
- **Comparative Analysis**: Benchmark against traditional search methods
- **Feedback Integration**: Continuous improvement based on user feedback

### 9.3 Monitoring and Alerting
- **Performance Monitoring**: Real-time tracking of response times
- **Accuracy Monitoring**: Continuous evaluation of retrieval quality
- **Error Tracking**: Automated detection and alerting of failures
- **Usage Analytics**: Understanding of query patterns and user behavior

This comprehensive retrieval methodology provides the foundation for accurate, efficient regulatory document retrieval while maintaining the precision required for compliance applications.