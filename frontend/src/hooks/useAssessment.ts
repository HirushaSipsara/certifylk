"use client";

import { useCallback, useEffect, useState } from "react";

import { api, rememberAssessment } from "@/lib/api";
import type { Assessment } from "@/types";

export function useAssessment(assessmentId: string) {
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAssessment(assessmentId);
      setAssessment(data);
      rememberAssessment(assessmentId);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load assessment.");
    } finally {
      setLoading(false);
    }
  }, [assessmentId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { assessment, setAssessment, loading, error, refresh };
}
