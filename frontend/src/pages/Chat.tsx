import { Camera, RotateCcw, Send, Trash2, X } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { clearChat, getChatHistory, sendChat, streamChat } from "../api/chat";
import { ApiError } from "../api/client";
import { ChatMarkdown } from "../components/ChatMarkdown";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/input";
import { useAuth } from "../hooks/useAuth";
import type { ChatMessage } from "../types";

const SUGGESTIONS = [
  { label: "Analyze my meal", prompt: "How am I doing today based on the meals I logged?" },
  { label: "How many calories should I eat?", prompt: "How many calories should I eat per day for my goal?" },
  { label: "High-protein foods", prompt: "What are some high-protein vegetarian foods?" },
  { label: "Healthy breakfast ideas", prompt: "What is a good breakfast for muscle gain?" },
  { label: "Help me lose weight", prompt: "Help me lose weight with practical meal ideas." },
  { label: "Help me gain muscle", prompt: "What should I eat after a workout to support muscle gain?" },
];

function conversationKey(userId: number) {
  return `nutrivision.conversation.${userId}`;
}

export function ChatPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [lastFailed, setLastFailed] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const stored = user ? localStorage.getItem(conversationKey(user.user_id)) : null;
    getChatHistory(stored)
      .then((data) => {
        setMessages(data.messages);
        if (data.conversationId) {
          setConversationId(data.conversationId);
          if (user) localStorage.setItem(conversationKey(user.user_id), data.conversationId);
        }
      })
      .catch(() => undefined);
  }, [user]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  function setPhoto(next: File | null) {
    if (preview) URL.revokeObjectURL(preview);
    setImage(next);
    setPreview(next ? URL.createObjectURL(next) : null);
  }

  async function submit(text: string, photo = image, retrying = false) {
    const message = text.trim();
    if ((!message && !photo) || busy) return;
    setBusy(true);
    setError("");
    setLastFailed(null);
    if (!retrying) setDraft("");
    const userLine = photo ? `${message || "What can you tell me about this food?"}` : message;
    setMessages((current) => [...current, { role: "user", content: userLine }]);
    setPhoto(null);

    try {
      if (photo) {
        const reply = await sendChat(message, conversationId, photo);
        setConversationId(reply.conversationId);
        if (user) localStorage.setItem(conversationKey(user.user_id), reply.conversationId);
        setMessages((current) => [...current, { role: "assistant", content: reply.response || reply.content }]);
      } else {
        try {
          let assembled = "";
          setMessages((current) => [...current, { role: "assistant", content: "" }]);
          const reply = await streamChat(message, conversationId, (token, cid) => {
            assembled += token;
            if (cid) {
              setConversationId(cid);
              if (user) localStorage.setItem(conversationKey(user.user_id), cid);
            }
            setMessages((current) => {
              const next = [...current];
              next[next.length - 1] = { role: "assistant", content: assembled };
              return next;
            });
          });
          const finalText = reply.response || reply.content || assembled;
          setConversationId(reply.conversationId);
          if (user) localStorage.setItem(conversationKey(user.user_id), reply.conversationId);
          setMessages((current) => {
            const next = [...current];
            next[next.length - 1] = { role: "assistant", content: finalText, message_id: reply.message_id };
            return next;
          });
        } catch {
          const reply = await sendChat(message, conversationId);
          setConversationId(reply.conversationId);
          if (user) localStorage.setItem(conversationKey(user.user_id), reply.conversationId);
          setMessages((current) => {
            const next = [...current];
            if (next[next.length - 1]?.role === "assistant") {
              next[next.length - 1] = { role: "assistant", content: reply.response || reply.content };
              return next;
            }
            return [...next, { role: "assistant", content: reply.response || reply.content }];
          });
        }
      }
    } catch (err) {
      setLastFailed(message);
      setError(err instanceof ApiError ? err.message : err instanceof Error ? err.message : "NutriCoach is unavailable right now.");
      setMessages((current) => current.filter((item, index) => !(index === current.length - 1 && item.role === "assistant" && !item.content)));
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submit(draft);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submit(draft);
    }
  }

  async function onClear() {
    if (conversationId) {
      try {
        await clearChat(conversationId);
      } catch {
        /* still reset the UI */
      }
    }
    setMessages([]);
    setConversationId(null);
    setError("");
    if (user) localStorage.removeItem(conversationKey(user.user_id));
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-9rem)] max-w-3xl flex-col">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-leaf">Assistant</p>
          <h1 className="font-display mt-1 text-4xl">NutriCoach</h1>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-2 rounded-full bg-leaf/15 px-3 py-1 text-xs text-leaf">
            <span className="h-2 w-2 rounded-full bg-leaf" /> Online
          </span>
          <Button variant="ghost" size="sm" onClick={() => void onClear()} disabled={busy}>
            <Trash2 size={14} /> Clear
          </Button>
        </div>
      </div>

      <section className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-[32px] border border-line bg-cream-soft">
        <div className="flex-1 space-y-4 overflow-y-auto p-5">
          {messages.length === 0 && !busy ? (
            <p className="text-stone">
              Ask any nutrition question, or attach a meal photo. Food-101 identifies the dish; estimated calories come
              from the nutrition table, not from the pixels.
            </p>
          ) : null}
          {messages.map((item, index) => (
            <article
              key={`${item.role}-${item.message_id ?? index}`}
              className={item.role === "user" ? "ml-8 rounded-3xl bg-forest px-4 py-3 text-cream-soft" : "mr-4 rounded-3xl bg-cream px-4 py-3"}
            >
              <p className={`text-xs uppercase tracking-[0.14em] ${item.role === "user" ? "text-cream/70" : "text-stone"}`}>
                {item.role === "user" ? "You" : "NutriVision AI"}
              </p>
              {item.role === "assistant" ? (
                <div className="mt-1 text-ink">
                  {item.content ? <ChatMarkdown text={item.content} /> : <p className="text-stone">AI is thinking…</p>}
                </div>
              ) : (
                <p className="mt-1 whitespace-pre-wrap leading-relaxed">{item.content}</p>
              )}
            </article>
          ))}
          {busy && messages[messages.length - 1]?.role !== "assistant" ? (
            <p className="text-sm text-stone">AI is thinking…</p>
          ) : null}
          {error ? (
            <div className="flex flex-wrap items-center gap-2 text-sm text-clay">
              <span>{error}</span>
              {lastFailed ? (
                <Button variant="ghost" size="sm" onClick={() => void submit(lastFailed, null, true)}>
                  <RotateCcw size={14} /> Retry
                </Button>
              ) : null}
            </div>
          ) : null}
          <div ref={endRef} />
        </div>

        <div className="flex flex-wrap gap-2 border-t border-line px-4 py-3">
          {SUGGESTIONS.map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => void submit(item.prompt)}
              className="rounded-full border border-line px-3 py-1.5 text-xs text-stone hover:border-forest/40 hover:text-forest"
            >
              {item.label}
            </button>
          ))}
        </div>

        {preview ? (
          <div className="flex items-center gap-3 border-t border-line px-4 py-2">
            <img src={preview} alt="Food to analyze" className="h-14 w-14 rounded-xl object-cover" />
            <p className="flex-1 text-xs text-stone">Photo will be classified with your Food-101 model before the nutrition reply.</p>
            <button type="button" onClick={() => setPhoto(null)} className="text-stone hover:text-ink">
              <X size={16} />
            </button>
          </div>
        ) : null}

        <form onSubmit={onSubmit} className="flex items-end gap-2 border-t border-line p-4">
          <input
            ref={fileRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(event) => setPhoto(event.target.files?.[0] ?? null)}
          />
          <Button type="button" variant="secondary" size="icon" onClick={() => fileRef.current?.click()} disabled={busy}>
            <Camera size={16} />
          </Button>
          <Textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask NutriVision AI..."
            maxLength={2000}
            rows={2}
            className="max-h-32 min-h-12 resize-none"
          />
          <Button type="submit" disabled={busy || (!draft.trim() && !image)}>
            Send <Send size={14} />
          </Button>
        </form>
      </section>
      <p className="mt-3 text-xs text-stone">
        General nutrition guidance only — not medical advice. Calories and macros are estimates. Enter sends, Shift+Enter
        adds a new line.
      </p>
    </div>
  );
}
