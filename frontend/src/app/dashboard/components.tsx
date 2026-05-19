"use client";

import {
  Camera, Bot, Leaf, Sparkles,
} from "lucide-react";

/* ─── Types ─── */
export type View = "home" | "scan" | "analyzing" | "result" | "chat";

export type ScoreItem = { label: string; score: number };

export type PredictionResult = {
  disease_id: number;
  label: string;
  label_en: string;
  confidence: number;
  severity: string;
  type: string;
  description: string;
  symptoms: string[];
  treatment: string[];
  prevention: string[];
  all_scores: ScoreItem[];
  inference_time_ms: number;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  text: string;
  image?: string;
  prediction?: PredictionResult;
};

/* ─── Constants ─── */
export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || (typeof window !== "undefined" ? window.location.origin : "");

export const VIEW_ANIM = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.35, ease: [0.22, 1, 0.36, 1] },
};

export const QUICK_PROMPTS = [
  "Bagaimana cara mengobatinya?",
  "Apa penyebab utamanya?",
  "Apakah menular ke tanaman lain?",
  "Rekomendasi fungisida?",
];

export const MOCK_PREDICTION: PredictionResult = {
  disease_id: 0,
  label: "Contoh (offline)",
  label_en: "Demo",
  confidence: 0.72,
  severity: "sedang",
  type: "leaf",
  description: "Backend tidak merespons. Ini contoh tampilan hasil.",
  symptoms: ["Bercak tidak merata pada daun", "Tepi daun mengering"],
  treatment: [
    "Isolasi tanaman terdampak",
    "Gunakan fungisida sesuai anjuran",
    "Jaga kelembaban dan sirkulasi udara",
  ],
  prevention: ["Rotasi tanaman", "Sanitasi alat", "Pemantauan mingguan"],
  all_scores: [],
  inference_time_ms: 0,
};

/* ─── Helpers ─── */
export function severityColor(sev: string) {
  const s = sev.toLowerCase();
  if (s.includes("parah")) return { bg: "bg-rose-50", text: "text-rose-700", border: "border-rose-200", dot: "bg-rose-500" };
  if (s.includes("sedang")) return { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200", dot: "bg-amber-500" };
  return { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" };
}

export function buildIntro(p: PredictionResult, usedMock: boolean) {
  const pct = Math.round(p.confidence * 100);
  const prefix = usedMock ? "(Mode contoh — sambungkan backend untuk hasil nyata.) " : "";
  return (
    `${prefix}Halo! Dari foto yang Anda kirim, saya mendeteksi **${p.label}** ` +
    `dengan tingkat keyakinan **${pct}%**.\n\n${p.description}\n\n` +
    `Silakan tanyakan detail penanganan, dosis, atau pencegahan — saya siap membantu!`
  );
}

export function mockReply(text: string, p: PredictionResult): string {
  const t = text.toLowerCase();
  if (t.includes("obat") || t.includes("fungisida") || t.includes("semprot"))
    return `Untuk ${p.label}: ${p.treatment[0] ?? "Ikuti petunjuk label pestisida."} Dokumentasikan perkembangan dengan foto baru.`;
  if (t.includes("cegah") || t.includes("hindari"))
    return `Pencegahan ${p.label}: ${p.prevention[0] ?? "Jaga sanitasi dan jarak tanam."}`;
  return `Berdasarkan diagnosis ${p.label}: ${p.treatment[1] ?? p.treatment[0] ?? p.prevention[0]}. Butuh detail langkah demi langkah?`;
}

/* ─── UI Components ─── */
export function LogoMark({ variant = "dark" }: { variant?: "dark" | "light" }) {
  const light = variant === "light";
  return (
    <div className="flex items-center gap-2.5">
      <div className={`relative flex h-8 w-8 items-center justify-center rounded-xl ${light ? "bg-white/10" : "bg-gradient-to-br from-primary-600 to-emerald-600"} shadow-sm`}>
        <Leaf className={`h-4 w-4 ${light ? "text-emerald-300" : "text-white"}`} />
      </div>
      <span className={`font-[family-name:var(--font-outfit),sans-serif] text-[15px] font-bold tracking-tight ${light ? "text-white" : "text-foreground"}`}>
        ChilliGuard
      </span>
    </div>
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  const c = severityColor(severity);
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-wide ${c.bg} ${c.text} ${c.border} border`}>
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`} />
      {severity}
    </span>
  );
}

export function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? "from-emerald-500 to-emerald-400" : pct >= 50 ? "from-amber-500 to-amber-400" : "from-rose-500 to-rose-400";
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold text-slate-500">Confidence</span>
        <span className="text-sm font-bold text-foreground">{pct}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div className={`cg-fill-bar h-full rounded-full bg-gradient-to-r ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-4">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary-100 text-primary-600">
        <Bot className="h-4 w-4" />
      </div>
      <div className="flex items-center gap-1.5 rounded-2xl bg-white px-5 py-3 shadow-sm border border-slate-100">
        {[0, 1, 2].map((i) => (
          <div key={i} className="cg-typing-dot h-2 w-2 rounded-full bg-primary-400" />
        ))}
      </div>
    </div>
  );
}

export function EmptyState({ onScan }: { onScan: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-20 text-center">
      <div className="cg-float mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-primary-100 to-emerald-100 shadow-lg shadow-primary-100/50">
        <Sparkles className="h-10 w-10 text-primary-600" />
      </div>
      <h2 className="font-[family-name:var(--font-outfit),sans-serif] text-2xl font-bold text-foreground">
        Mulai Diagnosis Pertama
      </h2>
      <p className="mt-2 max-w-sm text-sm leading-relaxed text-slate-500">
        Ambil foto daun cabai Anda dan biarkan AI kami menganalisis kondisi tanaman dalam hitungan detik.
      </p>
      <button
        onClick={onScan}
        className="mt-8 flex items-center gap-2 rounded-2xl bg-gradient-to-r from-primary-600 to-emerald-600 px-6 py-3.5 text-sm font-bold text-white shadow-lg shadow-primary-200/50 transition-all hover:shadow-xl hover:shadow-primary-200/60 active:scale-[0.98]"
      >
        <Camera className="h-5 w-5" />
        Mulai Scan
      </button>
    </div>
  );
}
