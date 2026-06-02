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

interface Conversation {
  id: string;
  title: string;
  createdAt: number;
  messages: Message[];
}

const SUGGESTED_QUERIES = [
  "砌体加固改造项目需要做哪些检测？引用哪些标准？",
  "回弹法检测混凝土的取样数量是多少？",
  "材料检测的平均折扣是多少？同比去年变化如何？",
  "钢结构工程中常见的质量缺陷有哪些？检测时需重点关注什么？",
];

function getConversations(): Conversation[] {
  try {
    const raw = localStorage.getItem("agent_conversations");
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function saveConversations(convs: Conversation[]) {
  try {
    localStorage.setItem("agent_conversations", JSON.stringify(convs));
  } catch { /* localStorage full */ }
}

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isComposing, setIsComposing] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadedFileCtx = useRef<{ name: string; text: string } | null>(null);

  const lastUserQuery = [...messages].reverse().find((m) => m.role === "user")?.content;

  // 初始化：从 localStorage 恢复
  useEffect(() => {
    const convs = getConversations();
    if (convs.length > 0) {
      setConversations(convs);
      setActiveConvId(convs[0].id);
      setMessages(convs[0].messages);
    } else {
      newConversation();
    }
  }, []);

  // 消息变化时持久化
  useEffect(() => {
    if (!activeConvId) return;
    const updated = conversations.map((c) =>
      c.id === activeConvId ? { ...c, messages } : c
    );
    setConversations(updated);
    saveConversations(updated);
  }, [messages]);

  // 滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  function newConversation() {
    const conv: Conversation = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      title: "新对话",
      createdAt: Date.now(),
      messages: [],
    };
    const updated = [conv, ...conversations];
    setConversations(updated);
    setActiveConvId(conv.id);
    setMessages([]);
    saveConversations(updated);
    setSidebarOpen(false);
  }

  function switchConversation(id: string) {
    const conv = conversations.find((c) => c.id === id);
    if (conv) {
      setActiveConvId(id);
      setMessages(conv.messages);
      setSidebarOpen(false);
    }
  }

  function deleteConversation(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    const updated = conversations.filter((c) => c.id !== id);
    setConversations(updated);
    saveConversations(updated);
    if (id === activeConvId) {
      if (updated.length > 0) {
        setActiveConvId(updated[0].id);
        setMessages(updated[0].messages);
      } else {
        newConversation();
      }
    }
  }

  function clearCurrentChat() {
    const updated = conversations.map((c) =>
      c.id === activeConvId ? { ...c, messages: [], title: "新对话" } : c
    );
    setConversations(updated);
    setMessages([]);
    saveConversations(updated);
  }

  async function sendMessage(content: string) {
    if (!content.trim() || loading) return;

    // 如果有上传的文件上下文，附加到消息中
    let fullContent = content.trim();
    if (uploadedFileCtx.current) {
      const { name, text } = uploadedFileCtx.current;
      fullContent = `[已上传文件: ${name}]\n以下是文件内容:\n${text}\n---\n用户问题: ${fullContent}`;
      uploadedFileCtx.current = null;  // 用完即清
    }

    const userMsg: Message = { role: "user", content: fullContent };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    // 第一条消息作为对话标题
    if (messages.length === 0) {
      const title = content.trim().slice(0, 30) + (content.trim().length > 30 ? "..." : "");
      const updatedConvs = conversations.map((c) =>
        c.id === activeConvId ? { ...c, title } : c
      );
      setConversations(updatedConvs);
      saveConversations(updatedConvs);
    }

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

        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

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

  async function uploadImage(file: File) {
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const resp = await fetch("/inspection/upload", { method: "POST", body: form });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: "上传失败" }));
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      // 图片文件：附带 URL 供 Agent 的 analyze_image 工具使用
      const text = data.image_url
        ? `[用户上传的图片，链接: ${data.image_url}]\n请使用 analyze_image 工具分析该图片。`
        : data.text || "";
      uploadedFileCtx.current = { name: file.name || "截图.png", text };

      setMessages((prev) => [...prev, {
        role: "assistant",
        content: `📎 已粘贴图片: **${file.name || "截图"}**\n\n输入你想对图片提的问题，如"分析这张图""提取文字""描述图片内容"`,
      }]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      alert("图片上传失败: " + msg);
    } finally {
      setUploading(false);
    }
  }

  function handlePaste(e: React.ClipboardEvent<HTMLTextAreaElement>) {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of Array.from(items)) {
      if (item.type.startsWith("image/")) {
        e.preventDefault();
        const file = item.getAsFile();
        if (file) uploadImage(file);
        return;
      }
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const resp = await fetch("/inspection/upload", { method: "POST", body: form });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: "上传失败" }));
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      uploadedFileCtx.current = { name: file.name, text: data.text || "" };

      // 只在聊天里显示文件名
      const systemMsg: Message = {
        role: "assistant",
        content: `📎 已上传: **${file.name}**（${data.text?.length || 0} 字）\n\n请描述你需要对这份文件做什么，比如"分析这份合同""总结这份报告""提取检测项目"`,
      };
      setMessages((prev) => [...prev, systemMsg]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      alert("文件上传失败: " + msg);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="flex h-screen">
      {/* 侧边栏遮罩（手机） */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-20 bg-black/40 md:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* 侧边栏 */}
      <aside className={`fixed md:relative z-30 h-full w-64 bg-white border-r border-zinc-200 flex flex-col transition-transform ${sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"} md:flex-shrink-0`}>
        <div className="px-4 py-3 border-b border-zinc-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-zinc-700">💬 对话记录</h2>
          <button onClick={newConversation} className="text-xl text-zinc-400 hover:text-zinc-700 leading-none" title="新对话">+</button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {conversations.map((c) => (
            <div
              key={c.id}
              onClick={() => switchConversation(c.id)}
              className={`px-4 py-2.5 cursor-pointer border-b border-zinc-50 group flex items-center justify-between ${c.id === activeConvId ? "bg-blue-50 border-l-2 border-l-blue-500" : "hover:bg-zinc-50"}`}
            >
              <div className="min-w-0 flex-1">
                <div className="text-xs font-medium text-zinc-700 truncate">{c.title}</div>
                <div className="text-[10px] text-zinc-400 mt-0.5">
                  {new Date(c.createdAt).toLocaleDateString("zh-CN")} · {c.messages.length} 条消息
                </div>
              </div>
              <button
                onClick={(e) => deleteConversation(c.id, e)}
                className="text-zinc-300 hover:text-red-500 text-xs opacity-0 group-hover:opacity-100 transition ml-2"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* 主内容区 */}
      <div className="flex-1 flex flex-col h-screen min-w-0">
        {/* Header */}
        <header className="bg-white border-b border-zinc-200 px-4 py-3 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="md:hidden text-zinc-600 text-lg"
            >
              ☰
            </button>
            <h1 className="text-lg font-semibold text-zinc-900">🏗️ 检测行业 Agent</h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={clearCurrentChat}
              disabled={messages.length === 0}
              className="text-xs text-zinc-500 hover:text-zinc-800 border border-zinc-200 rounded-md px-2.5 py-1 disabled:opacity-30 transition"
            >
              🗑 清空
            </button>
            <button
              onClick={() => setFeedbackOpen(true)}
              className="text-xs text-zinc-600 hover:text-zinc-900 border border-zinc-300 rounded-md px-3 py-1.5 transition"
            >
              📝 反馈
            </button>
            <span className="text-xs text-zinc-400 hidden sm:inline">DeepSeek + bge-zh + Chroma</span>
          </div>
        </header>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-10">
              <p className="text-zinc-600 mb-6 text-sm">问点啥呢?</p>
              <div className="grid sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
                {SUGGESTED_QUERIES.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(q)}
                    disabled={loading}
                    className="text-left text-sm bg-white border border-zinc-200 rounded-lg p-3 hover:border-zinc-400 hover:bg-zinc-50 transition disabled:opacity-50"
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
            <div className="flex items-center gap-2 text-zinc-500 text-sm">
              <div className="animate-pulse">●●●</div>
              <span>Agent 思考中...</span>
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-zinc-200 bg-white px-6 py-4"
      >
        {/* 文件附件提示 */}
        {uploadedFileCtx.current && (
          <div className="max-w-3xl mx-auto mb-2 flex items-center gap-2 text-xs text-blue-600 bg-blue-50 border border-blue-200 rounded-md px-3 py-1.5">
            <span>📎</span>
            <span className="font-medium">{uploadedFileCtx.current.name}</span>
            <span className="text-blue-400">已附加</span>
            <button
              type="button"
              onClick={() => { uploadedFileCtx.current = null; }}
              className="ml-auto text-blue-400 hover:text-red-500"
            >
              ✕ 移除
            </button>
          </div>
        )}
        <div className="max-w-3xl mx-auto flex gap-2 items-end">
          {/* 文件上传 */}
          <label className="flex items-center justify-center w-10 h-10 rounded-lg border border-zinc-300 bg-white cursor-pointer hover:bg-zinc-50 transition flex-shrink-0" title="上传文件 (PDF/Word/Excel/图片等)">
            {uploading
              ? <span className="text-sm animate-pulse">⏳</span>
              : <span className="text-xl">📎</span>
            }
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md,.pdf,.docx,.doc,.xlsx,.xls,.json,.csv,.py,.js,.ts,.html,.css,.xml,.yaml,.yml,.log,.png,.jpg,.jpeg,.gif,.bmp,.webp"
              onChange={handleFileUpload}
              className="hidden"
              disabled={uploading}
            />
          </label>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPaste={handlePaste}
            onCompositionStart={() => setIsComposing(true)}
            onCompositionEnd={(e) => {
              setIsComposing(false);
              setInput((e.target as HTMLTextAreaElement).value);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey && !isComposing) {
                e.preventDefault();
                sendMessage(input);
              }
            }}
            placeholder="输入工程检测问题(Enter 发送 / Shift+Enter 换行)"
            rows={2}
            className="flex-1 resize-none rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-zinc-900 text-white px-5 py-2 rounded-lg text-sm font-medium disabled:opacity-30 hover:bg-zinc-700 transition"
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
    </div>
  );
}

function MessageView({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="bg-zinc-900 text-white rounded-lg px-4 py-2.5 text-sm max-w-[80%]">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {message.toolEvents && message.toolEvents.length > 0 && (
        <div className="space-y-1">
          {message.toolEvents.map((ev, i) => (
            <ToolEventView key={i} event={ev} />
          ))}
        </div>
      )}
      {message.content && (
        <div className="bg-white border border-zinc-200 rounded-lg px-5 py-4 prose prose-sm prose-zinc max-w-none">
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

              {relatedQuery && (
                <div className="bg-zinc-50 border border-zinc-200 rounded-md px-3 py-2 text-xs text-zinc-600">
                  <span className="text-zinc-400">相关问题:</span>{" "}
                  {relatedQuery.slice(0, 80)}
                  {relatedQuery.length > 80 ? "..." : ""}
                </div>
              )}

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
