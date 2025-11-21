# .hooks/hook-manager.sh
#!/bin/bash
HOOKS_DIR=".hooks"
LOGS_DIR="$HOOKS_DIR/logs"
CONFIG_FILE="$HOOKS_DIR/config/hooks.yaml"

log_hook() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1: $2" >> "$LOGS_DIR/hooks.log"
}

run_hook() {
    local hook_name=$1
    local hook_script="$HOOKS_DIR/$hook_name/validate.sh"
    
    if [ -f "$hook_script" ]; then
        log_hook "RUNNING" "$hook_name"
        bash "$hook_script"
        local result=$?
        if [ $result -eq 0 ]; then
            log_hook "PASSED" "$hook_name"
        else
            log_hook "FAILED" "$hook_name"
            exit 1
        fi
    fi
}