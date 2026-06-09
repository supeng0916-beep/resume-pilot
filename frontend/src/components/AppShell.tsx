import { Activity, BriefcaseBusiness } from "lucide-react";
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
          <span className="brand">
            <BriefcaseBusiness size={16} />
            Agentic HR 招聘评估
          </span>
          <span className={health?.status === "ok" ? "health health--ok" : "health"}>
            <Activity size={14} />
            {health?.status === "ok" ? "服务在线" : "连接中"}
          </span>
        </div>
      </header>
      <nav className="sub-nav">
        <div className="sub-nav__inner">
          <strong>招聘团队工作台</strong>
          <div className="sub-nav__links">
            <a href="#batches">评估批次</a>
            <a href="#runs">候选人记录</a>
            <a href="#new-batch">创建评估</a>
            <a href="#reviews">复核队列</a>
          </div>
        </div>
      </nav>
      <section className="workspace">{children}</section>
    </main>
  );
}
