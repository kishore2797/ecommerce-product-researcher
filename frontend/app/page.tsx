"use client";

import { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatPanel from "./components/ChatPanel";
import DashboardPanel from "./components/DashboardPanel";
import AnalyticsPanel from "./components/AnalyticsPanel";

type Tab = "chat" | "dashboard" | "analytics";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("chat");

  return (
    <div className="flex h-screen bg-[#0a0a0a]">
      <Sidebar activeTab={activeTab} onTabChange={(tab) => setActiveTab(tab as Tab)} />

      <main className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-slate-800 flex items-center justify-between px-6 flex-shrink-0">
          <div>
            <h2 className="text-sm font-semibold text-white">
              {activeTab === "chat" && "Product Research Chat"}
              {activeTab === "dashboard" && "Sales & Research Dashboard"}
              {activeTab === "analytics" && "Agent Analytics"}
            </h2>
            <p className="text-[10px] text-slate-500">
              {activeTab === "chat" && "Ask about trends, competitors, product opportunities, and market research"}
              {activeTab === "dashboard" && "Sales performance, top products, and research history"}
              {activeTab === "analytics" && "Agent performance, query topics, and usage metrics"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 text-[10px] text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-full px-2.5 py-1">
              <span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-pulse" />
              Multi-Agent
            </span>
          </div>
        </header>

        <div className="flex-1 min-h-0">
          {activeTab === "chat" && <ChatPanel />}
          {activeTab === "dashboard" && <DashboardPanel />}
          {activeTab === "analytics" && <AnalyticsPanel />}
        </div>
      </main>
    </div>
  );
}
