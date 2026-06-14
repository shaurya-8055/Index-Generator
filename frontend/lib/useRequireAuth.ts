"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./store";

/** Redirect to /login when there is no token. Returns true once ready. */
export function useRequireAuth() {
  const router = useRouter();
  const token = useAuth((s) => s.token);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Wait for Zustand persist to hydrate before deciding.
    if (token === null) {
      const t = setTimeout(() => {
        if (!useAuth.getState().token) router.replace("/login");
        else setReady(true);
      }, 50);
      return () => clearTimeout(t);
    }
    setReady(true);
  }, [token, router]);

  return ready;
}
