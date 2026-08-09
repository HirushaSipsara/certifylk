"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { SchemeChip } from "@/types";

function resolveSchemeId(assessment: {
  scheme_id?: string;
  profile: Record<string, unknown>;
}): string | undefined {
  if (assessment.scheme_id) return assessment.scheme_id;
  const appDec = assessment.profile?.applicability_decision as
    | Record<string, unknown>
    | undefined;
  const recommended = appDec?.recommended_path_scheme_id;
  return typeof recommended === "string" ? recommended : undefined;
}

/** Loads the certification scheme linked to an assessment. */
export function useAssessmentScheme(assessmentId: string) {
  const [scheme, setScheme] = useState<SchemeChip | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [assessment, schemes] = await Promise.all([
          api.getAssessment(assessmentId),
          api.listSchemes(),
        ]);
        if (cancelled) return;
        const schemeId = resolveSchemeId(assessment);
        const found = schemeId ? schemes.find((s) => s.id === schemeId) : undefined;
        setScheme(found ?? null);
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Failed to load scheme.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [assessmentId]);

  return { scheme, loading, error };
}
