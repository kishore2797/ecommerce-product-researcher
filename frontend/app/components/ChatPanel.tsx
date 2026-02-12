"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Clock, Wrench, BookOpen, ThumbsUp, ThumbsDown } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { API, ChatMessage, Citation } from "../config/api";

export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showCitations, setShowCitations] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(API.chat, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage.content, session_id: sessionId }),
      });

      if (!res.ok) {
        throw new Error("Failed to get response");
      }

      const data = await res.json();
      if (!sessionId) setSessionId(data.session_id);

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: data.answer,
        citations: data.citations,
        category: data.category,
        tool_used: data.tool_used,
        tool_result: data.tool_result,
        processing_time: data.processing_time,
        timestamp: data.timestamp,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I couldn't connect to the backend. Make sure the API server is running on port 8000." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (rating: string, index: number) => {
    if (!sessionId) return;
    try {
      await fetch(API.chatFeedback, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message_index: index, rating }),
      });
    } catch {
      // silently fail
    }
  };

  const suggestions = [
    "What's trending in Home & Kitchen?",
    "Find products on Amazon in Pet Supplies",
    "Analyze competitors for portable ice maker",
    "Score the opportunity for LED closet lights",
    "Generate a research report for Beauty & Personal Care",
    "How are our sales performing?",
  ];

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center animate-fade-in">
            <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mb-4">
              <Bot size={28} className="text-amber-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-1">E-Commerce Product Researcher</h3>
            <p className="text-sm text-slate-400 mb-6 max-w-md">
              Multi-Agent system with Scraper, Analyst, and Report Writer agents. Powered by RAG on your sales history and MCP connections to Google Trends & Amazon.
            </p>
            <div className="grid grid-cols-2 gap-2 max-w-lg">
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  onClick={() => { setInput(s); }}
                  className="text-left text-xs px-3 py-2.5 rounded-lg bg-slate-800/40 border border-slate-700/30 text-slate-400 hover:text-amber-400 hover:border-amber-500/30 hover:bg-slate-800/60 transition-all"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 animate-fade-in ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "assistant" && (
              <div className="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                <Bot size={14} className="text-amber-400" />
              </div>
            )}

            <div className={`max-w-[75%] ${msg.role === "user" ? "order-first" : ""}`}>
              <div
                className={`rounded-xl px-4 py-3 text-sm ${
                  msg.role === "user"
                    ? "bg-amber-500/10 border border-amber-500/20 text-amber-100"
                    : "bg-slate-800/50 border border-slate-700/30 text-slate-200"
                }`}
              >
                {msg.role === "assistant" ? (
                  <div className="chat-markdown">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  msg.content
                )}
              </div>

              {/* Meta info for assistant messages */}
              {msg.role === "assistant" && (
                <div className="flex items-center gap-3 mt-1.5 px-1">
                  {msg.tool_used && (
                    <span className="flex items-center gap-1 text-[10px] text-amber-400/70">
                      <Wrench size={10} />
                      {msg.tool_used.replace(/_/g, " ")}
                    </span>
                  )}
                  {msg.processing_time && (
                    <span className="flex items-center gap-1 text-[10px] text-slate-500">
                      <Clock size={10} />
                      {msg.processing_time}s
                    </span>
                  )}
                  {msg.citations && msg.citations.length > 0 && (
                    <button
                      onClick={() => setShowCitations(showCitations === idx ? null : idx)}
                      className="flex items-center gap-1 text-[10px] text-blue-400/70 hover:text-blue-400 transition-colors"
                    >
                      <BookOpen size={10} />
                      {msg.citations.length} source{msg.citations.length > 1 ? "s" : ""}
                    </button>
                  )}
                  <div className="flex items-center gap-1 ml-auto">
                    <button
                      onClick={() => handleFeedback("positive", idx)}
                      className="p-1 rounded hover:bg-slate-700/50 text-slate-500 hover:text-green-400 transition-colors"
                    >
                      <ThumbsUp size={10} />
                    </button>
                    <button
                      onClick={() => handleFeedback("negative", idx)}
                      className="p-1 rounded hover:bg-slate-700/50 text-slate-500 hover:text-red-400 transition-colors"
                    >
                      <ThumbsDown size={10} />
                    </button>
                  </div>
                </div>
              )}

              {/* Citations panel */}
              {showCitations === idx && msg.citations && msg.citations.length > 0 && (
                <div className="mt-2 p-3 rounded-lg bg-slate-900/50 border border-slate-700/30 space-y-2">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Sources</p>
                  {msg.citations.map((c: Citation) => (
                    <div key={c.id} className="text-[11px] p-2 rounded bg-slate-800/40 border border-slate-700/20">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-amber-400 font-semibold">[{c.id}]</span>
                        <span className="text-slate-300">{c.source}</span>
                        {c.section && <span className="text-slate-500">— {c.section}</span>}
                        {c.page && <span className="text-slate-600">p.{c.page}</span>}
                      </div>
                      <p className="text-slate-400 text-[10px]">{c.text}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {msg.role === "user" && (
              <div className="w-7 h-7 rounded-lg bg-slate-700/50 border border-slate-600/30 flex items-center justify-center flex-shrink-0 mt-1">
                <User size={14} className="text-slate-300" />
              </div>
            )}
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex gap-3 animate-fade-in">
            <div className="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center flex-shrink-0">
              <Bot size={14} className="text-amber-400" />
            </div>
            <div className="bg-slate-800/50 border border-slate-700/30 rounded-xl px-4 py-3">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 bg-amber-400 rounded-full typing-dot" />
                <div className="w-2 h-2 bg-amber-400 rounded-full typing-dot" />
                <div className="w-2 h-2 bg-amber-400 rounded-full typing-dot" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-800 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
            placeholder="Ask about trends, competitors, product opportunities..."
            className="flex-1 bg-slate-800/40 border border-slate-700/30 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/40 focus:ring-1 focus:ring-amber-500/20 transition-all"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="px-4 py-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-400 hover:bg-amber-500/20 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
