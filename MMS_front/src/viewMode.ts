import { useEffect, useState } from "react";

export type ViewMode = "user" | "admin";

const KEY = "mms.view-mode";

function read(): ViewMode {
  if (typeof window === "undefined") return "user";
  const v = window.localStorage.getItem(KEY);
  return v === "admin" ? "admin" : "user";
}

export function useViewMode(): [ViewMode, (m: ViewMode) => void] {
  const [mode, setMode] = useState<ViewMode>(read);

  useEffect(() => {
    const onStorage = () => setMode(read());
    window.addEventListener("storage", onStorage);
    window.addEventListener("mms-view-mode", onStorage as EventListener);
    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("mms-view-mode", onStorage as EventListener);
    };
  }, []);

  const update = (next: ViewMode) => {
    window.localStorage.setItem(KEY, next);
    window.dispatchEvent(new Event("mms-view-mode"));
    setMode(next);
  };

  return [mode, update];
}
