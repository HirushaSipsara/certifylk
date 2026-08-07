# CertifyLK frontend

Next.js App Router, strict TypeScript, Tailwind CSS, React Hook Form, Zod, accessible reusable components, and native `fetch`.

Implemented entries are `/product-quality/select` and the Home-created `/process-management/{assessmentId}/business-profile`. There is intentionally no `/process-management/select` under D018. Both lead through applicability pages to the shared Assessment Hub. The legacy assessment pages remain available during certificate-specific engine conversion.

```bash
copy .env.example .env.local
npm install
npm run dev
npm run lint
npm run typecheck
npm test -- --run
npm run build
```

Only `NEXT_PUBLIC_API_BASE_URL` is required. `NEXT_PUBLIC_SHOW_MOCK_AI_STATUS=true` may enable the non-secret Mock label in an explicit QA build; it never selects a provider. Never place Gemini, database, AWS, or other credentials in `NEXT_PUBLIC_*` variables.

See `../docs/PRODUCT_REQUIREMENTS.md` for the target journey and `../docs/FULL_IMPLEMENTATION_PLAN.md` for unfinished pages/components.
