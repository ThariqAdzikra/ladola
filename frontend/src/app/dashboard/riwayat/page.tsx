"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ChevronLeft, MessageSquare } from "lucide-react";
import {
  loadChatSessions,
  type StoredChatSession,
} from "@/lib/chatHistory";

function formatDate(iso: string) {
  try {
    return new Intl.DateTimeFormat("id-ID", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export default function RiwayatChatPage() {
  const [sessions, setSessions] = useState<StoredChatSession[]>([]);

  useEffect(() => {
    queueMicrotask(() => {
      setSessions(loadChatSessions());
    });
  }, []);

  return (
    <div className="min-h-screen bg-white text-foreground">
      <header className="sticky top-0 z-10 border-b border-slate-100 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-lg items-center gap-3 px-4 py-4">
          <Link
            href="/dashboard"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-slate-200 text-slate-600 transition hover:bg-primary-50 hover:text-primary-800"
            aria-label="Kembali ke scan"
          >
            <ChevronLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="font-[family-name:var(--font-outfit),sans-serif] text-lg font-semibold text-foreground">
              Riwayat chat
            </h1>
            <p className="text-xs text-slate-500">
              Percakapan tersimpan di perangkat ini
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-lg px-4 py-6 pb-12">
        {sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/80 px-6 py-16 text-center">
            <MessageSquare className="mb-3 h-10 w-10 text-slate-300" />
            <p className="text-sm font-medium text-slate-700">
              Belum ada riwayat chat
            </p>
            <p className="mt-1 max-w-xs text-xs leading-relaxed text-slate-500">
              Setelah Anda mengobrol dengan AI dari hasil scan, percakapan akan
              muncul di sini.
            </p>
            <Link
              href="/dashboard"
              className="mt-6 rounded-full bg-primary-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-700"
            >
              Mulai scan
            </Link>
          </div>
        ) : (
          <ul className="space-y-3">
            {sessions.map((s) => {
              const messages = s.messages ?? [];
              return (
                <li
                  key={s.id}
                  className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="font-semibold text-foreground">{s.diagnosis}</p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        {formatDate(s.updatedAt)} · {messages.length} pesan
                      </p>
                    </div>
                  </div>
                  {messages.length > 0 && (
                    <p className="mt-3 line-clamp-2 text-sm text-slate-600">
                      {messages[messages.length - 1]?.text}
                    </p>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </main>
    </div>
  );
}
