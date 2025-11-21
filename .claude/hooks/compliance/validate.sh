# .hooks/compliance/validate.sh
#!/bin/bash

echo "⚖️ Compliance Continuous Validation Hook"

# Verificar audit trails
check_audit_trails() {
    echo "Checking audit trail implementation..."
    
    # Verificar que existe tabla de audit logs
    if grep -q "audit_log\|audit_trail" src/database/schema.sql; then
        echo "✅ Audit trail table found in schema"
    else
        echo "❌ Audit trail table missing from schema"
        exit 1
    fi
    
    # Verificar que operaciones críticas están siendo logged
    local critical_operations=("user_login" "document_upload" "query_execution" "report_generation")
    for operation in "${critical_operations[@]}"; do
        if grep -r -q "$operation" src/ --include="*.js" --include="*.ts" --include="*.py"; then
            echo "✅ $operation: Logging implemented"
        else
            echo "❌ $operation: Missing audit logging"
            exit 1
        fi
    done
}

# Verificar protección de datos sensibles
check_data_protection() {
    echo "Checking data protection implementation..."
    
    # Verificar que no hay secrets hardcodeados
    if grep -r -E "(password|secret|key)\s*=\s*['\"][^'\"]+['\"]" src/ --include="*.js" --include="*.ts" --include="*.py"; then
        echo "❌ Hardcoded secrets found"
        exit 1
    else
        echo "✅ No hardcoded secrets detected"
    fi
}

check_audit_trails
check_data_protection

echo "✅ Compliance validation passed"
