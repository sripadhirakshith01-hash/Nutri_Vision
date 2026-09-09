import { apiFetch, API_BASE, getToken } from "./client";
import type { ChatMessage, ChatResponse } from "../types";

export function sendChat(message: string, conversationId?: string | null, image?: File | null) {
  if (image) {
    const body = new FormData();
    body.append("message", message);
    if (conversationId) body.append("conversationId", conversationId);
    body.append("image", image);
    return apiFetch<ChatResponse>("/api/chat", { method: "POST", body });
  }
  return apiFetch<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message, conversationId: conversationId || null }),
  });
}

export async function streamChat(
  message: string,
  conversationId: string | null | undefined,
  onToken: (token: string, conversationId: string) => void,
): Promise<ChatResponse> {
  const headers = new Headers({ "Content-Type": "application/json" });
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/chat/stream`, {
      method: "POST",
      headers,
      body: JSON.stringify({ message, conversationId: conversationId || null }),
    });
  } catch {
    throw new Error("The backend is unavailable. Start the FastAPI server and try again.");
  }
  if (!response.ok || !response.body) {
    throw new Error("The nutrition assistant is unavailable right now.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let full = "";
  let cid = conversationId || "";
  let messageId: number | undefined;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const line = part.split("\n").find((item) => item.startsWith("data:"));
      if (!line) continue;
      try {
        const payload = JSON.parse(line.slice(5).trim()) as {
          token?: string;
          conversationId?: string;
          done?: boolean;
          error?: string;
          response?: string;
          message_id?: number;
        };
        if (payload.conversationId) cid = payload.conversationId;
        if (payload.error) {
          throw new Error(payload.error);
        }
        if (payload.token) {
          full += payload.token;
          onToken(payload.token, cid);
        }
        if (payload.response) full = payload.response;
        if (payload.message_id) messageId = payload.message_id;
      } catch (err) {
        if (err instanceof SyntaxError) continue;
        throw err;
      }
    }
  }

  return {
    role: "assistant",
    content: full,
    response: full,
    conversationId: cid,
    message_id: messageId,
  };
}

export async function getChatHistory(conversationId?: string | null) {
  const suffix = conversationId ? `?conversationId=${encodeURIComponent(conversationId)}` : "";
  const data = await apiFetch<{ conversationId: string | null; messages: ChatMessage[] } | ChatMessage[]>(
    `/api/chat/history${suffix}`,
  );
  if (Array.isArray(data)) return { conversationId: conversationId ?? null, messages: data };
  return data;
}

export function clearChat(conversationId: string) {
  return apiFetch<{ ok: boolean }>(`/api/chat?conversationId=${encodeURIComponent(conversationId)}`, {
    method: "DELETE",
  });
}
