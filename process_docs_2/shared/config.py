import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno
load_dotenv()

# Configuración de rutas
BASE_DIR = Path(__file__).parent.parent
UPLOADS_OCR_DIR = BASE_DIR / "uploads_ocr"
CHECKPOINT_DIR = BASE_DIR / "pipeline_checkpoints"
PENDING_DOCUMENTS_DIR = BASE_DIR / "pending_documents"
PENDING_CHUNKS_DIR = BASE_DIR / "pending_chunks"

# Crear directorios si no existen
CHECKPOINT_DIR.mkdir(exist_ok=True)
PENDING_DOCUMENTS_DIR.mkdir(exist_ok=True)
PENDING_CHUNKS_DIR.mkdir(exist_ok=True)

# Configuración de OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
LLM_MODEL_ADVANCED = os.getenv("LLM_MODEL_ADVANCED", "gpt-4")
EMBEDDING_MODEL = "text-embedding-3-small"

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Configuración de Tesseract OCR
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Configuración de procesamiento
DEFAULT_CHUNK_SIZE = 8000
MIN_CHUNK_SIZE = 200
MAX_CHUNKS = 100
OVERLAP_SIZE = 75
BATCH_SIZE = 20  # Para embeddings
PROCESS_BATCH_SIZE = 5  # Para procesamiento de chunks
ALLOW_ARTICLE_SUBDIVISION = False  # Deshabilitar subdivisión
MAX_ARTICLE_SIZE = 15000           # Solo subdividir casos extremos

# Configuración de rate limiting
OPENAI_RPM_LIMIT = 450  # Requests per minute
OPENAI_RETRY_ATTEMPTS = 5
OPENAI_WAIT_MIN = 1
OPENAI_WAIT_MAX = 60

# Configuración de workers
MAX_PROCESS_WORKERS = 5
MAX_CONCURRENT_DOCUMENTS = 2

# Logging
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

# Validación de configuración
def validate_config():
    """Valida que todas las configuraciones críticas estén presentes."""
    critical_vars = {
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": SUPABASE_SERVICE_KEY
    }
    
    missing = [var for var, value in critical_vars.items() if not value]
    if missing:
        raise ValueError(f"Variables de entorno faltantes: {', '.join(missing)}")
    
    if not Path(TESSERACT_CMD).exists():
        raise ValueError(f"Tesseract no encontrado en: {TESSERACT_CMD}")

# Validar al importar
try:
    validate_config()
except ValueError as e:
    print(f"Error de configuración: {e}")
    # No lanzar excepción para permitir importación, pero advertir
    pass