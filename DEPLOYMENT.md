# Deployment and Operations

## Services

Start MongoDB, Qdrant, and Ollama before FastAPI. Pull:

```powershell
ollama pull llama3.2
ollama pull nomic-embed-text
```

Development commands:

```powershell
cd backend
uvicorn app.main:app --reload

cd frontend
npm run dev
```

Production commands:

```powershell
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

cd frontend
npm ci
npm run build
npm run start
```

Dockerfiles are provided for the frontend and backend. MongoDB, Qdrant, and Ollama remain deployment dependencies; Ollama is not forced into a container.

## Troubleshooting

- Login failure: verify JWT secret, bootstrap account, account active state, and MongoDB.
- CORS failure: add the exact frontend origin to `CORS_ALLOWED_ORIGINS`.
- Qdrant degraded: verify port 6333 and collection configuration, then run vector backfill.
- Ollama failure: verify port 11434 and required models.
- Upload failure: verify supported type, 5 MB limit, and duplicate checksum.
- Port conflict: change the service port and update frontend/API/CORS variables together.

Health checks:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
```

After ingestion changes, Admins can run chunk, embedding, and vector backfills from the Maintenance page.
