# Audit Trail Specifications for Banking RAG Compliance System

## Executive Summary

This document defines comprehensive audit trail specifications for the Banking RAG Compliance System, ensuring full compliance with GDPR, MiFID II, Basel III, and other relevant financial regulations. The design implements immutable audit logging, regulatory compliance tracking, data lineage management, and advanced security monitoring required for banking sector operations. The audit framework supports forensic analysis, regulatory reporting, and continuous compliance monitoring across all system operations.

### Key Compliance Features
- **GDPR Article 30 Compliance** - Complete records of processing activities
- **MiFID II Audit Requirements** - Investment services transaction logging
- **Basel III Operational Risk** - Comprehensive operational risk event tracking
- **SOX Compliance** - Financial reporting controls and audit trails
- **PCI DSS Requirements** - Payment card industry security standards
- **ISO 27001** - Information security management system audit trails

## Regulatory Compliance Framework

### 1. Core Audit Tables Architecture

```sql
-- Primary audit log table with immutable records
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event identification
    event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    event_category TEXT NOT NULL CHECK (event_category IN (
        'authentication', 'authorization', 'data_access', 'data_modification',
        'system_admin', 'compliance', 'security', 'business_process',
        'regulatory_reporting', 'user_interaction', 'api_access'
    )),

    -- Actor information (who)
    user_id UUID REFERENCES auth.users(id),
    user_email TEXT,
    user_role TEXT,
    impersonated_by UUID REFERENCES auth.users(id), -- For admin impersonation
    service_account TEXT, -- For system-generated events

    -- Action details (what)
    action_type TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    resource_name TEXT,
    action_description TEXT,
    action_result TEXT CHECK (action_result IN ('success', 'failure', 'partial', 'pending')),

    -- Context information (when, where, how)
    timestamp_utc TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id TEXT,
    request_id TEXT,
    correlation_id TEXT, -- For tracking related events

    -- Technical details
    ip_address INET,
    user_agent TEXT,
    client_type TEXT CHECK (client_type IN ('web', 'mobile', 'api', 'system', 'admin')),
    api_version TEXT,
    endpoint_url TEXT,
    http_method TEXT,
    http_status_code INTEGER,

    -- Data change tracking
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],

    -- Business context
    business_process TEXT,
    compliance_category TEXT,
    regulatory_impact TEXT[],
    risk_level TEXT CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),

    -- Security context
    authentication_method TEXT,
    authorization_grants TEXT[],
    security_context JSONB DEFAULT '{}',

    -- Compliance metadata
    retention_policy TEXT DEFAULT 'banking_standard', -- 7 years for banking
    gdpr_lawful_basis TEXT,
    data_classification TEXT CHECK (data_classification IN ('public', 'internal', 'confidential', 'restricted')),
    processing_purpose TEXT[],

    -- Audit metadata
    audit_source TEXT NOT NULL DEFAULT 'application',
    audit_version TEXT DEFAULT '1.0',
    digital_signature TEXT, -- For critical events
    hash_chain_reference TEXT, -- For tamper detection

    -- Performance tracking
    execution_time_ms FLOAT,
    resource_usage JSONB,

    CONSTRAINT valid_timestamp CHECK (timestamp_utc <= NOW()),
    CONSTRAINT valid_execution_time CHECK (execution_time_ms >= 0)
);

-- Indexes for audit log performance
CREATE INDEX CONCURRENTLY idx_audit_logs_timestamp ON audit_logs (timestamp_utc DESC);
CREATE INDEX CONCURRENTLY idx_audit_logs_user_time ON audit_logs (user_id, timestamp_utc DESC);
CREATE INDEX CONCURRENTLY idx_audit_logs_event_type ON audit_logs (event_type, timestamp_utc DESC);
CREATE INDEX CONCURRENTLY idx_audit_logs_resource ON audit_logs (resource_type, resource_id, timestamp_utc DESC);
CREATE INDEX CONCURRENTLY idx_audit_logs_compliance ON audit_logs USING GIN (regulatory_impact);
CREATE INDEX CONCURRENTLY idx_audit_logs_risk_level ON audit_logs (risk_level, timestamp_utc DESC);
CREATE INDEX CONCURRENTLY idx_audit_logs_business_process ON audit_logs (business_process, timestamp_utc DESC);

-- Prevent modifications to audit logs (immutable)
CREATE POLICY audit_logs_no_modification ON audit_logs
    FOR UPDATE, DELETE
    TO PUBLIC
    USING (FALSE);

-- Allow only inserts and reads
CREATE POLICY audit_logs_insert_only ON audit_logs
    FOR INSERT
    TO authenticated
    WITH CHECK (TRUE);

CREATE POLICY audit_logs_read_access ON audit_logs
    FOR SELECT
    TO authenticated
    USING (
        -- Users can read their own audit logs
        user_id = auth.uid()
        OR
        -- Admins and compliance officers can read all logs
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
            AND ur.role_name IN ('admin', 'super_admin', 'compliance_officer', 'auditor')
            AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
        )
    );

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE audit_logs IS 'Immutable audit trail for all system activities with regulatory compliance';
```

### 2. Specialized Compliance Audit Tables

```sql
-- GDPR-specific data processing audit
CREATE TABLE gdpr_processing_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_log_id UUID REFERENCES audit_logs(id) ON DELETE CASCADE,

    -- GDPR Article 30 - Records of Processing Activities
    controller_name TEXT NOT NULL,
    processor_name TEXT,
    data_subject_category TEXT NOT NULL,
    personal_data_categories TEXT[] NOT NULL,
    processing_purposes TEXT[] NOT NULL,
    lawful_basis TEXT NOT NULL CHECK (lawful_basis IN (
        'consent', 'contract', 'legal_obligation', 'vital_interests', 'public_task', 'legitimate_interests'
    )),

    -- Data subject rights handling
    data_subject_request_type TEXT CHECK (data_subject_request_type IN (
        'access', 'rectification', 'erasure', 'restrict_processing', 'data_portability', 'object'
    )),
    request_response_time_hours INTEGER,
    request_fulfillment_status TEXT CHECK (request_fulfillment_status IN (
        'pending', 'completed', 'rejected', 'partially_completed'
    )),

    -- Cross-border transfers
    third_country_transfers JSONB,
    adequacy_decision_reference TEXT,
    appropriate_safeguards JSONB,

    -- Retention and deletion
    retention_period_months INTEGER,
    deletion_schedule DATE,
    anonymization_applied BOOLEAN DEFAULT FALSE,

    -- Consent management
    consent_timestamp TIMESTAMP WITH TIME ZONE,
    consent_method TEXT,
    consent_withdrawn_timestamp TIMESTAMP WITH TIME ZONE,
    marketing_consent BOOLEAN,

    -- Data breach tracking
    breach_detected BOOLEAN DEFAULT FALSE,
    breach_notification_authority TIMESTAMP WITH TIME ZONE,
    breach_notification_subjects TIMESTAMP WITH TIME ZONE,
    breach_risk_assessment TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Financial services specific audit (MiFID II)
CREATE TABLE financial_services_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_log_id UUID REFERENCES audit_logs(id) ON DELETE CASCADE,

    -- MiFID II Transaction Reporting
    transaction_type TEXT CHECK (transaction_type IN (
        'investment_advice', 'portfolio_management', 'reception_transmission_orders',
        'execution_orders', 'dealing_own_account', 'underwriting', 'market_making'
    )),
    client_classification TEXT CHECK (client_classification IN (
        'retail_client', 'professional_client', 'eligible_counterparty'
    )),
    instrument_identification TEXT,
    venue_identification TEXT,

    -- Best execution requirements
    execution_quality_data JSONB,
    venue_selection_rationale TEXT,

    -- Product governance
    target_market JSONB,
    distribution_strategy TEXT,
    product_review_date DATE,

    -- Conduct risk monitoring
    conduct_risk_indicators JSONB,
    suspicious_activity_flag BOOLEAN DEFAULT FALSE,
    regulatory_breach_flag BOOLEAN DEFAULT FALSE,

    -- Record keeping requirements
    communication_records JSONB,
    order_records JSONB,
    transaction_records JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Operational risk events (Basel III)
CREATE TABLE operational_risk_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_log_id UUID REFERENCES audit_logs(id) ON DELETE CASCADE,

    -- Basel III Operational Risk Categories
    event_category TEXT NOT NULL CHECK (event_category IN (
        'internal_fraud', 'external_fraud', 'employment_practices',
        'clients_products_business', 'damage_physical_assets',
        'business_disruption_system_failures', 'execution_delivery_process_management'
    )),

    -- Risk assessment
    gross_loss_amount DECIMAL(15,2),
    recovery_amount DECIMAL(15,2),
    net_loss_amount DECIMAL(15,2),
    currency_code TEXT DEFAULT 'EUR',

    -- Impact analysis
    business_line TEXT,
    affected_systems TEXT[],
    customer_impact_count INTEGER,
    reputational_impact TEXT CHECK (reputational_impact IN ('none', 'low', 'medium', 'high', 'severe')),

    -- Incident response
    detection_method TEXT,
    response_time_minutes INTEGER,
    containment_actions JSONB,
    recovery_time_minutes INTEGER,

    -- Root cause analysis
    root_cause_category TEXT,
    contributing_factors TEXT[],
    lessons_learned TEXT,
    preventive_measures JSONB,

    -- Regulatory reporting
    regulatory_reporting_required BOOLEAN DEFAULT FALSE,
    reported_to_authorities TIMESTAMP WITH TIME ZONE,
    reporting_reference TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data access and query audit for RAG system
CREATE TABLE rag_query_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_log_id UUID REFERENCES audit_logs(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id),
    message_id UUID REFERENCES messages(id),

    -- Query analysis
    query_text TEXT NOT NULL,
    query_embedding_model TEXT,
    query_classification TEXT,
    query_complexity_score FLOAT,
    query_language TEXT,

    -- Document access tracking
    documents_accessed UUID[],
    regulatory_authorities_queried TEXT[],
    jurisdictions_accessed TEXT[],
    document_types_accessed TEXT[],

    -- Response generation audit
    response_generation_time_ms FLOAT,
    llm_model_used TEXT,
    llm_temperature FLOAT,
    max_tokens INTEGER,
    token_usage JSONB,

    -- Source citation tracking
    sources_cited UUID[], -- document_chunk IDs
    citation_accuracy_score FLOAT,
    hallucination_risk_score FLOAT,

    -- User interaction patterns
    follow_up_queries INTEGER,
    feedback_provided BOOLEAN,
    session_duration_minutes INTEGER,

    -- Compliance context
    regulatory_topics TEXT[],
    compliance_sensitivity TEXT CHECK (compliance_sensitivity IN ('low', 'medium', 'high', 'critical')),
    cross_border_data_access BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3. Data Lineage and Provenance Tracking

```sql
-- Data lineage tracking for regulatory documents
CREATE TABLE data_lineage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source information
    source_system TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('document', 'database', 'api', 'manual_entry', 'calculation')),
    source_identifier TEXT NOT NULL,
    source_version TEXT,

    -- Target information
    target_system TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_identifier TEXT NOT NULL,
    target_version TEXT,

    -- Transformation details
    transformation_type TEXT NOT NULL CHECK (transformation_type IN (
        'extraction', 'transformation', 'enrichment', 'aggregation', 'anonymization', 'embedding_generation'
    )),
    transformation_rules JSONB,
    data_quality_score FLOAT,
    validation_status TEXT CHECK (validation_status IN ('pending', 'validated', 'rejected', 'warning')),

    -- Processing metadata
    processing_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_by UUID REFERENCES auth.users(id),
    processing_duration_ms FLOAT,
    data_volume_bytes BIGINT,

    -- Regulatory compliance
    data_classification TEXT,
    retention_policy TEXT,
    regulatory_requirements TEXT[],

    -- Chain tracking
    parent_lineage_id UUID REFERENCES data_lineage(id),
    lineage_depth INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for lineage queries
CREATE INDEX CONCURRENTLY idx_data_lineage_source ON data_lineage (source_type, source_identifier);
CREATE INDEX CONCURRENTLY idx_data_lineage_target ON data_lineage (target_type, target_identifier);
CREATE INDEX CONCURRENTLY idx_data_lineage_processing ON data_lineage (processing_timestamp DESC);
CREATE INDEX CONCURRENTLY idx_data_lineage_chain ON data_lineage (parent_lineage_id, lineage_depth);
```

### 4. Security and Access Control Audit

```sql
-- Authentication and session audit
CREATE TABLE authentication_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_log_id UUID REFERENCES audit_logs(id) ON DELETE CASCADE,

    -- Authentication details
    authentication_method TEXT NOT NULL CHECK (authentication_method IN (
        'password', 'mfa_totp', 'mfa_sms', 'sso_saml', 'sso_oauth', 'api_key', 'service_account'
    )),
    authentication_result TEXT NOT NULL CHECK (authentication_result IN ('success', 'failure', 'locked', 'expired')),
    failure_reason TEXT,

    -- Session management
    session_id TEXT,
    session_duration_minutes INTEGER,
    idle_time_minutes INTEGER,
    session_termination_reason TEXT,

    -- Security context
    ip_address INET,
    geolocation JSONB,
    device_fingerprint TEXT,
    risk_score INTEGER CHECK (risk_score >= 0 AND risk_score <= 100),
    anomaly_detected BOOLEAN DEFAULT FALSE,

    -- MFA details
    mfa_challenge_sent TIMESTAMP WITH TIME ZONE,
    mfa_challenge_completed TIMESTAMP WITH TIME ZONE,
    mfa_attempts INTEGER DEFAULT 0,

    -- Password policy compliance
    password_strength_score INTEGER,
    password_policy_violations TEXT[],
    password_age_days INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Authorization and permissions audit
CREATE TABLE authorization_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_log_id UUID REFERENCES audit_logs(id) ON DELETE CASCADE,

    -- Permission details
    permission_requested TEXT NOT NULL,
    permission_granted BOOLEAN NOT NULL,
    denial_reason TEXT,

    -- Role-based access
    user_roles TEXT[],
    effective_permissions TEXT[],
    permission_source TEXT CHECK (permission_source IN ('role', 'direct', 'group', 'inherited')),

    -- Resource access
    resource_sensitivity_level TEXT,
    access_justification TEXT,
    approval_required BOOLEAN DEFAULT FALSE,
    approved_by UUID REFERENCES auth.users(id),
    approval_timestamp TIMESTAMP WITH TIME ZONE,

    -- Privilege escalation tracking
    privilege_escalation BOOLEAN DEFAULT FALSE,
    escalation_method TEXT,
    escalation_approver UUID REFERENCES auth.users(id),
    escalation_expiry TIMESTAMP WITH TIME ZONE,

    -- Context-based access
    location_restriction BOOLEAN DEFAULT FALSE,
    time_restriction BOOLEAN DEFAULT FALSE,
    device_restriction BOOLEAN DEFAULT FALSE,
    network_restriction BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API access and rate limiting audit
CREATE TABLE api_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_log_id UUID REFERENCES audit_logs(id) ON DELETE CASCADE,

    -- API request details
    api_key_id UUID REFERENCES api_keys(id),
    endpoint_path TEXT NOT NULL,
    http_method TEXT NOT NULL,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    response_time_ms FLOAT,

    -- Rate limiting
    rate_limit_policy TEXT,
    requests_in_window INTEGER,
    rate_limit_exceeded BOOLEAN DEFAULT FALSE,
    throttled BOOLEAN DEFAULT FALSE,

    -- API versioning
    api_version TEXT,
    deprecated_endpoint BOOLEAN DEFAULT FALSE,
    deprecation_warning BOOLEAN DEFAULT FALSE,

    -- Usage patterns
    client_application TEXT,
    sdk_version TEXT,
    usage_pattern TEXT,

    -- Security monitoring
    suspicious_activity BOOLEAN DEFAULT FALSE,
    anomaly_score FLOAT,
    blocked_request BOOLEAN DEFAULT FALSE,
    security_rule_triggered TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Automated Audit Functions

### 1. Comprehensive Audit Logging Function

```sql
-- Central audit logging function
CREATE OR REPLACE FUNCTION create_audit_entry(
    p_event_type TEXT,
    p_event_category TEXT,
    p_action_type TEXT,
    p_resource_type TEXT,
    p_resource_id TEXT DEFAULT NULL,
    p_resource_name TEXT DEFAULT NULL,
    p_action_result TEXT DEFAULT 'success',
    p_old_values JSONB DEFAULT NULL,
    p_new_values JSONB DEFAULT NULL,
    p_business_process TEXT DEFAULT NULL,
    p_risk_level TEXT DEFAULT 'low',
    p_additional_metadata JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    audit_id UUID;
    current_user_record RECORD;
    session_info JSONB;
    request_context JSONB;
BEGIN
    -- Generate unique event ID
    audit_id := gen_random_uuid();

    -- Get current user information
    SELECT
        au.id,
        au.email,
        up.role,
        up.organization
    INTO current_user_record
    FROM auth.users au
    LEFT JOIN user_profiles up ON au.id = up.user_id
    WHERE au.id = auth.uid();

    -- Gather session and request context
    session_info := jsonb_build_object(
        'user_agent', current_setting('request.headers', true)::jsonb->'user-agent',
        'referer', current_setting('request.headers', true)::jsonb->'referer',
        'x_forwarded_for', current_setting('request.headers', true)::jsonb->'x-forwarded-for'
    );

    request_context := jsonb_build_object(
        'method', current_setting('request.method', true),
        'path', current_setting('request.path', true),
        'query_string', current_setting('request.query_string', true),
        'jwt_claims', current_setting('request.jwt.claims', true)::jsonb
    );

    -- Insert audit log entry
    INSERT INTO audit_logs (
        id,
        event_id,
        event_type,
        event_category,
        user_id,
        user_email,
        user_role,
        action_type,
        resource_type,
        resource_id,
        resource_name,
        action_result,
        timestamp_utc,
        session_id,
        request_id,
        correlation_id,
        ip_address,
        user_agent,
        client_type,
        old_values,
        new_values,
        business_process,
        risk_level,
        security_context,
        audit_source,
        execution_time_ms,
        changed_fields
    ) VALUES (
        audit_id,
        generate_event_id(p_event_type, current_user_record.id),
        p_event_type,
        p_event_category,
        current_user_record.id,
        current_user_record.email,
        current_user_record.role,
        p_action_type,
        p_resource_type,
        p_resource_id,
        p_resource_name,
        p_action_result,
        NOW(),
        current_setting('app.session_id', true),
        current_setting('app.request_id', true),
        current_setting('app.correlation_id', true),
        inet_client_addr(),
        session_info->>'user_agent',
        determine_client_type(session_info->>'user_agent'),
        p_old_values,
        p_new_values,
        p_business_process,
        p_risk_level,
        jsonb_build_object(
            'session_info', session_info,
            'request_context', request_context,
            'additional_metadata', p_additional_metadata
        ),
        'application',
        extract_execution_time(),
        extract_changed_fields(p_old_values, p_new_values)
    );

    -- Create specialized audit entries based on event type
    PERFORM create_specialized_audit_entries(audit_id, p_event_type, p_additional_metadata);

    RETURN audit_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Helper function to generate unique event IDs
CREATE OR REPLACE FUNCTION generate_event_id(
    p_event_type TEXT,
    p_user_id UUID
) RETURNS TEXT AS $$
BEGIN
    RETURN format('%s-%s-%s-%s',
        p_event_type,
        EXTRACT(EPOCH FROM NOW())::BIGINT,
        substring(p_user_id::TEXT, 1, 8),
        substring(md5(random()::TEXT), 1, 8)
    );
END;
$$ LANGUAGE plpgsql;

-- Function to create specialized audit entries
CREATE OR REPLACE FUNCTION create_specialized_audit_entries(
    p_audit_log_id UUID,
    p_event_type TEXT,
    p_metadata JSONB
) RETURNS VOID AS $$
BEGIN
    CASE
        WHEN p_event_type LIKE '%gdpr%' THEN
            PERFORM create_gdpr_audit_entry(p_audit_log_id, p_metadata);
        WHEN p_event_type LIKE '%query%' OR p_event_type LIKE '%rag%' THEN
            PERFORM create_rag_query_audit_entry(p_audit_log_id, p_metadata);
        WHEN p_event_type LIKE '%auth%' THEN
            PERFORM create_authentication_audit_entry(p_audit_log_id, p_metadata);
        WHEN p_event_type LIKE '%api%' THEN
            PERFORM create_api_audit_entry(p_audit_log_id, p_metadata);
        ELSE
            -- No specialized entry needed
            NULL;
    END CASE;
END;
$$ LANGUAGE plpgsql;
```

### 2. Automated Trigger-Based Auditing

```sql
-- Generic audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    audit_id UUID;
    old_values JSONB;
    new_values JSONB;
    changed_fields TEXT[];
BEGIN
    -- Prepare old and new values
    old_values := CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD)::JSONB ELSE NULL END;
    new_values := CASE WHEN TG_OP = 'INSERT' THEN row_to_json(NEW)::JSONB
                      WHEN TG_OP = 'UPDATE' THEN row_to_json(NEW)::JSONB
                      ELSE NULL END;

    -- Identify changed fields for UPDATE operations
    IF TG_OP = 'UPDATE' THEN
        changed_fields := identify_changed_fields(row_to_json(OLD)::JSONB, row_to_json(NEW)::JSONB);
    END IF;

    -- Create audit entry
    audit_id := create_audit_entry(
        p_event_type := format('table_%s', TG_OP),
        p_event_category := 'data_modification',
        p_action_type := TG_OP,
        p_resource_type := TG_TABLE_NAME,
        p_resource_id := COALESCE(
            (new_values->>'id'),
            (old_values->>'id')
        ),
        p_resource_name := TG_TABLE_NAME,
        p_action_result := 'success',
        p_old_values := old_values,
        p_new_values := new_values,
        p_business_process := determine_business_process(TG_TABLE_NAME),
        p_risk_level := determine_risk_level(TG_TABLE_NAME, TG_OP),
        p_additional_metadata := jsonb_build_object(
            'table_name', TG_TABLE_NAME,
            'operation', TG_OP,
            'changed_fields', changed_fields,
            'trigger_when', TG_WHEN,
            'trigger_level', TG_LEVEL
        )
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply audit triggers to sensitive tables
CREATE TRIGGER audit_documents AFTER INSERT OR UPDATE OR DELETE ON documents
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_user_profiles AFTER INSERT OR UPDATE OR DELETE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_user_roles AFTER INSERT OR UPDATE OR DELETE ON user_roles
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_conversations AFTER INSERT OR UPDATE OR DELETE ON conversations
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_gap_analyses AFTER INSERT OR UPDATE OR DELETE ON gap_analyses
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_reports AFTER INSERT OR UPDATE OR DELETE ON reports
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_regulatory_updates AFTER INSERT OR UPDATE OR DELETE ON regulatory_updates
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
```

### 3. Real-time Compliance Monitoring

```sql
-- Real-time compliance monitoring and alerting
CREATE TABLE compliance_monitoring_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name TEXT NOT NULL UNIQUE,
    rule_description TEXT,

    -- Rule conditions
    event_types TEXT[],
    event_categories TEXT[],
    risk_levels TEXT[],
    user_roles TEXT[],
    resource_types TEXT[],

    -- Condition logic
    condition_expression TEXT, -- SQL WHERE clause
    threshold_value NUMERIC,
    threshold_period_minutes INTEGER,

    -- Alert configuration
    alert_severity TEXT CHECK (alert_severity IN ('info', 'warning', 'critical', 'emergency')),
    alert_recipients UUID[],
    alert_channels TEXT[] DEFAULT ARRAY['email', 'in_app'],

    -- Regulatory context
    regulatory_requirements TEXT[],
    compliance_framework TEXT[],

    -- Rule management
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0
);

-- Function to check compliance rules
CREATE OR REPLACE FUNCTION check_compliance_rules()
RETURNS VOID AS $$
DECLARE
    rule_record RECORD;
    violation_count INTEGER;
    alert_id UUID;
BEGIN
    FOR rule_record IN
        SELECT * FROM compliance_monitoring_rules WHERE is_active = TRUE
    LOOP
        -- Check if rule conditions are met
        EXECUTE format('
            SELECT COUNT(*)
            FROM audit_logs
            WHERE %s
                AND timestamp_utc > NOW() - INTERVAL ''%s minutes''
                AND (%s IS NULL OR event_type = ANY(%L))
                AND (%s IS NULL OR event_category = ANY(%L))
                AND (%s IS NULL OR risk_level = ANY(%L))
        ',
            COALESCE(rule_record.condition_expression, 'TRUE'),
            rule_record.threshold_period_minutes,
            'event_types', rule_record.event_types,
            'event_categories', rule_record.event_categories,
            'risk_levels', rule_record.risk_levels
        ) INTO violation_count;

        -- Trigger alert if threshold exceeded
        IF violation_count >= rule_record.threshold_value THEN
            alert_id := create_compliance_alert(rule_record.id, violation_count);

            -- Update rule statistics
            UPDATE compliance_monitoring_rules
            SET last_triggered_at = NOW(),
                trigger_count = trigger_count + 1
            WHERE id = rule_record.id;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Schedule compliance monitoring
SELECT cron.schedule('compliance-monitoring', '*/5 * * * *', 'SELECT check_compliance_rules();');
```

## Regulatory Reporting and Analytics

### 1. GDPR Compliance Reports

```sql
-- GDPR Article 30 - Records of Processing Activities
CREATE OR REPLACE FUNCTION generate_gdpr_processing_report(
    p_start_date DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
    p_end_date DATE DEFAULT CURRENT_DATE
) RETURNS TABLE (
    controller_name TEXT,
    processing_purpose TEXT,
    data_categories TEXT,
    legal_basis TEXT,
    retention_period TEXT,
    processing_count BIGINT,
    data_subject_requests BIGINT,
    breach_incidents BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        gpl.controller_name,
        unnest(gpl.processing_purposes) as processing_purpose,
        array_to_string(gpl.personal_data_categories, ', ') as data_categories,
        gpl.lawful_basis as legal_basis,
        format('%s months', gpl.retention_period_months) as retention_period,
        COUNT(*) as processing_count,
        SUM(CASE WHEN gpl.data_subject_request_type IS NOT NULL THEN 1 ELSE 0 END) as data_subject_requests,
        SUM(CASE WHEN gpl.breach_detected THEN 1 ELSE 0 END) as breach_incidents
    FROM gdpr_processing_logs gpl
    JOIN audit_logs al ON gpl.audit_log_id = al.id
    WHERE al.timestamp_utc::DATE BETWEEN p_start_date AND p_end_date
    GROUP BY
        gpl.controller_name,
        unnest(gpl.processing_purposes),
        gpl.personal_data_categories,
        gpl.lawful_basis,
        gpl.retention_period_months
    ORDER BY processing_count DESC;
END;
$$ LANGUAGE plpgsql;
```

### 2. Financial Services Reporting

```sql
-- MiFID II Transaction Reporting
CREATE OR REPLACE FUNCTION generate_mifid_transaction_report(
    p_start_date DATE DEFAULT CURRENT_DATE - INTERVAL '1 month',
    p_end_date DATE DEFAULT CURRENT_DATE
) RETURNS TABLE (
    transaction_date DATE,
    transaction_type TEXT,
    client_classification TEXT,
    transaction_count BIGINT,
    total_volume DECIMAL,
    best_execution_breaches BIGINT,
    conduct_risk_incidents BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        al.timestamp_utc::DATE as transaction_date,
        fsa.transaction_type,
        fsa.client_classification,
        COUNT(*) as transaction_count,
        COALESCE(SUM((fsa.execution_quality_data->>'volume')::DECIMAL), 0) as total_volume,
        SUM(CASE WHEN fsa.execution_quality_data->>'best_execution_breach' = 'true' THEN 1 ELSE 0 END) as best_execution_breaches,
        SUM(CASE WHEN fsa.conduct_risk_indicators->>'risk_score'::INTEGER > 70 THEN 1 ELSE 0 END) as conduct_risk_incidents
    FROM financial_services_audit fsa
    JOIN audit_logs al ON fsa.audit_log_id = al.id
    WHERE al.timestamp_utc::DATE BETWEEN p_start_date AND p_end_date
    GROUP BY
        al.timestamp_utc::DATE,
        fsa.transaction_type,
        fsa.client_classification
    ORDER BY transaction_date DESC, transaction_count DESC;
END;
$$ LANGUAGE plpgsql;
```

### 3. Operational Risk Reporting

```sql
-- Basel III Operational Risk Event Summary
CREATE OR REPLACE FUNCTION generate_operational_risk_report(
    p_start_date DATE DEFAULT CURRENT_DATE - INTERVAL '3 months',
    p_end_date DATE DEFAULT CURRENT_DATE
) RETURNS TABLE (
    event_category TEXT,
    event_count BIGINT,
    total_gross_loss DECIMAL,
    total_recovery DECIMAL,
    total_net_loss DECIMAL,
    avg_response_time_minutes NUMERIC,
    regulatory_reports_required BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ore.event_category,
        COUNT(*) as event_count,
        SUM(ore.gross_loss_amount) as total_gross_loss,
        SUM(ore.recovery_amount) as total_recovery,
        SUM(ore.net_loss_amount) as total_net_loss,
        AVG(ore.response_time_minutes) as avg_response_time_minutes,
        SUM(CASE WHEN ore.regulatory_reporting_required THEN 1 ELSE 0 END) as regulatory_reports_required
    FROM operational_risk_events ore
    JOIN audit_logs al ON ore.audit_log_id = al.id
    WHERE al.timestamp_utc::DATE BETWEEN p_start_date AND p_end_date
    GROUP BY ore.event_category
    ORDER BY total_net_loss DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql;
```

## Data Retention and Archival

### 1. Regulatory Data Retention Management

```sql
-- Data retention policy implementation
CREATE TABLE retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_name TEXT NOT NULL UNIQUE,
    table_name TEXT NOT NULL,

    -- Retention rules
    retention_period_years INTEGER NOT NULL,
    retention_trigger_field TEXT NOT NULL, -- Field used to determine age

    -- Regulatory basis
    regulatory_requirement TEXT NOT NULL,
    jurisdiction TEXT,
    regulation_reference TEXT,

    -- Archive configuration
    archive_before_delete BOOLEAN DEFAULT TRUE,
    archive_location TEXT,
    archive_format TEXT DEFAULT 'jsonl',

    -- Policy status
    is_active BOOLEAN DEFAULT TRUE,
    last_applied TIMESTAMP WITH TIME ZONE,
    next_application TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Insert standard banking retention policies
INSERT INTO retention_policies (
    policy_name,
    table_name,
    retention_period_years,
    retention_trigger_field,
    regulatory_requirement,
    jurisdiction,
    regulation_reference
) VALUES
    ('audit_logs_banking', 'audit_logs', 7, 'timestamp_utc', 'Banking record keeping', 'EU', 'CRD IV Article 74'),
    ('gdpr_processing_logs', 'gdpr_processing_logs', 3, 'created_at', 'GDPR retention', 'EU', 'GDPR Article 5(1)(e)'),
    ('financial_services_audit', 'financial_services_audit', 5, 'created_at', 'MiFID II records', 'EU', 'MiFID II Article 25(2)'),
    ('operational_risk_events', 'operational_risk_events', 10, 'created_at', 'Basel III operational risk', 'Global', 'Basel III Pillar 1'),
    ('rag_query_audit', 'rag_query_audit', 2, 'created_at', 'System usage logs', 'Internal', 'Internal Policy'),
    ('authentication_audit', 'authentication_audit', 1, 'created_at', 'Access logs', 'Internal', 'Security Policy');

-- Function to apply retention policies
CREATE OR REPLACE FUNCTION apply_retention_policies()
RETURNS JSONB AS $$
DECLARE
    policy_record RECORD;
    deletion_sql TEXT;
    archive_sql TEXT;
    deleted_count INTEGER;
    archived_count INTEGER;
    results JSONB := '[]'::JSONB;
    policy_result JSONB;
BEGIN
    FOR policy_record IN
        SELECT * FROM retention_policies
        WHERE is_active = TRUE
        AND (next_application IS NULL OR next_application <= NOW())
    LOOP
        BEGIN
            -- Archive records before deletion if required
            IF policy_record.archive_before_delete THEN
                archive_sql := format(
                    'INSERT INTO %I_archive SELECT * FROM %I WHERE %I < NOW() - INTERVAL ''%s years''',
                    policy_record.table_name,
                    policy_record.table_name,
                    policy_record.retention_trigger_field,
                    policy_record.retention_period_years
                );

                EXECUTE archive_sql;
                GET DIAGNOSTICS archived_count = ROW_COUNT;
            ELSE
                archived_count := 0;
            END IF;

            -- Delete records older than retention period
            deletion_sql := format(
                'DELETE FROM %I WHERE %I < NOW() - INTERVAL ''%s years''',
                policy_record.table_name,
                policy_record.retention_trigger_field,
                policy_record.retention_period_years
            );

            EXECUTE deletion_sql;
            GET DIAGNOSTICS deleted_count = ROW_COUNT;

            -- Update policy application timestamp
            UPDATE retention_policies
            SET last_applied = NOW(),
                next_application = NOW() + INTERVAL '1 month'
            WHERE id = policy_record.id;

            -- Record policy execution
            policy_result := jsonb_build_object(
                'policy_name', policy_record.policy_name,
                'table_name', policy_record.table_name,
                'archived_count', archived_count,
                'deleted_count', deleted_count,
                'status', 'success',
                'applied_at', NOW()
            );

            results := results || policy_result;

            -- Audit the retention policy application
            PERFORM create_audit_entry(
                p_event_type := 'retention_policy_applied',
                p_event_category := 'compliance',
                p_action_type := 'DELETE',
                p_resource_type := policy_record.table_name,
                p_action_result := 'success',
                p_business_process := 'data_retention',
                p_risk_level := 'medium',
                p_additional_metadata := jsonb_build_object(
                    'policy_id', policy_record.id,
                    'archived_records', archived_count,
                    'deleted_records', deleted_count,
                    'retention_period_years', policy_record.retention_period_years,
                    'regulatory_requirement', policy_record.regulatory_requirement
                )
            );

        EXCEPTION
            WHEN OTHERS THEN
                -- Log retention policy failure
                policy_result := jsonb_build_object(
                    'policy_name', policy_record.policy_name,
                    'table_name', policy_record.table_name,
                    'status', 'failed',
                    'error_message', SQLERRM,
                    'applied_at', NOW()
                );

                results := results || policy_result;

                PERFORM create_audit_entry(
                    p_event_type := 'retention_policy_failed',
                    p_event_category := 'compliance',
                    p_action_type := 'DELETE',
                    p_resource_type := policy_record.table_name,
                    p_action_result := 'failure',
                    p_business_process := 'data_retention',
                    p_risk_level := 'high',
                    p_additional_metadata := jsonb_build_object(
                        'policy_id', policy_record.id,
                        'error_message', SQLERRM,
                        'retention_period_years', policy_record.retention_period_years
                    )
                );
        END;
    END LOOP;

    RETURN results;
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly retention policy application
SELECT cron.schedule('retention-policies', '0 2 1 * *', 'SELECT apply_retention_policies();');
```

## Security and Tamper Detection

### 1. Audit Log Integrity Protection

```sql
-- Hash chain for audit log integrity
CREATE TABLE audit_integrity_chain (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    block_number BIGINT NOT NULL UNIQUE,

    -- Block content
    audit_log_ids UUID[] NOT NULL,
    block_hash TEXT NOT NULL,
    previous_block_hash TEXT,

    -- Merkle tree root for batch verification
    merkle_root TEXT NOT NULL,

    -- Block metadata
    block_size INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Function to create integrity blocks
CREATE OR REPLACE FUNCTION create_audit_integrity_block()
RETURNS UUID AS $$
DECLARE
    block_id UUID;
    next_block_number BIGINT;
    previous_hash TEXT;
    audit_ids UUID[];
    block_hash_value TEXT;
    merkle_root_value TEXT;
BEGIN
    -- Get next block number and previous hash
    SELECT COALESCE(MAX(block_number), 0) + 1,
           COALESCE((SELECT block_hash FROM audit_integrity_chain ORDER BY block_number DESC LIMIT 1), '0')
    INTO next_block_number, previous_hash;

    -- Get unblocked audit log entries
    SELECT array_agg(id)
    INTO audit_ids
    FROM audit_logs
    WHERE NOT EXISTS (
        SELECT 1 FROM audit_integrity_chain aic
        WHERE audit_logs.id = ANY(aic.audit_log_ids)
    )
    ORDER BY timestamp_utc
    LIMIT 1000; -- Block size limit

    -- Calculate block hash and Merkle root
    block_hash_value := calculate_block_hash(audit_ids, previous_hash);
    merkle_root_value := calculate_merkle_root(audit_ids);

    -- Create integrity block
    INSERT INTO audit_integrity_chain (
        block_number,
        audit_log_ids,
        block_hash,
        previous_block_hash,
        merkle_root,
        block_size,
        created_by
    ) VALUES (
        next_block_number,
        audit_ids,
        block_hash_value,
        previous_hash,
        merkle_root_value,
        array_length(audit_ids, 1),
        auth.uid()
    ) RETURNING id INTO block_id;

    RETURN block_id;
END;
$$ LANGUAGE plpgsql;

-- Schedule regular integrity block creation
SELECT cron.schedule('audit-integrity-blocks', '0 */6 * * *', 'SELECT create_audit_integrity_block();');
```

### 2. Anomaly Detection and Monitoring

```sql
-- Audit anomaly detection
CREATE TABLE audit_anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Anomaly identification
    anomaly_type TEXT NOT NULL CHECK (anomaly_type IN (
        'unusual_access_pattern', 'privilege_escalation', 'data_exfiltration',
        'mass_deletion', 'off_hours_access', 'geographic_anomaly',
        'failed_authentication_spike', 'suspicious_query_pattern'
    )),

    -- Detection details
    detection_algorithm TEXT,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    severity_level TEXT CHECK (severity_level IN ('low', 'medium', 'high', 'critical')),

    -- Context information
    affected_user_id UUID REFERENCES auth.users(id),
    related_audit_logs UUID[],
    time_window_start TIMESTAMP WITH TIME ZONE,
    time_window_end TIMESTAMP WITH TIME ZONE,

    -- Anomaly metrics
    baseline_value FLOAT,
    observed_value FLOAT,
    deviation_percentage FLOAT,

    -- Investigation status
    investigation_status TEXT DEFAULT 'new' CHECK (investigation_status IN (
        'new', 'investigating', 'confirmed', 'false_positive', 'resolved'
    )),
    assigned_investigator UUID REFERENCES auth.users(id),
    investigation_notes TEXT,
    resolution_action TEXT,

    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    investigated_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Function to detect audit anomalies
CREATE OR REPLACE FUNCTION detect_audit_anomalies()
RETURNS INTEGER AS $$
DECLARE
    anomaly_count INTEGER := 0;
    user_record RECORD;
    baseline_queries FLOAT;
    current_queries FLOAT;
    deviation FLOAT;
BEGIN
    -- Detect unusual query patterns
    FOR user_record IN
        SELECT user_id, COUNT(*) as query_count
        FROM audit_logs
        WHERE timestamp_utc > NOW() - INTERVAL '1 hour'
        AND event_type LIKE '%query%'
        GROUP BY user_id
    LOOP
        -- Calculate baseline (average queries per hour over last 30 days)
        SELECT AVG(hourly_queries) INTO baseline_queries
        FROM (
            SELECT DATE_TRUNC('hour', timestamp_utc) as hour, COUNT(*) as hourly_queries
            FROM audit_logs
            WHERE user_id = user_record.user_id
            AND timestamp_utc > NOW() - INTERVAL '30 days'
            AND timestamp_utc < NOW() - INTERVAL '1 hour'
            AND event_type LIKE '%query%'
            GROUP BY DATE_TRUNC('hour', timestamp_utc)
        ) baseline;

        current_queries := user_record.query_count;

        -- Detect significant deviation (>300% of baseline)
        IF baseline_queries > 0 AND current_queries > baseline_queries * 3 THEN
            deviation := (current_queries - baseline_queries) / baseline_queries * 100;

            INSERT INTO audit_anomalies (
                anomaly_type,
                detection_algorithm,
                confidence_score,
                severity_level,
                affected_user_id,
                baseline_value,
                observed_value,
                deviation_percentage,
                time_window_start,
                time_window_end
            ) VALUES (
                'suspicious_query_pattern',
                'statistical_deviation',
                LEAST(deviation / 500, 1.0), -- Cap confidence at 1.0
                CASE
                    WHEN deviation > 1000 THEN 'critical'
                    WHEN deviation > 500 THEN 'high'
                    WHEN deviation > 300 THEN 'medium'
                    ELSE 'low'
                END,
                user_record.user_id,
                baseline_queries,
                current_queries,
                deviation,
                NOW() - INTERVAL '1 hour',
                NOW()
            );

            anomaly_count := anomaly_count + 1;
        END IF;
    END LOOP;

    RETURN anomaly_count;
END;
$$ LANGUAGE plpgsql;

-- Schedule anomaly detection
SELECT cron.schedule('audit-anomaly-detection', '*/15 * * * *', 'SELECT detect_audit_anomalies();');
```

## Performance Optimization

### 1. Audit Log Partitioning

```sql
-- Partition audit logs by month for better performance
CREATE TABLE audit_logs_template (LIKE audit_logs INCLUDING ALL);

-- Create monthly partitions
CREATE OR REPLACE FUNCTION create_audit_log_partitions(
    p_start_date DATE,
    p_end_date DATE
) RETURNS INTEGER AS $$
DECLARE
    partition_date DATE;
    partition_name TEXT;
    partition_count INTEGER := 0;
BEGIN
    partition_date := DATE_TRUNC('month', p_start_date);

    WHILE partition_date <= p_end_date LOOP
        partition_name := format('audit_logs_%s', TO_CHAR(partition_date, 'YYYY_MM'));

        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_logs
            FOR VALUES FROM (%L) TO (%L)
        ', partition_name, partition_date, partition_date + INTERVAL '1 month');

        partition_count := partition_count + 1;
        partition_date := partition_date + INTERVAL '1 month';
    END LOOP;

    RETURN partition_count;
END;
$$ LANGUAGE plpgsql;

-- Create partitions for next 12 months
SELECT create_audit_log_partitions(CURRENT_DATE, CURRENT_DATE + INTERVAL '12 months');
```

### 2. Index Optimization

```sql
-- Specialized indexes for audit log queries
CREATE INDEX CONCURRENTLY idx_audit_logs_regulatory_reporting
ON audit_logs (timestamp_utc DESC, regulatory_impact, risk_level)
WHERE array_length(regulatory_impact, 1) > 0;

CREATE INDEX CONCURRENTLY idx_audit_logs_security_events
ON audit_logs (timestamp_utc DESC, event_category, action_result)
WHERE event_category IN ('security', 'authentication', 'authorization');

CREATE INDEX CONCURRENTLY idx_audit_logs_compliance_category
ON audit_logs (compliance_category, timestamp_utc DESC)
WHERE compliance_category IS NOT NULL;

-- Composite index for common audit queries
CREATE INDEX CONCURRENTLY idx_audit_logs_user_activity_composite
ON audit_logs (user_id, timestamp_utc DESC, event_type, action_result);

-- Index for data lineage queries
CREATE INDEX CONCURRENTLY idx_data_lineage_regulatory_compliance
ON data_lineage (processing_timestamp DESC, regulatory_requirements)
WHERE array_length(regulatory_requirements, 1) > 0;
```

This comprehensive audit trail specification ensures full regulatory compliance while providing the necessary infrastructure for forensic analysis, regulatory reporting, and continuous compliance monitoring in the Banking RAG Compliance System.