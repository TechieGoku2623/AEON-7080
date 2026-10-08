"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

const TokenContext = createContext<string | null>(null);

export function useToken() {
  return useContext(TokenContext);
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const saved = sessionStorage.getItem("aeon-token");
    if (saved) {
      setToken(saved);
      return;
    }
    fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "demo@aeon7080.local", password: "demo" }),
    })
      .then(async (response) => {
        if (!response.ok) throw new Error(await response.text());
        return response.json();
      })
      .then((payload) => {
        sessionStorage.setItem("aeon-token", payload.token);
        setToken(payload.token);
      })
      .catch(() => setError("The API is not reachable. Start it on port 8000."));
  }, []);

  if (!token) {
    return (
      <div className="grid min-h-screen place-items-center px-6 text-center">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.22em] text-cyan">AEON 7080</p>
          <h1 className="mt-3 font-serif text-3xl">Opening the laboratory</h1>
          <p className="mt-3 text-mute">{error || "Signing in to the demo workspace."}</p>
        </div>
      </div>
    );
  }
  return <TokenContext.Provider value={token}>{children}</TokenContext.Provider>;
}
