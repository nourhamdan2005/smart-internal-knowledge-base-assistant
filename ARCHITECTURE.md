# Architecture

## Authentication

```mermaid
sequenceDiagram
  participant U as User
  participant F as Frontend
  participant A as FastAPI
  participant M as MongoDB
  U->>F: Email and password
  F->>A: POST /auth/login
  A->>M: Load active user
  A-->>F: Signed access token
  F->>A: Bearer token
  A->>M: Reload current role and active state
  A-->>F: Authorized response
```

Tokens never determine current authorization alone; protected requests reload the user.

## Ingestion and retrieval

```mermaid
flowchart TD
  File[Supported file] --> Extract[Extract text]
  Extract --> Document[(MongoDB document)]
  Document --> Chunk[Chunk content]
  Chunk --> Embed[Ollama embedding]
  Embed --> MongoChunks[(MongoDB chunks)]
  MongoChunks --> Vector[Qdrant synchronization]
  Question --> Keyword[MongoDB keyword search]
  Question --> QueryEmbed[Question embedding]
  QueryEmbed --> Semantic[Qdrant semantic search]
  Keyword --> Rank[Hybrid rank and diversity]
  Semantic --> Hydrate[Hydrate active MongoDB chunks]
  Hydrate --> Rank
  Rank --> Answer[Ollama grounded answer]
```

## Frontend

```mermaid
flowchart LR
  Routes[Next.js App Router] --> Shell[Authenticated app shell]
  Shell --> Providers[Auth, Query, Theme, Preferences]
  Shell --> Features[Feature folders]
  Features --> Client[Typed Axios client]
  Features --> Design[Shared design system]
  Permissions[Central permission matrix] --> Shell
  Permissions --> Features
```

Feature folders own API contracts and interactive views. Shared providers own session, query behavior, themes, and validated local preferences.

## Maintenance

Admin-confirmed backfills create missing chunks or embeddings and synchronize eligible vectors. Results are returned synchronously; the frontend keeps only a clearly labeled browser-session history.
