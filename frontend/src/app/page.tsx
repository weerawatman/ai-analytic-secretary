"use client";

import { useState, useRef, useEffect, FormEvent } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Message {
  role: "user" | "assistant" | "error";
  content: string;
  sql?: string;
}

const dataSources = [
  { name: "BigQuery", status: "connected", icon: "BQ" },
  { name: "CSV Upload", status: "ready", icon: "CSV" },
];

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
    setMessages((prev) => [...prev, { role: "user", content: question }]);
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

      const data = await res.json();

      if (data.error) {
        throw new Error(data.error);
      }

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, sql: data.sql },
      ]);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Something went wrong.";
      setMessages((prev) => [...prev, { role: "error", content: message }]);
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
                className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-emerald-600 text-white rounded-br-md"
                    : msg.role === "error"
                      ? "bg-red-500/15 text-red-300 border border-red-500/30 rounded-bl-md"
                      : "bg-white/10 text-slate-200 rounded-bl-md"
                }`}
              >
                {msg.content}
                {msg.sql && msg.sql !== "SQL log inside container" && (
                  <details className="mt-3 text-xs text-slate-400">
                    <summary className="cursor-pointer hover:text-slate-300 transition">
                      View SQL
                    </summary>
                    <pre className="mt-2 overflow-x-auto rounded-lg bg-black/30 p-3 text-slate-300">
                      {msg.sql}
                    </pre>
                  </details>
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
