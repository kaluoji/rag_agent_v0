---
name: rag-docker-dev
description: Starts the complete RAG stack (backend and frontend) using Docker Compose. Ideal for integrated development and testing without manual setup. Use when you want to run the entire application with a single command.
---

# RAG Docker Development Stack

## Instructions

When the user wants to run the full stack with Docker:

1. **Check Docker availability**
   - Verify Docker is installed: `docker --version`
   - Verify Docker Compose: `docker-compose --version`
   - Ensure Docker daemon is running

2. **Prepare environment**
   - Verify `docker-compose.yml` exists in project root
   - Check that `.env` file is in backend directory with API keys
   - Verify all required config is in place

3. **Start the stack**
   - Run: `docker-compose up`
   - Wait for both services to initialize:
     - Backend (FastAPI on port 8000)
     - Frontend (Vite on port 5173)

4. **Monitor startup**
   - Watch logs for any errors
   - Wait until both services are healthy
   - Confirm ports are accessible

5. **Provide access information**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

6. **Stopping the stack**
   - To stop: `docker-compose stop`
   - To remove containers: `docker-compose rm`
   - To view logs: `docker logs <container_name>`

## Examples

- "Start the development stack"
- "Run the full application with Docker"
- "I want to use Docker for development"
- "Start both backend and frontend"
- "Show me Docker logs"
