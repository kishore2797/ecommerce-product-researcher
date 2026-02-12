"use client";

import { useState, useEffect } from "react";
import { DollarSign, TrendingUp, ShoppingBag, BarChart3, Package, Store, RefreshCw, AlertCircle } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { API, SalesSummary, ResearchRecord } from "../config/api";

const COLORS = ["#f59e0b", "#3b82f6", "#10b981", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#f97316"];

export default function DashboardPanel() {
  const [sales, setSales] = useState<SalesSummary | null>(null);
  const [research, setResearch] = useState<ResearchRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const [salesRes, researchRes] = await Promise.all([
        fetch(API.salesSummary(3)),
        fetch(API.researchHistory),
      ]);
      if (salesRes.ok) {
        const salesData = await salesRes.json();
        if (!salesData.error) setSales(salesData);
      }
      if (researchRes.ok) {
        const researchData = await researchRes.json();
        setResearch(researchData.records || []);
      }
    } catch {
      setError("Could not connect to backend. Make sure the API is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-amber-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-slate-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertCircle size={32} className="text-red-400 mx-auto mb-3" />
          <p className="text-sm text-red-400">{error}</p>
          <button onClick={fetchData} className="mt-3 text-xs text-amber-400 hover:underline">Retry</button>
        </div>
      </div>
    );
  }

  const categoryData = sales?.categories?.map((c, i) => ({
    name: c.category,
    revenue: c.revenue,
    profit: c.profit,
    fill: COLORS[i % COLORS.length],
  })) || [];

  const storeData = sales?.stores?.map((s, i) => ({
    name: s.store,
    revenue: s.revenue,
    profit: s.profit,
    fill: COLORS[i % COLORS.length],
  })) || [];

  const outcomeCount = { winner: 0, failed: 0, breakeven: 0 };
  research.forEach((r) => {
    if (r.outcome === "winner") outcomeCount.winner++;
    else if (r.outcome === "failed") outcomeCount.failed++;
    else outcomeCount.breakeven++;
  });

  const outcomeData = [
    { name: "Winners", value: outcomeCount.winner, fill: "#10b981" },
    { name: "Failed", value: outcomeCount.failed, fill: "#ef4444" },
    { name: "Breakeven", value: outcomeCount.breakeven, fill: "#f59e0b" },
  ].filter((d) => d.value > 0);

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {/* Refresh */}
      <div className="flex justify-end">
        <button onClick={fetchData} className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-amber-400 transition-colors">
          <RefreshCw size={12} /> Refresh
        </button>
      </div>

      {/* KPI Cards */}
      {sales && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-800/30 border border-slate-700/30 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign size={14} className="text-amber-400" />
              <span className="text-[10px] text-slate-500 uppercase tracking-wider">Revenue</span>
            </div>
            <p className="text-xl font-bold text-white">${sales.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</p>
            <p className="text-[10px] text-slate-500 mt-1">{sales.period}</p>
          </div>
          <div className="bg-slate-800/30 border border-slate-700/30 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp size={14} className="text-green-400" />
              <span className="text-[10px] text-slate-500 uppercase tracking-wider">Profit</span>
            </div>
            <p className="text-xl font-bold text-white">${sales.total_profit.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</p>
            <p className="text-[10px] text-green-400 mt-1">{sales.overall_margin}% margin</p>
          </div>
          <div className="bg-slate-800/30 border border-slate-700/30 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 size={14} className="text-blue-400" />
              <span className="text-[10px] text-slate-500 uppercase tracking-wider">ROAS</span>
            </div>
            <p className="text-xl font-bold text-white">{sales.roas}x</p>
            <p className="text-[10px] text-slate-500 mt-1">Ad spend: ${sales.total_ad_spend.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</p>
          </div>
          <div className="bg-slate-800/30 border border-slate-700/30 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <ShoppingBag size={14} className="text-purple-400" />
              <span className="text-[10px] text-slate-500 uppercase tracking-wider">Orders</span>
            </div>
            <p className="text-xl font-bold text-white">{sales.total_orders.toLocaleString()}</p>
            <p className="text-[10px] text-slate-500 mt-1">{sales.period}</p>
          </div>
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue by Category */}
        {categoryData.length > 0 && (
          <div className="bg-slate-800/30 border border-slate-700/30 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Package size={14} className="text-amber-400" /> Revenue by Category
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={categoryData} layout="vertical">
                <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 10 }} tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`} />
                <YAxis type="category" dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} width={120} />
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px", fontSize: "11px" }}
                  formatter={(value: number) => [`$${value.toLocaleString()}`, "Revenue"]}
                />
                <Bar dataKey="revenue" radius={[0, 4, 4, 0]}>
                  {categoryData.map((entry, index) => (
                    <Cell key={index} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Revenue by Store */}
        {storeData.length > 0 && (
          <div className="bg-slate-800/30 border border-slate-700/30 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Store size={14} className="text-blue-400" /> Revenue by Store
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={storeData} layout="vertical">
                <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 10 }} tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`} />
                <YAxis type="category" dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} width={130} />
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px", fontSize: "11px" }}
                  formatter={(value: number) => [`$${value.toLocaleString()}`, "Revenue"]}
                />
                <Bar dataKey="revenue" radius={[0, 4, 4, 0]}>
                  {storeData.map((entry, index) => (
                    <Cell key={index} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Bottom Row: Top Products + Research History */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Products */}
        {sales && sales.top_products.length > 0 && (
          <div className="bg-slate-800/30 border border-slate-700/30 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-white mb-3">Top Products by Revenue</h3>
            <div className="space-y-2">
              {sales.top_products.slice(0, 8).map((p, i) => {
                const margin = p.revenue > 0 ? ((p.profit / p.revenue) * 100).toFixed(1) : "0";
                const maxRev = sales.top_products[0]?.revenue || 1;
                const barWidth = (p.revenue / maxRev) * 100;
                return (
                  <div key={i} className="relative">
                    <div className="flex items-center justify-between text-[11px] mb-0.5">
                      <span className="text-slate-300 truncate max-w-[60%]">{p.name}</span>
                      <span className="text-slate-400">${p.revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })} <span className={Number(margin) >= 30 ? "text-green-400" : Number(margin) >= 15 ? "text-amber-400" : "text-red-400"}>({margin}%)</span></span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-700/30 rounded-full overflow-hidden">
                      <div className="h-full bg-amber-500/40 rounded-full" style={{ width: `${barWidth}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Research History */}
        {research.length > 0 && (
          <div className="bg-slate-800/30 border border-slate-700/30 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white">Research History (RAG)</h3>
              {outcomeData.length > 0 && (
                <div className="flex items-center gap-2">
                  {outcomeData.map((d) => (
                    <span key={d.name} className="flex items-center gap-1 text-[9px]">
                      <span className="w-2 h-2 rounded-full" style={{ background: d.fill }} />
                      <span className="text-slate-400">{d.name}: {d.value}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {research.slice(0, 10).map((r) => (
                <div key={r.id} className="flex items-start gap-2 p-2 rounded-lg bg-slate-900/30 border border-slate-700/20">
                  <span className={`text-sm mt-0.5 ${r.outcome === "winner" ? "text-green-400" : r.outcome === "failed" ? "text-red-400" : "text-amber-400"}`}>
                    {r.outcome === "winner" ? "✅" : r.outcome === "failed" ? "❌" : "➡️"}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] text-white font-medium truncate">{r.product_name}</span>
                      <span className="text-[9px] text-slate-500">{r.niche}</span>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5 line-clamp-1">{r.reason}</p>
                    <div className="flex items-center gap-3 mt-1">
                      <span className={`text-[9px] ${r.margin_pct >= 30 ? "text-green-400" : r.margin_pct >= 10 ? "text-amber-400" : "text-red-400"}`}>
                        {r.margin_pct}% margin
                      </span>
                      <span className="text-[9px] text-slate-500">{r.months_active}mo active</span>
                      <span className="text-[9px] text-slate-500">${r.revenue_total.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
