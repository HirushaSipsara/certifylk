from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.services.seed_service import seed_catalogue  # noqa: E402


def main() -> None:
    with SessionLocal() as db:
        counts = seed_catalogue(db)
    print(
        "Seeded "
        f"{counts['requirements']} requirements, "
        f"{counts['questions']} questions, and "
        f"{counts['recommendations']} recommendations."
    )


if __name__ == "__main__":
    main()

