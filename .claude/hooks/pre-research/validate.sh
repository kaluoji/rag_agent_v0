# .hooks/pre-research/validate.sh
#!/bin/bash
source .hooks/hook-manager.sh

echo "🔍 Pre-Research Validation Hook"

# Verificar conectividad con servicios oficiales
check_service_connectivity() {
    local service=$1
    local url=$2
    
    if curl -s --head "$url" | head -n 1 | grep -q "200 OK"; then
        echo "✅ $service: Connectivity OK"
        return 0
    else
        echo "❌ $service: Connection failed"
        return 1
    fi
}

# Verificar fuentes oficiales
echo "Checking official documentation sources..."
check_service_connectivity "Azure OpenAI Docs" "https://docs.microsoft.com/azure/cognitive-services/openai/"
check_service_connectivity "Supabase Docs" "https://supabase.com/docs"
check_service_connectivity "Browserbase Docs" "https://docs.browserbase.com"

# Verificar que agentes tienen scope definido
echo "Validating agent scope definitions..."
for agent in prd-writer postgres-rag-architect rag-strategy-researcher scraping-strategy-researcher tech-stack-researcher architecture-designer integration-researcher; do
    if [ -f ".claude/agents/$agent.md" ]; then
        if grep -q "description:" ".claude/agents/$agent.md"; then
            echo "✅ $agent: Scope defined"
        else
            echo "❌ $agent: Missing scope definition"
            exit 1
        fi
    else
        echo "❌ $agent: Agent file not found"
        exit 1
    fi
done

echo "✅ Pre-Research validation passed"