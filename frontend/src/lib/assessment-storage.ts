export interface SavedAssessmentMeta {
  id: string;
  track?: string;
  schemeName?: string;
  productName?: string;
  createdAt: string;
  lastSeenAt: string;
}

const STORAGE_KEY = "certifylk_saved_assessments";

export function rememberAssessment(
  id: string,
  meta?: Partial<Omit<SavedAssessmentMeta, "id" | "lastSeenAt">>
): void {
  if (typeof window === "undefined") return;
  try {
    const existing = getRememberedAssessments();
    const now = new Date().toISOString();
    const foundIndex = existing.findIndex((item) => item.id === id);
    const newItem: SavedAssessmentMeta = {
      id,
      track: meta?.track ?? existing[foundIndex]?.track ?? "product_quality",
      schemeName: meta?.schemeName ?? existing[foundIndex]?.schemeName,
      productName: meta?.productName ?? existing[foundIndex]?.productName,
      createdAt: existing[foundIndex]?.createdAt ?? now,
      lastSeenAt: now,
    };
    if (foundIndex >= 0) {
      existing[foundIndex] = newItem;
    } else {
      existing.unshift(newItem);
    }
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(existing.slice(0, 20)));
  } catch {
    // Ignore localStorage errors
  }
}

export function getRememberedAssessments(): SavedAssessmentMeta[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      // Check fallback legacy key
      const legacyId = window.localStorage.getItem("certifylk_assessment_id");
      if (legacyId) {
        return [
          {
            id: legacyId,
            createdAt: new Date().toISOString(),
            lastSeenAt: new Date().toISOString(),
          },
        ];
      }
      return [];
    }
    return JSON.parse(raw) as SavedAssessmentMeta[];
  } catch {
    return [];
  }
}

export function removeRememberedAssessment(id: string): void {
  if (typeof window === "undefined") return;
  try {
    const existing = getRememberedAssessments().filter((item) => item.id !== id);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(existing));
  } catch {
    // Ignore localStorage errors
  }
}
