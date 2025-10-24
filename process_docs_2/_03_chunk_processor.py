"""
Módulo 3: Chunk Processor
Responsable de:
1. Cargar los chunks de la etapa anterior
2. Generar embeddings enriquecidos con contexto
3. Extraer título y resumen de cada chunk
4. Clasificar chunks por categoría
5. Extraer keywords
6. Preparar datos para inserción en base de datos
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
import tldextract
from dateutil import parser

# Importar configuración y utilidades compartidas
from shared.config import (
    CHECKPOINT_DIR, LLM_MODEL, EMBEDDING_MODEL,
    PROCESS_BATCH_SIZE, PENDING_CHUNKS_DIR
)
from shared.utils import (
    openai_client, rate_limited_openai_call,
    save_json, load_json, ensure_directory,
    save_failed_data, process_in_batches
)
from shared.models import (
    ProcessingCheckpoint, ProcessedChunk, ChunkMetadata,
    DocumentMetadata
)


class ChunkProcessor:
    """Procesa chunks para generar embeddings y metadatos enriquecidos."""
    
    def __init__(self, checkpoint_dir: Path = CHECKPOINT_DIR):
        self.checkpoint_dir = ensure_directory(checkpoint_dir)
        self.batch_size = PROCESS_BATCH_SIZE
    
    async def process_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Procesa todos los chunks de un documento.
        
        Args:
            doc_id: ID del documento a procesar
            
        Returns:
            Diccionario con información del procesamiento
        """
        # Cargar checkpoint
        checkpoint_file = self.checkpoint_dir / f"{doc_id}_checkpoint.json"
        if not checkpoint_file.exists():
            return {
                "success": False,
                "error": f"No se encontró checkpoint para documento {doc_id}"
            }
        
        checkpoint_data = load_json(checkpoint_file)
        checkpoint = ProcessingCheckpoint.from_dict(checkpoint_data)
        
        # Verificar que las etapas anteriores estén completas
        if not checkpoint.chunks_created or not checkpoint.chunks_file:
            return {
                "success": False,
                "error": "Los chunks no han sido creados aún"
            }
        
        # Si ya se procesaron los chunks, no reprocesar
        if checkpoint.chunks_processed:
            logging.info(f"Chunks ya procesados para documento {doc_id}")
            return {
                "success": True,
                "doc_id": doc_id,
                "already_processed": True
            }
        
        try:
            # Cargar chunks
            chunks_file = Path(checkpoint.chunks_file)
            if not chunks_file.exists():
                raise FileNotFoundError(f"Archivo de chunks no encontrado: {chunks_file}")
            
            chunks_with_metadata = load_json(chunks_file)
            
            # Cargar metadatos del documento
            document_metadata = DocumentMetadata.from_dict(checkpoint.metadata) if checkpoint.metadata else None
            
            logging.info(f"Procesando {len(chunks_with_metadata)} chunks para documento {doc_id}")
            
            # Procesar chunks en batches
            processed_chunks = await self._process_chunks_batch(
                chunks_with_metadata,
                checkpoint.file_path,
                checkpoint.document_id_db,
                document_metadata
            )
            
            # Guardar chunks procesados
            processed_file = self.checkpoint_dir / f"{doc_id}_processed.json"
            processed_data = [chunk.to_dict() for chunk in processed_chunks]
            save_json(processed_data, processed_file)
            
            # Actualizar checkpoint
            checkpoint.processed_file = str(processed_file)
            checkpoint.chunks_processed = True
            save_json(checkpoint.to_dict(), checkpoint_file)
            
            logging.info(f"Procesados {len(processed_chunks)} chunks para documento {doc_id}")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "chunks_processed": len(processed_chunks),
                "next_stage": "04_data_ingester"
            }
            
        except Exception as e:
            logging.error(f"Error procesando chunks del documento {doc_id}: {e}")
            
            # Actualizar checkpoint con error
            checkpoint.error = str(e)
            checkpoint.failed_at = datetime.now(timezone.utc).isoformat()
            save_json(checkpoint.to_dict(), checkpoint_file)
            
            return {
                "success": False,
                "doc_id": doc_id,
                "error": str(e)
            }
    
    async def _process_chunks_batch(
        self,
        chunks_with_metadata: List[Dict],
        file_path: str,
        document_id: Optional[int],
        document_metadata: Optional[DocumentMetadata]
    ) -> List[ProcessedChunk]:
        """
        Procesa todos los chunks en batches.
        """
        processed_chunks = []
        
        # Procesar en batches para evitar sobrecarga
        for i in range(0, len(chunks_with_metadata), self.batch_size):
            batch = chunks_with_metadata[i:i+self.batch_size]
            
            logging.info(f"Procesando batch {i//self.batch_size + 1} de {(len(chunks_with_metadata) + self.batch_size - 1)//self.batch_size}")
            
            # Procesar cada chunk del batch
            batch_tasks = []
            for idx, chunk_data in enumerate(batch):
                task = self._process_single_chunk(
                    chunk_data,
                    chunk_number=i + idx,
                    identifier=file_path,
                    document_id=document_id,
                    document_metadata=document_metadata
                )
                batch_tasks.append(task)
            
            # Ejecutar batch en paralelo
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Manejar resultados
            for idx, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logging.error(f"Error procesando chunk {i + idx}: {result}")
                    raise result
                else:
                    processed_chunks.append(result)
            
            # Pausa entre batches
            if i + self.batch_size < len(chunks_with_metadata):
                await asyncio.sleep(2)
        
        return processed_chunks
    
    async def _process_single_chunk(
        self,
        chunk_with_metadata: Dict,
        chunk_number: int,
        identifier: str,
        document_id: Optional[int],
        document_metadata: Optional[DocumentMetadata]
    ) -> ProcessedChunk:
        """
        Procesa un único chunk generando embeddings y metadatos enriquecidos.
        """
        # Extraer texto y metadata del chunk
        chunk_text = chunk_with_metadata.get("text", "")
        cluster_id = chunk_with_metadata.get("cluster_id", -1)
        cluster_size = chunk_with_metadata.get("cluster_size", 1)
        article_number = chunk_with_metadata.get("article_number")
        article_title = chunk_with_metadata.get("article_title")
        
        # Convertir document_metadata a dict si es necesario
        doc_meta_dict = document_metadata.to_dict() if document_metadata else {}
        
        # Paso 1: Extraer título y resumen
        extracted = await self._get_title_and_summary(chunk_text, identifier)
        summary = extracted.get('summary', '')
        
        # Paso 2: Construir input enriquecido para embedding
        embedding_input = self._build_enriched_embedding_input(
            chunk_text=chunk_text,
            summary=summary,
            document_metadata=doc_meta_dict,
            article_number=article_number,
            article_title=article_title
        )
        
        # Paso 3: Generar embedding
        embedding = await self._get_embedding(embedding_input)
        
        # Paso 4: Obtener metadatos adicionales
        date = self._extract_date_from_url(identifier)
        source = await self._get_source(identifier)
        
        # Obtener categoría y keywords
        category = await self._get_category(chunk_text)
        keywords = await self._extract_keywords(chunk_text)
        
        # Paso 5: Construir metadata completa
        metadata = ChunkMetadata(
            chunk_size=len(chunk_text),
            source_identifier=identifier,
            date=date,
            category=category,
            keywords=keywords,
            source=source,
            cluster_id=cluster_id,
            cluster_size=cluster_size,
            article_number=article_number,
            article_title=article_title,
            document_type=doc_meta_dict.get("document_type"),
            document_title=doc_meta_dict.get("document_title"),
            issuing_authority=doc_meta_dict.get("issuing_authority"),
            publication_date=doc_meta_dict.get("publication_date"),
            jurisdiction=doc_meta_dict.get("jurisdiction"),
            status=doc_meta_dict.get("status"),
            document_number=doc_meta_dict.get("document_number"),
            official_source=doc_meta_dict.get("official_source"),
            embedding_components_count=len(embedding_input.split('\n\n'))
        )
        
        # Añadir metadata adicional del chunk original
        for key in ['has_overlap', 'chunk_in_cluster', 'clustering_method', 'is_subdivision']:
            if key in chunk_with_metadata:
                setattr(metadata, key, chunk_with_metadata[key])
        
        return ProcessedChunk(
            url=identifier,
            chunk_number=chunk_number,
            title=extracted.get('title', ''),
            summary=summary,
            content=chunk_text,
            metadata=metadata.to_dict(),
            embedding=embedding,
            document_id=document_id
        )
    
    def _build_enriched_embedding_input(
        self,
        chunk_text: str,
        summary: str,
        document_metadata: Dict[str, Any],
        article_number: Optional[str] = None,
        article_title: Optional[str] = None
    ) -> str:
        """
        Construye un input enriquecido para generar embeddings más precisos.
        """
        embedding_components = []
        
        if article_number:
            embedding_components.append(f"Artículo: {article_number}")
        
        if article_title:
            embedding_components.append(f"Título del artículo: {article_title}")   

                # Añadir contexto del chunk
        if summary:
            embedding_components.append(f"Contexto del fragmento: {summary}") 
        
        # Añadir contexto del documento

        if document_metadata.get('document_type'):
            embedding_components.append(f"Tipo de documento: {document_metadata['document_type']}")

        if document_metadata.get('issuing_authority'):
            embedding_components.append(f"Autoridad emisora: {document_metadata['issuing_authority']}")

        if document_metadata.get('document_title'):
            embedding_components.append(f"Documento: {document_metadata['document_title']}")
        
        if document_metadata.get('jurisdiction'):
            embedding_components.append(f"Jurisdicción: {document_metadata['jurisdiction']}")
        
        
        # Construir el input final
        context_prefix = "\n".join(embedding_components)
        
        enriched_input = f"""{context_prefix}

Contenido del fragmento:
{chunk_text}"""
        
        return enriched_input
    
    async def _get_title_and_summary(self, chunk: str, identifier: str) -> Dict[str, str]:
        """
        Extrae título y resumen usando OpenAI.
        """
        system_prompt = (
            "You are an AI that extracts titles and summaries from documentation chunks in the same language as the chunk.\n"
            "Return a JSON object with 'title' and 'summary' keys.\n"
            "For the title: Extract its title.\n"
            "For the summary: Give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk and include any important cross-references to other provisions of the document. Answer only with the succinct context and nothing else.\n"
            "Keep both title and summary concise but informative."
        )
        
        try:
            async def call_api():
                return await openai_client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Identifier: {identifier}\n\nContent:\n{chunk[:1000]}..."}
                    ],
                    response_format={"type": "json_object"}
                )
            
            response = await rate_limited_openai_call(call_api)
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logging.error(f"Error al obtener título y resumen: {e}")
            return {
                "title": "Error procesando el título",
                "summary": "Error procesando el resumen"
            }
    
    async def _get_embedding(self, text: str) -> List[float]:
        """
        Obtiene el embedding del texto usando OpenAI.
        """
        try:
            async def call_api():
                return await openai_client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=text
                )
            
            response = await rate_limited_openai_call(call_api)
            return response.data[0].embedding
            
        except Exception as e:
            logging.error(f"Error al obtener embedding: {e}")
            # Vector nulo en caso de error
            return [0] * 1536
    
    async def _get_category(self, chunk: str) -> str:
        """
        Clasifica el fragmento en una categoría predefinida.
        """
        system_prompt = (
            "Eres un modelo de IA que clasifica fragmentos de texto en categorías y subcategorías predefinidas.\n"
            "La clasificación se organiza así:\n\n"
            "Categoría: Sostenibilidad\n"
            "Subcategoría: ESG\n"
            "Subcategoría: SFDR\n"
            "Subcategoría: Green MIFID\n"
            "Subcategoría: Métricas e informes de sostenibilidad\n"
            "Subcategoría: Estrategias de inversión responsable\n\n"
            "Categoría: Riesgos Financieros\n"
            "Subcategoría: Riesgo de crédito\n"
            "Subcategoría: Riesgo de mercado\n"
            "Subcategoría: Riesgo de contraparte\n"
            "Subcategoría: Riesgo operacional\n"
            "Subcategoría: Gestión de riesgo de terceros\n\n"
            "Categoría: Regulación y Supervisión\n"
            "Subcategoría: PBC/FT (Prevención de Blanqueo de Capitales / Financiación del Terrorismo)\n"
            "Subcategoría: MiCA (Markets in Crypto-Assets)\n"
            "Subcategoría: Regulación IA\n"
            "Subcategoría: Supervisión bancaria\n"
            "Subcategoría: Protección del consumidor\n\n"
            "Categoría: Seguridad Financiera\n"
            "Subcategoría: Fraude\n"
            "Subcategoría: Know Your Customer (KYC)\n"
            "Subcategoría: Protección de datos\n"
            "Subcategoría: Ciberseguridad\n"
            "Subcategoría: Medios de pago\n\n"
            "Categoría: Reporting Regulatorio\n"
            "Subcategoría: FINREP/COREP\n"
            "Subcategoría: Reportes de liquidez\n"
            "Subcategoría: IFRS\n"
            "Subcategoría: Reporting de capital y solvencia\n"
            "Subcategoría: Reporting ESG\n\n"
            "Categoría: Tesorería\n"
            "Subcategoría: Gestión de liquidez\n"
            "Subcategoría: Instrumentos de financiación\n"
            "Subcategoría: Control de pagos y cobros\n"
            "Subcategoría: Cobertura de riesgos de tipo de interés y tipo de cambio\n"
            "Subcategoría: Gestión de activos y pasivos a corto plazo\n\n"
            "A partir de esta lista, clasifica cada fragmento de texto en exactamente una categoría y una subcategoría (la que consideres más relevante)."
        )
        
        try:
            async def call_api():
                return await openai_client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Content:\n{chunk[:1000]}..."}
                    ]
                )
            
            response = await rate_limited_openai_call(call_api)
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"Error al obtener la categoría: {e}")
            return "Otros"
    
    async def _extract_keywords(self, chunk: str) -> str:
        """
        Extrae palabras clave representativas del fragmento.
        """
        system_prompt = (
            "Eres un modelo de IA que extrae palabras clave de fragmentos de texto.\n"
            "Para cada fragmento identifica el tipo de documento regulatorio y devuelve dos palabras clave que representan los temas principales del contenido."
        )
        
        try:
            async def call_api():
                return await openai_client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Content:\n{chunk[:1000]}..."}
                    ]
                )
            
            response = await rate_limited_openai_call(call_api)
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"Error al obtener palabras clave: {e}")
            return "Otros"
    
    def _extract_date_from_url(self, identifier: str) -> str:
        """
        Intenta extraer una fecha del identifier.
        """
        try:
            parsed = urlparse(identifier)
            path_segments = parsed.path.split('/')
            for segment in path_segments:
                try:
                    date = parser.parse(segment, fuzzy=False)
                    return date.isoformat()
                except (ValueError, OverflowError):
                    continue
        except Exception as e:
            logging.error(f"Error al extraer fecha: {e}")
        
        return datetime.now(timezone.utc).isoformat()
    
    async def _get_source(self, identifier: str) -> str:
        """
        Devuelve la fuente a partir del identifier.
        """
        try:
            if identifier.startswith("http"):
                extracted = tldextract.extract(identifier)
                domain = f"{extracted.domain}.{extracted.suffix}"
                return domain
            else:
                return os.path.basename(identifier)
        except Exception as e:
            logging.error(f"Error al obtener la fuente: {e}")
            return "fuente_desconocida"


async def main():
    """Función principal para procesar documentos pendientes."""
    processor = ChunkProcessor()
    
    # Buscar documentos que necesitan procesamiento de chunks
    checkpoint_files = list(CHECKPOINT_DIR.glob("*_checkpoint.json"))
    
    documents_to_process = []
    for checkpoint_file in checkpoint_files:
        checkpoint_data = load_json(checkpoint_file)
        if (checkpoint_data and 
            checkpoint_data.get("chunks_created") and 
            not checkpoint_data.get("chunks_processed")):
            doc_id = checkpoint_data["doc_id"]
            documents_to_process.append(doc_id)
    
    if not documents_to_process:
        logging.info("No se encontraron documentos pendientes de procesamiento de chunks.")
        return
    
    logging.info(f"Encontrados {len(documents_to_process)} documentos para procesar chunks.")
    
    # Procesar documentos
    for doc_id in documents_to_process:
        logging.info(f"\n{'='*60}")
        logging.info(f"Procesando chunks para documento: {doc_id}")
        logging.info(f"{'='*60}")
        
        result = await processor.process_document(doc_id)
        
        if result["success"]:
            logging.info(f"✓ Chunks procesados exitosamente: {doc_id}")
            logging.info(f"  - Chunks procesados: {result.get('chunks_processed', 'N/A')}")
            logging.info(f"  - Siguiente etapa: {result.get('next_stage', 'N/A')}")
        else:
            logging.error(f"✗ Error procesando chunks: {doc_id}")
            logging.error(f"  - Error: {result.get('error', 'Desconocido')}")
    
    logging.info("\n" + "="*60)
    logging.info("Procesamiento de chunks completado")
    logging.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())