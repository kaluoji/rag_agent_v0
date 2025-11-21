# Multi-Stage Reranking Strategies for Banking Regulatory Documents

## Executive Summary

This document outlines sophisticated reranking strategies designed specifically for banking regulatory compliance documents. The multi-stage approach combines cross-encoder models, regulatory-specific scoring algorithms, and contextual relevance assessment to achieve >98% precision in regulatory query resolution, reducing from initial retrieval sets of 100+ documents to precisely ranked top-10 results.

## 1. Reranking Architecture Overview

### 1.1 Multi-Stage Pipeline

```
Initial Retrieval (100+ docs) → Stage 1: Fast Reranking → Stage 2: Deep Reranking → Stage 3: Regulatory Scoring → Final Results (10 docs)
     ↓                           ↓                        ↓                        ↓
Hybrid Search Results    Cross-Encoder Filtering    Contextual Analysis      Compliance-Aware Ranking
```

### 1.2 Performance Targets

| Stage | Input Size | Output Size | Processing Time | Accuracy Gain |
|-------|------------|-------------|-----------------|---------------|
| **Stage 1** | 100-200 docs | 50 docs | <500ms | +15% precision |
| **Stage 2** | 50 docs | 20 docs | <1000ms | +20% precision |
| **Stage 3** | 20 docs | 10 docs | <300ms | +10% precision |
| **Total** | 100-200 docs | 10 docs | <1800ms | +45% precision |

## 2. Stage 1: Fast Cross-Encoder Reranking

### 2.1 Model Selection and Architecture

#### Primary Model: Regulatory-Tuned Cross-Encoder
```python
from sentence_transformers import CrossEncoder

class RegulatoryReranker:
    def __init__(self):
        self.models = {
            'fast_reranker': CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2'),
            'legal_reranker': CrossEncoder('cross-encoder/nli-deberta-v3-base'),
            'multilingual_reranker': CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')
        }

        # Fine-tune on regulatory document pairs
        self.regulatory_model = self._load_regulatory_tuned_model()

    def _load_regulatory_tuned_model(self):
        # Custom model fine-tuned on regulatory query-document pairs
        model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        # Load regulatory domain weights
        model.load_state_dict(torch.load('regulatory_reranker_weights.pt'))
        return model
```

#### Model Specifications
- **Base Model**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Fine-tuning Dataset**: 50K regulatory query-document pairs
- **Training Focus**: EU banking regulations (EBA, ESMA, EIOPA)
- **Languages**: English, Spanish (with multilingual fallback)
- **Input Length**: 512 tokens max (query + document excerpt)

### 2.2 Query-Document Pair Formation

#### Smart Excerpt Generation
```python
def create_reranking_pairs(query: str, documents: List[Document]) -> List[Tuple[str, str]]:
    pairs = []

    for doc in documents:
        # Strategy 1: Use chunk with highest initial score
        primary_excerpt = doc.get_best_chunk(max_tokens=400)

        # Strategy 2: Create contextual excerpt
        contextual_excerpt = doc.create_contextual_excerpt(
            query=query,
            max_tokens=400,
            include_hierarchy=True,
            include_references=True
        )

        # Strategy 3: Use regulatory-specific excerpt
        regulatory_excerpt = doc.extract_regulatory_content(
            query=query,
            focus_areas=['requirements', 'definitions', 'calculations', 'deadlines']
        )

        # Select best excerpt based on query type
        if query_type == 'definition':
            excerpt = doc.get_definition_context(query)
        elif query_type == 'requirement':
            excerpt = regulatory_excerpt
        else:
            excerpt = contextual_excerpt

        pairs.append((query, excerpt))

    return pairs
```

#### Context Enhancement
- **Hierarchical Context**: Include article/section headers
- **Cross-Reference Context**: Include referenced definitions
- **Temporal Context**: Include effective dates and amendments
- **Authority Context**: Include issuing authority information

### 2.3 Regulatory-Specific Scoring

#### Enhanced Scoring Function
```python
class RegulatoryScorer:
    def __init__(self):
        self.legal_term_weights = self._load_legal_term_weights()
        self.authority_weights = {
            'EBA': 1.0,
            'ESMA': 1.0,
            'EIOPA': 1.0,
            'ECB': 0.9,
            'Bank of Spain': 0.8,
            'CNMV': 0.8
        }

    def enhanced_score(self, base_score: float, query: str, document: Document) -> float:
        # Base cross-encoder score
        enhanced_score = base_score

        # Legal terminology boost
        legal_boost = self._calculate_legal_term_boost(query, document)
        enhanced_score += legal_boost * 0.1

        # Authority relevance boost
        authority_boost = self.authority_weights.get(document.authority, 0.5)
        enhanced_score *= authority_boost

        # Temporal relevance boost
        temporal_boost = self._calculate_temporal_relevance(document)
        enhanced_score += temporal_boost * 0.05

        # Cross-reference relevance boost
        cross_ref_boost = self._calculate_cross_reference_relevance(query, document)
        enhanced_score += cross_ref_boost * 0.08

        return enhanced_score

    def _calculate_legal_term_boost(self, query: str, document: Document) -> float:
        query_terms = set(query.lower().split())
        doc_legal_terms = set(document.extract_legal_terms())

        overlap = len(query_terms.intersection(doc_legal_terms))
        total_terms = len(query_terms.union(doc_legal_terms))

        return overlap / total_terms if total_terms > 0 else 0.0

    def _calculate_temporal_relevance(self, document: Document) -> float:
        if not document.effective_date:
            return 0.0

        days_since_effective = (datetime.now() - document.effective_date).days

        # Prefer more recent regulations
        if days_since_effective < 365:  # Less than 1 year
            return 0.2
        elif days_since_effective < 1095:  # Less than 3 years
            return 0.1
        else:
            return 0.0

    def _calculate_cross_reference_relevance(self, query: str, document: Document) -> float:
        # Extract references from query
        query_refs = extract_legal_references(query)
        doc_refs = document.cross_references

        if not query_refs:
            return 0.0

        matching_refs = len(set(query_refs).intersection(set(doc_refs)))
        return min(matching_refs * 0.1, 0.3)  # Cap at 0.3
```

### 2.4 Batch Processing Optimization

#### Efficient Batching Strategy
```python
async def fast_rerank_batch(query: str, documents: List[Document], batch_size: int = 32) -> List[Document]:
    # Prepare all query-document pairs
    pairs = create_reranking_pairs(query, documents)

    # Process in batches for efficiency
    all_scores = []
    for i in range(0, len(pairs), batch_size):
        batch_pairs = pairs[i:i + batch_size]
        batch_scores = await self.cross_encoder.predict(batch_pairs)
        all_scores.extend(batch_scores)

    # Enhance scores with regulatory factors
    enhanced_scores = []
    for score, doc in zip(all_scores, documents):
        enhanced_score = self.regulatory_scorer.enhanced_score(score, query, doc)
        enhanced_scores.append(enhanced_score)

    # Sort and return top results
    scored_docs = list(zip(enhanced_scores, documents))
    scored_docs.sort(key=lambda x: x[0], reverse=True)

    return [doc for score, doc in scored_docs[:50]]  # Top 50 for next stage
```

## 3. Stage 2: Deep Contextual Reranking

### 3.1 Advanced Cross-Encoder Models

#### Regulatory-Specialized Models
```python
class DeepRegulatoryReranker:
    def __init__(self):
        self.models = {
            'deberta_large': CrossEncoder('microsoft/deberta-v3-large'),
            'legal_bert': CrossEncoder('nlpaueb/legal-bert-base-uncased'),
            'regulatory_custom': self._load_custom_regulatory_model()
        }

        # Ensemble configuration
        self.ensemble_weights = {
            'deberta_large': 0.4,
            'legal_bert': 0.3,
            'regulatory_custom': 0.3
        }

    async def deep_rerank(self, query: str, documents: List[Document]) -> List[Document]:
        # Extract comprehensive contexts
        enriched_pairs = self._create_enriched_pairs(query, documents)

        # Run ensemble of models
        ensemble_scores = await self._run_ensemble(enriched_pairs)

        # Apply contextual scoring
        final_scores = self._apply_contextual_scoring(ensemble_scores, query, documents)

        # Sort and return top 20
        scored_docs = list(zip(final_scores, documents))
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        return [doc for score, doc in scored_docs[:20]]
```

### 3.2 Context-Aware Pair Creation

#### Enhanced Context Extraction
```python
def _create_enriched_pairs(self, query: str, documents: List[Document]) -> List[Tuple[str, str]]:
    enriched_pairs = []

    for doc in documents:
        # Full document context
        doc_context = self._build_document_context(doc)

        # Query-specific context
        query_context = self._build_query_context(query, doc)

        # Combined enriched context
        enriched_context = f"""
        Query: {query}

        Document Authority: {doc.authority}
        Document Type: {doc.document_type}
        Effective Date: {doc.effective_date}

        Hierarchical Context:
        {doc.hierarchical_path}

        Main Content:
        {doc_context}

        Cross-References:
        {', '.join(doc.cross_references[:5])}

        Related Definitions:
        {query_context}
        """

        enriched_pairs.append((query, enriched_context))

    return enriched_pairs

def _build_document_context(self, doc: Document) -> str:
    context_parts = []

    # Include parent section if available
    if doc.parent_section:
        context_parts.append(f"Parent Section: {doc.parent_section.title}")
        context_parts.append(doc.parent_section.summary)

    # Main content with enhanced formatting
    context_parts.append(f"Main Content: {doc.content}")

    # Include subsections if available
    if doc.subsections:
        for subsection in doc.subsections[:3]:  # Top 3 subsections
            context_parts.append(f"Subsection: {subsection.title}")
            context_parts.append(subsection.summary)

    return "\n\n".join(context_parts)

def _build_query_context(self, query: str, doc: Document) -> str:
    query_terms = extract_key_terms(query)

    # Find related definitions in the document
    related_definitions = []
    for term in query_terms:
        definition = doc.find_definition(term)
        if definition:
            related_definitions.append(f"{term}: {definition}")

    # Find related calculations
    related_calculations = []
    if 'calculate' in query.lower() or 'formula' in query.lower():
        calculations = doc.extract_calculations()
        related_calculations.extend(calculations[:2])  # Top 2 calculations

    context_parts = []
    if related_definitions:
        context_parts.append("Related Definitions:\n" + "\n".join(related_definitions))
    if related_calculations:
        context_parts.append("Related Calculations:\n" + "\n".join(related_calculations))

    return "\n\n".join(context_parts)
```

### 3.3 Ensemble Model Strategy

#### Multi-Model Scoring
```python
async def _run_ensemble(self, enriched_pairs: List[Tuple[str, str]]) -> List[float]:
    model_scores = {}

    # Run each model
    for model_name, model in self.models.items():
        scores = await model.predict(enriched_pairs)
        model_scores[model_name] = scores

    # Ensemble scoring
    ensemble_scores = []
    for i in range(len(enriched_pairs)):
        weighted_score = 0.0
        for model_name, weight in self.ensemble_weights.items():
            weighted_score += model_scores[model_name][i] * weight
        ensemble_scores.append(weighted_score)

    return ensemble_scores
```

### 3.4 Contextual Relevance Scoring

#### Advanced Contextual Factors
```python
def _apply_contextual_scoring(self, base_scores: List[float], query: str, documents: List[Document]) -> List[float]:
    contextual_scores = []

    for score, doc in zip(base_scores, documents):
        # Base ensemble score
        final_score = score

        # Document completeness factor
        completeness_factor = self._calculate_completeness_factor(doc)
        final_score *= (1.0 + completeness_factor * 0.1)

        # Query-document semantic alignment
        semantic_alignment = self._calculate_semantic_alignment(query, doc)
        final_score += semantic_alignment * 0.15

        # Regulatory precision factor
        precision_factor = self._calculate_regulatory_precision(query, doc)
        final_score += precision_factor * 0.1

        # Cross-reference completeness
        cross_ref_completeness = self._calculate_cross_ref_completeness(doc)
        final_score += cross_ref_completeness * 0.05

        contextual_scores.append(final_score)

    return contextual_scores

def _calculate_completeness_factor(self, doc: Document) -> float:
    # Assess document completeness based on structure
    completeness_score = 0.0

    # Has clear hierarchical structure
    if doc.hierarchical_path:
        completeness_score += 0.2

    # Has definitions
    if doc.definitions:
        completeness_score += 0.2

    # Has cross-references
    if doc.cross_references:
        completeness_score += 0.2

    # Has effective date
    if doc.effective_date:
        completeness_score += 0.2

    # Has examples or calculations
    if doc.examples or doc.calculations:
        completeness_score += 0.2

    return completeness_score

def _calculate_semantic_alignment(self, query: str, doc: Document) -> float:
    # Use semantic similarity between query and document key phrases
    query_embedding = self.embedding_model.encode(query)

    # Extract key phrases from document
    key_phrases = doc.extract_key_phrases()
    if not key_phrases:
        return 0.0

    # Calculate semantic similarity
    phrase_embeddings = self.embedding_model.encode(key_phrases)
    similarities = cosine_similarity([query_embedding], phrase_embeddings)[0]

    return np.mean(similarities)

def _calculate_regulatory_precision(self, query: str, doc: Document) -> float:
    # Assess how precisely the document addresses regulatory aspects
    precision_score = 0.0

    # Check for specific regulatory keywords
    regulatory_keywords = ['shall', 'must', 'requirement', 'obligation', 'compliance']
    query_has_regulatory = any(keyword in query.lower() for keyword in regulatory_keywords)
    doc_has_regulatory = any(keyword in doc.content.lower() for keyword in regulatory_keywords)

    if query_has_regulatory and doc_has_regulatory:
        precision_score += 0.3

    # Check for numerical requirements
    if re.search(r'\d+%|\d+\.\d+%|\d+ basis points', query) and re.search(r'\d+%|\d+\.\d+%|\d+ basis points', doc.content):
        precision_score += 0.2

    # Check for date/deadline alignment
    if re.search(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}', query) and doc.effective_date:
        precision_score += 0.1

    return precision_score
```

## 4. Stage 3: Regulatory Compliance Scoring

### 4.1 Compliance-Aware Ranking

#### Regulatory Importance Scoring
```python
class ComplianceScorer:
    def __init__(self):
        self.compliance_weights = {
            'mandatory_requirement': 1.0,
            'recommended_practice': 0.8,
            'guidance': 0.6,
            'example': 0.4,
            'background': 0.2
        }

        self.urgency_weights = {
            'immediate': 1.0,
            'within_6_months': 0.9,
            'within_12_months': 0.8,
            'within_24_months': 0.7,
            'no_deadline': 0.5
        }

    def calculate_compliance_score(self, base_score: float, document: Document, query: str) -> float:
        # Start with base reranking score
        compliance_score = base_score

        # Apply regulatory importance multiplier
        importance_type = self._classify_regulatory_importance(document)
        importance_multiplier = self.compliance_weights.get(importance_type, 0.5)
        compliance_score *= importance_multiplier

        # Apply urgency multiplier
        urgency_level = self._assess_urgency(document, query)
        urgency_multiplier = self.urgency_weights.get(urgency_level, 0.5)
        compliance_score *= urgency_multiplier

        # Add penalty/risk factor
        penalty_factor = self._calculate_penalty_factor(document)
        compliance_score += penalty_factor * 0.2

        # Add implementation complexity factor
        complexity_factor = self._calculate_complexity_factor(document)
        compliance_score -= complexity_factor * 0.1  # Lower score for high complexity

        return compliance_score

    def _classify_regulatory_importance(self, document: Document) -> str:
        content_lower = document.content.lower()

        # Mandatory requirements
        if any(phrase in content_lower for phrase in ['shall', 'must', 'required to', 'obligation']):
            return 'mandatory_requirement'

        # Recommended practices
        elif any(phrase in content_lower for phrase in ['should', 'recommended', 'best practice']):
            return 'recommended_practice'

        # Guidance
        elif any(phrase in content_lower for phrase in ['guidance', 'interpretation', 'clarification']):
            return 'guidance'

        # Examples
        elif any(phrase in content_lower for phrase in ['example', 'illustration', 'for instance']):
            return 'example'

        # Background information
        else:
            return 'background'

    def _assess_urgency(self, document: Document, query: str) -> str:
        # Check for deadline-related keywords in query
        query_lower = query.lower()
        if any(phrase in query_lower for phrase in ['urgent', 'immediate', 'asap', 'deadline']):
            return 'immediate'

        # Check document for implementation deadlines
        content = document.content

        # Look for specific dates
        current_date = datetime.now()
        date_patterns = [
            r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
            r'(\d{4})-(\d{2})-(\d{2})',
            r'(\d{2})/(\d{2})/(\d{4})'
        ]

        for pattern in date_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    # Parse date and calculate urgency
                    if 'January' in match.group(0):  # Word format
                        date_str = match.group(0)
                        deadline = datetime.strptime(date_str, '%d %B %Y')
                    else:  # Numeric format
                        date_str = match.group(0)
                        deadline = datetime.strptime(date_str, '%Y-%m-%d')

                    days_until_deadline = (deadline - current_date).days

                    if days_until_deadline <= 30:
                        return 'immediate'
                    elif days_until_deadline <= 180:
                        return 'within_6_months'
                    elif days_until_deadline <= 365:
                        return 'within_12_months'
                    elif days_until_deadline <= 730:
                        return 'within_24_months'

                except ValueError:
                    continue

        return 'no_deadline'

    def _calculate_penalty_factor(self, document: Document) -> float:
        content_lower = document.content.lower()
        penalty_factor = 0.0

        # High penalty indicators
        high_penalty_terms = ['administrative penalty', 'fine', 'sanctions', 'enforcement action']
        if any(term in content_lower for term in high_penalty_terms):
            penalty_factor += 0.3

        # Medium penalty indicators
        medium_penalty_terms = ['breach', 'violation', 'non-compliance', 'infringement']
        if any(term in content_lower for term in medium_penalty_terms):
            penalty_factor += 0.2

        # Low penalty indicators
        low_penalty_terms = ['remedial action', 'corrective measures', 'improvement']
        if any(term in content_lower for term in low_penalty_terms):
            penalty_factor += 0.1

        return penalty_factor

    def _calculate_complexity_factor(self, document: Document) -> float:
        complexity_score = 0.0

        # Check for complex calculations
        if re.search(r'formula|calculation|compute', document.content, re.IGNORECASE):
            complexity_score += 0.2

        # Check for multiple cross-references
        if len(document.cross_references) > 5:
            complexity_score += 0.2

        # Check for conditional logic
        conditional_terms = ['if', 'unless', 'provided that', 'except', 'subject to']
        conditional_count = sum(1 for term in conditional_terms if term in document.content.lower())
        complexity_score += min(conditional_count * 0.05, 0.3)

        # Check document length
        if len(document.content.split()) > 1000:
            complexity_score += 0.1

        return complexity_score
```

### 4.2 Jurisdiction-Specific Ranking

#### Authority-Based Prioritization
```python
class JurisdictionRanker:
    def __init__(self):
        self.authority_hierarchy = {
            'EU': {
                'EBA': {'priority': 1.0, 'scope': 'banking'},
                'ESMA': {'priority': 1.0, 'scope': 'securities'},
                'EIOPA': {'priority': 1.0, 'scope': 'insurance'},
                'ECB': {'priority': 0.95, 'scope': 'monetary_policy'},
                'European Commission': {'priority': 0.9, 'scope': 'general'}
            },
            'Spain': {
                'Bank of Spain': {'priority': 0.9, 'scope': 'banking'},
                'CNMV': {'priority': 0.85, 'scope': 'securities'}
            }
        }

    def apply_jurisdiction_ranking(self, documents: List[Document], query: str, user_jurisdiction: str = 'EU') -> List[Document]:
        # Determine query scope
        query_scope = self._determine_query_scope(query)

        # Apply jurisdiction-specific scoring
        jurisdiction_scores = []
        for doc in documents:
            base_score = doc.current_score
            jurisdiction_score = self._calculate_jurisdiction_score(doc, query_scope, user_jurisdiction)
            final_score = base_score * jurisdiction_score
            jurisdiction_scores.append((final_score, doc))

        # Sort by jurisdiction-adjusted score
        jurisdiction_scores.sort(key=lambda x: x[0], reverse=True)

        return [doc for score, doc in jurisdiction_scores]

    def _determine_query_scope(self, query: str) -> str:
        query_lower = query.lower()

        if any(term in query_lower for term in ['bank', 'credit', 'capital', 'lending', 'deposit']):
            return 'banking'
        elif any(term in query_lower for term in ['securities', 'market', 'trading', 'investment']):
            return 'securities'
        elif any(term in query_lower for term in ['insurance', 'pension', 'actuarial']):
            return 'insurance'
        elif any(term in query_lower for term in ['monetary', 'policy', 'interest rate']):
            return 'monetary_policy'
        else:
            return 'general'

    def _calculate_jurisdiction_score(self, document: Document, query_scope: str, user_jurisdiction: str) -> float:
        doc_authority = document.authority

        # Find authority in hierarchy
        jurisdiction_info = None
        for jurisdiction, authorities in self.authority_hierarchy.items():
            if doc_authority in authorities:
                jurisdiction_info = authorities[doc_authority]
                break

        if not jurisdiction_info:
            return 0.5  # Default score for unknown authorities

        # Base priority score
        priority_score = jurisdiction_info['priority']

        # Scope alignment boost
        if jurisdiction_info['scope'] == query_scope:
            priority_score *= 1.1
        elif jurisdiction_info['scope'] == 'general':
            priority_score *= 0.95
        else:
            priority_score *= 0.9

        # User jurisdiction preference
        if user_jurisdiction in self.authority_hierarchy:
            if doc_authority in self.authority_hierarchy[user_jurisdiction]:
                priority_score *= 1.05  # Small boost for user's jurisdiction

        return priority_score
```

### 4.3 Final Ranking Algorithm

#### Comprehensive Scoring Integration
```python
class FinalRanker:
    def __init__(self):
        self.compliance_scorer = ComplianceScorer()
        self.jurisdiction_ranker = JurisdictionRanker()

        # Final scoring weights
        self.scoring_weights = {
            'reranking_score': 0.5,      # Base reranking score
            'compliance_score': 0.25,    # Regulatory compliance importance
            'jurisdiction_score': 0.15,  # Authority/jurisdiction relevance
            'temporal_score': 0.1        # Recency and temporal relevance
        }

    def final_ranking(self, documents: List[Document], query: str, user_context: Dict) -> List[Document]:
        final_scored_docs = []

        for doc in documents:
            # Get component scores
            base_score = doc.current_score
            compliance_score = self.compliance_scorer.calculate_compliance_score(base_score, doc, query)
            jurisdiction_score = self.jurisdiction_ranker._calculate_jurisdiction_score(
                doc,
                self.jurisdiction_ranker._determine_query_scope(query),
                user_context.get('jurisdiction', 'EU')
            )
            temporal_score = self._calculate_temporal_score(doc)

            # Calculate weighted final score
            final_score = (
                base_score * self.scoring_weights['reranking_score'] +
                compliance_score * self.scoring_weights['compliance_score'] +
                jurisdiction_score * self.scoring_weights['jurisdiction_score'] +
                temporal_score * self.scoring_weights['temporal_score']
            )

            # Apply user-specific adjustments
            if user_context.get('role') == 'compliance_officer':
                final_score *= 1.1 if 'requirement' in doc.content.lower() else 1.0
            elif user_context.get('role') == 'risk_manager':
                final_score *= 1.1 if any(term in doc.content.lower() for term in ['risk', 'penalty', 'breach']) else 1.0

            final_scored_docs.append((final_score, doc))

        # Sort by final score
        final_scored_docs.sort(key=lambda x: x[0], reverse=True)

        # Apply diversity to avoid over-concentration from single authority
        diversified_docs = self._apply_diversity(final_scored_docs)

        return [doc for score, doc in diversified_docs[:10]]  # Return top 10

    def _calculate_temporal_score(self, document: Document) -> float:
        if not document.effective_date:
            return 0.5

        current_date = datetime.now()
        days_since_effective = (current_date - document.effective_date).days

        # Prefer recent documents but not too recent (might be drafts)
        if days_since_effective < 30:
            return 0.8  # Very recent, might be draft
        elif days_since_effective < 365:
            return 1.0  # Optimal recency
        elif days_since_effective < 1095:  # 3 years
            return 0.9
        elif days_since_effective < 1825:  # 5 years
            return 0.7
        else:
            return 0.5  # Older documents

    def _apply_diversity(self, scored_docs: List[Tuple[float, Document]], max_per_authority: int = 4) -> List[Tuple[float, Document]]:
        authority_counts = {}
        diversified_docs = []

        for score, doc in scored_docs:
            authority = doc.authority
            current_count = authority_counts.get(authority, 0)

            if current_count < max_per_authority:
                diversified_docs.append((score, doc))
                authority_counts[authority] = current_count + 1
            elif len(diversified_docs) < 10:  # Fill remaining slots if needed
                diversified_docs.append((score * 0.9, doc))  # Slight penalty for concentration

        return diversified_docs
```

## 5. Performance Optimization

### 5.1 Caching Strategy

#### Multi-Level Caching
```python
class RerankerCache:
    def __init__(self):
        self.l1_cache = {}  # In-memory cache for recent queries
        self.l2_cache = redis.Redis(host='localhost', port=6379, db=1)  # Redis cache

    async def get_cached_reranking(self, query_hash: str, doc_ids: List[str]) -> Optional[List[float]]:
        # Check L1 cache first
        cache_key = f"{query_hash}:{':'.join(sorted(doc_ids))}"

        if cache_key in self.l1_cache:
            return self.l1_cache[cache_key]

        # Check L2 cache
        cached_scores = self.l2_cache.get(cache_key)
        if cached_scores:
            scores = json.loads(cached_scores)
            self.l1_cache[cache_key] = scores  # Promote to L1
            return scores

        return None

    async def cache_reranking_results(self, query_hash: str, doc_ids: List[str], scores: List[float]):
        cache_key = f"{query_hash}:{':'.join(sorted(doc_ids))}"

        # Store in both caches
        self.l1_cache[cache_key] = scores
        self.l2_cache.setex(cache_key, 3600, json.dumps(scores))  # 1 hour TTL
```

### 5.2 Parallel Processing

#### Concurrent Reranking
```python
async def parallel_reranking_pipeline(query: str, documents: List[Document]) -> List[Document]:
    # Stage 1: Fast reranking in parallel batches
    stage1_tasks = []
    batch_size = 32

    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        task = asyncio.create_task(fast_rerank_batch(query, batch))
        stage1_tasks.append(task)

    stage1_results = await asyncio.gather(*stage1_tasks)
    stage1_docs = [doc for batch_result in stage1_results for doc in batch_result]

    # Stage 2: Deep reranking
    stage2_docs = await deep_rerank(query, stage1_docs[:50])

    # Stage 3: Compliance scoring
    stage3_docs = await compliance_rank(query, stage2_docs[:20])

    return stage3_docs[:10]
```

## 6. Evaluation and Monitoring

### 6.1 Reranking Quality Metrics

#### Evaluation Framework
```python
class RerankingEvaluator:
    def __init__(self):
        self.metrics = {
            'precision_at_k': [1, 3, 5, 10],
            'ndcg_at_k': [3, 5, 10],
            'mrr': True,  # Mean Reciprocal Rank
            'map': True   # Mean Average Precision
        }

    def evaluate_reranking_quality(self,
                                 query: str,
                                 retrieved_docs: List[Document],
                                 reranked_docs: List[Document],
                                 ground_truth: List[str]) -> Dict[str, float]:

        results = {}

        # Calculate improvement from initial retrieval to reranked
        for k in self.metrics['precision_at_k']:
            initial_precision = self._precision_at_k(retrieved_docs[:k], ground_truth)
            reranked_precision = self._precision_at_k(reranked_docs[:k], ground_truth)
            results[f'precision_at_{k}_improvement'] = reranked_precision - initial_precision

        # Calculate NDCG improvement
        for k in self.metrics['ndcg_at_k']:
            initial_ndcg = self._ndcg_at_k(retrieved_docs[:k], ground_truth)
            reranked_ndcg = self._ndcg_at_k(reranked_docs[:k], ground_truth)
            results[f'ndcg_at_{k}_improvement'] = reranked_ndcg - initial_ndcg

        return results

    def _precision_at_k(self, docs: List[Document], ground_truth: List[str]) -> float:
        relevant_count = 0
        for doc in docs:
            if doc.document_id in ground_truth:
                relevant_count += 1
        return relevant_count / len(docs) if docs else 0.0

    def _ndcg_at_k(self, docs: List[Document], ground_truth: List[str]) -> float:
        dcg = 0.0
        for i, doc in enumerate(docs):
            if doc.document_id in ground_truth:
                dcg += 1.0 / math.log2(i + 2)  # i+2 because log2(1) = 0

        # Calculate IDCG (Ideal DCG)
        idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(ground_truth), len(docs))))

        return dcg / idcg if idcg > 0 else 0.0
```

### 6.2 Real-time Monitoring

#### Performance Tracking
```python
class RerankingMonitor:
    def __init__(self):
        self.metrics_collector = MetricsCollector()

    async def track_reranking_performance(self,
                                        query: str,
                                        stage_times: Dict[str, float],
                                        quality_scores: Dict[str, float]):

        # Track latency metrics
        await self.metrics_collector.record_histogram(
            'reranking_stage1_latency',
            stage_times['stage1']
        )
        await self.metrics_collector.record_histogram(
            'reranking_stage2_latency',
            stage_times['stage2']
        )
        await self.metrics_collector.record_histogram(
            'reranking_stage3_latency',
            stage_times['stage3']
        )

        # Track quality metrics
        await self.metrics_collector.record_gauge(
            'reranking_precision_improvement',
            quality_scores.get('precision_at_5_improvement', 0.0)
        )

        # Track query patterns
        query_type = classify_query_type(query)
        await self.metrics_collector.increment_counter(
            'reranking_query_types',
            tags={'type': query_type}
        )
```

## 7. Implementation Timeline

### 7.1 Development Phases

#### Phase 1: Foundation (Weeks 1-2)
- Implement Stage 1 fast cross-encoder reranking
- Set up basic caching infrastructure
- Create evaluation framework

#### Phase 2: Enhancement (Weeks 3-4)
- Implement Stage 2 deep contextual reranking
- Add regulatory-specific scoring
- Implement parallel processing

#### Phase 3: Specialization (Weeks 5-6)
- Implement Stage 3 compliance scoring
- Add jurisdiction-specific ranking
- Fine-tune regulatory models

#### Phase 4: Optimization (Weeks 7-8)
- Performance optimization and caching
- Comprehensive testing and evaluation
- Monitoring and alerting setup

This multi-stage reranking strategy provides the precision and compliance-awareness required for regulatory document retrieval while maintaining sub-2 second processing times for optimal user experience.