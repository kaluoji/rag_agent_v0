---
name: rag-frontend-setup
description: Sets up the React/Vite frontend environment. Installs Node dependencies and configures environment variables. Use for initial frontend setup or when preparing frontend development on a new machine.
---

# RAG Frontend Setup

## Instructions

When the user needs to setup the frontend:

1. **Navigate to frontend directory**
   - Go to `frontend/` folder

2. **Install Node dependencies**
   - Run: `npm install`
   - Wait for all packages to install
   - Verify critical packages: @mui/material, axios, zustand, @tiptap/react, mammoth, react-router-dom

3. **Setup .env file**
   - Create `frontend/.env` with:
     ```
     VITE_API_URL=http://localhost:8000
     ```
   - Update URL if backend is on different port/host

4. **Verify setup**
   - Check npm version
   - List installed packages
   - Verify Vite is available

5. **Provide development commands**
   - Development: `npm run dev` (runs on http://localhost:5173)
   - Build: `npm run build`
   - Lint: `npm run lint`

6. **Frontend ready**
   - Confirm setup is complete and ready for development

## Examples

- "Setup the frontend"
- "Install React dependencies"
- "Configure the Vite development server"
- "Prepare frontend for development"
