"""
Orchestrator: Coordinador del Pipeline de Procesamiento de Documentos
Coordina la ejecución de todas las etapas del pipeline:
1. Document Extractor - Extracción de texto y metadatos
2. Text Splitter - División semántica del texto
3. Chunk Processor - Generación de embeddings y enriquecimiento
4. Data Ingester - Inserción en base de datos
"""

import os
import sys
import asyncio
import logging
import argparse
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json

# Añadir el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos del pipeline
from _01_document_extractor import DocumentExtractor
from _02_text_splitter import TextSplitter
from _03_chunk_processor import ChunkProcessor
from _04_data_ingester import DataIngester

# Importar configuración y utilidades
from shared.config import (
    CHECKPOINT_DIR, UPLOADS_OCR_DIR, MAX_CONCURRENT_DOCUMENTS,
    LOG_FORMAT
)
from shared.utils import (
    load_json, save_json, ensure_directory
)
from shared.models import ProcessingCheckpoint


class PipelineOrchestrator:
    """Orquesta la ejecución del pipeline completo de procesamiento."""
    
    def __init__(self, checkpoint_dir: Path = CHECKPOINT_DIR):
        self.checkpoint_dir = ensure_directory(checkpoint_dir)
        self.extractor = DocumentExtractor(checkpoint_dir)
        self.splitter = TextSplitter(checkpoint_dir)
        self.processor = ChunkProcessor(checkpoint_dir)
        self.ingester = DataIngester(checkpoint_dir)
        
        # Configurar logging
        self.setup_logging()
    
    def setup_logging(self):
        """Configura el sistema de logging."""
        log_dir = Path("logs")
        ensure_directory(log_dir)
        
        # Crear archivo de log con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"pipeline_{timestamp}.log"
        
        # Configurar handlers
        file_handler = logging.FileHandler(log_file)
        console_handler = logging.StreamHandler()
        
        # Configurar formato
        formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Configurar logger raíz
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        logging.info(f"Logging configurado. Archivo de log: {log_file}")
    
    async def process_document_pipeline(self, file_path: str) -> Dict[str, Any]:
        """
        Procesa un documento a través de todo el pipeline.
        
        Args:
            file_path: Ruta al archivo del documento
            
        Returns:
            Diccionario con el resultado del procesamiento
        """
        start_time = datetime.now()
        doc_id = None
        current_stage = "initialization"
        
        try:
            logging.info(f"\n{'='*80}")
            logging.info(f"INICIANDO PIPELINE PARA: {file_path}")
            logging.info(f"{'='*80}")
            
            # Etapa 1: Extracción de documento
            current_stage = "document_extraction"
            logging.info(f"\n[1/4] Extrayendo texto y metadatos...")
            extraction_result = await self.extractor.process_document(file_path)
            
            if not extraction_result["success"]:
                raise Exception(f"Fallo en extracción: {extraction_result.get('error')}")
            
            doc_id = extraction_result["doc_id"]
            logging.info(f"✓ Extracción completada - Doc ID: {doc_id}")
            
            # Etapa 2: Text Splitting
            current_stage = "text_splitting"
            logging.info(f"\n[2/4] Dividiendo texto en chunks...")
            splitting_result = await self.splitter.process_document(doc_id)
            
            if not splitting_result["success"]:
                raise Exception(f"Fallo en splitting: {splitting_result.get('error')}")
            
            chunks_count = splitting_result.get("chunks_count", 0)
            logging.info(f"✓ Splitting completado - {chunks_count} chunks creados")
            
            # Etapa 3: Procesamiento de chunks
            current_stage = "chunk_processing"
            logging.info(f"\n[3/4] Procesando chunks (embeddings, metadatos)...")
            processing_result = await self.processor.process_document(doc_id)
            
            if not processing_result["success"]:
                raise Exception(f"Fallo en procesamiento: {processing_result.get('error')}")
            
            logging.info(f"✓ Procesamiento completado - {processing_result.get('chunks_processed', 0)} chunks procesados")
            
            # Etapa 4: Ingesta de datos
            current_stage = "data_ingestion"
            logging.info(f"\n[4/4] Insertando en base de datos...")
            ingestion_result = await self.ingester.process_document(doc_id)
            
            if not ingestion_result["success"]:
                raise Exception(f"Fallo en ingesta: {ingestion_result.get('error')}")
            
            successful_inserts = ingestion_result.get("successful_inserts", 0)
            failed_chunks = ingestion_result.get("failed_chunks", 0)
            
            logging.info(f"✓ Ingesta completada - {successful_inserts} chunks insertados")
            if failed_chunks > 0:
                logging.warning(f"  ⚠ {failed_chunks} chunks fallaron y se guardaron para reintento")
            
            # Calcular tiempo total
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            # Resultado exitoso
            result = {
                "success": True,
                "file_path": file_path,
                "doc_id": doc_id,
                "elapsed_time": elapsed_time,
                "stages_completed": 4,
                "chunks_created": chunks_count,
                "chunks_inserted": successful_inserts,
                "chunks_failed": failed_chunks
            }
            
            logging.info(f"\n{'='*80}")
            logging.info(f"✓ PIPELINE COMPLETADO EXITOSAMENTE")
            logging.info(f"  Tiempo total: {elapsed_time:.2f} segundos")
            logging.info(f"  Chunks procesados: {successful_inserts}/{chunks_count}")
            logging.info(f"{'='*80}\n")
            
            return result
            
        except Exception as e:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            logging.error(f"\n{'='*80}")
            logging.error(f"✗ ERROR EN PIPELINE")
            logging.error(f"  Archivo: {file_path}")
            logging.error(f"  Etapa: {current_stage}")
            logging.error(f"  Error: {str(e)}")
            logging.error(f"  Tiempo transcurrido: {elapsed_time:.2f} segundos")
            logging.error(f"{'='*80}\n")
            
            return {
                "success": False,
                "file_path": file_path,
                "doc_id": doc_id,
                "error": str(e),
                "failed_stage": current_stage,
                "elapsed_time": elapsed_time
            }
    
    async def process_multiple_documents(
        self, 
        file_paths: List[str], 
        max_concurrent: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Procesa múltiples documentos con concurrencia limitada.
        
        Args:
            file_paths: Lista de rutas de archivos
            max_concurrent: Número máximo de documentos procesados en paralelo
            
        Returns:
            Diccionario con resumen del procesamiento
        """
        if max_concurrent is None:
            max_concurrent = MAX_CONCURRENT_DOCUMENTS
        
        start_time = datetime.now()
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(file_path: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.process_document_pipeline(file_path)
        
        # Procesar todos los documentos
        results = await asyncio.gather(
            *[process_with_semaphore(fp) for fp in file_paths],
            return_exceptions=True
        )
        
        # Analizar resultados
        successful = []
        failed = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed.append({
                    "file_path": file_paths[i],
                    "error": str(result)
                })
            elif isinstance(result, dict):
                if result.get("success"):
                    successful.append(result)
                else:
                    failed.append(result)
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        # Resumen
        summary = {
            "total_documents": len(file_paths),
            "successful": len(successful),
            "failed": len(failed),
            "total_time": total_time,
            "average_time": total_time / len(file_paths) if file_paths else 0,
            "successful_documents": successful,
            "failed_documents": failed
        }
        
        # Logging del resumen
        logging.info(f"\n{'='*80}")
        logging.info("RESUMEN DEL PROCESAMIENTO")
        logging.info(f"{'='*80}")
        logging.info(f"Total de documentos: {summary['total_documents']}")
        logging.info(f"Exitosos: {summary['successful']}")
        logging.info(f"Fallidos: {summary['failed']}")
        logging.info(f"Tiempo total: {summary['total_time']:.2f} segundos")
        logging.info(f"Tiempo promedio: {summary['average_time']:.2f} segundos/documento")
        
        if failed:
            logging.warning("\nDocumentos fallidos:")
            for doc in failed:
                logging.warning(f"  - {doc.get('file_path', 'Unknown')}: {doc.get('error', 'Unknown error')}")
        
        logging.info(f"{'='*80}\n")
        
        return summary
    
    async def resume_incomplete_pipelines(self) -> Dict[str, Any]:
        """
        Busca y resume pipelines incompletos desde sus checkpoints.
        
        Returns:
            Diccionario con resultados de la reanudación
        """
        logging.info(f"\n{'='*80}")
        logging.info("BUSCANDO PIPELINES INCOMPLETOS")
        logging.info(f"{'='*80}")
        
        checkpoint_files = list(self.checkpoint_dir.glob("*_checkpoint.json"))
        incomplete_pipelines = []
        
        for checkpoint_file in checkpoint_files:
            checkpoint_data = load_json(checkpoint_file)
            if checkpoint_data and not checkpoint_data.get("ingested") and not checkpoint_data.get("error"):
                checkpoint = ProcessingCheckpoint.from_dict(checkpoint_data)
                current_stage = checkpoint.get_current_stage()
                
                if current_stage != "completed":
                    incomplete_pipelines.append({
                        "doc_id": checkpoint.doc_id,
                        "file_path": checkpoint.file_path,
                        "current_stage": current_stage,
                        "checkpoint": checkpoint
                    })
        
        if not incomplete_pipelines:
            logging.info("No se encontraron pipelines incompletos")
            return {"resumed": 0, "completed": 0, "failed": 0}
        
        logging.info(f"Encontrados {len(incomplete_pipelines)} pipelines incompletos")
        
        completed = 0
        failed = 0
        
        for pipeline in incomplete_pipelines:
            doc_id = pipeline["doc_id"]
            stage = pipeline["current_stage"]
            
            logging.info(f"\nReanudando pipeline para {doc_id} desde etapa: {stage}")
            
            try:
                # Ejecutar etapas pendientes según el estado actual
                if stage == "metadata_extracted" or stage == "text_extracted":
                    # Continuar desde text splitting
                    await self.splitter.process_document(doc_id)
                    await self.processor.process_document(doc_id)
                    await self.ingester.process_document(doc_id)
                    
                elif stage == "chunks_created":
                    # Continuar desde procesamiento
                    await self.processor.process_document(doc_id)
                    await self.ingester.process_document(doc_id)
                    
                elif stage == "chunks_processed":
                    # Solo falta ingesta
                    await self.ingester.process_document(doc_id)
                
                completed += 1
                logging.info(f"✓ Pipeline completado para {doc_id}")
                
            except Exception as e:
                failed += 1
                logging.error(f"✗ Error reanudando pipeline para {doc_id}: {e}")
        
        return {
            "resumed": len(incomplete_pipelines),
            "completed": completed,
            "failed": failed
        }
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual de todos los documentos en el pipeline.
        
        Returns:
            Diccionario con estadísticas detalladas
        """
        checkpoint_files = list(self.checkpoint_dir.glob("*_checkpoint.json"))
        
        status = {
            "total_documents": len(checkpoint_files),
            "by_stage": {
                "not_started": 0,
                "metadata_extracted": 0,
                "text_extracted": 0,
                "chunks_created": 0,
                "chunks_processed": 0,
                "completed": 0,
                "failed": 0
            },
            "documents": []
        }
        
        for checkpoint_file in checkpoint_files:
            checkpoint_data = load_json(checkpoint_file)
            if not checkpoint_data:
                continue
            
            checkpoint = ProcessingCheckpoint.from_dict(checkpoint_data)
            stage = checkpoint.get_current_stage()
            
            status["by_stage"][stage] = status["by_stage"].get(stage, 0) + 1
            
            doc_info = {
                "doc_id": checkpoint.doc_id,
                "file_path": checkpoint.file_path,
                "stage": stage,
                "progress": checkpoint.get_progress_percentage(),
                "chunks_count": checkpoint.chunks_count,
                "document_title": checkpoint.metadata.get("document_title") if checkpoint.metadata else "Unknown"
            }
            
            if checkpoint.error:
                doc_info["error"] = checkpoint.error
            
            status["documents"].append(doc_info)
        
        return status
    
    def generate_status_report(self, output_file: Optional[str] = None) -> None:
        """
        Genera un reporte detallado del estado del pipeline.
        
        Args:
            output_file: Archivo donde guardar el reporte (opcional)
        """
        status = self.get_pipeline_status()
        
        # Crear reporte
        report_lines = [
            "=" * 80,
            "REPORTE DE ESTADO DEL PIPELINE",
            "=" * 80,
            f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total de documentos: {status['total_documents']}",
            "",
            "DISTRIBUCIÓN POR ETAPA:",
            "-" * 40
        ]
        
        for stage, count in status["by_stage"].items():
            if count > 0:
                percentage = (count / status["total_documents"]) * 100
                report_lines.append(f"{stage:20} {count:5d} ({percentage:5.1f}%)")
        
        report_lines.extend([
            "",
            "DOCUMENTOS EN PROGRESO:",
            "-" * 40
        ])
        
        in_progress = [d for d in status["documents"] if d["stage"] not in ["completed", "failed"]]
        for doc in sorted(in_progress, key=lambda x: x["progress"], reverse=True):
            report_lines.append(
                f"{doc['doc_id']} - {doc['document_title'][:40]:40} "
                f"[{doc['stage']:20}] {doc['progress']:5.1f}%"
            )
        
        # Documentos fallidos
        failed = [d for d in status["documents"] if d["stage"] == "failed"]
        if failed:
            report_lines.extend([
                "",
                "DOCUMENTOS FALLIDOS:",
                "-" * 40
            ])
            for doc in failed:
                report_lines.append(f"{doc['doc_id']} - {doc.get('error', 'Unknown error')}")
        
        report_lines.append("=" * 80)
        
        # Imprimir reporte
        report = "\n".join(report_lines)
        print(report)
        
        # Guardar si se especificó archivo
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\nReporte guardado en: {output_file}")


async def main():
    """Función principal con interfaz de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Orchestrator del Pipeline de Procesamiento de Documentos"
    )
    
    parser.add_argument(
        "command",
        choices=["process", "resume", "status", "retry-failed"],
        help="Comando a ejecutar"
    )
    
    parser.add_argument(
        "--files",
        nargs="+",
        help="Archivos a procesar (para comando 'process')"
    )
    
    parser.add_argument(
        "--folder",
        default=str(UPLOADS_OCR_DIR),
        help="Carpeta con archivos a procesar"
    )
    
    parser.add_argument(
        "--concurrent",
        type=int,
        default=MAX_CONCURRENT_DOCUMENTS,
        help="Número máximo de documentos a procesar en paralelo"
    )
    
    parser.add_argument(
        "--report",
        help="Archivo donde guardar el reporte de estado"
    )
    
    args = parser.parse_args()
    
    # Crear orchestrator
    orchestrator = PipelineOrchestrator()
    
    if args.command == "process":
        # Obtener archivos a procesar
        if args.files:
            file_paths = args.files
        else:
            # Buscar en carpeta
            folder = Path(args.folder)
            if not folder.exists():
                print(f"Error: La carpeta {folder} no existe")
                return
            
            file_paths = [
                str(folder / f)
                for f in os.listdir(folder)
                if f.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.tiff'))
            ]
        
        if not file_paths:
            print("No se encontraron archivos para procesar")
            return
        
        print(f"Procesando {len(file_paths)} archivos...")
        
        # Procesar documentos
        if len(file_paths) == 1:
            # Un solo documento
            result = await orchestrator.process_document_pipeline(file_paths[0])
        else:
            # Múltiples documentos
            result = await orchestrator.process_multiple_documents(
                file_paths,
                max_concurrent=args.concurrent
            )
    
    elif args.command == "resume":
        # Reanudar pipelines incompletos
        result = await orchestrator.resume_incomplete_pipelines()
        print(f"\nPipelines reanudados: {result['resumed']}")
        print(f"Completados exitosamente: {result['completed']}")
        print(f"Fallidos: {result['failed']}")
    
    elif args.command == "status":
        # Generar reporte de estado
        orchestrator.generate_status_report(args.report)
    
    elif args.command == "retry-failed":
        # Reintentar chunks fallidos
        ingester = DataIngester()
        failed_files = list(PENDING_CHUNKS_DIR.glob("*_failed_*.json"))
        
        if not failed_files:
            print("No se encontraron chunks fallidos para reintentar")
            return
        
        print(f"Reintentando {len(failed_files)} archivos con chunks fallidos...")
        
        for failed_file in failed_files:
            print(f"\nReintentando: {failed_file.name}")
            result = await ingester.retry_failed_chunks(failed_file)
            if result["success"]:
                print(f"  Exitosos: {result['successful_retries']}/{result['total_chunks']}")
                if result['still_failing'] > 0:
                    print(f"  Aún fallando: {result['still_failing']}")


if __name__ == "__main__":
    asyncio.run(main())