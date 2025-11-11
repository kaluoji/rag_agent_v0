import logging
import datetime
import httpx
from typing import List
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.settings import ModelSettings
import pandas as pd
from app.core.config import settings

# Configuración básica
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelo simplificado - similar al de referencia
model = OpenAIModel(settings.llm_model)

# URLs controladas para scraping
REGULATORY_URLS = [
    {
        "name": "European Insurance Guidelines",
        "url": "https://www.eiopa.europa.eu/document-library/guidelines_en",
        "type": "guidelines",
        "region": "EU",
        "sector": "insurance"
    },
]

# ------------------------------
# 1) Modelos simplificados
# ------------------------------

class Regulation(BaseModel):
    """Modelo simplificado para una regulación"""
    title: str = Field(description="Title of the regulation")
    reference_number: str | None = Field(description="Reference number (e.g., EIOPA-BoS-20/600)", default=None)
    publication_date: str | None = Field(description="Publication date", default=None)
    document_url: str | None = Field(description="URL to the document", default=None)
    source: str | None = Field(description="Source organization", default=None)

class RegulationResults(BaseModel):
    """Resultado del scraping"""
    regulations: List[Regulation] = Field(description="List of regulations found")

class WebScrapingDeps(BaseModel):
    """
    Dependencias para el agente de Web Scraping.
    El campo http_client es un tipo arbitrario (httpx.Client), así que activamos
    arbitrary_types_allowed en model_config para que Pydantic no intente
    generar un schema interno para él.
    """
    http_client: httpx.AsyncClient

    model_config = {
        "arbitrary_types_allowed": True
    }


# ------------------------------
# 2) Agente simplificado
# ------------------------------

web_scraping_agent = Agent(
    name="Web Scraping Agent",
    model=model,
    system_prompt="""
You are a professional regulatory content extraction agent that operates exclusively with pre-approved sources.

Your primary function is to extract and structure regulatory information from a curated list of trusted sources. You never attempt to access URLs that are not in your predefined list.

WORKFLOW:
1. Use fetch_regulatory_content() to retrieve content from approved regulatory sources
2. Analyze the extracted content to identify relevant regulatory information
3. Extract and structure regulations with their key details:
   - Title and reference numbers
   - Publication dates
   - Document URLs (when available)
   - Regulatory authority/source

IMPORTANT CONSTRAINTS:
- You only access pre-approved URLs through the fetch_regulatory_content tool
- You never generate or attempt to access speculative URLs
- You focus on extracting structured information from the content you receive
- You prioritize recent publications and updates when available

Your goal is to provide comprehensive, structured regulatory information from trusted sources while maintaining complete control over which sources are accessed.
""",
    retries=2,
    result_type=RegulationResults,
    model_settings=ModelSettings(
        max_tokens=4000,
        temperature=0.0
    ),
)


# ------------------------------
# 3) Herramienta de scraping
# ------------------------------

@web_scraping_agent.tool(retries=1)
async def fetch_regulatory_content(ctx, source_identifier: str = "all") -> str:
    """
    Fetches content from predefined regulatory URLs only.
    
    This tool operates exclusively with URLs from our curated list,
    ensuring controlled and predictable scraping behavior.
    
    Args:
        source_identifier: Specific source to scrape, or "all" for all sources
        
    Returns:
        str: Combined content from the specified regulatory sources
    """
    
    # Determine which URLs to process based on the identifier
    urls_to_process = []
    
    if source_identifier == "all":
        # Process all URLs in our curated list
        urls_to_process = REGULATORY_URLS
        logger.info(f"Processing all {len(REGULATORY_URLS)} regulatory sources")
    else:
        # Look for specific sources by name, type, sector, or region
        matching_sources = []
        for source in REGULATORY_URLS:
            if (source_identifier.lower() in source["name"].lower() or 
                source_identifier.lower() == source["type"].lower() or
                source_identifier.lower() == source["sector"].lower() or
                source_identifier.lower() == source["region"].lower()):
                matching_sources.append(source)
        
        if matching_sources:
            urls_to_process = matching_sources
            logger.info(f"Found {len(matching_sources)} matching sources for '{source_identifier}'")
        else:
            # If no match found, default to first source to avoid empty results
            urls_to_process = [REGULATORY_URLS[0]]
            logger.info(f"No matches for '{source_identifier}', defaulting to first source")
    
    # Configure headers for professional scraping
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }
    
    combined_content = []
    successful_sources = 0
    
    # Process each URL in our controlled list
    async with httpx.AsyncClient(
        headers=headers, 
        timeout=30,
        follow_redirects=True,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    ) as client:
        
        for source in urls_to_process:
            try:
                logger.info(f"Fetching content from: {source['name']}")
                response = await client.get(source["url"])
                
                if response.status_code == 200:
                    # Verify content is HTML
                    content_type = response.headers.get('content-type', '').lower()
                    if 'text/html' in content_type:
                        # Parse and clean the content
                        soup = BeautifulSoup(response.text, "html.parser")
                        
                        # Remove unnecessary elements
                        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
                            element.decompose()
                        
                        # Extract clean text
                        text_content = soup.get_text()
                        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                        clean_text = '\n'.join(lines)
                        
                        # Add source identification and content
                        source_header = f"\n--- CONTENT FROM: {source['name']} ({source['type']}) ---\n"
                        combined_content.append(source_header + clean_text)
                        successful_sources += 1
                        
                        logger.info(f"Successfully extracted {len(clean_text)} characters from {source['name']}")
                    else:
                        logger.warning(f"Non-HTML content from {source['name']}: {content_type}")
                else:
                    logger.warning(f"HTTP {response.status_code} from {source['name']}: {source['url']}")
                    
            except Exception as e:
                logger.error(f"Error processing {source['name']}: {str(e)}")
                continue
    
    # Combine all successful content
    if combined_content:
        final_content = '\n\n'.join(combined_content)
        logger.info(f"Successfully processed {successful_sources}/{len(urls_to_process)} sources")
        return final_content
    else:
        return "No content could be extracted from any of the specified regulatory sources."