# .hooks/research-quality/validate.sh
#!/bin/bash

echo "🎯 Research Quality Gate Hook"

validate_research_output() {
    local agent=$1
    local output_file="./research_outputs/${agent}_output.md"
    
    if [ ! -f "$output_file" ]; then
        echo "❌ $agent: Output file missing"
        return 1
    fi
    
    # Verificar que no hay placeholders
    if grep -q -i "TODO\|PLACEHOLDER\|TBD\|FIXME" "$output_file"; then
        echo "❌ $agent: Contains placeholders or TODOs"
        return 1
    fi
    
    # Verificar especificaciones concretas
    if grep -q -i "concrete\|specific\|exact" "$output_file"; then
        echo "✅ $agent: Contains concrete specifications"
    else
        echo "⚠️  $agent: May lack concrete specifications"
    fi
    
    # Verificar justificaciones técnicas
    if grep -q -i "because\|rationale\|justification\|reason" "$output_file"; then
        echo "✅ $agent: Includes technical justifications"
    else
        echo "❌ $agent: Missing technical justifications"
        return 1
    fi
    
    return 0
}

# Validar todos los outputs de research
for agent in prd-writer postgres-rag-architect rag-strategy-researcher scraping-strategy-researcher tech-stack-researcher architecture-designer integration-researcher; do
    validate_research_output "$agent"
done

echo "✅ Research Quality Gate passed"