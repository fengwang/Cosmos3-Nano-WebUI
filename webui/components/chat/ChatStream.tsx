"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import { useLiveRegion } from "@/app/(studio)/useLiveRegion";
import { Banner } from "@/components/Banner";
import { Textarea } from "@/components/Textarea";
import { Card, PillButton } from "@/design-system";
import { API_PREFIX } from "@/lib/api/client";
import { createEventStream } from "@/lib/sse/createEventStream";

import styles from "./chat.module.css";

interface Turn {
  role: "user" | "assistant";
  text: string;
}

/**
 * Reasoning chat over `POST /api/v1/reason` SSE (token `{delta}` / error / done). The reason stream
 * carries no event ids, so a mid-stream drop cannot resume — `onError` resets the partial and shows a
 * "reconnecting…" notice while `createEventStream` re-POSTs and the server restarts the completion (EC-U2).
 */
export function ChatStream() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  // Streamed deltas accumulate in a ref and flush to React state once per animation frame, so a long
  // (now-uncapped) response renders in full without an O(n²) re-render-per-token cliff (FR-10, R-09).
  const pendingRef = useRef("");
  const frameRef = useRef<number | null>(null);
  const announce = useLiveRegion();

  // Abort an in-flight stream + drop any pending flush if the user navigates away mid-completion.
  useEffect(
    () => () => {
      abortRef.current?.abort();
      if (frameRef.current != null) cancelAnimationFrame(frameRef.current);
    },
    [],
  );

  function updateAssistant(fn: (text: string) => string) {
    setTurns((prev) => {
      const copy = [...prev];
      const last = copy[copy.length - 1];
      if (last && last.role === "assistant") copy[copy.length - 1] = { ...last, text: fn(last.text) };
      return copy;
    });
  }

  // Render the full accumulated buffer into the assistant turn.
  function renderPending() {
    updateAssistant(() => pendingRef.current);
  }

  // Coalesce a burst of tokens into a single flush per frame.
  function scheduleFlush() {
    if (frameRef.current != null) return;
    frameRef.current = requestAnimationFrame(() => {
      frameRef.current = null;
      renderPending();
    });
  }

  function cancelPendingFlush() {
    if (frameRef.current != null) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
  }

  async function send(event: FormEvent) {
    event.preventDefault();
    const prompt = input.trim();
    if (!prompt || streaming) return;
    setError(null);
    setInput("");
    setTurns((prev) => [...prev, { role: "user", text: prompt }, { role: "assistant", text: "" }]);
    setStreaming(true);
    announce("Reasoning started.");

    const controller = new AbortController();
    abortRef.current = controller;
    pendingRef.current = "";
    let gotToken = false;
    let sawError = false;
    await createEventStream({
      url: `${API_PREFIX}/v1/reason`,
      method: "POST",
      headers: { "content-type": "application/json" },
      // No max_output_tokens: the backend context window is the only ceiling (FR-10, INV-12).
      body: JSON.stringify({ prompt }),
      signal: controller.signal,
      heartbeatTimeoutMs: 30_000,
      onEvent: (ev) => {
        if (ev.event === "token") {
          gotToken = true;
          setReconnecting(false);
          try {
            const data = JSON.parse(ev.data) as { delta?: unknown };
            if (typeof data.delta === "string") {
              pendingRef.current += data.delta;
              scheduleFlush();
            }
          } catch {
            // ignore a malformed token frame
          }
        } else if (ev.event === "error") {
          sawError = true;
          try {
            const data = JSON.parse(ev.data) as { message?: unknown };
            setError(typeof data.message === "string" ? data.message : "Reasoning failed.");
          } catch {
            setError("Reasoning failed.");
          }
        }
      },
      onError: () => {
        // id-less stream: a drop restarts the completion — clear the partial + show reconnecting.
        gotToken = false;
        setReconnecting(true);
        pendingRef.current = "";
        cancelPendingFlush();
        renderPending();
      },
    });

    // Final flush: render any tokens still buffered from the last frame; no flush is left pending.
    cancelPendingFlush();
    renderPending();
    setStreaming(false);
    setReconnecting(false);
    abortRef.current = null;
    if (!gotToken && !sawError && !controller.signal.aborted) {
      // Reconnect retries exhausted before any output — never leave a silent empty turn (RK-09).
      setError("Reasoning was interrupted before any response. Please try again.");
    }
    announce(sawError || (!gotToken && !controller.signal.aborted) ? "Reasoning failed." : "Reasoning complete.");
  }

  return (
    <Card title="Reasoning chat">
      <div className={styles.chat}>
        <ol className={styles.transcript} data-testid="transcript">
          {turns.map((turn, i) => (
            <li
              key={i}
              className={turn.role === "user" ? styles.user : styles.assistant}
              data-role={turn.role}
              data-testid={turn.role === "assistant" ? "assistant-turn" : "user-turn"}
            >
              <span className={styles.role}>{turn.role === "user" ? "You" : "Reasoner"}</span>
              <p className={styles.bubble}>{turn.text || (turn.role === "assistant" && streaming ? "…" : "")}</p>
            </li>
          ))}
        </ol>

        {reconnecting ? (
          <p className={styles.reconnect} data-testid="reconnecting" role="status">
            Connection dropped — reconnecting…
          </p>
        ) : null}
        {error ? <Banner severity="error">{error}</Banner> : null}

        <form onSubmit={send} className={styles.composer}>
          <Textarea
            label="Your message"
            value={input}
            rows={2}
            placeholder="Ask the reasoner…"
            onChange={(e) => setInput(e.target.value)}
            data-testid="chat-input"
          />
          <PillButton tone="accent" type="submit" disabled={streaming || input.trim().length === 0} data-testid="chat-send">
            {streaming ? "Streaming…" : "Send"}
          </PillButton>
        </form>
      </div>
    </Card>
  );
}
