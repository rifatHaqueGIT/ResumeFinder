"use client";

import { useState, useRef, useEffect } from "react";
import { fetchAPI } from "@/lib/api";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: Array<{ filename: string; doc_type: string; relevance: number; excerpt: string }>;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const res = await fetchAPI<{ answer: string; sources: ChatMessage["sources"] }>("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, sources: res.sources },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Failed to get response. Is Ollama running?" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in flex flex-col h-[calc(100vh-48px)]">
      <div className="mb-4">
        <h1 className="text-lg font-semibold text-text-bright tracking-tight mb-1">AI Chat</h1>
        <p className="text-[13px] text-text-secondary">Ask questions about your resumes using semantic search</p>
      </div>

      {/* Message area */}
      <div className="flex-1 overflow-y-auto bg-surface-raised border border-border-default rounded-[6px] p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-16">
            <div className="text-text-muted text-[13px] mb-4">No messages yet. Try asking:</div>
            <div className="flex flex-col gap-2 items-center">
              {[
                "Which resume mentions AWS?",
                "What companies has Rifat worked at?",
                "Which resume is best for a data analyst role?",
                "What programming languages are listed?",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => { setInput(q); }}
                  className="text-[12px] text-text-secondary hover:text-primary border border-border-default hover:border-primary/30 rounded-[6px] px-3 py-1.5 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[70%] rounded-[6px] px-4 py-2.5 text-[13px] leading-relaxed ${
                msg.role === "user"
                  ? "bg-primary text-white"
                  : "bg-surface-overlay border border-border-default text-text-primary"
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-2 border-t border-border-default">
                  <div className="text-[10px] text-text-muted uppercase tracking-wide mb-1.5">Sources</div>
                  <div className="space-y-1">
                    {msg.sources.map((s, j) => (
                      <div key={j} className="text-[11px] flex items-center gap-2">
                        <span className={`inline-block w-1.5 h-1.5 rounded-full shrink-0 ${
                          s.relevance >= 0.7 ? "bg-positive" : s.relevance >= 0.5 ? "bg-warning" : "bg-text-muted"
                        }`} />
                        <span className="text-text-secondary truncate">{s.filename}</span>
                        <span className="text-text-muted ml-auto shrink-0">{(s.relevance * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-surface-overlay border border-border-default rounded-[6px] px-4 py-3">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-1.5 h-1.5 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-1.5 h-1.5 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="mt-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask about your resumes..."
          className="flex-1 bg-surface-raised border border-border-default rounded-[6px] px-4 py-2.5 text-[13px] text-text-bright placeholder:text-text-muted focus:outline-none focus:border-primary"
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="bg-primary hover:bg-primary-hover text-white px-5 py-2.5 rounded-[6px] text-[13px] font-medium transition-colors disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </div>
  );
}
