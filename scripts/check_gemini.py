"""Run one low-cost structured Gemini request using backend-only configuration."""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.ai.gemini import GeminiAIProvider  # noqa: E402
from app.core.config import get_settings  # noqa: E402


async def main() -> None:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise SystemExit("Set GEMINI_API_KEY in backend/.env before running this check.")
    provider = GeminiAIProvider(
        settings.gemini_api_key,
        settings.gemini_model,
        timeout=settings.gemini_timeout_seconds,
        temperature=settings.gemini_temperature,
        max_output_tokens=settings.gemini_max_output_tokens,
    )
    result = await provider.plan_adaptive_questions(
        {
            "product": "Chilli paste",
            "category": "processed_food",
            "packaging": "glass_bottle",
            "storage": "room_temperature",
        },
        ["PROC_TEMP_01", "PACK_GRADE_01", "DOC_BATCH_01"],
    )
    print(f"Gemini structured-output check passed with model: {provider.model}")
    print(f"Returned approved IDs: {', '.join(result.question_ids)}")


if __name__ == "__main__":
    asyncio.run(main())
