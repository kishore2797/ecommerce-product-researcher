"use client";

import { useState, useRef } from "react";
import {
  MessageSquare,
  BarChart3,
  PieChart,
  Upload,
  FileSpreadsheet,
  ChevronLeft,
  ChevronRight,
  ShoppingCart,
  TrendingUp,
  Search,
  Zap,
} from "lucide-react";
import { API } from "../config/api";

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

interface UploadedFile {
  id: string;
  filename: string;
  upload_time: string;
  records_parsed: number;
  size_bytes: number;
}

export default function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [uploadMessage, setUploadMessage] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchFiles = async () => {
    try {
      const res = await fetch(API.salesFiles);
      if (res.ok) {
        const data = await res.json();
        setUploadedFiles(data.files || []);
      }
    } catch {
      // silently fail
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(API.salesUpload, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        setUploadMessage(`Error: ${err.detail || "Upload failed"}`);
        return;
      }

      const data = await res.json();
      setUploadMessage(`✅ ${data.message}`);
      fetchFiles();
    } catch {
      setUploadMessage("Error: Could not connect to backend");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const navItems = [
    { id: "chat", label: "Research Chat", icon: MessageSquare },
    { id: "dashboard", label: "Dashboard", icon: PieChart },
    { id: "analytics", label: "Analytics", icon: BarChart3 },
  ];

  return (
    <aside
      className={`${
        collapsed ? "w-16" : "w-72"
      } h-screen bg-[#0d0d0d] border-r border-slate-800 flex flex-col transition-all duration-300 flex-shrink-0`}
    >
      {/* Header */}
      <div className="h-14 border-b border-slate-800 flex items-center justify-between px-3 flex-shrink-0">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
              <ShoppingCart size={16} className="text-amber-400" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-white leading-tight">Product Researcher</h1>
              <p className="text-[9px] text-slate-500">Multi-Agent + RAG + MCP</p>
            </div>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-lg hover:bg-slate-800/60 text-slate-500 hover:text-white transition-colors"
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="p-2 space-y-1">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
              activeTab === item.id
                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                : "text-slate-400 hover:bg-slate-800/60 hover:text-white border border-transparent"
            }`}
          >
            <item.icon size={16} />
            {!collapsed && <span>{item.label}</span>}
          </button>
        ))}
      </nav>

      {/* Upload Section */}
      {!collapsed && (
        <div className="px-3 mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
              Sales Data
            </span>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleUpload}
            className="hidden"
          />

          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg border border-dashed border-slate-700/50 hover:border-amber-500/30 bg-slate-800/20 hover:bg-slate-800/40 text-slate-400 hover:text-amber-400 text-xs transition-all disabled:opacity-50"
          >
            {uploading ? (
              <>
                <div className="w-3 h-3 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                Parsing...
              </>
            ) : (
              <>
                <Upload size={12} />
                Upload Sales CSV
              </>
            )}
          </button>

          {uploadMessage && (
            <p className={`text-[10px] mt-2 ${uploadMessage.startsWith("Error") ? "text-red-400" : "text-amber-400"}`}>
              {uploadMessage}
            </p>
          )}

          {uploadedFiles.length > 0 && (
            <div className="mt-3 space-y-1.5 max-h-32 overflow-y-auto">
              {uploadedFiles.map((f) => (
                <div
                  key={f.id}
                  className="flex items-center gap-2 px-2 py-1.5 rounded-md bg-slate-800/30 border border-slate-700/30"
                >
                  <FileSpreadsheet size={12} className="text-amber-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-[10px] text-slate-300 truncate">{f.filename}</p>
                    <p className="text-[9px] text-slate-500">{f.records_parsed} records</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Quick Stats */}
      {!collapsed && (
        <div className="px-3 mt-auto mb-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/30 border border-slate-700/30">
              <Zap size={12} className="text-amber-400" />
              <div>
                <p className="text-[10px] text-slate-300">3 Specialized Agents</p>
                <p className="text-[9px] text-slate-500">Scraper → Analyst → Writer</p>
              </div>
            </div>
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/30 border border-slate-700/30">
              <Search size={12} className="text-blue-400" />
              <div>
                <p className="text-[10px] text-slate-300">RAG on Sales History</p>
                <p className="text-[9px] text-slate-500">12 months of data indexed</p>
              </div>
            </div>
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/30 border border-slate-700/30">
              <TrendingUp size={12} className="text-green-400" />
              <div>
                <p className="text-[10px] text-slate-300">MCP Integrations</p>
                <p className="text-[9px] text-slate-500">Google Trends, Amazon API</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
