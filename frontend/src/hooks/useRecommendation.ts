import { useCallback, useEffect, useRef, useState } from "react";
import { streamRecommendations } from "../api";
import type { SearchRequest, Shop } from "../types";

export function useRecommendation() {
  const [shops, setShops] = useState<Shop[]>([]);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);
  const requestIdRef = useRef(0);

  useEffect(() => () => {
    requestIdRef.current += 1;
    controllerRef.current?.abort();
  }, []);

  const search = useCallback(async (request: SearchRequest) => {
    controllerRef.current?.abort();
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    const controller = new AbortController();
    controllerRef.current = controller;
    setShops([]);
    setAnswer("");
    setError("");
    setIsLoading(true);
    try {
      await streamRecommendations(
        request,
        (nextShops) => {
          if (requestIdRef.current === requestId) setShops(nextShops);
        },
        (chunk) => {
          if (requestIdRef.current === requestId) setAnswer((current) => current + chunk);
        },
        controller.signal,
      );
    } catch (reason) {
      if (!controller.signal.aborted && requestIdRef.current === requestId) {
        setError(reason instanceof Error ? reason.message : "Search failed.");
      }
    } finally {
      if (!controller.signal.aborted && requestIdRef.current === requestId) setIsLoading(false);
    }
  }, []);

  return { shops, answer, error, isLoading, search };
}
