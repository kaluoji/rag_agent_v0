# .hooks/design-validation/validate.sh
#!/bin/bash

echo "📋 Design Synthesis Validation Hook"

# Verificar MANIFEST.md completeness
validate_manifest() {
    local manifest_file="./research_outputs/MANIFEST.md"
    
    if [ ! -f "$manifest_file" ]; then
        echo "❌ MANIFEST.md not found"
        exit 1
    fi
    
    # Verificar que mapea 100% de requerimientos del PRD
    local prd_requirements=$(grep -c "requirement\|feature\|user story" "./research_outputs/prd_document.md")
    local manifest_mappings=$(grep -c "requirement\|feature\|user story" "$manifest_file")
    
    if [ "$manifest_mappings" -ge "$prd_requirements" ]; then
        echo "✅ MANIFEST.md maps all PRD requirements"
    else
        echo "❌ MANIFEST.md missing requirement mappings ($manifest_mappings/$prd_requirements)"
        exit 1
    fi
}

# Verificar contradicciones entre agentes
check_contradictions() {
    echo "Checking for contradictions between agent outputs..."
    
    # Ejemplo: verificar que todos usan la misma base de datos
    local db_choices=$(grep -h -i "database\|postgresql\|mysql" ./research_outputs/*.md | sort | uniq -c)
    echo "Database technology choices: $db_choices"
    
    # Aquí puedes añadir más verificaciones específicas
}

validate_manifest
check_contradictions

echo "✅ Design Synthesis validation passed"