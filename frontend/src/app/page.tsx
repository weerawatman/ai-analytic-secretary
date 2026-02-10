"use client";

import { useState, useRef, useEffect, FormEvent, useMemo } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Message {
  role: "user" | "assistant" | "error";
  type?: "chat" | "data" | "error";
  message: string;
  analysis?: string;
  sql?: string;
  data?: Record<string, unknown>[];
}

const dataSources = [
  { name: "BigQuery", status: "connected", icon: "BQ" },
  { name: "CSV Upload", status: "ready", icon: "CSV" },
];

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}/;
const CHART_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

/* ── AutoChart Component ── */
function AutoChart({ data }: { data: Record<string, unknown>[] }) {
  const chartConfig = useMemo(() => {
    if (!data || data.length === 0) return null;

    const firstRow = data[0];
    const stringKeys: string[] = [];
    const numberKeys: string[] = [];
    const dateKeys: string[] = [];

    for (const key of Object.keys(firstRow)) {
      const val = firstRow[key];
      if (typeof val === "number" || (typeof val === "string" && val !== "" && !isNaN(Number(val)) && !ISO_DATE_RE.test(val))) {
        numberKeys.push(key);
      } else if (typeof val === "string" && ISO_DATE_RE.test(val)) {
        dateKeys.push(key);
      } else {
        stringKeys.push(key);
      }
    }

    // 1 dateKey + ≥1 numberKey → LineChart
    if (dateKeys.length >= 1 && numberKeys.length >= 1) {
      return { type: "line" as const, xKey: dateKeys[0], yKeys: numberKeys };
    }
    // ≥1 stringKey + ≥1 numberKey → BarChart
    if (stringKeys.length >= 1 && numberKeys.length >= 1) {
      return { type: "bar" as const, xKey: stringKeys[0], yKeys: [numberKeys[0]] };
    }
    // fallback — let DataTable handle it
    return null;
  }, [data]);

  if (!chartConfig) return null;

  // Coerce number strings to actual numbers for recharts
  const chartData = data.map((row) => {
    const out: Record<string, unknown> = { ...row };
    for (const k of chartConfig.yKeys) {
      const v = out[k];
      if (typeof v === "string") out[k] = Number(v);
    }
    return out;
  });

  return (
    <div className="mt-3 rounded-lg border border-white/10 bg-white/5 p-3 overflow-hidden">
      <ResponsiveContainer width="100%" height={320}>
        {chartConfig.type === "line" ? (
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
            <XAxis dataKey={chartConfig.xKey} tick={{ fill: "#94a3b8", fontSize: 11 }} tickLine={false} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} tickLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: "#1e293b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: "#94a3b8" }}
            />
            <Legend wrapperStyle={{ fontSize: 12, color: "#94a3b8" }} />
            {chartConfig.yKeys.map((key, i) => (
              <Line key={key} type="monotone" dataKey={key} stroke={CHART_COLORS[i % CHART_COLORS.length]} strokeWidth={2} dot={false} name={key} />
            ))}
          </LineChart>
        ) : (
          <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
            <XAxis dataKey={chartConfig.xKey} tick={{ fill: "#94a3b8", fontSize: 11 }} tickLine={false} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} tickLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: "#1e293b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: "#94a3b8" }}
            />
            <Legend wrapperStyle={{ fontSize: 12, color: "#94a3b8" }} />
            {chartConfig.yKeys.map((key, i) => (
              <Bar key={key} dataKey={key} fill={CHART_COLORS[i % CHART_COLORS.length]} radius={[4, 4, 0, 0]} name={key} />
            ))}
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}

/* ── Insight Box Component ── */
function InsightBox({ analysis }: { analysis: string }) {
  return (
    <div className="mt-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-md bg-emerald-500/20 text-emerald-400 text-xs">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5.002 5.002 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </span>
        <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">AI Insight</span>
      </div>
      <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">{analysis}</p>
    </div>
  );
}

/* ── Data Table Component ── */
function DataTable({ data }: { data: Record<string, unknown>[] }) {
  if (!data || data.length === 0) return null;
  const columns = Object.keys(data[0]);

  return (
    <div className="mt-3 overflow-x-auto rounded-lg border border-white/10">
      <table className="w-full text-xs text-left">
        <thead>
          <tr className="bg-white/5 border-b border-white/10">
            {columns.map((col) => (
              <th
                key={col}
                className="px-3 py-2 font-semibold text-emerald-400 whitespace-nowrap"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr
              key={i}
              className="border-b border-white/5 hover:bg-white/5 transition"
            >
              {columns.map((col) => (
                <td
                  key={col}
                  className="px-3 py-2 text-slate-300 whitespace-nowrap"
                >
                  {String(row[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="px-3 py-1.5 text-[10px] text-slate-500 bg-white/[.02] border-t border-white/5">
        {data.length} row{data.length !== 1 ? "s" : ""}
      </div>
    </div>
  );
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function sendMessage(e: FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || isLoading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", message: question }]);
    setIsLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(
          errData?.detail || errData?.error || `Server error (${res.status})`
        );
      }

      const resData = await res.json();

      if (resData.type === "error") {
        throw new Error(resData.message);
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          type: resData.type,
          message: resData.message || "",
          analysis: resData.analysis || undefined,
          sql: resData.sql || undefined,
          data: resData.data || undefined,
        },
      ]);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Something went wrong.";
      setMessages((prev) => [...prev, { role: "error", message }]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* ── Sidebar ── */}
      <aside className="hidden md:flex w-64 flex-col border-r border-white/10 bg-white/5 backdrop-blur-xl">
        {/* Brand */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-white/10">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400 font-bold text-sm">
            AI
          </div>
          <div>
            <h1 className="text-sm font-semibold leading-tight">
              Executive Cockpit
            </h1>
            <p className="text-[11px] text-slate-400">Analytics Assistant</p>
          </div>
        </div>

        {/* Data Sources */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          <p className="mb-3 text-[11px] font-medium uppercase tracking-wider text-slate-500">
            Data Sources
          </p>
          <ul className="space-y-2">
            {dataSources.map((ds) => (
              <li
                key={ds.name}
                className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-slate-300 bg-white/5 hover:bg-white/10 transition"
              >
                <span className="flex h-8 w-8 items-center justify-center rounded-md bg-slate-700/60 text-[11px] font-bold text-slate-300">
                  {ds.icon}
                </span>
                <span className="flex-1">{ds.name}</span>
                <span
                  className={`h-2 w-2 rounded-full ${
                    ds.status === "connected"
                      ? "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,.6)]"
                      : "bg-slate-500"
                  }`}
                />
              </li>
            ))}
          </ul>
        </div>

        {/* Footer */}
        <div className="border-t border-white/10 px-5 py-3">
          <p className="text-[11px] text-slate-500">
            Powered by Vanna AI + Ollama
          </p>
        </div>
      </aside>

      {/* ── Main Area ── */}
      <main className="flex flex-1 flex-col min-w-0">
        {/* Header */}
        <header className="flex items-center justify-between border-b border-white/10 px-6 py-3 bg-white/[.02]">
          <h2 className="text-sm font-medium text-slate-300">Chat</h2>
          <div className="flex items-center gap-2 text-[11px] text-slate-500">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,.6)]" />
            System Online
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {messages.length === 0 && !isLoading && (
            <div className="flex flex-col items-center justify-center h-full text-center text-slate-500 gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-400">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-8 w-8"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155"
                  />
                </svg>
              </div>
              <div>
                <p className="text-base font-medium text-slate-400">
                  AI Executive Cockpit
                </p>
                <p className="mt-1 text-sm text-slate-600">
                  Ask a question about your data to get started.
                </p>
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-emerald-600 text-white rounded-br-md"
                    : msg.role === "error"
                      ? "bg-red-500/15 text-red-300 border border-red-500/30 rounded-bl-md"
                      : "bg-white/10 text-slate-200 rounded-bl-md"
                }`}
              >
                {/* Message text */}
                {msg.message && (
                  <p className="whitespace-pre-wrap">{msg.message}</p>
                )}

                {/* AI Insight — rendered first (above chart & table) */}
                {msg.type === "data" && msg.analysis && (
                  <InsightBox analysis={msg.analysis} />
                )}

                {/* AutoChart — rendered between insight and SQL */}
                {msg.type === "data" && msg.data && msg.data.length > 0 && (
                  <AutoChart data={msg.data} />
                )}

                {/* SQL (collapsible) — only for data type */}
                {msg.sql && (
                  <details className="mt-3 text-xs text-slate-400">
                    <summary className="cursor-pointer hover:text-slate-300 transition">
                      View SQL
                    </summary>
                    <pre className="mt-2 overflow-x-auto rounded-lg bg-black/30 p-3 text-slate-300">
                      {msg.sql}
                    </pre>
                  </details>
                )}

                {/* Data Table — only for data type */}
                {msg.type === "data" && msg.data && msg.data.length > 0 && (
                  <DataTable data={msg.data} />
                )}

                {/* Empty result notice — only when there is truly nothing to show */}
                {msg.type === "data" &&
                  (!msg.data || msg.data.length === 0) &&
                  !msg.analysis && (
                    <p className="mt-2 text-xs text-slate-500 italic">
                      No results returned.
                    </p>
                  )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="rounded-2xl rounded-bl-md bg-white/10 px-4 py-3 text-sm text-slate-400">
                <span className="inline-flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span
                    className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"
                    style={{ animationDelay: "0.2s" }}
                  />
                  <span
                    className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"
                    style={{ animationDelay: "0.4s" }}
                  />
                  <span className="ml-2">Thinking...</span>
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form
          onSubmit={sendMessage}
          className="border-t border-white/10 bg-white/[.02] px-4 py-3"
        >
          <div className="mx-auto flex max-w-3xl items-center gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your data..."
              disabled={isLoading}
              className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-slate-500 outline-none transition focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white transition hover:bg-emerald-500 disabled:opacity-40 disabled:hover:bg-emerald-600"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
