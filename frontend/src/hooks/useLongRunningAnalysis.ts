"use client";

import { useEffect, useState } from "react";

export function useLongRunningAnalysis(active: boolean, delayMs = 8000): boolean {
  const [takingLonger, setTakingLonger] = useState(false);

  useEffect(() => {
    setTakingLonger(false);
    if (!active) return;
    const timeout = window.setTimeout(() => setTakingLonger(true), delayMs);
    return () => window.clearTimeout(timeout);
  }, [active, delayMs]);

  return takingLonger;
}
