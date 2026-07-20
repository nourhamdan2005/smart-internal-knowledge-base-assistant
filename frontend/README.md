# CGC Knowledge AI Frontend

Next.js 16 frontend for CGC Knowledge AI.

```powershell
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Production verification:

```powershell
npm run lint
npx tsc --noEmit
npm run build
npm run start
```

The frontend uses offline-safe system fonts. Project-wide setup, architecture, security, and deployment guidance live in the repository root documentation.
