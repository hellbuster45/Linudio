# Linudio frontend

The Next.js UI for Linudio. See the [main README](../README.md) for what the project is and how
to set up the backend, which this app needs in order to do anything.

## Run it

```bash
npm install
npm run dev
```

Open <http://localhost:3000>. The backend is expected at <http://localhost:8000>; to use a
different address, copy `.env.example` to `.env.local` and change `NEXT_PUBLIC_API_URL`
(the backend must also allow the frontend's origin through its `CORS_ORIGINS` setting).

## Scripts

| Command         | What it does                         |
| --------------- | ------------------------------------ |
| `npm run dev`   | Development server with hot reload   |
| `npm run build` | Production build                     |
| `npm run start` | Serve the production build           |
| `npm run lint`  | ESLint                               |

Built with Next.js 16, React 19, TypeScript, HeroUI and Tailwind CSS.
