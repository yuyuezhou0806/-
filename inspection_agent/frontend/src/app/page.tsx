"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MessageRole = "user" | "assistant";

interface Message {
  role: MessageRole;
  content: string;
  toolEvents?: ToolEvent[];
}

interface ToolEvent {
  kind: "call" | "result";
  name?: string;
  args?: Record<string, unknown>;
  preview?: string;
}

const SUGGESTED_QUERIES = [
  "砌体加固改造项目需要做哪些检测？引用哪些标准？",
  "回弹法检测混凝土的取样数量是多少？",
  "材料检测的平均折扣是多少？同比去年变化如何？",
  "钢结构工程中常见的质量缺陷有哪些？检测时需重点关注什么？",
];

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isComposing, setIsComposing] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // 最近一条用户问题(给反馈用作上下文)
  const lastUserQuery = [...messages].reverse().find((m) => m.role === "user")?.content;

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  async function sendMessage(content: string) {
    if (!content.trim() || loading) return;

    const userMsg: Message = { role: "user", content: content.trim() };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    // 占位的 assistant 消息,后续逐步填充
    const assistantIdx = newMessages.length;
    setMessages((prev) => [...prev, { role: "assistant", content: "", toolEvents: [] }]);

    try {
      const resp = await fetch("/inspection/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: newMessages.map(({ role, content }) => ({ role, content })),
        }),
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }
      if (!resp.body) {
        throw new Error("没有响应流");
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // 按 SSE 分隔(\n\n)切
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || ""; // 保留不完整的最后一段

        for (const line of lines) {
          if (!line.startsWith("data:")) continue;
          const payload = line.slice(5).trim();
          if (!payload) continue;
          try {
            const evt = JSON.parse(payload);
            applyEvent(assistantIdx, evt);
          } catch (e) {
            console.warn("parse SSE payload failed:", payload, e);
          }
        }
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setMessages((prev) => {
        const copy = [...prev];
        copy[assistantIdx] = {
          role: "assistant",
          content: `❌ 出错:${msg}`,
        };
        return copy;
      });
    } finally {
      setLoading(false);
    }
  }

  function applyEvent(idx: number, evt: { type: string; [k: string]: unknown }) {
    setMessages((prev) => {
      const copy = [...prev];
      const m = { ...copy[idx] };
      const events = [...(m.toolEvents || [])];

      switch (evt.type) {
        case "tool_call":
          events.push({
            kind: "call",
            name: evt.name as string,
            args: evt.args as Record<string, unknown>,
          });
          m.toolEvents = events;
          break;
        case "tool_result":
          events.push({
            kind: "result",
            preview: (evt.content as string)?.slice(0, 300) || "",
          });
          m.toolEvents = events;
          break;
        case "text":
          // 整段替换(Agent 输出非流式 token,而是整段)
          m.content = evt.content as string;
          break;
        case "error":
          m.content = `❌ ${evt.message as string}`;
          break;
      }

      copy[idx] = m;
      return copy;
    });
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="flex flex-col h-screen bg-amber-50">
      {/* Header */}
      <header className="bg-white border-b border-orange-200 px-6 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-orange-500 text-white rounded-full flex items-center justify-center text-lg font-bold shadow-md">
            刚
          </div>
          <div>
            <h1 className="text-lg font-bold text-orange-900">刚子</h1>
            <p className="text-xs text-orange-600">检测行业智能助手</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setFeedbackOpen(true)}
            className="text-xs text-orange-700 hover:text-orange-900 border border-orange-300 rounded-md px-3 py-1.5 transition"
          >
            📝 反馈
          </button>
          <span className="text-xs text-orange-400 hidden sm:inline">DeepSeek + bge-zh + Chroma</span>
        </div>
      </header>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-10">
              <div className="inline-flex items-center gap-2 mb-4">
                <div className="w-10 h-10 bg-orange-500 text-white rounded-full flex items-center justify-center text-xl font-bold shadow-md">刚</div>
                <div className="bg-white border border-orange-200 rounded-2xl rounded-tl-none px-4 py-3 text-left shadow-sm">
                  <p className="text-orange-900 text-sm">嘿，我是<span className="font-bold">检测大师刚子</span>，有啥问题尽管问！</p>
                </div>
              </div>
              <p className="text-orange-600 mb-6 text-sm">或者点下面这些问题试试：</p>
              <div className="grid sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
                {SUGGESTED_QUERIES.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(q)}
                    disabled={loading}
                    className="text-left text-sm bg-white border border-orange-200 rounded-lg p-3 hover:border-orange-400 hover:bg-orange-50 transition disabled:opacity-50"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <MessageView key={i} message={m} />
          ))}

          {loading && messages[messages.length - 1]?.content === "" && (
            <div className="flex items-center gap-2 text-orange-600 text-sm">
              <div className="w-6 h-6 bg-orange-500 text-white rounded-full flex items-center justify-center text-xs font-bold">刚</div>
              <span>刚子正在翻资料...</span>
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-orange-200 bg-white px-6 py-4"
      >
        <div className="max-w-3xl mx-auto flex gap-3 items-end">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onCompositionStart={() => setIsComposing(true)}
            onCompositionEnd={(e) => {
              setIsComposing(false);
              setInput((e.target as HTMLTextAreaElement).value);
            }}
            onKeyDown={(e) => {
              // 中文输入法上屏 Enter 不应触发发送
              if (e.key === "Enter" && !e.shiftKey && !isComposing) {
                e.preventDefault();
                sendMessage(input);
              }
            }}
            placeholder="有问题直接问刚子 (Enter 发送 / Shift+Enter 换行)"
            rows={2}
            className="flex-1 resize-none rounded-lg border border-orange-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-orange-500 text-white px-5 py-2 rounded-lg text-sm font-medium disabled:opacity-30 hover:bg-orange-600 transition"
          >
            {loading ? "..." : "发送"}
          </button>
        </div>
      </form>

      {feedbackOpen && (
        <FeedbackModal
          relatedQuery={lastUserQuery}
          onClose={() => setFeedbackOpen(false)}
        />
      )}
    </div>
  );
}

function MessageView({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="bg-orange-500 text-white rounded-lg px-4 py-2.5 text-sm max-w-[80%]">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 mb-1">
        <div className="w-5 h-5 bg-orange-500 text-white rounded-full flex items-center justify-center text-xs font-bold">刚</div>
        <span className="text-xs text-orange-400">刚子</span>
      </div>
      {message.toolEvents && message.toolEvents.length > 0 && (
        <div className="space-y-1">
          {message.toolEvents.map((ev, i) => (
            <ToolEventView key={i} event={ev} />
          ))}
        </div>
      )}
      {message.content && (
        <div className="bg-white border border-orange-200 rounded-lg px-5 py-4 prose prose-sm prose-zinc max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
}

function ToolEventView({ event }: { event: ToolEvent }) {
  if (event.kind === "call") {
    const argsStr = event.args ? JSON.stringify(event.args).slice(0, 120) : "";
    return (
      <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-md px-3 py-1.5 text-xs text-blue-900">
        <span>🔧</span>
        <span className="font-mono">{event.name}</span>
        <span className="text-blue-700 truncate max-w-md">{argsStr}</span>
      </div>
    );
  }

  return (
    <details className="bg-zinc-50 border border-zinc-200 rounded-md px-3 py-1.5 text-xs text-zinc-700">
      <summary className="cursor-pointer flex items-center gap-2">
        <span>📄</span>
        <span>工具返回</span>
      </summary>
      <pre className="mt-2 whitespace-pre-wrap text-zinc-600 text-xs font-mono">
        {event.preview}
      </pre>
    </details>
  );
}

function FeedbackModal({
  relatedQuery,
  onClose,
}: {
  relatedQuery?: string;
  onClose: () => void;
}) {
  const [rating, setRating] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!message.trim()) {
      setError("请填写反馈内容");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const resp = await fetch("/inspection/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: message.trim(),
          rating,
          name: name.trim() || null,
          related_query: relatedQuery || null,
        }),
      });
      if (!resp.ok) {
        const detail = await resp.text();
        throw new Error(`HTTP ${resp.status}: ${detail.slice(0, 100)}`);
      }
      setSubmitted(true);
      setTimeout(onClose, 1500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        {submitted ? (
          <div className="text-center py-8">
            <div className="text-5xl mb-3">✅</div>
            <h2 className="text-lg font-semibold text-zinc-900">感谢反馈!</h2>
            <p className="text-sm text-zinc-500 mt-1">已收到,会持续改进 🙏</p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-zinc-900">📝 用户反馈</h2>
              <button
                type="button"
                onClick={onClose}
                className="text-zinc-400 hover:text-zinc-700 text-xl leading-none"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Rating */}
              <div>
                <label className="block text-xs text-zinc-600 mb-1.5">
                  整体评价(可选)
                </label>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button
                      key={n}
                      type="button"
                      onClick={() => setRating(n === rating ? null : n)}
                      className={`w-9 h-9 rounded-md border text-base transition ${
                        rating !== null && n <= rating
                          ? "bg-yellow-50 border-yellow-300 text-yellow-600"
                          : "border-zinc-300 text-zinc-400 hover:bg-zinc-50"
                      }`}
                    >
                      ★
                    </button>
                  ))}
                </div>
              </div>

              {/* Related query */}
              {relatedQuery && (
                <div className="bg-zinc-50 border border-zinc-200 rounded-md px-3 py-2 text-xs text-zinc-600">
                  <span className="text-zinc-400">相关问题:</span>{" "}
                  {relatedQuery.slice(0, 80)}
                  {relatedQuery.length > 80 ? "..." : ""}
                </div>
              )}

              {/* Message */}
              <div>
                <label className="block text-xs text-zinc-600 mb-1.5">
                  反馈内容 <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="哪里好 / 哪里需要改进 / 有什么 bug / 想加什么功能..."
                  rows={4}
                  required
                  className="w-full resize-none rounded-md border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Name */}
              <div>
                <label className="block text-xs text-zinc-600 mb-1.5">
                  你的姓名(可选,匿名也行)
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="例:王工"
                  className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {error && (
                <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
                  {error}
                </div>
              )}

              <div className="flex gap-3 justify-end pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-sm text-zinc-600 hover:text-zinc-900"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={submitting || !message.trim()}
                  className="bg-zinc-900 text-white px-5 py-2 rounded-md text-sm font-medium disabled:opacity-30 hover:bg-zinc-700 transition"
                >
                  {submitting ? "提交中..." : "提交"}
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
