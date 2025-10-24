"""
Módulo 2: Text Splitter
Responsable de:
1. Cargar el texto extraído de la etapa anterior
2. Aplicar semantic chunking (clustering jerárquico para textos generales)
3. Detectar y dividir por artículos para documentos normativos
4. Guardar chunks con metadata para la siguiente etapa
"""

import os
import json
import asyncio
import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from datetime import datetime
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity

# Importar configuración y utilidades compartidas
from shared.config import (
    CHECKPOINT_DIR, DEFAULT_CHUNK_SIZE, MIN_CHUNK_SIZE,
    MAX_CHUNKS, OVERLAP_SIZE, BATCH_SIZE, EMBEDDING_MODEL,
    ALLOW_ARTICLE_SUBDIVISION, MAX_ARTICLE_SIZE
)
from shared.utils import (
    openai_client, rate_limited_openai_call,
    save_json, load_json, ensure_directory,
    save_failed_data, clean_headers_footers
)
from shared.models import ProcessingCheckpoint


class TextSplitter:
    """Divide texto en chunks semánticamente coherentes."""
    
    def __init__(self, checkpoint_dir: Path = CHECKPOINT_DIR):
        self.checkpoint_dir = ensure_directory(checkpoint_dir)
        self.chunk_size = DEFAULT_CHUNK_SIZE
        self.min_chunk_size = MIN_CHUNK_SIZE
        self.max_chunks = MAX_CHUNKS
        self.overlap_size = OVERLAP_SIZE
        self.allow_article_subdivision = ALLOW_ARTICLE_SUBDIVISION
        self.max_article_size = MAX_ARTICLE_SIZE
    
    async def process_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Procesa un documento desde su checkpoint y divide el texto en chunks.
        
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
        
        # Verificar que la etapa anterior esté completa
        if not checkpoint.text_extracted or not checkpoint.text_file:
            return {
                "success": False,
                "error": "El texto no ha sido extraído aún"
            }
        
        # Si ya se crearon chunks, no reprocesar
        if checkpoint.chunks_created:
            logging.info(f"Chunks ya creados para documento {doc_id}")
            return {
                "success": True,
                "doc_id": doc_id,
                "chunks_count": checkpoint.chunks_count,
                "already_processed": True
            }
        
        try:
            # Cargar el texto extraído
            text_file = Path(checkpoint.text_file)
            if not text_file.exists():
                raise FileNotFoundError(f"Archivo de texto no encontrado: {text_file}")
            
            text = text_file.read_text(encoding='utf-8')
            
            # Determinar si es un documento normativo
            is_regulatory = self._is_regulatory_document(text, checkpoint.metadata)
            
            logging.info(f"Procesando documento {doc_id} - Tipo: {'normativo' if is_regulatory else 'general'}")
            
            # Aplicar semantic chunking
            chunks_with_metadata = await self.semantic_chunk_text(
                text=text,
                is_regulatory=is_regulatory,
                document_metadata=checkpoint.metadata
            )
            
            # Validar chunks
            validation = self._validate_chunks(chunks_with_metadata)
            if not validation["valid"]:
                logging.warning(f"Validación de chunks falló: {validation['errors']}")
                logging.info("Manteniendo chunks por artículos a pesar de las advertencias")
            
            # Guardar chunks
            chunks_file = self.checkpoint_dir / f"{doc_id}_chunks.json"
            save_json(chunks_with_metadata, chunks_file)
            
            # Actualizar checkpoint
            checkpoint.chunks_file = str(chunks_file)
            checkpoint.chunks_count = len(chunks_with_metadata)
            checkpoint.chunks_created = True
            save_json(checkpoint.to_dict(), checkpoint_file)
            
            logging.info(f"Documento {doc_id} dividido en {len(chunks_with_metadata)} chunks")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "chunks_count": len(chunks_with_metadata),
                "validation": validation,
                "next_stage": "03_chunk_processor"
            }
            
        except Exception as e:
            logging.error(f"Error dividiendo texto del documento {doc_id}: {e}")
            
            # Actualizar checkpoint con error
            checkpoint.error = str(e)
            checkpoint.failed_at = datetime.now().isoformat()
            save_json(checkpoint.to_dict(), checkpoint_file)
            
            return {
                "success": False,
                "doc_id": doc_id,
                "error": str(e)
            }
    
    def _is_regulatory_document(self, text: str, metadata: Optional[Dict] = None) -> bool:
        """
        Determina si un documento es normativo basándose en su contenido y metadatos.
        """
        # Verificar por tipo de documento en metadatos
        if metadata and metadata.get("document_type"):
            doc_type = metadata["document_type"].lower()
            regulatory_types = ["ley", "reglamento", "decreto", "circular", "directiva", 
                              "norma", "código", "resolución", "acuerdo"]
            if any(r_type in doc_type for r_type in regulatory_types):
                return True
        
        # Verificar por patrones en el texto
        regulatory_patterns = [
            r'(?i)art(?:ículo|iculo|\.)\s+\d+',
            r'(?i)ARTÍCULO\s+\d+',
            r'(?i)(?:CAPÍTULO|TÍTULO|SECCIÓN)\s+[IVXLCDM]+',
            r'(?i)(?:LEY|REGLAMENTO|DECRETO|CÓDIGO)\s+(?:FEDERAL|GENERAL|DE)',
            r'(?i)Norma\s+\d+'
        ]
        
        # Contar coincidencias
        matches = sum(1 for pattern in regulatory_patterns 
                     if re.search(pattern, text[:10000]))  # Solo verificar inicio
        
        return matches >= 2
    
    async def semantic_chunk_text(self, text: str, is_regulatory: bool = True, document_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Divide el texto en fragmentos por artículos.
        Siempre usa detección de artículos para documentos normativos.
        """
        return await self._chunk_regulatory_document(text, document_metadata)
        
    
    async def _chunk_regulatory_document(
        self, 
        text: str,
        document_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Divide un documento normativo por artículos.
        """
        # Identificar artículos en el texto
        articles = self._extract_articles(text)
        
        
        # Detectar estructura jerárquica
        structures = self._extract_hierarchical_structure(text)
        
        # Asignar estructura a cada artículo
        for article in articles:
            article["hierarchy"] = self._get_article_hierarchy(
                article["start_pos"], 
                structures
            )
        
        # Extraer título del documento si es posible
        document_title = self._extract_document_title(articles, document_metadata)
        
        # Crear chunks finales
        final_chunks = []
        
        for i, article in enumerate(articles):
            # Manejar artículos muy largos
            if len(article["content"]) > self.chunk_size:
                sub_chunks = self._subdivide_article(article, i, document_title)
                final_chunks.extend(sub_chunks)
            else:
                # Crear chunk normal
                chunk = self._create_article_chunk(article, i, len(articles), document_title)
                final_chunks.append(chunk)
        
        return final_chunks
    
    def _extract_articles(self, text: str) -> List[Dict]:
        """
        Extrae artículos del texto normativo.
        Patrón actualizado para reconocer: Artículo [número]°.- [Título]
        """
        
        # Buscar inicios de artículos con el patrón específico del documento
        article_starts = []
        
        # Patrón principal: Artículo [número]°.- [título]
        # Explicación del patrón:
        # (?i) - insensible a mayúsculas/minúsculas
        # (?:^|\n+) - inicio de línea o después de uno o más saltos de línea
        # (Artículo\s+\d+°\.-) - captura "Artículo [espacio] [número] ° . -"
        # \s* - espacios opcionales después del patrón
        # (.*?) - captura no voraz del título hasta el salto de línea
        
        #main_pattern = r'(?im)(?:^|\n+)(Norma\s+(\d+)\.\s*)(.*?)(?=\n|$)'
        
        main_pattern = r'(?i)(?:^|\n+)(Artículo\s+(\d+)\.-)\s*(.*?)(?=\n|$)' #Regulación Peru
        
        # main_pattern = r'(?i)(?:^|\n)(Artículo\s+(\d+))\s*\n+([^\n]+)(?=\s*\n.*?1\.)'
        # main_pattern = r'(?i)(?:^|\n\s*)(Artículo\s+(\d+))\s*\n+([^\n]+)(?=\s*\n)' #GDPR
        # main_pattern = r'(?i)(?:^|\n+)(Artículo\s+(\d+)\.)\s*(.*?)(?=\n|$)' #LFPDPPP
        
        logging.info("Buscando artículos con patrón: Artículo [número]°.- [título]")
        
        for match in re.finditer(main_pattern, text):
            full_match = match.group(1)  # "Artículo X°.-"
            article_num = match.group(2)  # Solo el número
            article_title_part = match.group(3).strip() if len(match.groups()) > 2 else ""
            start_pos = match.start()
            
            article_starts.append((article_num, start_pos, full_match, article_title_part))
            
            # Log detallado para debugging
            logging.info(f"Encontrado: {full_match} {article_title_part} en posición {start_pos}")
        
        # Si el patrón principal no encuentra artículos, intentar variaciones
        if not article_starts:
            logging.info("Patrón principal no encontró artículos, probando variaciones...")
            
            # Patrón alternativo sin el símbolo de grado
            alt_pattern = r'(?i)(?:^|\n)(Artículo\s+(\d+))\s*\n+([^\n]+)'
            
            for match in re.finditer(alt_pattern, text):
                full_match = match.group(1)
                article_num = match.group(2)
                article_title_part = match.group(3).strip() if len(match.groups()) > 2 else ""
                start_pos = match.start()
                
                article_starts.append((article_num, start_pos, full_match, article_title_part))
                logging.info(f"Encontrado (patrón alt): {full_match} {article_title_part} en posición {start_pos}")
        
        # Si aún no encuentra artículos, intentar un patrón más amplio
        if not article_starts:
            logging.info("Patrones específicos no encontraron artículos, usando patrón amplio...")
            
            # Patrón más permisivo para capturar diferentes variaciones
            broad_pattern = r'(?i)(?:^|\n+)(Artículo\s+(\d+)?\.?-?)\s*(.*?)(?=\n|$)'
            
            for match in re.finditer(broad_pattern, text):
                full_match = match.group(1)
                article_num = match.group(2)
                article_title_part = match.group(3).strip() if len(match.groups()) > 2 else ""
                start_pos = match.start()
                
                article_starts.append((article_num, start_pos, full_match, article_title_part))
                logging.info(f"Encontrado (patrón amplio): {full_match} {article_title_part} en posición {start_pos}")
        
        # Si no encuentra ningún artículo, retornar lista vacía
        if not article_starts:
            logging.warning("No se encontraron artículos en el documento con ningún patrón")
            return []
        
        # Ordenar por posición en el texto
        article_starts.sort(key=lambda x: x[1])
        
        logging.info(f"Total de artículos encontrados: {len(article_starts)}")
        
        # Extraer el contenido completo de cada artículo
        articles = []
        for i, (article_num, start_pos, full_match, title_part) in enumerate(article_starts):
            # Determinar dónde termina este artículo (donde empieza el siguiente o final del texto)
            end_pos = article_starts[i+1][1] if i < len(article_starts) - 1 else len(text)
            
            # Extraer todo el contenido del artículo
            article_content = text[start_pos:end_pos].strip()
            
            # Crear el título completo del artículo
            if title_part:
                article_title = f"Norma {article_num}°.- {title_part}"
            else:
                article_title = f"Artículo {article_num}°.-"
            
            # Mostrar información de debugging sobre el contenido extraído
            content_preview = article_content[:150] + "..." if len(article_content) > 150 else article_content
            logging.info(f"Artículo {article_num}: {len(article_content)} caracteres")
            logging.info(f"  Título: {article_title}")
            logging.info(f"  Preview: {content_preview}")
            logging.info(f"  Rango: {start_pos}-{end_pos}")
            
            articles.append({
                "number": article_num,
                "title": article_title,
                "content": article_content,
                "start_pos": start_pos,
                "end_pos": end_pos,
                "full_match": full_match,  # Para referencia de debugging
                "title_part": title_part   # Solo la parte del título después de ".-"
            })
        
        return articles
    
    def _extract_hierarchical_structure(self, text: str) -> List[Dict]:
        """
        Extrae la estructura jerárquica del documento (capítulos, títulos, etc).
        """
        structure_pattern = r'(?i)(?:^|\n+)(CAPÍTULO|TÍTULO|SECCIÓN)\s+([IVX]+|[0-9]+)\.?\s*[-–—]?\s*(.*?)(?=\n+)'
        structures = []
        
        for match in re.finditer(structure_pattern, text, re.DOTALL):
            struct_type = match.group(1).upper()
            struct_num = match.group(2)
            struct_title = match.group(3).strip() if len(match.groups()) > 2 else ""
            
            structures.append({
                "type": struct_type,
                "number": struct_num,
                "title": struct_title,
                "start_pos": match.start(),
                "end_pos": match.end()
            })
        
        return structures
    
    def _get_article_hierarchy(self, article_pos: int, structures: List[Dict]) -> List[Dict]:
        """
        Obtiene la jerarquía estructural para un artículo dado.
        """
        current_hierarchy = []
        
        for structure in structures:
            if structure["start_pos"] < article_pos:
                # Determinar si reemplazar estructura del mismo tipo
                replaced = False
                for i, h in enumerate(current_hierarchy):
                    if h["type"] == structure["type"]:
                        current_hierarchy[i] = {
                            "type": structure["type"],
                            "number": structure["number"],
                            "title": structure["title"]
                        }
                        replaced = True
                        break
                
                if not replaced:
                    current_hierarchy.append({
                        "type": structure["type"],
                        "number": structure["number"],
                        "title": structure["title"]
                    })
        
        return current_hierarchy
    
    def _extract_document_title(
        self, 
        articles: List[Dict],
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Extrae el título del documento.
        """
        # Primero intentar desde metadata
        if metadata and metadata.get("document_title"):
            return metadata["document_title"]
        
        # Buscar en la estructura jerárquica
        for article in articles:
            if article.get("hierarchy"):
                for h in article["hierarchy"]:
                    if h["type"] in ["LEY", "CÓDIGO", "REGLAMENTO", "DECRETO"]:
                        return f"{h['type']} {h['title']}"
        
        return None
    
    def _subdivide_article(
        self, 
        article: Dict, 
        article_index: int,
        document_title: Optional[str]
    ) -> List[Dict]:
        """
        Subdivide un artículo largo en múltiples chunks.
        """
        content = article["content"]
        chunks = []
        
        # Dividir por párrafos
        paragraphs = [p for p in re.split(r'\n{2,}', content) if p.strip()]
        
        if len(paragraphs) < 2:
            paragraphs = re.split(r'(?<=\.)\s+', content)
        
        current_chunk = ""
        chunk_index = 1
        
        for para in paragraphs:
            if len(current_chunk) + len(para) > self.chunk_size and len(current_chunk) >= self.min_chunk_size:
                # Crear chunk
                chunk_data = self._format_article_chunk(
                    article, 
                    current_chunk.strip(),
                    f"{article['number']}.{chunk_index}",
                    f"{article['title']} (Parte {chunk_index})",
                    article_index,
                    is_subdivision=True
                )
                chunks.append(chunk_data)
                
                chunk_index += 1
                current_chunk = para
            else:
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para
        
        # Añadir último chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunk_data = self._format_article_chunk(
                article,
                current_chunk.strip(),
                f"{article['number']}.{chunk_index}",
                f"{article['title']} (Parte {chunk_index})",
                article_index,
                is_subdivision=True
            )
            chunks.append(chunk_data)
        
        return chunks
    
    def _create_article_chunk(
        self, 
        article: Dict, 
        index: int, 
        total_articles: int,
        document_title: Optional[str]
    ) -> Dict:
        """
        Crea un chunk para un artículo completo.
        """
        # Limpiar contenido
        clean_content = clean_headers_footers(article["content"], document_title)
        
        formatted_text = clean_content.strip()
        
        return self._format_article_chunk(
            article,
            formatted_text,
            article["number"],
            article["title"],
            index,
            is_subdivision=False
        )
    
    def _format_article_chunk(
        self,
        article: Dict,
        text: str,
        article_number: str,
        article_title: str,
        cluster_id: int,
        is_subdivision: bool = False
    ) -> Dict:
        """
        Formatea los datos de un chunk de artículo.
        """
        return {
            "text": text,
            "cluster_id": cluster_id,
            "cluster_size": 1,  # Se actualizará después
            "has_overlap": False,
            "article_number": article_number,
            "article_title": article_title,
            "is_subdivision": is_subdivision,
            "hierarchy": article.get("hierarchy", [])
        }
    
    
    def _validate_chunks(self, chunks: List[Dict]) -> Dict[str, Any]:
        """
        Valida la calidad de los chunks generados.
        """
        errors = []
        
        # Verificar chunks vacíos
        empty_chunks = [i for i, c in enumerate(chunks) 
                       if not c.get('text', '').strip()]
        if empty_chunks:
            errors.append(f"Chunks vacíos en posiciones: {empty_chunks}")
        
        # Verificar tamaños
        sizes = [(i, len(c.get('text', ''))) for i, c in enumerate(chunks)]
        tiny_chunks = [(i, s) for i, s in sizes if s < self.min_chunk_size]
        huge_chunks = [(i, s) for i, s in sizes if s > self.chunk_size * 3]
        
        if tiny_chunks:
            errors.append(f"Chunks muy pequeños: {tiny_chunks}")
        if huge_chunks:
            errors.append(f"Chunks muy grandes: {huge_chunks}")
        
        # Verificar metadatos básicos
        missing_metadata = [i for i, c in enumerate(chunks) 
                          if 'cluster_id' not in c]
        if missing_metadata:
            errors.append(f"Chunks sin metadata en: {missing_metadata}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'stats': {
                'total_chunks': len(chunks),
                'avg_size': sum(s for _, s in sizes) / len(sizes) if sizes else 0,
                'min_size': min(s for _, s in sizes) if sizes else 0,
                'max_size': max(s for _, s in sizes) if sizes else 0
            }
        }
    
async def main():
    """Función principal para procesar documentos pendientes de splitting."""
    splitter = TextSplitter()
    
    # Buscar documentos que necesitan splitting
    checkpoint_files = list(CHECKPOINT_DIR.glob("*_checkpoint.json"))
    
    documents_to_process = []
    for checkpoint_file in checkpoint_files:
        checkpoint_data = load_json(checkpoint_file)
        if checkpoint_data and checkpoint_data.get("text_extracted") and not checkpoint_data.get("chunks_created"):
            doc_id = checkpoint_data["doc_id"]
            documents_to_process.append(doc_id)
    
    if not documents_to_process:
        logging.info("No se encontraron documentos pendientes de splitting.")
        return
    
    logging.info(f"Encontrados {len(documents_to_process)} documentos para procesar.")
    
    # Procesar documentos
    for doc_id in documents_to_process:
        logging.info(f"\n{'='*60}")
        logging.info(f"Procesando splitting para documento: {doc_id}")
        logging.info(f"{'='*60}")
        
        result = await splitter.process_document(doc_id)
        
        if result["success"]:
            logging.info(f"✓ Documento dividido exitosamente: {doc_id}")
            logging.info(f"  - Chunks creados: {result['chunks_count']}")
            if result.get("validation"):
                logging.info(f"  - Validación: {'Pasada' if result['validation']['valid'] else 'Con advertencias'}")
                if result['validation'].get('stats'):
                    stats = result['validation']['stats']
                    logging.info(f"  - Tamaño promedio: {stats['avg_size']:.0f} caracteres")
                    logging.info(f"  - Rango: {stats['min_size']} - {stats['max_size']} caracteres")
            logging.info(f"  - Siguiente etapa: {result.get('next_stage', 'N/A')}")
        else:
            logging.error(f"✗ Error dividiendo documento: {doc_id}")
            logging.error(f"  - Error: {result.get('error', 'Desconocido')}")
    
    logging.info("\n" + "="*60)
    logging.info("Procesamiento de text splitting completado")
    logging.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())