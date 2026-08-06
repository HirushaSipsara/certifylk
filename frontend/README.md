# CertifyLK frontend

Next.js App Router, strict TypeScript, Tailwind CSS, React Hook Form, Zod, and native fetch.

```bash
copy .env.example .env.local
npm install
npm run dev
npm run typecheck
npm test -- --run
```

Only `NEXT_PUBLIC_API_BASE_URL` is required. `NEXT_PUBLIC_SHOW_MOCK_AI_STATUS=true` may be used for an explicit production-mode QA build; development and test already show the Mock label. The flag never selects a provider. AI credentials must never be placed in frontend variables.
