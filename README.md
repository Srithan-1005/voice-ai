# voice-ai

## Deploying on Vercel

The root `vercel.json` deploys the `backend` FastAPI app and `frontend` Vite app as
services in one Vercel project. Requests under `/api/*` (including `/api/health`)
are routed to the backend; all other paths are routed to the frontend. The frontend
uses same-origin API requests in production and keeps `VITE_API_URL` available for
local development.

The backend does not call another service in this repository, so this configuration
does not declare service bindings.