"""
Módulo 1: Extractor de Documentos
Responsable de:
1. Extraer texto de documentos (PDF, imágenes)
2. Extraer metadatos del documento usando GPT-4
3. Insertar documento en la tabla regulatory_documents
4. Guardar el texto extraído para la siguiente etapa
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import pdfplumber
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from concurrent.futures import ProcessPoolExecutor
import atexit
from datetime import datetime, timezone
from dateutil import parser
import tempfile
from markitdown import MarkItDown
import re

# Importar configuración y utilidades compartidas
from shared.config import (
    TESSERACT_CMD, UPLOADS_OCR_DIR, CHECKPOINT_DIR,
    LLM_MODEL_ADVANCED, PENDING_DOCUMENTS_DIR,
    MAX_PROCESS_WORKERS
)
from shared.utils import (
    openai_client, supabase, rate_limited_openai_call,
    generate_doc_id, save_json, load_json, ensure_directory,
    save_failed_data, clean_headers_footers
)
from shared.models import (
    DocumentMetadata, ExtractedText, ProcessingCheckpoint
)

# Configurar Tesseract
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Pool de procesos para operaciones intensivas
process_pool = ProcessPoolExecutor(max_workers=MAX_PROCESS_WORKERS)
atexit.register(lambda: process_pool.shutdown(wait=True))


class DocumentExtractor:
    """Extrae texto y metadatos de documentos normativos."""
    
    def __init__(self, checkpoint_dir: Path = CHECKPOINT_DIR):
        self.checkpoint_dir = ensure_directory(checkpoint_dir)
        self.process_pool = process_pool
    
    async def extract_document_metadata(self, file_path: str) -> DocumentMetadata:
        """
        Analiza un documento normativo y extrae sus metadatos principales usando GPT.
        
        Args:
            file_path: Ruta al archivo del documento normativo
            
        Returns:
            DocumentMetadata con los metadatos extraídos
        """
        logging.info(f"Extrayendo metadatos del documento: {file_path}")
        
        try:
            # Extraer texto solo de las primeras páginas (suficiente para metadatos)
            document_start = ""
            
            if file_path.lower().endswith('.pdf'):
                with pdfplumber.open(file_path) as pdf:
                    # Tomar las primeras 3 páginas o menos si el documento es más corto
                    pages_to_analyze = min(3, len(pdf.pages))
                    for i in range(pages_to_analyze):
                        page_text = pdf.pages[i].extract_text() or ""
                        document_start += page_text + f"\n\n--- Página {i + 1} ---\n\n"
            else:
                # Para otros tipos de archivo, extraer todo el texto
                extracted_text = await self.extract_text(file_path)
                # Limitar a los primeros 200000 caracteres aproximadamente
                document_start = extracted_text.content[:200000]
            
            # Sistema de prompts para GPT
            system_prompt = """
            Eres un asistente especializado en análisis de documentos jurídicos y normativos.
            Tu tarea es extraer la siguiente información clave de un documento normativo:
            
            1. Tipo de documento (Ley, Reglamento, Circular, Directiva, Decreto, etc.)
            2. Título completo del documento
            3. Autoridad emisora (quién emitió el documento)
            4. Fecha de publicación (en formato YYYY-MM-DD)
            5. Fecha de entrada en vigor (en formato YYYY-MM-DD)
            6. Jurisdicción (País, estado o región al que hace referencia el documento)
            7. Estado del documento (vigente, derogado, modificado, etc.)
            8. Número o identificador del documento (si no lo conoces, usa el nombre del documento)
            9. Fuente oficial (Diario Oficial, Boletín, etc.)
            
            Responde SOLO en formato JSON válido con las claves exactas:
            {
              "document_type": string,
              "document_title": string,
              "issuing_authority": string,
              "publication_date": string,
              "effective_date": string,
              "jurisdiction": string,
              "status": string,
              "document_number": string,
              "official_source": string
            }
            
            Si no puedes determinar algún valor, usa null. La información debe ser precisa.
            """
            
            async def call_api():
                return await openai_client.chat.completions.create(
                    model=os.getenv(LLM_MODEL_ADVANCED, "gpt-3.5-turbo"), # Usar GPT-4 para mejor extracción
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Analiza el documento normativo y extrae la información solicitada:\n\n{document_start}"}
                    ],
                    response_format={"type": "json_object"}
                )
            
            # Llamar a la API con control de rate limit
            response = await rate_limited_openai_call(call_api)
            metadata_dict = json.loads(response.choices[0].message.content)
            
            # Procesar fechas para asegurar formato correcto
            for date_field in ['publication_date', 'effective_date']:
                if metadata_dict.get(date_field):
                    try:
                        # Intentar parsear la fecha y convertirla a formato ISO
                        parsed_date = parser.parse(metadata_dict[date_field])
                        metadata_dict[date_field] = parsed_date.strftime('%Y-%m-%d')
                    except:
                        # Si falla, mantener el valor original
                        pass
            
            # Añadir información adicional
            metadata_dict['original_url'] = file_path
            metadata_dict['file_name'] = os.path.basename(file_path)
            metadata_dict['extraction_date'] = datetime.now(timezone.utc).isoformat()
            
            # Crear objeto DocumentMetadata
            metadata = DocumentMetadata.from_dict(metadata_dict)
            
            logging.info(f"Metadatos extraídos con éxito para: {file_path}")
            return metadata
            
        except Exception as e:
            logging.error(f"Error al extraer metadatos del documento {file_path}: {e}")
            # Devolver metadatos mínimos en caso de error
            return DocumentMetadata(
                document_type="Desconocido",
                document_title=os.path.basename(file_path),
                original_url=file_path,
                file_name=os.path.basename(file_path),
                extraction_error=str(e)
            )
    
    async def insert_document(self, metadata: DocumentMetadata) -> Optional[int]:
        """
        Inserta o actualiza un documento en la tabla regulatory_documents.
        
        Args:
            metadata: Metadatos del documento
            
        Returns:
            ID del documento insertado o None si falla
        """
        try:
            # Construir datos para inserción
            doc_data = metadata.to_db_format()
            
            # Insertar documento y obtener ID
            result = supabase.table("regulatory_documents").insert(doc_data).execute()
            
            if result.data and len(result.data) > 0:
                document_id = result.data[0]['id']
                logging.info(f"Documento insertado con ID: {document_id}")
                return document_id
            else:
                logging.error("No se pudo obtener el ID del documento insertado")
                return None
                
        except Exception as e:
            logging.error(f"Error al insertar documento en la base de datos: {e}")
            
            # Guardar datos localmente como respaldo
            await save_failed_data(
                metadata.to_dict(),
                e,
                metadata.document_title or "unknown",
                PENDING_DOCUMENTS_DIR
            )
            
            return None
    
    async def extract_text(self, file_path: str) -> ExtractedText:
        """
        Extrae el texto de un archivo de forma asíncrona.
        """
        start_time = datetime.now()
        
        if file_path.lower().endswith('.pdf'):
            content = await self._extract_text_from_pdf(file_path)
            method = "pdfplumber"
        else:
            loop = asyncio.get_running_loop()
            content = await loop.run_in_executor(
                self.process_pool, 
                self._extract_text_from_file, 
                file_path
            )
            method = "ocr"
        
        # Convertir a Markdown
        markdown_content = await self._convert_to_markdown(content)
        
        # Calcular tiempo de extracción
        extraction_time = (datetime.now() - start_time).total_seconds()
        
        # Contar páginas aproximadas
        page_count = len(re.findall(r'--- Página \d+ ---', content))
        
        return ExtractedText(
            content=markdown_content,
            page_count=page_count or 1,
            extraction_method=method,
            extraction_time=extraction_time
        )
    
    async def _extract_text_from_pdf(self, file_path: str) -> str:
        """
        Abre el PDF con pdfplumber y procesa cada página en paralelo.
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                tasks = []
                for i, page in enumerate(pdf.pages):
                    tasks.append(self._extract_text_from_page(page, i))
                texts = await asyncio.gather(*tasks)
                return "".join(texts)
        except Exception as e:
            logging.error(f"Error al extraer texto del PDF {file_path}: {e}")
            return ""
    
    async def _extract_text_from_page(self, page, page_number: int) -> str:
        """
        Extrae el texto de una única página de un PDF de forma asíncrona.
        """
        loop = asyncio.get_running_loop()
        try:
            # Extraer texto con pdfplumber
            text = page.extract_text() or ""
            
            # Si hay poco texto, realizar OCR en la imagen de la página
            if len(text.strip()) < 50:
                img = page.to_image()
                img_pil = img.original
                
                # Ejecutar OCR en el executor para no bloquear
                text = await loop.run_in_executor(
                    self.process_pool, 
                    lambda: pytesseract.image_to_string(
                        self._preprocess_image(img_pil), 
                        config="--psm 6"
                    )
                )
            
            return text + f"\n\n--- Página {page_number + 1} ---\n\n"
        except Exception as e:
            logging.error(f"Error al extraer texto de la página {page_number}: {e}")
            return ""
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """
        Extrae texto de un archivo no PDF (principalmente imágenes).
        Esta función se ejecuta en el process pool.
        """
        try:
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff')):
                img = Image.open(file_path)
                processed_img = self._preprocess_image(img)
                return pytesseract.image_to_string(processed_img, config="--psm 6")
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logging.error(f"Error al extraer texto del archivo {file_path}: {e}")
            return ""
    
    def _preprocess_image(self, pil_img: Image.Image) -> Image.Image:
        """
        Aplica preprocesamiento a la imagen: conversión a escala de grises, 
        ajuste de contraste y afilado.
        """
        pil_img = pil_img.convert('L')
        enhancer = ImageEnhance.Contrast(pil_img)
        pil_img = enhancer.enhance(2)
        pil_img = pil_img.filter(ImageFilter.SHARPEN)
        return pil_img
    
    async def _convert_to_markdown(self, text: str) -> str:
        """
        Convierte el texto extraído mediante OCR a formato Markdown
        para preservar su estructura original.
        """
        # Guardar el texto en un archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(text)
            temp_path = temp_file.name
        
        try:
            logging.info("Iniciando conversión a Markdown con MarkItDown")
            
            # Inicializar MarkItDown
            try:
                md = MarkItDown()
                logging.info("MarkItDown inicializado correctamente")
            except Exception as e:
                logging.warning(f"Error al inicializar MarkItDown: {e}")
                return self._basic_markdown_conversion(text)
            
            # Convertir el archivo a Markdown
            result = md.convert(temp_path)
            
            # Mejorar el formato del Markdown generado
            improved_content = self._post_process_markdown(result.text_content)
            logging.info("Conversión y post-procesamiento de Markdown completados")
            
            return improved_content
        
        except Exception as e:
            logging.error(f"Error en la conversión a Markdown: {e}")
            return self._basic_markdown_conversion(text)
        finally:
            # Eliminar el archivo temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def _post_process_markdown(self, content: str) -> str:
        """
        Mejora el formato del contenido Markdown, especialmente para tablas,
        y elimina elementos de paginación, cabeceras repetitivas y encabezados del documento.
        """
        lines = content.split('\n')
        output_lines = []
        in_table = False
        table_rows = []
        
        # Patrones para identificar elementos de paginación
        page_patterns = [
            re.compile(r'^\s*---\s*[Pp]ágina\s+\d+\s*---\s*'),
            re.compile(r'^\s*\d+\s+de\s+\d+\s*'),
            re.compile(r'^\s*[Pp]ágina\s+\d+\s*'),
            re.compile(r'^\s*-\s*\d+\s*-\s*')
        ]
        
        # Patrones para identificar encabezados repetitivos del documento
        header_patterns = [
            re.compile(r'^\s*LEY FEDERAL DE PROTECCIÓN DE DATOS PERSONALES EN POSESIÓN DE LOS PARTICULARES\s*$', re.IGNORECASE),
            re.compile(r'^\s*CÁMARA DE DIPUTADOS DEL H\.\s*CONGRESO DE LA UNIÓN\s*$', re.IGNORECASE),
            re.compile(r'^\s*Secretaría General\s*$', re.IGNORECASE),
            re.compile(r'^\s*Secretaría de Servicios Parlamentarios\s*$', re.IGNORECASE),
            re.compile(r'^\s*Nueva Ley DOF \d{2}-\d{2}-\d{4}\s*$', re.IGNORECASE),
            re.compile(r'^\s*\d+\s+de\s+\d+\s*$'),  # Numeración de páginas
            re.compile(r'^\s*L\s+\d+/\d+\s+ES\s+Diario Oficial de la Unión Europea\s+\d+\.\d+\.\d+\s*$', re.IGNORECASE),
            re.compile(r'^\s*L\s+\d+/\d+.*?Diario Oficial de la Unión Europea.*?\d+\.\d+\.\d+\s*$', re.IGNORECASE)
            # Agregar más patrones si identificas otros encabezados repetitivos
        ]
        
        for line in lines:
            # Comprobar si es un marcador de página
            is_page_marker = any(pattern.match(line) for pattern in page_patterns)
            
            # Comprobar si es un encabezado repetitivo del documento
            is_header = any(pattern.match(line) for pattern in header_patterns)
            
            if is_page_marker or is_header:
                continue
            
            # Procesar tablas
            if '|' in line and line.count('|') >= 2:
                if not in_table:
                    in_table = True
                    table_rows = [line]
                else:
                    table_rows.append(line)
            else:
                if in_table:
                    processed_table = self._format_table(table_rows)
                    output_lines.extend(processed_table)
                    in_table = False
                    table_rows = []
                
                output_lines.append(line)
        
        # Si quedó una tabla al final
        if in_table:
            processed_table = self._format_table(table_rows)
            output_lines.extend(processed_table)
        
        return '\n'.join(output_lines)
    
    def _format_table(self, table_rows: List[str]) -> List[str]:
        """Formatea correctamente una tabla Markdown."""
        if not table_rows:
            return []
        
        # Limpiar espacios y formatear filas
        cleaned_rows = []
        for row in table_rows:
            cleaned_row = re.sub(r'\s*\|\s*', ' | ', row.strip())
            if not cleaned_row.startswith('| '):
                cleaned_row = '| ' + cleaned_row
            if not cleaned_row.endswith(' |'):
                cleaned_row = cleaned_row + ' |'
            cleaned_rows.append(cleaned_row)
        
        if len(cleaned_rows) < 2:
            header = cleaned_rows[0]
            separator = '| ' + ' | '.join(['---' for _ in range(header.count('|')-1)]) + ' |'
            return [header, separator]
        
        return cleaned_rows
    
    def _basic_markdown_conversion(self, text: str) -> str:
        """Método de respaldo para convertir a markdown."""
        lines = text.split('\n')
        markdown_lines = []
        
        for line in lines:
            line = line.rstrip()
            
            # Detectar encabezados
            if line.isupper() and len(line) < 60 and line.strip():
                markdown_lines.append(f'\n## {line.strip()}\n')
            else:
                markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)
    
    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Procesa un documento completo: extrae metadatos, texto y guarda checkpoint.
        
        Returns:
            Diccionario con información del procesamiento
        """
        doc_id = generate_doc_id(file_path)
        
        # Cargar o crear checkpoint
        checkpoint_file = self.checkpoint_dir / f"{doc_id}_checkpoint.json"
        if checkpoint_file.exists():
            checkpoint_data = load_json(checkpoint_file)
            checkpoint = ProcessingCheckpoint.from_dict(checkpoint_data)
        else:
            checkpoint = ProcessingCheckpoint(doc_id=doc_id, file_path=file_path)
        
        try:
            # Etapa 1: Extraer metadatos
            if not checkpoint.metadata_extracted:
                logging.info(f"Extrayendo metadatos de: {file_path}")
                metadata = await self.extract_document_metadata(file_path)
                checkpoint.metadata = metadata.to_dict()
                checkpoint.metadata_extracted = True
                save_json(checkpoint.to_dict(), checkpoint_file)
            
            # Etapa 2: Insertar documento en BD
            if checkpoint.metadata_extracted and not checkpoint.document_id_db:
                logging.info(f"Insertando documento en base de datos")
                metadata = DocumentMetadata.from_dict(checkpoint.metadata)
                document_id = await self.insert_document(metadata)
                
                if document_id:
                    checkpoint.document_id_db = document_id
                    save_json(checkpoint.to_dict(), checkpoint_file)
                else:
                    logging.warning("No se pudo insertar el documento en BD")
            
            # Etapa 3: Extraer texto
            if not checkpoint.text_extracted:
                logging.info(f"Extrayendo texto de: {file_path}")
                extracted_text = await self.extract_text(file_path)
                
                # Guardar texto extraído
                text_file = self.checkpoint_dir / f"{doc_id}_text.txt"
                text_file.write_text(extracted_text.content, encoding='utf-8')
                
                # Guardar información de extracción
                extraction_info_file = self.checkpoint_dir / f"{doc_id}_extraction_info.json"
                save_json(extracted_text.to_dict(), extraction_info_file)
                
                checkpoint.text_file = str(text_file)
                checkpoint.text_extracted = True
                save_json(checkpoint.to_dict(), checkpoint_file)
            
            logging.info(f"Documento procesado completamente: {file_path}")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "checkpoint": checkpoint.to_dict(),
                "next_stage": "02_text_splitter"
            }
            
        except Exception as e:
            logging.error(f"Error procesando documento {file_path}: {e}")
            checkpoint.error = str(e)
            checkpoint.failed_at = datetime.now(timezone.utc).isoformat()
            save_json(checkpoint.to_dict(), checkpoint_file)
            
            return {
                "success": False,
                "doc_id": doc_id,
                "error": str(e),
                "checkpoint": checkpoint.to_dict()
            }


async def main():
    """Función principal para procesar documentos desde uploads_ocr."""
    extractor = DocumentExtractor()
    
    # Obtener archivos para procesar
    file_paths = []
    if UPLOADS_OCR_DIR.exists():
        file_paths = [
            str(UPLOADS_OCR_DIR / f)
            for f in os.listdir(UPLOADS_OCR_DIR)
            if f.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.tiff'))
        ]
    
    if not file_paths:
        logging.info("No se encontraron documentos para procesar.")
        return
    
    logging.info(f"Encontrados {len(file_paths)} documentos para procesar.")
    
    # Procesar documentos secuencialmente para esta etapa
    for file_path in file_paths:
        logging.info(f"\n{'='*60}")
        logging.info(f"Procesando: {file_path}")
        logging.info(f"{'='*60}")
        
        result = await extractor.process_document(file_path)
        
        if result["success"]:
            logging.info(f"✓ Documento procesado exitosamente: {file_path}")
            logging.info(f"  - Doc ID: {result['doc_id']}")
            logging.info(f"  - Siguiente etapa: {result['next_stage']}")
        else:
            logging.error(f"✗ Error procesando documento: {file_path}")
            logging.error(f"  - Error: {result['error']}")
    
    logging.info("\n" + "="*60)
    logging.info("Procesamiento de documentos completado")
    logging.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())