import { Activity } from "lucide-react";
import type { ReactNode } from "react";
import type { HealthResponse } from "../api/types";

interface AppShellProps {
  health: HealthResponse | null;
  children: ReactNode;
}

export function AppShell({ health, children }: AppShellProps) {
  return (
    <main className="app-shell">
      <header className="top-bar">
        <div className="top-bar__inner">
          <span className="brand">Agentic HR</span>
          <span className={health?.status === "ok" ? "health health--ok" : "health"}>
            <Activity size={14} />
            {health?.status ?? "checking"}
          </span>
        </div>
      </header>
      <nav className="sub-nav">
        <div className="sub-nav__inner">
          <strong>React Control Cabin</strong>
          <div className="sub-nav__links">
            <a href="#runs">Runs</a>
            <a href="#reviews">Reviews</a>
            <a href="#trace">Trace</a>
          </div>
        </div>
      </nav>
      <section className="workspace">{children}</section>
    </main>
  );
}
