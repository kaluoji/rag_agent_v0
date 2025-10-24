import os
import time
import random
import asyncio
import logging
import json
from typing import Callable, Any, Optional, Dict, List
from pathlib import Path
from datetime import datetime
from hashlib import md5
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)
import re

# Importar clientes globales
from openai import AsyncOpenAI
from supabase import create_client, Client

from .config import (
    OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY,
    OPENAI_RPM_LIMIT, OPENAI_RETRY_ATTEMPTS, OPENAI_WAIT_MIN, OPENAI_WAIT_MAX,
    LOG_FORMAT, LOG_LEVEL
)

# Configurar logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)

# ---------------------------
# Inicializar clientes globales
# ---------------------------
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# ---------------------------
# Rate Limiting para OpenAI
# ---------------------------
class OpenAIRateLimiter:
    """
    Implementa un limitador de tasa para las llamadas a la API de OpenAI.
    Extrae el tiempo de espera sugerido de los mensajes de error y espera
    ese tiempo exacto antes de reintentar.
    """
    def __init__(self, rpm_limit=OPENAI_RPM_LIMIT):
        self.rpm_limit = rpm_limit
        self.request_timestamps = []
        self.lock = asyncio.Lock()
    
    async def wait_if_needed(self):
        """Espera si es necesario para no exceder el límite de RPM."""
        async with self.lock:
            now = time.time()
            # Eliminar timestamps más antiguos que 60 segundos
            self.request_timestamps = [ts for ts in self.request_timestamps if now - ts < 60]
            
            if len(self.request_timestamps) >= self.rpm_limit:
                # Calcular cuánto tiempo esperar
                oldest = min(self.request_timestamps)
                wait_time = 60 - (now - oldest) + random.uniform(0.1, 0.5)  # Añadir jitter
                logging.info(f"Limitando tasa: esperando {wait_time:.2f} segundos")
                await asyncio.sleep(wait_time)
                
                # Limpiar timestamps antiguos nuevamente después de esperar
                now = time.time()
                self.request_timestamps = [ts for ts in self.request_timestamps if now - ts < 60]
            
            # Registrar esta solicitud
            self.request_timestamps.append(now)


# Inicializar el limitador de tasa global
openai_limiter = OpenAIRateLimiter()


# Decorador para controlar tasa y reintentos
@retry(
    retry=retry_if_exception_type((TimeoutError, Exception)),
    wait=wait_exponential(multiplier=1, min=OPENAI_WAIT_MIN, max=OPENAI_WAIT_MAX),
    stop=stop_after_attempt(OPENAI_RETRY_ATTEMPTS)
)
async def rate_limited_openai_call(func: Callable, *args, **kwargs) -> Any:
    """
    Ejecuta una función de llamada a la API de OpenAI con control de tasa
    y reintentos automáticos en caso de error.
    Extrae el tiempo de espera sugerido de los mensajes de error 429.
    """
    await openai_limiter.wait_if_needed()
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        error_str = str(e)
        if "429" in error_str:
            logging.warning(f"OpenAI rate limit alcanzado: {e}")
            
            # Intentar extraer el tiempo de espera recomendado
            wait_time_match = re.search(r'Please try again in (\d+\.\d+)s', error_str)
            
            if wait_time_match:
                wait_time = float(wait_time_match.group(1))
                # Añadir un pequeño margen
                wait_time = wait_time + 0.5
                logging.info(f"Esperando {wait_time:.2f} segundos según lo recomendado por OpenAI")
                await asyncio.sleep(wait_time)
            else:
                # Si no podemos extraer el tiempo, esperamos un tiempo razonable
                await asyncio.sleep(random.uniform(2.0, 5.0))
        raise


# ---------------------------
# Utilidades de archivo
# ---------------------------
def generate_doc_id(file_path: str) -> str:
    """Genera un ID único para un documento basado en su path."""
    return md5(file_path.encode()).hexdigest()[:12]


def safe_filename(filename: str, max_length: int = 50) -> str:
    """Convierte un string en un nombre de archivo seguro."""
    # Reemplazar caracteres no válidos
    safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in filename)
    # Limitar longitud
    if len(safe) > max_length:
        safe = safe[:max_length]
    # Eliminar espacios al inicio y final
    return safe.strip()


def ensure_directory(path: Path) -> Path:
    """Asegura que un directorio existe, creándolo si es necesario."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------
# Utilidades de JSON
# ---------------------------
def save_json(data: Any, file_path: Path, indent: int = 2) -> None:
    """Guarda datos en un archivo JSON con manejo de errores."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent, default=str)
        logging.debug(f"JSON guardado en: {file_path}")
    except Exception as e:
        logging.error(f"Error al guardar JSON en {file_path}: {e}")
        raise


def load_json(file_path: Path) -> Any:
    """Carga datos desde un archivo JSON con manejo de errores."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"Archivo no encontrado: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error al decodificar JSON en {file_path}: {e}")
        raise
    except Exception as e:
        logging.error(f"Error al cargar JSON desde {file_path}: {e}")
        raise


# ---------------------------
# Utilidades de procesamiento por lotes
# ---------------------------
async def process_in_batches(
    items: List[Any],
    process_func: Callable,
    batch_size: int = 5,
    delay_between_batches: float = 1.0
) -> List[Any]:
    """
    Procesa una lista de items en lotes con un delay entre cada lote.
    
    Args:
        items: Lista de items a procesar
        process_func: Función asíncrona que procesa un item
        batch_size: Tamaño de cada lote
        delay_between_batches: Segundos de espera entre lotes
        
    Returns:
        Lista de resultados procesados
    """
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        logging.info(f"Procesando batch {i//batch_size + 1} de {(len(items) + batch_size - 1)//batch_size}")
        
        # Procesar batch en paralelo
        batch_results = await asyncio.gather(
            *[process_func(item) for item in batch],
            return_exceptions=True
        )
        
        # Manejar excepciones
        for idx, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logging.error(f"Error procesando item {i + idx}: {result}")
            else:
                results.append(result)
        
        # Delay entre batches (excepto el último)
        if i + batch_size < len(items):
            await asyncio.sleep(delay_between_batches)
    
    return results


# ---------------------------
# Utilidades de validación
# ---------------------------
def validate_text_content(text: str, min_length: int = 50) -> bool:
    """Valida que el contenido de texto sea válido."""
    if not text or not isinstance(text, str):
        return False
    
    cleaned = text.strip()
    if len(cleaned) < min_length:
        return False
    
    # Verificar que no sea solo caracteres especiales o números
    alphanumeric_ratio = sum(c.isalnum() for c in cleaned) / len(cleaned)
    if alphanumeric_ratio < 0.3:  # Menos del 30% de caracteres alfanuméricos
        return False
    
    return True


def validate_metadata(metadata: Dict[str, Any], required_fields: List[str]) -> tuple[bool, List[str]]:
    """
    Valida que los metadatos contengan los campos requeridos.
    
    Returns:
        Tupla (es_válido, lista_de_campos_faltantes)
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in metadata or metadata[field] is None or metadata[field] == "":
            missing_fields.append(field)
    
    return len(missing_fields) == 0, missing_fields


# ---------------------------
# Utilidades de limpieza de texto
# ---------------------------
def clean_headers_footers(content: str, document_title: Optional[str] = None) -> str:
    """
    Elimina encabezados y pies de página repetitivos de un texto legal.
    
    Args:
        content: El texto a limpiar
        document_title: Título opcional del documento para eliminar repeticiones
    
    Returns:
        Texto limpio sin encabezados/pies repetitivos
    """
    # Dividir en líneas para analizar
    lines = content.split('\n')
    cleaned_lines = []
    
    # Patrones comunes de encabezados/pies de página
    header_footer_patterns = [
        # Patrones de encabezados
        r'^DIARIO\s+OFICIAL',
        r'^BOLETÍN\s+OFICIAL',
        r'^GACETA\s+OFICIAL',
        r'^LEY\s+FEDERAL',
        r'^LEY\s+GENERAL',
        r'^REGLAMENTO',
        r'^CÓDIGO',
        r'^DECRETO',
        r'^NOM\-\d+',
        r'^Página\s+\d+',
        r'^\d+\s+de\s+\d+',
        r'^(?:CAPÍTULO|TÍTULO|LIBRO|PARTE|SECCIÓN)\s+[IVXLCDM0-9]+$',
        
        # Patrones de pies de página
        r'^\s*\d+\s+de\s+\d+\s*$',
        r'^\s*www\.',
        r'^\s*[Pp]ágina\s*\d+\s*$',
        r'^\s*-+\s*$',
    ]
    
    # Si tenemos título del documento, añadir como patrón
    if document_title:
        escaped_title = re.escape(document_title)
        header_footer_patterns.append(f'^{escaped_title}$')
        # Versión corta (primeras palabras)
        short_title = ' '.join(document_title.split()[:3])
        if len(short_title) > 15:
            escaped_short_title = re.escape(short_title)
            header_footer_patterns.append(f'^.*{escaped_short_title}.*$')
    
    # Patrón combinado para mayor eficiencia
    combined_pattern = '|'.join(f'({p})' for p in header_footer_patterns)
    header_footer_regex = re.compile(combined_pattern, re.IGNORECASE)
    
    # Indicador para saber si estamos al principio/fin del texto
    at_beginning = True
    consecutive_headers = 0
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Comprobar si es un encabezado/pie de página
        is_header_footer = bool(header_footer_regex.match(line_stripped))
        
        # Lógica especial para el inicio del texto
        if at_beginning:
            if not line_stripped or is_header_footer:
                consecutive_headers += 1
                continue
            else:
                at_beginning = False
                consecutive_headers = 0
        
        # Lógica para líneas intermedias
        if is_header_footer:
            # Verificar si hay líneas similares cercanas
            nearby_similar = False
            
            # Comprobar líneas anteriores
            for j in range(max(0, i-5), i):
                if lines[j].strip() == line_stripped:
                    nearby_similar = True
                    break
            
            # Comprobar líneas siguientes
            for j in range(i+1, min(len(lines), i+5)):
                if lines[j].strip() == line_stripped:
                    nearby_similar = True
                    break
            
            # Si es una línea repetida o un encabezado/pie claro, omitirla
            if nearby_similar:
                continue
        
        # Líneas en blanco: eliminar consecutivas
        if not line_stripped:
            if cleaned_lines and not cleaned_lines[-1].strip():
                continue
        
        # Si llegamos aquí, la línea se conserva
        cleaned_lines.append(line)
    
    # Eliminar líneas en blanco al final
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()
    
    # Eliminar líneas en blanco al principio
    while cleaned_lines and not cleaned_lines[0].strip():
        cleaned_lines.pop(0)
    
    return '\n'.join(cleaned_lines)


# ---------------------------
# Utilidades de backup local
# ---------------------------
async def save_failed_data(
    data: Dict[str, Any],
    error: Exception,
    prefix: str,
    directory: Path
) -> Optional[str]:
    """
    Guarda datos que fallaron al procesarse para recuperación posterior.
    
    Args:
        data: Datos a guardar
        error: Excepción que causó el fallo
        prefix: Prefijo para el nombre del archivo
        directory: Directorio donde guardar
        
    Returns:
        Path del archivo guardado o None si falla
    """
    try:
        ensure_directory(directory)
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_prefix = safe_filename(prefix)
        file_path = directory / f"{safe_prefix}_{timestamp}_failed.json"
        
        # Añadir información del error
        data_with_error = {
            **data,
            "_error": {
                "type": type(error).__name__,
                "message": str(error),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        save_json(data_with_error, file_path)
        logging.info(f"Datos fallidos guardados en: {file_path}")
        
        return str(file_path)
        
    except Exception as e:
        logging.error(f"Error al guardar datos fallidos: {e}")
        return None