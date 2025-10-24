from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json

@dataclass
class ProcessedChunk:
    """Representa un chunk procesado listo para insertar en la base de datos."""
    url: str
    chunk_number: int
    title: str
    summary: str
    content: str
    metadata: Dict[str, Any]
    embedding: List[float]
    document_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el chunk a diccionario para serialización."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessedChunk':
        """Crea una instancia desde un diccionario."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Serializa el chunk a JSON."""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ProcessedChunk':
        """Deserializa desde JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class DocumentMetadata:
    """Metadatos extraídos de un documento normativo."""
    document_type: Optional[str] = None
    document_title: Optional[str] = None
    issuing_authority: Optional[str] = None
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    jurisdiction: Optional[str] = None
    status: Optional[str] = None
    document_number: Optional[str] = None
    official_source: Optional[str] = None
    original_url: Optional[str] = None
    file_name: Optional[str] = None
    extraction_date: Optional[str] = None
    extraction_error: Optional[str] = None
    
    def __post_init__(self):
        """Validación y procesamiento post-inicialización."""
        if not self.extraction_date:
            self.extraction_date = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario, excluyendo valores None."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentMetadata':
        """Crea una instancia desde un diccionario."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
    
    def to_db_format(self) -> Dict[str, Any]:
        """Formatea los datos para inserción en la base de datos."""
        db_data = {
            "document_type": self.document_type or "Desconocido",
            "document_title": self.document_title or "Sin título",
            "issuing_authority": self.issuing_authority,
            "publication_date": self.publication_date,
            "effective_date": self.effective_date,
            "jurisdiction": self.jurisdiction,
            "status": self.status,
            "document_number": self.document_number,
            "official_source": self.official_source,
            "original_url": self.original_url,
            "metadata": {}
        }
        
        # Campos adicionales van en metadata
        extra_fields = {
            "file_name": self.file_name,
            "extraction_date": self.extraction_date,
            "extraction_error": self.extraction_error
        }
        
        db_data["metadata"] = {k: v for k, v in extra_fields.items() if v is not None}
        
        return db_data


@dataclass
class ChunkMetadata:
    """Metadatos específicos de un chunk."""
    chunk_size: int
    crawled_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_identifier: str = ""
    date: str = ""
    category: str = ""
    keywords: str = ""
    source: str = ""
    cluster_id: int = -1
    cluster_size: int = 1
    article_number: Optional[str] = None
    article_title: Optional[str] = None
    document_type: Optional[str] = None
    document_title: Optional[str] = None
    issuing_authority: Optional[str] = None
    publication_date: Optional[str] = None
    jurisdiction: Optional[str] = None
    status: Optional[str] = None
    document_number: Optional[str] = None
    official_source: Optional[str] = None
    embedding_type: str = "enriched_with_context"
    embedding_components_count: int = 0
    has_overlap: bool = False
    chunk_in_cluster: int = 0
    clustering_method: str = ""
    is_subdivision: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)


@dataclass
class ProcessingCheckpoint:
    """Estado del procesamiento de un documento."""
    doc_id: str
    file_path: str
    metadata_extracted: bool = False
    text_extracted: bool = False
    chunks_created: bool = False
    chunks_processed: bool = False
    ingested: bool = False
    metadata: Optional[Dict[str, Any]] = None
    text_file: Optional[str] = None
    chunks_file: Optional[str] = None
    chunks_count: int = 0
    processed_file: Optional[str] = None
    document_id_db: Optional[int] = None
    error: Optional[str] = None
    failed_at: Optional[str] = None
    completed_at: Optional[str] = None
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingCheckpoint':
        """Crea una instancia desde un diccionario."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
    
    def get_current_stage(self) -> str:
        """Obtiene la etapa actual del procesamiento."""
        if self.error:
            return "failed"
        elif self.ingested:
            return "completed"
        elif self.chunks_processed:
            return "chunks_processed"
        elif self.chunks_created:
            return "chunks_created"
        elif self.text_extracted:
            return "text_extracted"
        elif self.metadata_extracted:
            return "metadata_extracted"
        else:
            return "not_started"
    
    def get_progress_percentage(self) -> float:
        """Calcula el porcentaje de progreso."""
        stages = [
            self.metadata_extracted,
            self.text_extracted,
            self.chunks_created,
            self.chunks_processed,
            self.ingested
        ]
        completed = sum(1 for stage in stages if stage)
        return (completed / len(stages)) * 100


@dataclass
class ExtractedText:
    """Texto extraído de un documento."""
    content: str
    page_count: int = 0
    extraction_method: str = "unknown"  # "pdfplumber", "ocr", "mixed"
    extraction_time: float = 0.0  # segundos
    
    def get_preview(self, chars: int = 500) -> str:
        """Obtiene una vista previa del contenido."""
        if len(self.content) <= chars:
            return self.content
        return self.content[:chars] + "..."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "content": self.content,
            "page_count": self.page_count,
            "extraction_method": self.extraction_method,
            "extraction_time": self.extraction_time,
            "content_length": len(self.content)
        }