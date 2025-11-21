---
name: rag-test-backend
description: Runs backend tests using pytest to validate code changes. Supports running all tests or specific test files. Use for validating backend functionality and ensuring tests pass before commits.
---

# RAG Backend Testing

## Instructions

When the user wants to run backend tests:

1. **Navigate to backend**
   - Go to `backend/` directory

2. **Activate virtual environment**
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. **Run tests**
   - **All tests**: `pytest`
   - **Specific test file**: `pytest tests/test_integration_complete.py`
   - **Verbose output**: `pytest -v`
   - **Short traceback**: `pytest --tb=short`
   - **Stop on first failure**: `pytest -x`
   - **Combined**: `pytest tests/test_integration_complete.py -v --tb=short -x`

4. **Interpret results**
   - Show passed/failed counts
   - Highlight any failures with clear error messages
   - Provide suggestions for fixing failures

5. **Coverage (optional)**
   - Run with coverage: `pytest --cov=app tests/`
   - Show coverage report

6. **Report findings**
   - Summary of test results
   - Recommendations for next steps

## Examples

- "Run backend tests"
- "Run the integration tests"
- "Test my changes"
- "Check if tests pass"
- "Run a specific test file"
- "Show test coverage"

## Testing Notes

- Integration tests are in `backend/tests/`
- Test structure mirrors `backend/` directory
- Uses `pytest-asyncio` for async tests
- Uses mocking for external dependencies
