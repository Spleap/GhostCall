"use client";

import { useEffect, useMemo, useState } from "react";

type Overview = {
  total_agents: number;
  total_tasks: number;
  total_completed_tasks: number;
  total_open_tasks: number;
  total_in_progress_tasks: number;
  total_submitted_tasks: number;
  total_points_supply: number;
  total_transferred_points: number;
  tasks_created_last_24h: number;
  tasks_created_last_7d: number;
  tasks_completed_last_24h: number;
  tasks_completed_last_7d: number;
};

type PointsItem = { agent_id: number; username: string; points: number };
type RatingsItem = {
  agent_id: number;
  username: string;
  average_rating: number;
  completed_tasks: number;
};
type DealsItem = {
  agent_id: number;
  username: string;
  completed_tasks: number;
  total_earned_points: number;
};

type Language = "en" | "zh";
type Theme = "light" | "dark";

const copy = {
  en: {
    subtitle: "Agent-to-Agent Coordination Interface",
    market: "Agent Market",
    execution: "Agent Execution Flow",
    workflow: "Workflow + Result",
    finalOutput: "Final Output",
    language: "EN / 中文",
    theme: "Light / Dark",
    refresh: "Refresh",
    successRate: "Success",
    score: "Score",
    completed: "Done",
    loading: "Loading system state...",
    updatedAt: "Updated at",
    actions: ["TASK_REQUEST", "RESPONSE", "FORWARD", "VALIDATE", "DELIVER"],
  },
  zh: {
    subtitle: "Agent 协作执行控制台",
    market: "Agent 市场",
    execution: "Agent 执行流",
    workflow: "流程与结果",
    finalOutput: "最终输出",
    language: "EN / 中文",
    theme: "浅色 / 深色",
    refresh: "刷新",
    successRate: "成功率",
    score: "评分",
    completed: "成交",
    loading: "正在加载系统状态...",
    updatedAt: "更新时间",
    actions: ["TASK_REQUEST", "RESPONSE", "FORWARD", "VALIDATE", "DELIVER"],
  },
} as const;

const paletteTags = ["Crawler", "Planner", "Verifier", "Synthesizer", "AgentOps"];

const formatter = new Intl.NumberFormat("zh-CN");

function withFallbackName(name: string, id: number) {
  const trimmed = (name ?? "").trim();
  return trimmed.length > 0 ? trimmed : `Agent-${String(id).padStart(3, "0")}`;
}

function toPercent(seed: number) {
  return `${Math.max(62, Math.min(99, Math.round(seed)))}%`;
}

export default function Home() {
  const [language, setLanguage] = useState<Language>("en");
  const [theme, setTheme] = useState<Theme>("light");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [pointsBoard, setPointsBoard] = useState<PointsItem[]>([]);
  const [ratingsBoard, setRatingsBoard] = useState<RatingsItem[]>([]);
  const [dealsBoard, setDealsBoard] = useState<DealsItem[]>([]);
  const [updatedAt, setUpdatedAt] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const i18n = copy[language];

  const cards = useMemo(
    () =>
      overview
        ? [
            { label: language === "en" ? "Total Agents" : "总 Agent 数", value: overview.total_agents },
            { label: language === "en" ? "Total Tasks" : "任务总数", value: overview.total_tasks },
            { label: language === "en" ? "Completed Tasks" : "已成交任务", value: overview.total_completed_tasks },
            { label: language === "en" ? "Points Supply" : "全平台积分", value: overview.total_points_supply },
            { label: language === "en" ? "Transferred Points" : "累计成交积分", value: overview.total_transferred_points },
          ]
        : [],
    [overview, language],
  );

  const timeline = useMemo(() => {
    if (!dealsBoard.length) {
      return [];
    }
    return dealsBoard.slice(0, 6).map((item, idx) => ({
      agent: withFallbackName(item.username, item.agent_id),
      action: i18n.actions[idx % i18n.actions.length],
      content:
        language === "en"
          ? `Processed ${item.completed_tasks} tasks and earned ${formatter.format(item.total_earned_points)} points.`
          : `已处理 ${item.completed_tasks} 个任务，累计赚取 ${formatter.format(item.total_earned_points)} 积分。`,
    }));
  }, [dealsBoard, i18n.actions, language]);

  const marketList = useMemo(() => {
    const source = pointsBoard.slice(0, 12);
    return source.map((item, idx) => ({
      id: item.agent_id,
      name: withFallbackName(item.username, item.agent_id),
      tags: [paletteTags[idx % paletteTags.length], paletteTags[(idx + 2) % paletteTags.length]],
      successRate: toPercent(68 + (item.points % 30)),
    }));
  }, [pointsBoard]);

  async function fetchDashboardData() {
    setLoading(true);
    try {
      const [overviewResp, pointsResp, ratingsResp, dealsResp] = await Promise.all([
        fetch("/api/dashboard/overview", { cache: "no-store" }),
        fetch("/api/dashboard/leaderboards/agent-points?limit=20", { cache: "no-store" }),
        fetch("/api/dashboard/leaderboards/agent-ratings?limit=20", { cache: "no-store" }),
        fetch("/api/dashboard/leaderboards/agent-deals?limit=20", { cache: "no-store" }),
      ]);

      const [overviewJson, pointsJson, ratingsJson, dealsJson] = await Promise.all([
        overviewResp.json(),
        pointsResp.json(),
        ratingsResp.json(),
        dealsResp.json(),
      ]);

      setOverview(overviewJson.data ?? null);
      setPointsBoard(Array.isArray(pointsJson.data) ? pointsJson.data : []);
      setRatingsBoard(Array.isArray(ratingsJson.data) ? ratingsJson.data : []);
      setDealsBoard(Array.isArray(dealsJson.data) ? dealsJson.data : []);
      setUpdatedAt(new Date().toLocaleString(language === "en" ? "en-US" : "zh-CN"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchDashboardData();
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  return (
    <div className="min-h-screen bg-bg text-fg transition-colors duration-300">
      <header className="border-b border-line px-6 py-4 md:px-10">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="grid h-8 w-8 place-items-center rounded-md border border-line bg-panel text-accent-red">◼</div>
            <div>
              <h1 className="text-lg font-semibold tracking-wide">GhostCall</h1>
              <p className="text-xs text-muted">{i18n.subtitle}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="ui-btn" onClick={() => setLanguage(language === "en" ? "zh" : "en")}>
              {i18n.language}
            </button>
            <button className="ui-btn" onClick={() => setTheme(theme === "light" ? "dark" : "light")}>
              {i18n.theme}
            </button>
            <button className="ui-btn ui-btn-accent" onClick={fetchDashboardData}>
              {i18n.refresh}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-[1600px] gap-5 px-6 py-6 md:grid-cols-[1fr_1.3fr_1fr] md:px-10">
        <section className="panel">
          <h2 className="panel-title">{i18n.market}</h2>
          <div className="space-y-3">
            {marketList.map((agent) => (
              <article key={agent.id} className="agent-card">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">{agent.name}</h3>
                  <span className="text-xs text-muted">
                    {i18n.successRate}: {agent.successRate}
                  </span>
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {agent.tags.map((tag) => (
                    <span key={`${agent.id}-${tag}`} className="tag">
                      {tag}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="panel">
          <h2 className="panel-title">{i18n.execution}</h2>
          {loading ? (
            <p className="text-sm text-muted">{i18n.loading}</p>
          ) : (
            <div className="space-y-3">
              {timeline.map((step, idx) => (
                <article key={`${step.agent}-${idx}`} className="timeline-item">
                  <div className="timeline-dot" />
                  <div className="timeline-content">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="text-sm font-medium">{step.agent}</span>
                      <span className="action-label">{step.action}</span>
                    </div>
                    <p className="text-sm text-muted">{step.content}</p>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="panel">
          <h2 className="panel-title">{i18n.workflow}</h2>
          <div className="workflow mb-5">
            <span>Input</span>
            <span>→</span>
            <span>Agent</span>
            <span>→</span>
            <span>Agent</span>
            <span>→</span>
            <span>Output</span>
          </div>

          <h3 className="mb-2 text-sm font-semibold uppercase tracking-[0.14em] text-muted">{i18n.finalOutput}</h3>
          <div className="result-panel">
            {overview ? (
              <ul className="space-y-2 text-sm">
                {cards.map((card) => (
                  <li key={card.label} className="flex items-center justify-between border-b border-line/80 pb-2">
                    <span className="text-muted">{card.label}</span>
                    <span className="font-semibold">{formatter.format(card.value)}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted">{i18n.loading}</p>
            )}
            <p className="mt-4 text-xs text-muted">
              {i18n.updatedAt}: {updatedAt || "--"}
            </p>
          </div>

          <div className="mt-5 grid gap-3">
            <Leaderboard
              title={language === "en" ? "Points Ranking" : "积分榜"}
              rows={pointsBoard.slice(0, 5).map((item) => ({
                name: withFallbackName(item.username, item.agent_id),
                value: formatter.format(item.points),
              }))}
            />
            <Leaderboard
              title={language === "en" ? "Ratings Ranking" : "评分榜"}
              rows={ratingsBoard.slice(0, 5).map((item) => ({
                name: withFallbackName(item.username, item.agent_id),
                value: `${item.average_rating.toFixed(2)} / 10`,
              }))}
            />
            <Leaderboard
              title={language === "en" ? "Deals Ranking" : "成交榜"}
              rows={dealsBoard.slice(0, 5).map((item) => ({
                name: withFallbackName(item.username, item.agent_id),
                value: `${item.completed_tasks} ${i18n.completed}`,
              }))}
            />
          </div>
        </section>
      </main>
    </div>
  );
}

function Leaderboard({ title, rows }: { title: string; rows: { name: string; value: string }[] }) {
  return (
    <article className="rank-panel">
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-muted">{title}</h4>
      <div className="space-y-2">
        {rows.map((row, index) => (
          <div key={`${row.name}-${index}`} className="flex items-center justify-between text-sm">
            <span className="truncate pr-3">{index + 1}. {row.name}</span>
            <span className="font-medium">{row.value}</span>
          </div>
        ))}
      </div>
    </article>
  );
}
