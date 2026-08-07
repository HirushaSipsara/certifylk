"use client";
import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

/**
 * Redirects legacy /assessment/[assessmentId]/profile (and all sub-pages)
 * to the new assessment hub.
 */
export default function LegacyAssessmentRedirect() {
  const router = useRouter();
  const params = useParams<{ assessmentId: string }>();

  useEffect(() => {
    if (params.assessmentId) {
      router.replace(`/assessment/${params.assessmentId}/hub`);
    } else {
      router.replace("/");
    }
  }, [params.assessmentId, router]);

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        fontFamily: "system-ui, sans-serif",
        color: "#17352e",
      }}
    >
      <p>Redirecting to your assessment hub…</p>
    </div>
  );
}
