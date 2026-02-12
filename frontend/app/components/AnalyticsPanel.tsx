"use client";

import { useState, useEffect } from "react";
import { BarChart3, Clock, ThumbsUp, ThumbsDown, MessageSquare, FileText, Search, Database, RefreshCw, AlertCircle } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { API, Analytics } from "../config/api";

const COLORS = ["#f59e0b", "#3b82f6", "#10b981", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#f97316"];

export default function AnalyticsPanel() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchAnalytics = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(API.analytics);
      if (res.ok) {
        setAnalytics(await res.json());
      } else {
        setError("Failed to load analytics");
      }
    } catch {
      setError("Could not connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !analytics) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-amber-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-slate-400">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error && !analytics) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertCircle size={32} className="text-red-400 mx-auto mb-3" />
          <p className="text-sm text-red-400">{error}</p>
          <button onClick={fetchAnalytics} className="mt-3 text-xs text-amber-400 hover:underline">Retry</button>
        </div>
      </div>
    );
  }

  if (!analytics) return null;

  const queryTypeData = Object.entries(analytics.queries_by_type || {}).map(([name, value], i) => ({
    name: name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    value,
    fill: COLORS[i % COLORS.length],
  }));

  const satisfactionData = [
    { name: "Positive", value: analytics.feedback_positive, fill: "#10b981" },
    { name: "Negative", value: analytics.feedback_negative, fill: "#ef4444" },
  ].filter((d) => d.value > 0);

  const statCards = [
    { label: "Total Queries", value: analytics.total_queries, icon: MessageSquare, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
    { label: "Avg Response Time", value: `${analytics.avg_response_time}s`, icon: Clock, color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
    { label: "Products Researched", value: analytics.products_researched, icon: Search, color: "text-green-400", bg: "bg-green-500/10 border-green-500/20" },
    { label: "Reports Generated", value: analytics.reports_generated, icon: FileText, color: "text-purple-400", bg: "bg-purple-500/10 border-purple-500/20" },
    { label: "Files Uploaded", value: analytics.files_uploaded, icon: Database, color: "text-cyan-400", bg: "bg-cyan-500/10 border-cyan-500/20" },
    { label: "Satisfaction Rate", value: `${analytics.satisfaction_rate}%`, icon: ThumbsUp, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
    { label: "Knowledge Chunks", value: analytics.knowledge_chunks, icon: Database, color: "text-orange-400", bg: "bg-orange-500/10 border-orange-500/20" },
    { label: "Active Sessions", value: analytics.active_sessions, icon: MessageSquare, color: "text-pink-400", bg: "bg-pink-500/10 border-pink-500/20" },
  ];

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {/* Refresh */}
      <div className="flex justify-end">
        <button onClick={fetchAnalytics} className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-amber-400 transition-colors">
          <RefreshCw size={12} /> Refresh
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card) => (
          <div key={card.label} className={`rounded-xl p-4 border ${card.bg}`}>
            <div className="flex items-center gap-2 mb-2">
              <card.icon size={14} className={card.color} />
              <span className="text-[10px] text-slate-500 uppercase tracking-wider">{card.label}</span>
            </div>
            <p className="text-xl font-bold text-white">{card.value}</p>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Query Types */}
        {queryTypeData.length > 0 && (
          <div className="bg-slate-800/30 border border-slate-700/30 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <BarChart3 size={14} className="text-amber-400" /> Queries by Type
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={queryTypeData}>
                <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} angle={-20} textAnchor="end" height={50} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px", fontSize: "11px" }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {queryTypeData.map((entry, index) => (
                    <Cell key={index} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Satisfaction */}
        {satisfactionData.length > 0 && (
          <div className="bg-slate-800/30 border border-slate-700/30 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <ThumbsUp size={14} className="text-green-400" /> User Satisfaction
            </h3>
            <div className="flex items-center justify-center">
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={satisfactionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {satisfactionData.map((entry, index) => (
                      <Cell key={index} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px", fontSize: "11px" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-6 mt-2">
              {satisfactionData.map((d) => (
                <div key={d.name} className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full" style={{ background: d.fill }} />
                  <span className="text-xs text-slate-400">{d.name}: {d.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* System Info */}
      <div className="bg-slate-800/30 border border-slate-700/30 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white mb-3">System Information</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="text-center p-3 rounded-lg bg-slate-900/30 border border-slate-700/20">
            <p className="text-lg font-bold text-amber-400">{analytics.knowledge_chunks}</p>
            <p className="text-[10px] text-slate-500">Knowledge Chunks</p>
          </div>
          <div className="text-center p-3 rounded-lg bg-slate-900/30 border border-slate-700/20">
            <p className="text-lg font-bold text-blue-400">{analytics.sales_records?.toLocaleString()}</p>
            <p className="text-[10px] text-slate-500">Sales Records (RAG)</p>
          </div>
          <div className="text-center p-3 rounded-lg bg-slate-900/30 border border-slate-700/20">
            <p className="text-lg font-bold text-green-400">{analytics.research_records}</p>
            <p className="text-[10px] text-slate-500">Research Records (RAG)</p>
          </div>
          <div className="text-center p-3 rounded-lg bg-slate-900/30 border border-slate-700/20">
            <p className="text-lg font-bold text-purple-400">6</p>
            <p className="text-[10px] text-slate-500">Agent Tools</p>
          </div>
        </div>
      </div>
    </div>
  );
}
