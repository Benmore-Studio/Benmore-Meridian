// chat-component.tsx — React chat UI starter.
//
// Renders an always-on bottom bar plus an overlay panel triggered by Cmd+K.
// Sends POST /api/v1/chat/ with auth, renders the response with suggestion
// chips, handles `navigate_to` (zero-render route change) and `upsell`
// (inline CTA for tier-gated tools).
//
// SCAFFOLD: assumes you have `useAuth()` returning `{ accessToken }`,
// a `useNavigate()` from your router, and a `cn()` className helper. Adapt
// imports as needed.

// @ts-nocheck — disabled because this is a SCAFFOLD.

import { useState, useCallback, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

interface ChatHistoryMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatAction {
  tool: string;
  args: Record<string, unknown>;
  result: unknown;
}

interface ChatSuggestion {
  label: string;
  message: string;
}

interface UpsellPayload {
  label: string;
  path: string;
  feature: string;
}

interface ChatResponse {
  response: string;
  actions: ChatAction[];
  confidence?: number;
  intent_matched?: string | null;
  suggestions?: ChatSuggestion[];
  navigate_to?: string | null;
  error_code?: string | null;
  upsell?: UpsellPayload | null;
}

interface AssistantMessage extends ChatHistoryMessage {
  role: "assistant";
  actions?: ChatAction[];
  suggestions?: ChatSuggestion[];
  upsell?: UpsellPayload | null;
}

type ChatMessage = ChatHistoryMessage | AssistantMessage;

// Replace with your own auth hook.
function useAuth() {
  return { accessToken: localStorage.getItem("access_token") };
}

export function ChatPanel({ contextProps = {} }: { contextProps?: Record<string, unknown> }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const messagesRef = useRef(messages);
  messagesRef.current = messages;

  // Cmd+K trigger.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const send = useCallback(
    async (text: string) => {
      if (!text.trim()) return;
      setLoading(true);

      // Append user message immediately for snappy UX.
      const userMsg: ChatMessage = { role: "user", content: text };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");

      // Build history from the message list (last 19 + new user message).
      const history = [
        ...messagesRef.current
          .slice(-19)
          .map((m) => ({ role: m.role, content: m.content })),
        { role: "user" as const, content: text },
      ];

      try {
        const resp = await fetch("/api/v1/chat/smart/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            message: text,
            history,
            context: { page: window.location.pathname, ...contextProps },
          }),
        });

        if (resp.status === 401) {
          // TODO: implement token refresh + retry; or redirect to login.
          throw new Error("Unauthorized");
        }
        if (!resp.ok) {
          throw new Error(`HTTP ${resp.status}`);
        }

        const data: ChatResponse = await resp.json();

        // Zero-render navigation: route without showing an assistant bubble.
        if (data.navigate_to) {
          setIsOpen(false);
          navigate(data.navigate_to);
          return;
        }

        const assistantMsg: AssistantMessage = {
          role: "assistant",
          content: data.response,
          actions: data.actions,
          suggestions: data.suggestions,
          upsell: data.upsell ?? null,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        const errMsg: ChatMessage = {
          role: "assistant",
          content:
            err instanceof Error && err.message === "Unauthorized"
              ? "Your session expired. Please sign in again."
              : "Sorry — the assistant errored out. Try again in a moment.",
        };
        setMessages((prev) => [...prev, errMsg]);
      } finally {
        setLoading(false);
      }
    },
    [accessToken, contextProps, navigate],
  );

  return (
    <>
      {/* Always-on bottom bar */}
      <div className="fixed bottom-4 inset-x-0 mx-auto max-w-2xl px-4 z-40">
        <button
          className="w-full bg-white dark:bg-zinc-900 border rounded-full px-4 py-2 text-left text-zinc-500 shadow"
          onClick={() => setIsOpen(true)}
        >
          Ask anything… <span className="text-xs">⌘K</span>
        </button>
      </div>

      {/* Overlay panel */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-50 flex items-end sm:items-center justify-center"
          onClick={() => setIsOpen(false)}
        >
          <div
            className="bg-white dark:bg-zinc-900 w-full max-w-2xl rounded-t-2xl sm:rounded-2xl p-4 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Message list */}
            <div className="space-y-3 max-h-[60vh] overflow-y-auto mb-3">
              {messages.map((m, i) => (
                <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                  <div
                    className={
                      "inline-block px-3 py-2 rounded-2xl " +
                      (m.role === "user"
                        ? "bg-blue-500 text-white"
                        : "bg-zinc-100 dark:bg-zinc-800")
                    }
                  >
                    {m.content}
                  </div>
                  {/* Suggestion chips on the most recent assistant message */}
                  {m.role === "assistant" &&
                    i === messages.length - 1 &&
                    (m as AssistantMessage).suggestions?.length ? (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {(m as AssistantMessage).suggestions!.map((s, j) => (
                        <button
                          key={j}
                          className="px-2 py-1 text-xs rounded-full border hover:bg-zinc-100 active:scale-[0.97]"
                          onClick={() => send(s.message)}
                        >
                          {s.label}
                        </button>
                      ))}
                    </div>
                  ) : null}
                  {/* Pro upsell payload */}
                  {m.role === "assistant" && (m as AssistantMessage).upsell ? (
                    <a
                      href={(m as AssistantMessage).upsell!.path}
                      className="inline-block mt-2 px-3 py-1.5 rounded-full bg-amber-500 text-white text-sm hover:bg-amber-600"
                    >
                      {(m as AssistantMessage).upsell!.label}
                    </a>
                  ) : null}
                </div>
              ))}
              {loading && (
                <div className="text-zinc-400 text-sm italic">Thinking…</div>
              )}
            </div>

            {/* Input */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                send(input);
              }}
              className="flex gap-2"
            >
              <input
                autoFocus
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask anything… (Esc to close)"
                className="flex-1 border rounded-full px-3 py-2"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="px-4 py-2 rounded-full bg-blue-500 text-white disabled:opacity-50 active:scale-[0.97]"
              >
                Send
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
