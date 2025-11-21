# .claude/hooks/validate-all.sh
#!/bin/bash

echo "🚀 Running complete validation suite..."

# Ejecutar todos los hooks en orden
.claude/hooks/hook-manager.sh run_hook "pre-research"
.claude/hooks/hook-manager.sh run_hook "research-quality"
.claude/hooks/hook-manager.sh run_hook "design-validation"
.claude/hooks/hook-manager.sh run_hook "pre-implementation"
.claude/hooks/hook-manager.sh run_hook "tdd-enforcement"
.claude/hooks/hook-manager.sh run_hook "compliance"

echo "✅ All validation hooks passed successfully"
echo "📊 Validation summary:"
if [ -f ".claude/hooks/logs/hooks.log" ]; then
    tail -20 .claude/hooks/logs/hooks.log
else
    echo "No log entries yet"
fi