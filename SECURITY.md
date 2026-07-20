# Security

- Passwords are Argon2-hashed and never returned by the API.
- JWTs expire and are validated for type, signature, and subject.
- Protected endpoints reload the MongoDB user, so role changes and deactivation apply immediately.
- Frontend route checks improve UX; FastAPI RBAC remains authoritative.
- Uploads are restricted by extension, MIME expectations, size, and non-empty content.
- AI answers render through a constrained parser; no raw HTML injection is used.
- External links opened in new tabs use `noopener noreferrer`.
- Error normalization avoids stack traces and provider details.
- CORS must contain exact trusted origins in production.

## Remaining limitation

Access tokens are stored in browser storage and are therefore exposed to successful same-origin script injection. A future security-hardening project should move authentication to Secure, HttpOnly, SameSite cookies with appropriate CSRF protection. This migration was intentionally not attempted during release polish.

## Production requirements

- Use TLS at the reverse proxy.
- Generate a unique JWT secret; never reuse examples.
- Remove bootstrap passwords after provisioning.
- Restrict MongoDB, Qdrant, Ollama, and FastAPI network exposure.
- Configure backups, secret management, centralized logs, and monitoring.
