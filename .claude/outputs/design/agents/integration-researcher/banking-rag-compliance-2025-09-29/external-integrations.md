# External Integrations Strategy
## Banking RAG Compliance System

**Project**: banking-rag-compliance
**Document**: External Systems Integration Architecture
**Date**: 2025-09-29
**Author**: Integration Researcher Agent

---

## Executive Summary

This document defines comprehensive integration strategies for external compliance systems within the Banking RAG Compliance System. Based on 2025 market research and regulatory requirements, the architecture prioritizes secure, scalable, and compliant integrations with banking core systems, regulatory authorities, third-party compliance tools, and AI services.

**Key Integration Categories**:
- **AI/ML Platforms**: Azure OpenAI with enterprise-grade security
- **Regulatory Data Sources**: Direct API and web scraping integrations
- **Banking Core Systems**: Open Banking API and proprietary system connectors
- **Compliance Platforms**: GRC tools and audit system integrations
- **Identity & Authentication**: Enterprise SSO and multi-factor authentication
- **Monitoring & Analytics**: Real-time compliance monitoring and alerting

---

## 1. AI Platform Integrations

### 1.1 Azure OpenAI Service Integration

**Integration Type**: Primary AI/LLM Platform
**Security Level**: Enterprise Banking Grade
**Compliance**: SOC 2 Type II, ISO 27001, GDPR-aligned, HIPAA attestation

#### Architecture Pattern
```python
from azure.identity import ManagedIdentity
from azure.ai.openai import AzureOpenAIClient
from azure.keyvault.secrets import SecretClient

class SecureAzureOpenAIIntegration:
    def __init__(self):
        # Managed Identity for authentication
        self.credential = ManagedIdentity()

        # Azure Key Vault for secret management
        self.key_vault = SecretClient(
            vault_url="https://{vault-name}.vault.azure.net/",
            credential=self.credential
        )

        # Azure OpenAI client with regional deployment
        self.client = AzureOpenAIClient(
            endpoint=self.key_vault.get_secret("aoai-endpoint").value,
            credential=self.credential
        )

    async def process_compliance_query(self, query: str, context: dict) -> dict:
        """Process compliance query with audit logging"""

        # Audit log entry
        audit_entry = {
            "timestamp": datetime.utcnow(),
            "user_id": context.get("user_id"),
            "tenant_id": context.get("tenant_id"),
            "query_hash": hashlib.sha256(query.encode()).hexdigest(),
            "action": "compliance_query"
        }

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a banking compliance expert."},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,  # Low temperature for compliance accuracy
                max_tokens=4000
            )

            audit_entry.update({
                "status": "success",
                "tokens_used": response.usage.total_tokens,
                "response_id": response.id
            })

            return {
                "response": response.choices[0].message.content,
                "metadata": {
                    "model": response.model,
                    "tokens": response.usage.total_tokens,
                    "audit_id": audit_entry["audit_id"]
                }
            }

        except Exception as e:
            audit_entry.update({
                "status": "error",
                "error": str(e)
            })
            raise
        finally:
            await self.log_audit_entry(audit_entry)
```

#### Key Integration Features
- **Regional Deployment**: Data processing within specific Azure regions for compliance
- **Provisioned Throughput Units (PTUs)**: Predictable pricing and performance
- **Token-based Authentication**: Azure Entra ID integration with automatic token refresh
- **Audit Logging**: Complete audit trail for all AI interactions
- **Cost Management**: Built-in budget alerts and chargeback capabilities

### 1.2 Browserbase Integration for Regulatory Monitoring

**Integration Type**: Web Automation & Data Extraction
**Security Level**: Enterprise Compliance
**Features**: HIPAA and SOC 2 compliance, automated CAPTCHA solving

#### Implementation Pattern
```javascript
import { Browserbase } from '@browserbase/sdk';

class ComplianceWebScraper {
    constructor() {
        this.browserbase = new Browserbase({
            apiKey: process.env.BROWSERBASE_API_KEY,
            projectId: process.env.BROWSERBASE_PROJECT_ID
        });
    }

    async monitorRegulatorySource(source) {
        const session = await this.browserbase.createSession({
            keepAlive: true,
            timeout: 300000,
            proxyType: 'residential',
            browserSettings: {
                stealth: true,
                compliance: 'banking'
            }
        });

        try {
            // Navigate to regulatory source
            await session.goto(source.url);

            // Extract regulatory updates
            const updates = await session.evaluate(() => {
                // Source-specific extraction logic
                return this.extractRegulatoryUpdates();
            });

            // Process and validate updates
            return await this.processRegulatoryUpdates(updates, source);

        } finally {
            await session.close();
        }
    }

    async setupWebhookNotifications() {
        // Configure webhooks for real-time updates
        return await this.browserbase.webhooks.create({
            url: `${process.env.API_BASE_URL}/webhooks/regulatory-updates`,
            events: ['session_completed', 'data_extracted'],
            secret: process.env.WEBHOOK_SECRET
        });
    }
}
```

---

## 2. Banking Core Systems Integration

### 2.1 Open Banking API Integration

**Standards**: PSD2 (Europe), FDX (Global), CDS (Australia)
**Authentication**: OAuth 2.0 authorization code flow
**Security**: FAPI (Financial-grade API) compliance

#### Integration Architecture
```python
from authlib.integrations.httpx_client import OAuth2Session
import httpx
import jwt

class OpenBankingAPIIntegrator:
    def __init__(self, bank_config: dict):
        self.config = bank_config
        self.oauth_session = OAuth2Session(
            client_id=self.config['client_id'],
            client_secret=self.config['client_secret'],
            redirect_uri=self.config['redirect_uri']
        )

    async def authenticate_customer(self, customer_id: str) -> dict:
        """Initiate OAuth flow for customer authentication"""

        # Generate authorization URL
        auth_url, state = self.oauth_session.create_authorization_url(
            self.config['authorization_endpoint'],
            scope=['accounts', 'transactions', 'compliance-data'],
            state=customer_id
        )

        return {
            "auth_url": auth_url,
            "state": state,
            "expires_in": 300  # 5 minutes
        }

    async def fetch_compliance_data(self, access_token: str) -> dict:
        """Fetch compliance-relevant data from core banking system"""

        headers = {
            'Authorization': f'Bearer {access_token}',
            'x-fapi-financial-id': self.config['financial_id'],
            'x-fapi-interaction-id': str(uuid.uuid4()),
            'Content-Type': 'application/json'
        }

        async with httpx.AsyncClient() as client:
            # Fetch account information
            accounts = await client.get(
                f"{self.config['api_base']}/accounts",
                headers=headers
            )

            # Fetch transaction data for compliance analysis
            transactions = await client.get(
                f"{self.config['api_base']}/transactions",
                headers=headers,
                params={
                    'fromDate': '2024-01-01',
                    'toDate': datetime.now().isoformat()
                }
            )

            return {
                "accounts": accounts.json(),
                "transactions": transactions.json(),
                "compliance_flags": await self.analyze_compliance_data(
                    accounts.json(), transactions.json()
                )
            }
```

### 2.2 Legacy Core Banking System Integration

**Integration Methods**: SOAP/REST APIs, Message Queues, File-based ETL
**Security**: VPN tunneling, certificate-based authentication
**Data Formats**: ISO 20022, MT messages, proprietary formats

#### Adapter Pattern Implementation
```python
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET

class CoreBankingAdapter(ABC):
    """Abstract adapter for core banking system integration"""

    @abstractmethod
    async def fetch_customer_data(self, customer_id: str) -> dict:
        pass

    @abstractmethod
    async def fetch_transaction_data(self, account_id: str, date_range: tuple) -> list:
        pass

class LegacySOAPAdapter(CoreBankingAdapter):
    """Adapter for legacy SOAP-based core banking systems"""

    def __init__(self, wsdl_url: str, credentials: dict):
        self.wsdl_url = wsdl_url
        self.credentials = credentials
        self.client = self._create_soap_client()

    async def fetch_customer_data(self, customer_id: str) -> dict:
        """Fetch customer data via SOAP API"""

        soap_request = f"""
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <GetCustomerData>
                    <CustomerId>{customer_id}</CustomerId>
                    <IncludeComplianceData>true</IncludeComplianceData>
                </GetCustomerData>
            </soap:Body>
        </soap:Envelope>
        """

        response = await self.client.post(
            self.wsdl_url,
            data=soap_request,
            headers={'SOAPAction': 'GetCustomerData'}
        )

        return self._parse_soap_response(response.text)

class ModernRESTAdapter(CoreBankingAdapter):
    """Adapter for modern REST-based core banking systems"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = httpx.AsyncClient(
            headers={'Authorization': f'Bearer {api_key}'}
        )

    async def fetch_customer_data(self, customer_id: str) -> dict:
        """Fetch customer data via REST API"""

        response = await self.session.get(
            f"{self.base_url}/customers/{customer_id}",
            params={'include': 'compliance,kyc,aml'}
        )

        return response.json()
```

---

## 3. Regulatory Authority Integrations

### 3.1 European Regulatory Sources Integration

Based on our research, we have identified 7 key regulatory sources with varying integration capabilities:

#### Tier 1: API-First Sources
- **Bank of Spain**: JSON API with statistical data
- **ESMA**: Open data portal with GitHub integration
- **EIOPA**: EU Open Data Portal integration

#### Tier 2: Structured Data Sources
- **EBA**: Open data frameworks with established APIs
- **EC DG FISMA**: API development in progress

#### Tier 3: Traditional Web Sources
- **IOSCO**: PDF-based publications
- **CNMV**: Traditional web structure

### 3.2 Regulatory Data Integration Framework

```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional

class SourceType(Enum):
    API_NATIVE = "api_native"
    OPEN_DATA_PORTAL = "open_data_portal"
    WEB_SCRAPING = "web_scraping"
    RSS_FEED = "rss_feed"

@dataclass
class RegulatorySource:
    name: str
    type: SourceType
    base_url: str
    api_endpoint: Optional[str]
    authentication: Optional[dict]
    rate_limits: dict
    update_frequency: str

class RegulatoryDataIntegrator:
    def __init__(self):
        self.sources = self._initialize_sources()
        self.scrapers = {}
        self.api_clients = {}

    def _initialize_sources(self) -> Dict[str, RegulatorySource]:
        return {
            "bank_of_spain": RegulatorySource(
                name="Bank of Spain",
                type=SourceType.API_NATIVE,
                base_url="https://www.bde.es",
                api_endpoint="/webbde/es/estadis/infoest/si_1_1.json",
                authentication=None,  # Public API
                rate_limits={"requests_per_minute": 60},
                update_frequency="daily"
            ),
            "esma": RegulatorySource(
                name="ESMA",
                type=SourceType.OPEN_DATA_PORTAL,
                base_url="https://www.esma.europa.eu",
                api_endpoint="/api/esma_library",
                authentication=None,
                rate_limits={"requests_per_minute": 30},
                update_frequency="weekly"
            ),
            "eiopa": RegulatorySource(
                name="EIOPA",
                type=SourceType.OPEN_DATA_PORTAL,
                base_url="https://www.eiopa.europa.eu",
                api_endpoint="/data-portal/api/v1",
                authentication=None,
                rate_limits={"requests_per_minute": 30},
                update_frequency="monthly"
            ),
            "iosco": RegulatorySource(
                name="IOSCO",
                type=SourceType.WEB_SCRAPING,
                base_url="https://www.iosco.org",
                api_endpoint=None,
                authentication=None,
                rate_limits={"requests_per_minute": 10},
                update_frequency="quarterly"
            )
        }

    async def fetch_regulatory_updates(self, source_name: str) -> List[dict]:
        """Fetch updates from specific regulatory source"""

        source = self.sources[source_name]

        if source.type == SourceType.API_NATIVE:
            return await self._fetch_via_api(source)
        elif source.type == SourceType.OPEN_DATA_PORTAL:
            return await self._fetch_via_open_data(source)
        elif source.type == SourceType.WEB_SCRAPING:
            return await self._fetch_via_scraping(source)
        else:
            raise ValueError(f"Unsupported source type: {source.type}")

    async def _fetch_via_api(self, source: RegulatorySource) -> List[dict]:
        """Fetch data using native API"""

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{source.base_url}{source.api_endpoint}",
                headers={
                    'User-Agent': 'BankingRAGCompliance/1.0',
                    'Accept': 'application/json'
                }
            )

            response.raise_for_status()
            return response.json()
```

### 3.3 Real-Time Update Monitoring

```python
import asyncio
from datetime import datetime, timedelta

class RegulatoryUpdateMonitor:
    def __init__(self, integrator: RegulatoryDataIntegrator):
        self.integrator = integrator
        self.webhook_urls = {}
        self.last_check = {}

    async def start_monitoring(self):
        """Start continuous monitoring of all regulatory sources"""

        tasks = []
        for source_name in self.integrator.sources:
            task = asyncio.create_task(
                self._monitor_source(source_name)
            )
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def _monitor_source(self, source_name: str):
        """Monitor specific regulatory source for updates"""

        source = self.integrator.sources[source_name]
        check_interval = self._calculate_check_interval(source.update_frequency)

        while True:
            try:
                updates = await self.integrator.fetch_regulatory_updates(source_name)
                new_updates = await self._filter_new_updates(source_name, updates)

                if new_updates:
                    await self._process_updates(source_name, new_updates)
                    await self._send_webhook_notifications(source_name, new_updates)

                self.last_check[source_name] = datetime.utcnow()

            except Exception as e:
                logger.error(f"Error monitoring {source_name}: {str(e)}")

            await asyncio.sleep(check_interval)

    def _calculate_check_interval(self, frequency: str) -> int:
        """Calculate monitoring interval based on update frequency"""

        intervals = {
            "daily": 3600,      # Check every hour
            "weekly": 3600 * 6,  # Check every 6 hours
            "monthly": 3600 * 12, # Check every 12 hours
            "quarterly": 3600 * 24 # Check every 24 hours
        }

        return intervals.get(frequency, 3600)
```

---

## 4. Third-Party Compliance Tools Integration

### 4.1 GRC Platform Integration

**Target Platforms**: RSA Archer, ServiceNow GRC, MetricStream, SAI Global
**Integration Methods**: REST APIs, SCIM for identity, webhook notifications

```python
class GRCPlatformIntegrator:
    """Integration with Governance, Risk & Compliance platforms"""

    def __init__(self, platform_config: dict):
        self.config = platform_config
        self.client = self._create_api_client()

    async def sync_compliance_findings(self, findings: List[dict]) -> dict:
        """Synchronize compliance findings with GRC platform"""

        payload = {
            "source": "Banking RAG Compliance System",
            "findings": [
                {
                    "id": finding["id"],
                    "title": finding["title"],
                    "description": finding["description"],
                    "severity": finding["severity"],
                    "regulatory_reference": finding["regulation"],
                    "remediation_plan": finding.get("remediation"),
                    "due_date": finding.get("due_date"),
                    "status": "open"
                }
                for finding in findings
            ],
            "sync_timestamp": datetime.utcnow().isoformat()
        }

        response = await self.client.post(
            f"{self.config['base_url']}/api/v1/findings/bulk",
            json=payload,
            headers={
                'Authorization': f"Bearer {self.config['api_token']}",
                'Content-Type': 'application/json'
            }
        )

        return response.json()

    async def create_compliance_workflow(self, gap_analysis: dict) -> str:
        """Create automated compliance workflow based on gap analysis"""

        workflow = {
            "name": f"Compliance Gap Remediation - {gap_analysis['regulation']}",
            "description": f"Automated workflow for {gap_analysis['gap_count']} identified gaps",
            "steps": [
                {
                    "name": "Review Gaps",
                    "type": "approval",
                    "assignee": "compliance_team",
                    "due_days": 3
                },
                {
                    "name": "Create Action Plan",
                    "type": "task",
                    "assignee": "business_owner",
                    "due_days": 7,
                    "dependencies": ["Review Gaps"]
                },
                {
                    "name": "Implement Controls",
                    "type": "task",
                    "assignee": "implementation_team",
                    "due_days": 30,
                    "dependencies": ["Create Action Plan"]
                },
                {
                    "name": "Validate Implementation",
                    "type": "approval",
                    "assignee": "audit_team",
                    "due_days": 5,
                    "dependencies": ["Implement Controls"]
                }
            ]
        }

        response = await self.client.post(
            f"{self.config['base_url']}/api/v1/workflows",
            json=workflow,
            headers={'Authorization': f"Bearer {self.config['api_token']}"}
        )

        return response.json()["workflow_id"]
```

### 4.2 Document Management System Integration

**Target Systems**: SharePoint, Box, Google Drive, OneDrive
**Capabilities**: Automated document classification, version control, audit trails

```python
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

class DocumentManagementIntegrator:
    """Integration with document management systems"""

    def __init__(self, storage_account: str):
        self.credential = DefaultAzureCredential()
        self.blob_client = BlobServiceClient(
            account_url=f"https://{storage_account}.blob.core.windows.net",
            credential=self.credential
        )

    async def store_regulatory_document(self, document: dict) -> dict:
        """Store regulatory document with compliance metadata"""

        container_name = f"regulatory-docs-{document['authority'].lower()}"
        blob_name = f"{document['publication_date']}/{document['document_id']}.pdf"

        # Upload document
        blob_client = self.blob_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )

        await blob_client.upload_blob(
            document['content'],
            metadata={
                'authority': document['authority'],
                'document_type': document['type'],
                'publication_date': document['publication_date'],
                'regulatory_topic': document.get('topic', ''),
                'compliance_classification': document.get('classification', 'public'),
                'retention_period': str(document.get('retention_years', 7))
            },
            overwrite=True
        )

        return {
            "document_url": blob_client.url,
            "container": container_name,
            "blob_name": blob_name,
            "upload_timestamp": datetime.utcnow().isoformat()
        }
```

---

## 5. Identity and Access Management Integration

### 5.1 Microsoft Entra ID (Azure AD) Integration

**Features**: Multi-factor authentication, conditional access, role-based access control
**Protocols**: OAuth 2.0, OpenID Connect, SAML 2.0

```python
from azure.identity import DefaultAzureCredential
from microsoft.graph import GraphServiceClient

class EntraIDIntegrator:
    """Integration with Microsoft Entra ID for authentication and authorization"""

    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.graph_client = GraphServiceClient(
            credentials=self.credential,
            scopes=['https://graph.microsoft.com/.default']
        )

    async def authenticate_user(self, token: str) -> dict:
        """Authenticate user and retrieve profile information"""

        try:
            # Validate token and get user info
            user = await self.graph_client.me.get()

            # Get user's group memberships for role determination
            groups = await self.graph_client.me.member_of.get()

            # Determine compliance roles
            compliance_roles = self._extract_compliance_roles(groups.value)

            return {
                "user_id": user.id,
                "display_name": user.display_name,
                "email": user.user_principal_name,
                "department": user.department,
                "compliance_roles": compliance_roles,
                "tenant_id": user.tenant_id,
                "authentication_method": "entra_id"
            }

        except Exception as e:
            raise AuthenticationError(f"Failed to authenticate user: {str(e)}")

    def _extract_compliance_roles(self, groups: list) -> list:
        """Extract compliance-specific roles from AD groups"""

        role_mapping = {
            "Compliance-Viewer": ["query", "read"],
            "Compliance-Analyst": ["query", "read", "report_generate", "gap_analysis"],
            "Compliance-Manager": ["query", "read", "report_generate", "gap_analysis", "document_upload"],
            "Compliance-Admin": ["*"]  # All permissions
        }

        user_roles = []
        for group in groups:
            if group.display_name in role_mapping:
                user_roles.extend(role_mapping[group.display_name])

        return list(set(user_roles))
```

### 5.2 Multi-Factor Authentication Implementation

```python
import pyotp
from azure.keyvault.secrets import SecretClient

class MFAIntegrator:
    """Multi-factor authentication integration"""

    def __init__(self, key_vault_url: str):
        self.credential = DefaultAzureCredential()
        self.key_vault = SecretClient(
            vault_url=key_vault_url,
            credential=self.credential
        )

    async def setup_mfa_for_user(self, user_id: str) -> dict:
        """Setup MFA for compliance system access"""

        # Generate TOTP secret
        secret = pyotp.random_base32()

        # Store secret in Key Vault
        secret_name = f"mfa-secret-{user_id}"
        await self.key_vault.set_secret(secret_name, secret)

        # Generate QR code data for authenticator app
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_id,
            issuer_name="Banking RAG Compliance System"
        )

        return {
            "secret": secret,
            "qr_code_uri": totp_uri,
            "backup_codes": self._generate_backup_codes(user_id)
        }

    async def verify_mfa_token(self, user_id: str, token: str) -> bool:
        """Verify MFA token for user"""

        try:
            # Retrieve secret from Key Vault
            secret_name = f"mfa-secret-{user_id}"
            secret = await self.key_vault.get_secret(secret_name)

            # Verify TOTP token
            totp = pyotp.TOTP(secret.value)
            return totp.verify(token, valid_window=1)

        except Exception as e:
            logger.error(f"MFA verification failed for user {user_id}: {str(e)}")
            return False
```

---

## 6. Monitoring and Analytics Integration

### 6.1 Datadog Integration for Compliance Monitoring

```python
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.metrics_api import MetricsApi

class ComplianceMonitoringIntegrator:
    """Integration with Datadog for compliance metrics and alerting"""

    def __init__(self, api_key: str, app_key: str):
        self.configuration = Configuration()
        self.configuration.api_key["apiKeyAuth"] = api_key
        self.configuration.api_key["appKeyAuth"] = app_key

        self.api_client = ApiClient(self.configuration)
        self.metrics_api = MetricsApi(self.api_client)

    async def send_compliance_metrics(self, metrics: dict):
        """Send compliance-related metrics to Datadog"""

        metric_points = []

        for metric_name, value in metrics.items():
            metric_points.append({
                "metric": f"compliance.{metric_name}",
                "points": [[int(time.time()), value]],
                "tags": [
                    f"tenant:{metrics.get('tenant_id', 'default')}",
                    f"regulation:{metrics.get('regulation', 'general')}",
                    "service:banking_rag_compliance"
                ]
            })

        await self.metrics_api.submit_metrics({"series": metric_points})

    async def create_compliance_dashboard(self) -> str:
        """Create compliance monitoring dashboard"""

        dashboard_config = {
            "title": "Banking Compliance Monitoring",
            "description": "Real-time compliance metrics and alerts",
            "widgets": [
                {
                    "definition": {
                        "type": "timeseries",
                        "requests": [
                            {
                                "q": "avg:compliance.gap_analysis_score{*} by {regulation}",
                                "display_type": "line"
                            }
                        ],
                        "title": "Compliance Gap Scores by Regulation"
                    }
                },
                {
                    "definition": {
                        "type": "query_value",
                        "requests": [
                            {
                                "q": "sum:compliance.regulatory_updates_processed{*}",
                                "aggregator": "sum"
                            }
                        ],
                        "title": "Regulatory Updates Processed Today"
                    }
                }
            ]
        }

        # Create dashboard via Datadog API
        # Implementation details would go here

        return "dashboard_url"
```

---

## 7. Integration Security Framework

### 7.1 API Security Standards

**Authentication**: OAuth 2.0, JWT tokens, mTLS for high-security integrations
**Authorization**: RBAC with fine-grained permissions
**Data Protection**: AES-256 encryption, field-level encryption for PII

```python
import jwt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

class IntegrationSecurityManager:
    """Centralized security management for all integrations"""

    def __init__(self, key_vault_client):
        self.key_vault = key_vault_client
        self.private_key = None
        self.public_key = None
        self._load_keys()

    async def create_secure_jwt_token(self, payload: dict, expires_hours: int = 1) -> str:
        """Create signed JWT token for API authentication"""

        payload.update({
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=expires_hours),
            'iss': 'banking-rag-compliance-system'
        })

        token = jwt.encode(
            payload,
            self.private_key,
            algorithm='RS256'
        )

        return token

    async def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data before external API calls"""

        encrypted = self.public_key.encrypt(
            data.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return base64.b64encode(encrypted).decode('utf-8')

    async def verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature for secure external integrations"""

        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, f"sha256={expected_signature}")
```

---

## 8. Integration Monitoring and Health Checks

### 8.1 Health Check Framework

```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheckResult:
    service: str
    status: HealthStatus
    response_time_ms: int
    message: str
    timestamp: datetime

class IntegrationHealthMonitor:
    """Monitor health of all external integrations"""

    def __init__(self):
        self.integrations = {}
        self.health_checks = {}

    async def check_all_integrations(self) -> Dict[str, HealthCheckResult]:
        """Perform health checks on all registered integrations"""

        results = {}

        # Check Azure OpenAI
        results['azure_openai'] = await self._check_azure_openai()

        # Check Browserbase
        results['browserbase'] = await self._check_browserbase()

        # Check regulatory sources
        for source_name in ['bank_of_spain', 'esma', 'eiopa']:
            results[source_name] = await self._check_regulatory_source(source_name)

        # Check GRC platforms
        results['grc_platform'] = await self._check_grc_platform()

        return results

    async def _check_azure_openai(self) -> HealthCheckResult:
        """Health check for Azure OpenAI service"""

        start_time = time.time()

        try:
            # Simple health check query
            response = await self.azure_openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": "Health check"}],
                max_tokens=10
            )

            response_time = int((time.time() - start_time) * 1000)

            return HealthCheckResult(
                service="azure_openai",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                message="Service responding normally",
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            return HealthCheckResult(
                service="azure_openai",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=int((time.time() - start_time) * 1000),
                message=f"Service error: {str(e)}",
                timestamp=datetime.utcnow()
            )
```

---

## 9. Integration Testing Strategy

### 9.1 Automated Integration Testing

```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestIntegrationFramework:
    """Comprehensive testing framework for all integrations"""

    @pytest.fixture
    async def mock_azure_openai(self):
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Mock response"))],
            usage=Mock(total_tokens=100),
            id="test-response-id"
        )
        return mock_client

    @pytest.mark.asyncio
    async def test_azure_openai_integration(self, mock_azure_openai):
        """Test Azure OpenAI integration with compliance query"""

        integrator = SecureAzureOpenAIIntegration()
        integrator.client = mock_azure_openai

        result = await integrator.process_compliance_query(
            "What are the capital requirements for banks?",
            {"user_id": "test_user", "tenant_id": "test_tenant"}
        )

        assert "response" in result
        assert "metadata" in result
        assert result["metadata"]["tokens"] == 100

    @pytest.mark.asyncio
    async def test_regulatory_source_integration(self):
        """Test regulatory source data fetching"""

        integrator = RegulatoryDataIntegrator()

        # Mock the HTTP client
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = [{"title": "Test Regulation"}]
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await integrator.fetch_regulatory_updates("bank_of_spain")

            assert len(result) > 0
            assert "title" in result[0]

    @pytest.mark.asyncio
    async def test_webhook_security(self):
        """Test webhook signature verification"""

        security_manager = IntegrationSecurityManager(mock_key_vault)

        payload = b'{"test": "data"}'
        secret = "test_secret"

        # Generate valid signature
        signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        is_valid = await security_manager.verify_webhook_signature(
            payload, f"sha256={signature}", secret
        )

        assert is_valid is True
```

---

## 10. Implementation Roadmap

### Phase 1: Core Integrations (Months 1-3)
1. **Azure OpenAI Integration**
   - Set up regional deployment with PTUs
   - Implement authentication with Azure Entra ID
   - Configure audit logging and monitoring

2. **Regulatory Sources (Tier 1)**
   - Implement Bank of Spain API integration
   - Set up ESMA open data portal connection
   - Configure EIOPA data access

3. **Basic Security Framework**
   - Implement OAuth 2.0 authentication
   - Set up Azure Key Vault integration
   - Configure basic monitoring

### Phase 2: Extended Integrations (Months 4-6)
1. **Banking Core Systems**
   - Open Banking API integration
   - Legacy system adapters
   - Transaction data synchronization

2. **Browserbase Integration**
   - Web scraping for Tier 3 regulatory sources
   - Automated monitoring workflows
   - Webhook notifications

3. **GRC Platform Integration**
   - Compliance findings synchronization
   - Automated workflow creation
   - Document management integration

### Phase 3: Advanced Features (Months 7-9)
1. **Multi-Tenant Architecture**
   - Tenant isolation implementation
   - Resource sharing optimization
   - Billing and usage tracking

2. **Advanced Monitoring**
   - Datadog dashboard creation
   - Custom compliance metrics
   - Predictive alerting

3. **Integration Testing**
   - Automated test suites
   - Performance testing
   - Security validation

---

## Conclusion

This external integrations strategy provides a comprehensive framework for connecting the Banking RAG Compliance System with all necessary external services and data sources. The architecture prioritizes security, compliance, and scalability while maintaining flexibility for future enhancements.

Key success factors include:
- **Security-first approach** with enterprise-grade authentication and encryption
- **Regulatory compliance** through proper data handling and audit trails
- **Scalable architecture** supporting multi-tenant deployments
- **Comprehensive monitoring** with proactive alerting and health checks
- **Flexible integration patterns** accommodating various external systems

The phased implementation approach ensures systematic deployment while managing risks and dependencies effectively.