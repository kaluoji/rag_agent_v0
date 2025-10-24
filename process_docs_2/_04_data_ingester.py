"""
Módulo 4: Data Ingester
Responsable de:
1. Cargar los chunks procesados de la etapa anterior
2. Insertar los chunks en la tabla 'pd_peru' de Supabase
3. Manejar errores y guardar localmente los chunks que fallen
4. Actualizar el checkpoint como completado
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timezone

# Importar configuración y utilidades compartidas
from shared.config import (
    CHECKPOINT_DIR, PENDING_CHUNKS_DIR, PROCESS_BATCH_SIZE
)
from shared.utils import (
    supabase, save_json, load_json, ensure_directory,
    save_failed_data
)
from shared.models import (
    ProcessingCheckpoint, ProcessedChunk
)


class DataIngester:
    """Ingesta chunks procesados en la base de datos Supabase."""
    
    def __init__(self, checkpoint_dir: Path = CHECKPOINT_DIR):
        self.checkpoint_dir = ensure_directory(checkpoint_dir)
        self.pending_chunks_dir = ensure_directory(PENDING_CHUNKS_DIR)
        self.batch_size = PROCESS_BATCH_SIZE
    
    async def process_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Ingesta todos los chunks procesados de un documento en Supabase.
        
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
        if not checkpoint.chunks_processed or not checkpoint.processed_file:
            return {
                "success": False,
                "error": "Los chunks no han sido procesados aún"
            }
        
        # Si ya se ingirieron los datos, no reprocesar
        if checkpoint.ingested:
            logging.info(f"Datos ya ingeridos para documento {doc_id}")
            return {
                "success": True,
                "doc_id": doc_id,
                "already_ingested": True
            }
        
        try:
            # Cargar chunks procesados
            processed_file = Path(checkpoint.processed_file)
            if not processed_file.exists():
                raise FileNotFoundError(f"Archivo de chunks procesados no encontrado: {processed_file}")
            
            processed_chunks_data = load_json(processed_file)
            
            # Convertir a objetos ProcessedChunk
            processed_chunks = [
                ProcessedChunk.from_dict(chunk_data) 
                for chunk_data in processed_chunks_data
            ]
            
            logging.info(f"Insertando {len(processed_chunks)} chunks en la base de datos para documento {doc_id}")
            
            # Insertar chunks en batches
            successful_inserts = 0
            failed_chunks = []
            
            for i in range(0, len(processed_chunks), self.batch_size):
                batch = processed_chunks[i:i+self.batch_size]
                
                logging.info(f"Insertando batch {i//self.batch_size + 1} de {(len(processed_chunks) + self.batch_size - 1)//self.batch_size}")
                
                # Insertar cada chunk del batch
                for chunk in batch:
                    result = await self._insert_chunk(chunk)
                    if result["success"]:
                        successful_inserts += 1
                    else:
                        failed_chunks.append({
                            "chunk": chunk.to_dict(),
                            "error": result.get("error", "Unknown error")
                        })
                
                # Pausa entre batches para evitar sobrecargar la BD
                if i + self.batch_size < len(processed_chunks):
                    await asyncio.sleep(1)
            
            # Guardar chunks fallidos si los hay
            if failed_chunks:
                await self._save_failed_chunks(doc_id, failed_chunks)
                logging.warning(f"Se guardaron {len(failed_chunks)} chunks fallidos para procesamiento posterior")
            
            # Actualizar checkpoint
            checkpoint.ingested = successful_inserts == len(processed_chunks)
            checkpoint.completed_at = datetime.now(timezone.utc).isoformat()
            save_json(checkpoint.to_dict(), checkpoint_file)
            
            logging.info(f"Ingesta completada: {successful_inserts}/{len(processed_chunks)} chunks insertados exitosamente")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "total_chunks": len(processed_chunks),
                "successful_inserts": successful_inserts,
                "failed_chunks": len(failed_chunks),
                "complete": successful_inserts == len(processed_chunks)
            }
            
        except Exception as e:
            logging.error(f"Error durante la ingesta del documento {doc_id}: {e}")
            
            # Actualizar checkpoint con error
            checkpoint.error = str(e)
            checkpoint.failed_at = datetime.now(timezone.utc).isoformat()
            save_json(checkpoint.to_dict(), checkpoint_file)
            
            return {
                "success": False,
                "doc_id": doc_id,
                "error": str(e)
            }
    
    async def _insert_chunk(self, chunk: ProcessedChunk) -> Dict[str, Any]:
        """
        Inserta un chunk en la tabla 'pd_peru' de Supabase.
        
        Args:
            chunk: Chunk procesado a insertar
            
        Returns:
            Diccionario con resultado de la inserción
        """
        try:
            # Preparar datos para inserción
            data = {
                "url": chunk.url,
                "chunk_number": chunk.chunk_number,
                "title": chunk.title,
                "summary": chunk.summary,
                "content": chunk.content,
                "metadata": chunk.metadata,
                "embedding": chunk.embedding,
                "document_id": chunk.document_id
            }
            
            # Insertar en Supabase
            result = supabase.table("pd_peru").insert(data).execute()
            
            logging.debug(f"Insertado chunk {chunk.chunk_number} para {chunk.url}")
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            logging.error(f"Error al insertar chunk {chunk.chunk_number}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _save_failed_chunks(self, doc_id: str, failed_chunks: List[Dict[str, Any]]) -> None:
        """
        Guarda los chunks que fallaron al insertarse para procesamiento posterior.
        
        Args:
            doc_id: ID del documento
            failed_chunks: Lista de chunks fallidos con sus errores
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_path = self.pending_chunks_dir / f"{doc_id}_failed_{timestamp}.json"
            
            failed_data = {
                "doc_id": doc_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_failed": len(failed_chunks),
                "chunks": failed_chunks
            }
            
            save_json(failed_data, file_path)
            logging.info(f"Chunks fallidos guardados en: {file_path}")
            
        except Exception as e:
            logging.error(f"Error al guardar chunks fallidos: {e}")
    
    async def retry_failed_chunks(self, failed_file_path: Path) -> Dict[str, Any]:
        """
        Reintenta insertar chunks que fallaron previamente.
        
        Args:
            failed_file_path: Path al archivo con chunks fallidos
            
        Returns:
            Diccionario con resultados del reintento
        """
        try:
            failed_data = load_json(failed_file_path)
            if not failed_data:
                return {
                    "success": False,
                    "error": "No se pudo cargar el archivo de chunks fallidos"
                }
            
            chunks_data = failed_data.get("chunks", [])
            successful_retries = 0
            still_failing = []
            
            logging.info(f"Reintentando {len(chunks_data)} chunks fallidos")
            
            for chunk_info in chunks_data:
                chunk_dict = chunk_info["chunk"]
                chunk = ProcessedChunk.from_dict(chunk_dict)
                
                result = await self._insert_chunk(chunk)
                if result["success"]:
                    successful_retries += 1
                else:
                    still_failing.append({
                        "chunk": chunk_dict,
                        "error": result.get("error", "Unknown error"),
                        "retry_count": chunk_info.get("retry_count", 0) + 1
                    })
            
            # Si aún hay chunks fallando, actualizar el archivo
            if still_failing:
                failed_data["chunks"] = still_failing
                failed_data["retry_timestamp"] = datetime.now(timezone.utc).isoformat()
                failed_data["total_failed"] = len(still_failing)
                save_json(failed_data, failed_file_path)
            else:
                # Si todos se insertaron exitosamente, eliminar el archivo
                failed_file_path.unlink()
                logging.info(f"Todos los chunks se insertaron exitosamente. Archivo eliminado: {failed_file_path}")
            
            return {
                "success": True,
                "total_chunks": len(chunks_data),
                "successful_retries": successful_retries,
                "still_failing": len(still_failing)
            }
            
        except Exception as e:
            logging.error(f"Error durante el reintento: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_ingestion_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado general de la ingesta de todos los documentos.
        
        Returns:
            Diccionario con estadísticas de ingesta
        """
        checkpoint_files = list(self.checkpoint_dir.glob("*_checkpoint.json"))
        
        status = {
            "total_documents": len(checkpoint_files),
            "completed": 0,
            "partial": 0,
            "pending": 0,
            "failed": 0,
            "details": []
        }
        
        for checkpoint_file in checkpoint_files:
            checkpoint_data = load_json(checkpoint_file)
            if not checkpoint_data:
                continue
            
            doc_id = checkpoint_data.get("doc_id", "unknown")
            
            if checkpoint_data.get("ingested"):
                status["completed"] += 1
                stage = "completed"
            elif checkpoint_data.get("error"):
                status["failed"] += 1
                stage = "failed"
            elif checkpoint_data.get("chunks_processed"):
                status["pending"] += 1
                stage = "pending_ingestion"
            else:
                stage = "in_progress"
            
            status["details"].append({
                "doc_id": doc_id,
                "stage": stage,
                "chunks_count": checkpoint_data.get("chunks_count", 0),
                "document_title": checkpoint_data.get("metadata", {}).get("document_title", "Unknown")
            })
        
        # Verificar chunks fallidos pendientes
        failed_files = list(self.pending_chunks_dir.glob("*_failed_*.json"))
        status["pending_failed_chunks"] = len(failed_files)
        
        return status


async def main():
    """Función principal para ingerir documentos procesados."""
    ingester = DataIngester()
    
    # Buscar documentos que necesitan ingesta
    checkpoint_files = list(CHECKPOINT_DIR.glob("*_checkpoint.json"))
    
    documents_to_ingest = []
    for checkpoint_file in checkpoint_files:
        checkpoint_data = load_json(checkpoint_file)
        if (checkpoint_data and 
            checkpoint_data.get("chunks_processed") and 
            not checkpoint_data.get("ingested")):
            doc_id = checkpoint_data["doc_id"]
            documents_to_ingest.append(doc_id)
    
    if not documents_to_ingest:
        logging.info("No se encontraron documentos pendientes de ingesta.")
    else:
        logging.info(f"Encontrados {len(documents_to_ingest)} documentos para ingerir.")
        
        # Procesar documentos
        for doc_id in documents_to_ingest:
            logging.info(f"\n{'='*60}")
            logging.info(f"Ingiriendo datos para documento: {doc_id}")
            logging.info(f"{'='*60}")
            
            result = await ingester.process_document(doc_id)
            
            if result["success"]:
                logging.info(f"✓ Ingesta completada para: {doc_id}")
                logging.info(f"  - Chunks insertados: {result.get('successful_inserts', 0)}/{result.get('total_chunks', 0)}")
                if result.get('failed_chunks', 0) > 0:
                    logging.warning(f"  - Chunks fallidos: {result['failed_chunks']}")
            else:
                logging.error(f"✗ Error en ingesta: {doc_id}")
                logging.error(f"  - Error: {result.get('error', 'Desconocido')}")
    
    # Verificar si hay chunks fallidos para reintentar
    failed_files = list(PENDING_CHUNKS_DIR.glob("*_failed_*.json"))
    if failed_files:
        logging.info(f"\n{'='*60}")
        logging.info(f"Encontrados {len(failed_files)} archivos con chunks fallidos")
        logging.info(f"{'='*60}")
        
        for failed_file in failed_files:
            logging.info(f"\nReintentando chunks de: {failed_file.name}")
            retry_result = await ingester.retry_failed_chunks(failed_file)
            
            if retry_result["success"]:
                logging.info(f"  - Reintentos exitosos: {retry_result.get('successful_retries', 0)}/{retry_result.get('total_chunks', 0)}")
                if retry_result.get('still_failing', 0) > 0:
                    logging.warning(f"  - Aún fallando: {retry_result['still_failing']}")
    
    # Mostrar estado general
    logging.info(f"\n{'='*60}")
    logging.info("ESTADO GENERAL DE INGESTA")
    logging.info(f"{'='*60}")
    
    status = await ingester.get_ingestion_status()
    logging.info(f"Total de documentos: {status['total_documents']}")
    logging.info(f"  - Completados: {status['completed']}")
    logging.info(f"  - Pendientes: {status['pending']}")
    logging.info(f"  - Fallidos: {status['failed']}")
    logging.info(f"  - Archivos con chunks fallidos: {status['pending_failed_chunks']}")
    
    logging.info("\n" + "="*60)
    logging.info("Proceso de ingesta finalizado")
    logging.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())