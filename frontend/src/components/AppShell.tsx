import {
  Activity,
  BriefcaseBusiness,
  Database,
  GitBranch,
  LayoutDashboard,
  ListChecks,
  PlusCircle,
  ShieldCheck,
  UsersRound
} from "lucide-react";
import type { ReactNode } from "react";
import type { HealthResponse } from "../api/types";

export type AppView = "overview" | "evaluations" | "candidates" | "reviews" | "detail";

interface AppShellProps {
  activeView: AppView;
  health: HealthResponse | null;
  queueLabel: string;
  selectedRunId?: string | null;
  children: ReactNode;
  onNavigate: (view: AppView) => void;
}

const navigationItems: Array<{ view: AppView; label: string; description: string; icon: ReactNode }> = [
  {
    view: "overview",
    label: "运营总览",
    description: "系统状态与关键指标",
    icon: <LayoutDashboard size={18} />
  },
  {
    view: "evaluations",
    label: "评估任务",
    description: "创建批量候选人评估",
    icon: <PlusCircle size={18} />
  },
  {
    view: "candidates",
    label: "候选人库",
    description: "查看运行记录与评分",
    icon: <UsersRound size={18} />
  },
  {
    view: "reviews",
    label: "人工复核",
    description: "处理高风险候选人",
    icon: <ShieldCheck size={18} />
  }
];

function formatStorageLabel(storage?: string) {
  if (!storage) {
    return "数据层待连接";
  }
  if (storage === "sqlite") {
    return "评估数据层";
  }
  if (storage === "postgresql" || storage === "postgres") {
    return "生产数据层";
  }
  return "评估数据层";
}

function formatQueueLabel(queueBackend: string) {
  if (queueBackend.includes("rq") || queueBackend.includes("redis")) {
    return "异步任务调度";
  }
  if (queueBackend.includes("background")) {
    return "任务调度就绪";
  }
  return "任务调度";
}

export function AppShell({
  activeView,
  health,
  queueLabel,
  selectedRunId,
  children,
  onNavigate
}: AppShellProps) {
  const online = health?.status === "ok";

  return (
    <main className="app-shell app-shell--console">
      <aside className="sidebar" aria-label="主导航">
        <div className="brand brand--sidebar">
          <span className="brand__mark">
            <BriefcaseBusiness size={19} />
          </span>
          <span>
            <strong>Agentic HR</strong>
            <small>Supervisor Control Cabin</small>
          </span>
        </div>

        <nav className="sidebar__nav">
          {navigationItems.map((item) => (
            <button
              className={activeView === item.view ? "nav-item nav-item--active" : "nav-item"}
              key={item.view}
              type="button"
              onClick={() => onNavigate(item.view)}
            >
              <span className="nav-item__icon">{item.icon}</span>
              <span>
                <strong>{item.label}</strong>
                <small>{item.description}</small>
              </span>
            </button>
          ))}
          {selectedRunId ? (
            <button
              className={activeView === "detail" ? "nav-item nav-item--active" : "nav-item"}
              type="button"
              onClick={() => onNavigate("detail")}
            >
              <span className="nav-item__icon">
                <ListChecks size={18} />
              </span>
              <span>
                <strong>运行详情</strong>
                <small>{selectedRunId}</small>
              </span>
            </button>
          ) : null}
        </nav>

        <div className="sidebar__footer">
          <span className={online ? "health health--ok" : "health"}>
            <Activity size={14} />
            {online ? "服务在线" : "服务连接中"}
          </span>
          <span className="health">
            <Database size={14} />
            {formatStorageLabel(health?.storage)}
          </span>
        </div>
      </aside>

      <section className="console">
        <header className="console-topbar">
          <div>
            <p className="eyebrow">AI Hiring Operations</p>
            <h1>Agentic HR 工作台</h1>
          </div>
          <div className="console-topbar__signals" aria-label="系统运行状态">
            <span className="signal-card">
              <GitBranch size={15} />
              {formatQueueLabel(queueLabel)}
            </span>
            <span className={online ? "signal-card signal-card--ok" : "signal-card"}>
              <Activity size={15} />
              {online ? "服务就绪" : "服务连接中"}
            </span>
          </div>
        </header>
        <div className="workspace">{children}</div>
      </section>
    </main>
  );
}
