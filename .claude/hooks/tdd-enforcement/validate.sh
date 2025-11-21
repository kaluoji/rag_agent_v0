# .hooks/tdd-enforcement/validate.sh
#!/bin/bash

echo "🔴🟢✅ TDD Discipline Enforcement Hook"

# Verificar que estamos en la fase correcta del ciclo TDD
check_tdd_phase() {
    local phase_file=".hooks/logs/current_tdd_phase.txt"
    
    if [ ! -f "$phase_file" ]; then
        echo "RED" > "$phase_file"
        echo "🔴 Starting RED phase - Write failing test first"
        return 0
    fi
    
    local current_phase=$(cat "$phase_file")
    
    case $current_phase in
        "RED")
            # Verificar que existe al menos un test que falla
            if npm test 2>&1 | grep -q "FAIL\|failed"; then
                echo "🟢 Moving to GREEN phase - Implement minimal solution"
                echo "GREEN" > "$phase_file"
            else
                echo "❌ RED phase incomplete - No failing tests found"
                exit 1
            fi
            ;;
        "GREEN")
            # Verificar que tests ahora pasan
            if npm test 2>&1 | grep -q "PASS\|passed"; then
                echo "✅ Moving to VERIFY phase - User validation required"
                echo "VERIFY" > "$phase_file"
            else
                echo "❌ GREEN phase incomplete - Tests still failing"
                exit 1
            fi
            ;;
        "VERIFY")
            # Requiere aprobación manual del usuario
            echo "✅ VERIFY phase - Please confirm feature works as expected"
            read -p "Does the feature work correctly? (y/n): " user_approval
            if [ "$user_approval" = "y" ]; then
                echo "🔴 Starting new RED phase for next feature"
                echo "RED" > "$phase_file"
            else
                echo "❌ User rejected feature - staying in GREEN phase"
                echo "GREEN" > "$phase_file"
                exit 1
            fi
            ;;
    esac
}

# Verificar cobertura de tests
check_test_coverage() {
    if command -v nyc &> /dev/null; then
        local coverage=$(nyc report --reporter=text-summary | grep "Lines" | awk '{print $3}' | sed 's/%//')
        local min_coverage=$(yq '.quality_gates.test_coverage_minimum' .hooks/config/hooks.yaml | sed 's/%//')
        
        if [ "$coverage" -ge "$min_coverage" ]; then
            echo "✅ Test coverage: $coverage% (min: $min_coverage%)"
        else
            echo "❌ Test coverage insufficient: $coverage% (min: $min_coverage%)"
            exit 1
        fi
    fi
}

check_tdd_phase
check_test_coverage

echo "✅ TDD Discipline enforcement passed"
