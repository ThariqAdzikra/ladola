"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import {
  ChevronLeft,
  Camera,
  Loader2,
  Send,
  Bot,
  User,
  HelpCircle,
  Menu,
  Check,
  RefreshCw,
  X,
  History,
  MessageSquare,
  LogOut,
  Images,
  Trash2,
} from "lucide-react";
import { motion, AnimatePresence, useScroll, useTransform, useSpring } from "framer-motion";
import { useSession, signOut } from "next-auth/react";
import { useTheme } from "@/context/ThemeContext";
import NextImage from "next/image";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_BASE = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || (typeof window !== "undefined" ? window.location.origin : "");

type View = "home" | "scan" | "analyzing" | "result" | "chat";
type ScoreItem = { label: string; score: number };
type PredictionResult = {
  disease_id: number; label: string; label_en: string; confidence: number;
  severity: string; type: string; description: string; symptoms: string[];
  treatment: string[]; prevention: string[]; all_scores: ScoreItem[]; inference_time_ms: number;
};
type ChatMessage = { id: string; role: "user" | "assistant" | "system"; text: string; image?: string; prediction?: PredictionResult; };
type StoredChatSession = { id: number; title: string; created_at: string; diagnosis?: string; };

const VIEW_TRANSITION = { initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -10 }, transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] as const } };

const QUICK_PROMPTS = [
  "Bagaimana cara mengobatinya secara organik?", "Apa penyebab utama penyakit ini muncul?",
  "Apakah menular ke tanaman cabai lain di sekitarnya?", "Rekomendasi fungisida atau pestisida yang tepat?",
  "Cara mencegahnya datang kembali musim depan?", "Apakah cuaca berpengaruh terhadap tingkat keparahan?",
  "Berapa dosis pemupukan yang ideal untuk pemulihan?", "Tanda-tanda awal yang harus saya waspadai sejak dini?",
];

function buildIntro(p: PredictionResult, usedMock: boolean) {
  const pct = Math.round(p.confidence * 100);
  const prefix = usedMock ? "(Mode contoh) " : "";
  return `${prefix}Halo, saya asisten ChilliGuard. Terdeteksi ${p.label} (${pct}%). ${p.description}\n\nSilakan tanya penanganan atau dosis—saya merujuk hasil scan ini.`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/** Safely parse JSON from a fetch Response — avoids SyntaxError when the server
 *  returns an HTML error page (e.g. nginx 502). */
async function safeJson<T = unknown>(res: Response): Promise<T> {
  const ct = res.headers.get("content-type") ?? "";
  if (!ct.includes("application/json")) {
    const text = await res.text().catch(() => "");
    throw new Error(
      `Server returned HTTP ${res.status} (${res.statusText || "error"}) — expected JSON but got: ${text.slice(0, 120)}`
    );
  }
  return res.json() as Promise<T>;
}

function getChatErrorMessage(errorData: unknown, status: number) {
  const detail = isRecord(errorData) ? errorData.detail : undefined;
  const detailRecord = isRecord(detail) ? detail : undefined;
  const code = typeof detailRecord?.code === "string" ? detailRecord.code : undefined;
  const detailMessage = detailRecord?.message;
  const rawMessage = typeof detail === "string" ? detail : typeof detailMessage === "string" ? detailMessage : undefined;
  const normalized = `${code ?? ""} ${rawMessage ?? ""}`.toLowerCase();

  if (status === 429 || normalized.includes("quota") || normalized.includes("rate limit") || normalized.includes("rate-limits")) {
    return "Kuota atau rate limit Gemini sedang habis. Silakan coba lagi sebentar lagi, atau ganti API key/aktifkan billing Gemini agar chat AI kembali normal.";
  }

  if (status === 501 || code === "AI_NOT_CONFIGURED") {
    return "Gemini API belum dikonfigurasi di server. Tambahkan GEMINI_API_KEY atau GOOGLE_API_KEY di backend lalu restart server.";
  }

  if (status === 503 && code === "AI_BUSY") {
    return "Model AI sedang sibuk/overload. Silakan coba lagi sebentar lagi.";
  }

  if (typeof rawMessage === "string" && rawMessage.trim() && status < 500) {
    return rawMessage;
  }

  return "Maaf, layanan AI sedang tidak dapat dihubungi. Silakan coba lagi nanti.";
}

async function resizeAndBase64(file: File, maxWidth = 600): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader(); 
    reader.onerror = () => reject(new Error("Gagal membaca file"));
    reader.readAsDataURL(file);
    reader.onload = (e) => {
      const b64 = e.target?.result as string;
      const img = document.createElement("img");
      img.onerror = () => resolve(b64); // Fallback to original if load fails
      img.src = b64;
      img.onload = () => {
        const canvas = document.createElement("canvas"); const ctx = canvas.getContext("2d");
        if (!ctx) { resolve(b64); return; }
        const ratio = Math.min(maxWidth / img.width, 1); canvas.width = img.width * ratio; canvas.height = img.height * ratio;
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height); resolve(canvas.toDataURL("image/jpeg", 0.6));
      };
    };
  });
}

const GithubIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.02c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A4.8 4.8 0 0 0 8 18v4" /></svg>
);
const InstagramIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="20" height="20" x="2" ry="5" rx="5" /><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" /><line x1="17.5" x2="17.51" y1="6.5" y2="6.5" /></svg>
);
const FacebookIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" /></svg>
);

interface HomeViewProps {
  activeSection: string;
  setView: (v: View) => void; setMessages: (m: ChatMessage[]) => void;
  setPrediction: (p: PredictionResult | null) => void; setScanFile: (f: File | null) => void;
  setScanPreviewUrl: (u: string | null) => void; setResultSession: (s: number) => void;
  setScanSidebarOpen: (o: boolean) => void; containerRef: React.RefObject<HTMLElement | null>;
}

function HomeView({ 
  activeSection, setView, setScanSidebarOpen, containerRef 
}: HomeViewProps) {
  const { theme } = useTheme();
  const howToRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress: howToScrollY } = useScroll({ container: containerRef as React.MutableRefObject<HTMLElement | null>, target: howToRef as React.MutableRefObject<HTMLDivElement | null>, offset: ["start 80%", "end 50%"] });
  const flowWidth = useSpring(useTransform(howToScrollY, [0, 0.8], ["0%", "100%"]), { stiffness: 80, damping: 20 });

  return (
    <motion.div key="home" {...VIEW_TRANSITION} className="w-full relative z-10">
      <div className="sticky top-4 md:top-6 z-[120] hidden md:flex items-center flex-nowrap gap-2 px-3 py-2 rounded-full transition-all border shadow-xl backdrop-blur-md w-[92vw] md:w-fit mx-auto overflow-x-auto no-scrollbar" style={{ backgroundColor: theme === "light" ? "rgba(255,255,255,0.7)" : "rgba(30,41,59,0.7)", borderColor: theme === "light" ? "rgba(0,0,0,0.05)" : "rgba(255,255,255,0.05)" }}>
        {["BERANDA", "CARA PAKAI", "MANFAAT", "KREATOR"].map((item) => {
          const id = item.toLowerCase().replace(" ", "-"); const isActive = activeSection === id;
          return (
            <a href={`#${id}`} key={item} className={`relative px-4 py-2 rounded-full text-[10px] font-bold tracking-widest transition-all shrink-0 ${isActive ? "text-white" : (theme === "light" ? "text-slate-500 hover:text-primary-600" : "text-slate-400 hover:text-primary-400")}`} style={{ fontFamily: "Inter, sans-serif" }}>
              {isActive && <motion.div layoutId="nav-pill" className="absolute inset-0 rounded-full z-[-1]" style={{ background: "#5b9e2a", boxShadow: "0 4px 10px rgba(91,158,42,0.4)" }} />}
              <span className="relative z-10">{item}</span>
            </a>
          );
        })}
      </div>

      <section id="beranda" className="min-h-screen flex flex-col items-center justify-center px-6 text-center pt-20 pb-10">
        <motion.div 
          initial={{ y: 30, opacity: 0 }} 
          animate={{ y: 0, opacity: 1 }} 
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-col items-center"
        >
          <div className="cg-float relative mb-8">
            <div className="relative h-40 w-40 md:h-48 md:w-48 mx-auto pixelated">
              <NextImage
 
                src="/img/logo.png" 
                alt="ChilliGuard" 
                fill 
                sizes="(max-width: 768px) 160px, 192px"
                priority
                loading="eager"
                className="object-contain drop-shadow-xl" 
              />
            </div>
          </div>
          <h1 className="font-pixel text-3xl md:text-6xl tracking-wider mb-4 drop-shadow-sm flex justify-center text-center" style={{ color: theme === "light" ? "#3a6219" : "#7cbd40" }}>CHILLIGUARD</h1>
          <p className="max-w-xl text-xs md:text-sm font-bold tracking-widest mb-12 flex justify-center flex-wrap text-center" style={{ color: theme === "light" ? "#8b6e37" : "#9dd16b", fontFamily: "Inter, sans-serif" }}>✦ ASISTEN PETANI CABAI ✦</p>
          <p className="max-w-xl text-sm md:text-sm leading-relaxed mb-10 text-center px-6" style={{ color: theme === "light" ? "#4a3728" : "#94a3b8", opacity: theme === "light" ? 0.9 : 1, fontFamily: "Inter, sans-serif" }}>Asisten AI cerdas untuk mendiagnosis penyakit pada daun cabai secara akurat. Dapatkan solusi instan, rekomendasi pengobatan, dan pantau kesehatan tanaman Anda.</p>
          <div className="flex flex-col md:flex-row gap-3 md:gap-4 w-full max-w-md justify-center px-6 md:px-0">
            <button onClick={() => setView("scan")} className="w-full md:w-auto px-8 py-3 md:py-4 rounded-xl text-white font-bold bg-primary-600 shadow-lg flex items-center justify-center gap-2 hover:-translate-y-1 active:scale-95 transition-all text-sm"><Camera className="w-5 h-5" /> MULAI SEKARANG</button>
            <button onClick={() => setScanSidebarOpen(true)} className="w-full md:w-auto px-8 py-3 md:py-4 rounded-xl font-bold border transition-all flex items-center justify-center gap-2 hover:-translate-y-1 shadow-lg text-sm" style={{ background: theme === "light" ? "rgba(255,255,255,0.9)" : "rgba(30, 41, 59, 0.9)", color: theme === "light" ? "#3a6219" : "#7cbd40", border: `1.5px solid ${theme === "light" ? "rgba(91, 158, 42, 0.3)" : "rgba(255, 255, 255, 0.1)"}` }}><History className="w-5 h-5" /> RIWAYAT</button>
          </div>
        </motion.div>
      </section>

      <section id="cara-pakai" className="min-h-screen py-24 px-6 max-w-5xl mx-auto flex flex-col items-center justify-center text-center">
        <motion.h2 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="font-pixel text-3xl md:text-5xl tracking-wider mb-20" style={{ color: theme === "light" ? "#2d2118" : "#f8fafc" }}
        >
          CARA MENGGUNAKAN
        </motion.h2>
        <div ref={howToRef} className="relative flex flex-col md:flex-row items-center justify-center gap-12 w-full mt-4">
          <div className="hidden md:block absolute top-[40%] left-[10%] right-[10%] h-1 rounded-full overflow-hidden" style={{ background: theme === "light" ? "rgba(107,82,41,0.08)" : "rgba(255,255,255,0.05)", boxShadow: "inset 0 1px 3px rgba(0,0,0,0.05)" }}><motion.div className="h-full rounded-full bg-[#5b9e2a]" style={{ width: flowWidth }} /></div>
          {[
            { icon: "/img/camera.png", title: "1. Foto Daun", desc: "Ambil foto daun cabai yang terlihat memiliki gejala penyakit." },
            { icon: "/img/detail.png", title: "2. Analisis AI", desc: "Sistem kecerdasan buatan akan mendeteksi penyakit dalam hitungan detik." },
            { icon: "/img/logo.png", title: "3. Solusi", desc: "Dapatkan saran penanganan, dosis obat, dan cara pencegahan yang tepat." }
          ].map((step, i) => (
            <motion.div 
              key={i} 
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ 
                duration: 0.5, 
                delay: i * 0.2,
                y: { type: "spring", stiffness: 350, damping: 25 },
                scale: { type: "spring", stiffness: 350, damping: 25 }
              }}
              whileHover={{ y: -8, scale: 1.02 }}
              className="relative z-10 flex flex-col items-center p-8 text-center rounded-[2rem] border-2 flex-1 cursor-pointer shadow-md hover:shadow-2xl transition-[box-shadow,border-color,background-color] duration-300 ease-out" 
              style={{ 
                backgroundColor: theme === "light" ? "rgba(255,255,255,0.85)" : "rgba(30,41,59,0.85)", 
                borderColor: theme === "light" ? "white" : "rgba(51,65,85,1)", 
                backdropFilter: "blur(12px)",
                willChange: "transform"
              }}
            >
              <div className="absolute -top-4 -right-4 w-10 h-10 rounded-full flex items-center justify-center text-white font-pixel text-lg bg-[#5b9e2a] border-2 border-white shadow-md">{i + 1}</div>
              <div className="relative h-20 w-20 mb-6 pixelated"><NextImage src={step.icon} alt={step.title} fill sizes="80px" className="object-contain" /></div>
              <h3 className="font-pixel text-xl tracking-wide mb-3" style={{ color: theme === "light" ? "#3a6219" : "#7cbd40" }}>{step.title.replace(/^\d+\.\s*/, '')}</h3>
              <p className="text-sm leading-relaxed" style={{ opacity: theme === "light" ? 0.8 : 0.9, fontFamily: "Inter, sans-serif", color: theme === "light" ? "#2d2118" : "#cbd5e1" }}>{step.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section id="manfaat" className="min-h-screen py-24 px-6 max-w-5xl mx-auto flex flex-col items-center justify-center text-center">
        <motion.h2 
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="font-pixel text-2xl md:text-4xl tracking-wider mb-12" style={{ color: theme === "light" ? "#2d2118" : "#f8fafc" }}
        >
          MANFAAT CHILLIGUARD
        </motion.h2>
        <style>{`
          .puzzle-mask {
            -webkit-mask-image: radial-gradient(circle 24px at 50% 0px, transparent 24px, black 24.5px);
            mask-image: radial-gradient(circle 24px at 50% 0px, transparent 24px, black 24.5px);
          }
          .puzzle-tab {
            position: absolute;
            border-radius: 50%;
            z-index: 10;
          }
          /* Mobile: tab at bottom */
          .puzzle-tab-pos {
            bottom: -24px;
            left: 50%;
            transform: translateX(-50%);
            width: 48px;
            height: 48px;
          }
          @media (min-width: 768px) {
            .puzzle-mask {
              -webkit-mask-image: radial-gradient(circle 24px at 0px 50%, transparent 24px, black 24.5px);
              mask-image: radial-gradient(circle 24px at 0px 50%, transparent 24px, black 24.5px);
            }
            /* Desktop: tab at right */
            .puzzle-tab-pos {
              right: -24px;
              top: 50%;
              transform: translateY(-50%);
              width: 48px;
              height: 48px;
              bottom: auto;
              left: auto;
            }
          }
        `}</style>
        <div className="flex flex-col md:flex-row w-full max-w-4xl mx-auto z-10 gap-0" style={{ filter: "drop-shadow(0 15px 25px rgba(0,0,0,0.05))" }}>
          {[
            { title: "Deteksi Akurat", desc: "Didukung oleh AI yang terlatih khusus daun cabai.", bg: theme === "light" ? "#eff3e3" : "#1e293b", radius: "rounded-t-3xl md:rounded-l-3xl md:rounded-tr-none md:rounded-bl-3xl", hasSocket: false, hasTab: true },
            { title: "Solusi Instan", desc: "Rekomendasi fungisida dan dosis pengobatan tepat sasaran.", bg: theme === "light" ? "#f6f8ef" : "#334155", radius: "rounded-none", hasSocket: true, hasTab: true },
            { title: "Real-time", desc: "Hasil analisis presisi muncul dalam hitungan detik.", bg: theme === "light" ? "#ffffff" : "#475569", radius: "rounded-b-3xl md:rounded-r-3xl md:rounded-bl-none md:rounded-tr-3xl", hasSocket: true, hasTab: false }
          ].map((b, i) => (
            <motion.div 
              key={i} 
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ 
                duration: 0.5, 
                delay: i * 0.15,
                y: { type: "spring", stiffness: 350, damping: 25 },
                scale: { type: "spring", stiffness: 350, damping: 25 }
              }}
              whileHover={{ y: -8, scale: 1.02, zIndex: 40 }} 
              className="flex-1 flex flex-col relative cursor-pointer transition-[filter] duration-300 ease-out hover:drop-shadow-[0_20px_25px_rgba(0,0,0,0.2)]" 
              style={{ zIndex: i, willChange: "transform" }}
            >
              <div className={`absolute inset-0 ${b.radius} ${b.hasSocket ? "puzzle-mask" : ""}`} style={{ background: b.bg }} />
              {b.hasTab && <div className="puzzle-tab puzzle-tab-pos" style={{ backgroundColor: b.bg }} />}
              <div className="relative z-20 p-10 flex flex-col items-center justify-center text-center h-full">
                <h3 className="font-pixel text-lg tracking-wide mb-3" style={{ color: theme === "light" ? "#3a6219" : "#f1f5f9" }}>{b.title}</h3>
                <p className="text-sm leading-relaxed" style={{ color: theme === "light" ? "#7a6050" : "#cbd5e1", fontFamily: "Inter, sans-serif" }}>{b.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      <section id="kreator" className="min-h-[70vh] py-24 px-6 max-w-3xl mx-auto flex flex-col items-center justify-center text-center">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="w-full flex flex-col items-center"
        >
          <h2 className="font-pixel text-3xl md:text-5xl tracking-wider mb-12" style={{ color: theme === "light" ? "#2d2118" : "#f8fafc" }}>KREATOR</h2>
          <div className="cg-cozy-card p-10 flex flex-col items-center max-w-md w-full transition-colors duration-300 shadow-xl bg-white dark:bg-slate-800 rounded-3xl border">
            <div className="relative h-24 w-24 rounded-full overflow-hidden mb-6 border-4" style={{ borderColor: theme === "light" ? "rgba(91, 158, 42, 0.2)" : "rgba(255, 255, 255, 0.1)" }}>
              <NextImage
 
                src="/img/iconchatbot.png" 
                alt="Creator" 
                fill 
                sizes="96px"
                className="object-cover" 
              />
            </div>
            <h3 className="font-pixel text-2xl tracking-wide mb-2" style={{ color: theme === "light" ? "#3a6219" : "#7cbd40" }}>Thariq Adzikra</h3>
            <p className="text-xs font-semibold uppercase tracking-wider mb-4 transition-colors duration-300" style={{ opacity: theme === "light" ? 0.7 : 0.6, color: theme === "light" ? "#2d2118" : "#f1f5f9" }}>Fullstack AI Developer</p>
            <p className="text-sm leading-relaxed mb-6" style={{ color: theme === "light" ? "#4a3728" : "#94a3b8", opacity: theme === "light" ? 0.9 : 1, fontFamily: "Inter, sans-serif" }}>Membangun ChilliGuard untuk membantu petani cabai mendiagnosis penyakit tanaman secara presisi dengan bantuan AI.</p>
            <a href="mailto:thariqadzikra@student.uir.ac.id" className="px-6 py-2.5 rounded-lg text-xs font-bold transition-all bg-primary-500 text-white shadow-lg hover:bg-primary-600">Hubungi Kreator</a>
          </div>
        </motion.div>
      </section>

      <footer className="w-full mt-12 py-8 px-6 lg:px-12 flex flex-col md:flex-row items-center justify-between border-t" style={{ borderTop: `1px solid ${theme === "light" ? "rgba(107, 82, 41, 0.15)" : "rgba(255, 255, 255, 0.1)"}` }}>
        <p className="text-[10px] sm:text-xs font-bold uppercase tracking-widest whitespace-nowrap mb-4 md:mb-0 transition-colors duration-300" style={{ opacity: theme === "light" ? 0.7 : 0.6, color: theme === "light" ? "#2d2118" : "#f1f5f9" }}>© {new Date().getFullYear()} ChilliGuard</p>
        <div className="flex items-center gap-4 sm:gap-6">
          <a href="https://github.com/ThariqAdzikra" target="_blank" rel="noopener noreferrer" className={`transition-colors ${theme === "light" ? "text-[#8b6e37] hover:text-[#5b9e2a]" : "text-slate-400 hover:text-primary-400"}`}><GithubIcon className="w-4 h-4 sm:w-5 sm:h-5" /></a>
          <a href="https://www.instagram.com/thrqdz_/" target="_blank" rel="noopener noreferrer" className={`transition-colors ${theme === "light" ? "text-[#8b6e37] hover:text-[#5b9e2a]" : "text-slate-400 hover:text-primary-400"}`}><InstagramIcon className="w-4 h-4 sm:w-5 sm:h-5" /></a>
          <a href="https://web.facebook.com/thariq.biji" target="_blank" rel="noopener noreferrer" className={`transition-colors ${theme === "light" ? "text-[#8b6e37] hover:text-[#5b9e2a]" : "text-slate-400 hover:text-primary-400"}`}><FacebookIcon className="w-4 h-4 sm:w-5 sm:h-5" /></a>
        </div>
      </footer>
    </motion.div>
  );
}

export default function DashboardPage() {
  const { data: session } = useSession(); const { theme, mounted } = useTheme();
  const [view, setView] = useState<View>("home"); // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [scanFile, setScanFile] = useState<File | null>(null);
  const [scanPreviewUrl, setScanPreviewUrl] = useState<string | null>(null); const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [resultSession, setResultSession] = useState(0); const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState(""); const [showFAQ, setShowFAQ] = useState(false);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null); const [editText, setEditText] = useState("");
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null); const [scanSidebarOpen, setScanSidebarOpen] = useState(false);
  const [sidebarSessions, setSidebarSessions] = useState<StoredChatSession[]>([]); const [isTyping, setIsTyping] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<{ id: number; title: string } | null>(null);
  const [deleteBusy, setDeleteBusy] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [cameraFacingUser, setCameraFacingUser] = useState(false);
  const isAnalyzingRef = useRef(false);
  const mainScrollRef = useRef<HTMLElement>(null); const videoRef = useRef<HTMLVideoElement>(null); 
  const streamRef = useRef<MediaStream | null>(null); const galleryInputRef = useRef<HTMLInputElement>(null); 
  const chatEndRef = useRef<HTMLDivElement>(null); const prevViewRef = useRef<View>("home");
  const messageIdCounterRef = useRef(0);
  const [activeSection, setActiveSection] = useState("beranda");

  const generateMessageId = useCallback((prefix: string) => {
    return `${prefix}-${Date.now()}-${++messageIdCounterRef.current}`;
  }, []);

  const revokePreview = useCallback((url: string | null) => { if (url) URL.revokeObjectURL(url); }, []);

  const runAnalysis = useCallback(async (file: File) => {
    if (isAnalyzingRef.current) return;
    isAnalyzingRef.current = true;
    setView("analyzing");

    try {
      const base64Image = await resizeAndBase64(file);
      const startTime = Date.now();

      const fd = new FormData();
      fd.append("file", file);

      const controller = new AbortController();
      const tid = setTimeout(() => controller.abort(), 75000); // 75s timeout to allow VPS CPU inference to complete

      const res = await fetch(`${API_BASE}/predict`, { 
        method: "POST", 
        body: fd,
        signal: controller.signal 
      });
      clearTimeout(tid);

      if (!res.ok) {
        const errText = await res.text().catch(() => "");
        throw new Error(`Prediction failed: HTTP ${res.status} — ${errText.slice(0, 120)}`);
      }

      const data = await safeJson<PredictionResult>(res);

      const elapsed = Date.now() - startTime;
      if (elapsed < 2000) await new Promise(r => setTimeout(r, 2000 - elapsed));

       setPrediction(data);
      const intro = buildIntro(data, false);
      const newMsg: ChatMessage = { id: generateMessageId("s"), role: "system", text: intro, image: base64Image, prediction: data };

      setMessages(prev => [...prev, newMsg]);
      setView("chat");

      if (session?.user?.email) {
        try {
          const saveRes = await fetch(`${API_BASE}/api/history/integrated-save`, { 
            method: "POST", headers: { "Content-Type": "application/json" }, 
            body: JSON.stringify({ 
              user_email: session.user.email, image_url: base64Image, 
              disease_label: data.label, confidence: data.confidence, 
              severity: data.severity, session_id: resultSession, 
              title: data.label, intro_text: intro 
            }) 
          });
          const saveData = await saveRes.json(); setResultSession(saveData.session_id);
        } catch (e) { console.error("Save error:", e); }
      }
    } catch (e: any) { 
      console.error("Analysis Error:", e);
      await new Promise(r => setTimeout(r, 1000));
      setView("chat");
      const isTimeout = e?.name === "AbortError" || e?.message?.toLowerCase().includes("abort");
      const errorMsg = isTimeout
        ? "Waktu analisis melebihi batas tunggu (server sedang memproses gambar dengan beban tinggi). Silakan coba lagi beberapa saat lagi."
        : "Maaf, terjadi gangguan saat menganalisis gambar. Silakan coba lagi.";
      setMessages(prev => [...prev, { id: generateMessageId("err"), role: "assistant", text: errorMsg }]);
    } finally {
      isAnalyzingRef.current = false;
      setScanFile(null);
    }
  }, [session, resultSession, generateMessageId]);

  const setImageFromFile = useCallback((file: File | null) => {
    if (!file || !file.type.startsWith("image/")) return;
    setScanPreviewUrl((prev) => { revokePreview(prev); return URL.createObjectURL(file); });
    setScanFile(file);
    runAnalysis(file);
  }, [revokePreview, runAnalysis]);

  useEffect(() => {
    if (view === "home" || view === "chat") prevViewRef.current = view;
    const container = mainScrollRef.current;
    if (!container) return;
    const handleScroll = () => {
      const sections = ["beranda", "cara-pakai", "manfaat", "kreator"];
      const scrollPosition = container.scrollTop + container.clientHeight / 3;
      for (const section of sections) {
        const element = document.getElementById(section);
        if (element && scrollPosition >= element.offsetTop && scrollPosition < element.offsetTop + element.offsetHeight) setActiveSection(section);
      }
    };
    container.addEventListener("scroll", handleScroll);
    return () => container.removeEventListener("scroll", handleScroll);
  }, [view]);

  useEffect(() => {
    async function syncSidebar() {
      if (session?.user?.email) {
        try {
          const res = await fetch(`${API_BASE}/api/chat-sessions?email=${encodeURIComponent(session.user.email)}`);
          if (res.ok) {
            const ct = res.headers.get("content-type") ?? "";
            if (ct.includes("application/json")) setSidebarSessions(await res.json());
          }
        } catch (e) { console.error("Sync error:", e); }
      }
    }
    syncSidebar();
  }, [view, session]);


  useEffect(() => {
    if (view !== "scan" || scanPreviewUrl) {
      if (streamRef.current) { streamRef.current.getTracks().forEach(t => t.stop()); streamRef.current = null; }
      if (videoRef.current) videoRef.current.srcObject = null;
      return;
    }
    let alive = true;
    void (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: cameraFacingUser ? "user" : "environment" },
          audio: false
        });
        if (!alive) { stream.getTracks().forEach(t => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play().catch(() => {});
        }
      } catch (e) { console.error("Camera error:", e); }
    })();
    return () => {
      alive = false;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
        streamRef.current = null;
      }
    };
  }, [view, scanPreviewUrl, cameraFacingUser]);

  const captureFromVideo = useCallback(() => {
    const v = videoRef.current; if (!v || v.readyState < 2) return;
    const canvas = document.createElement("canvas"); canvas.width = v.videoWidth; canvas.height = v.videoHeight;
    const ctx = canvas.getContext("2d"); if (!ctx) return;
    if (cameraFacingUser) { ctx.translate(v.videoWidth, 0); ctx.scale(-1, 1); } ctx.drawImage(v, 0, 0);
    canvas.toBlob((blob) => { if (blob) setImageFromFile(new File([blob], "scan.jpg", { type: "image/jpeg" })); }, "image/jpeg", 0.88);
  }, [setImageFromFile, cameraFacingUser]);

  useEffect(() => {
    if (view === "chat" && chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, view, isTyping]);

  const handleLogout = () => signOut({ callbackUrl: "/" });
  const resetToHome = () => { setScanFile(null); setScanPreviewUrl(null); setPrediction(null); setChatInput(""); setView("home"); };

  const sendChat = useCallback(async (overrideText?: string) => {
    const text = (overrideText || chatInput).trim(); 
    if (!text || !prediction) return;
    
    // Add user message immediately
    const userMsg: ChatMessage = { id: generateMessageId("u"), role: "user", text };
    setMessages(prev => [...prev, userMsg]);
    setChatInput(""); 
    setIsTyping(true);

    if (resultSession > 0) {
      void fetch(`${API_BASE}/api/chat-sessions/${resultSession}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sender: "user", text }),
      });
    }
    
    try {
      // Map history to match backend expectations (Gemini roles: user and model)
      // Filter out messages without text and ensure valid roles
      const formattedHistory = messages
        .filter(m => m.text && m.text.trim() !== "")
        .map(m => ({
          role: m.role === "user" ? "user" : "model",
          text: m.text
        }));

      const res = await fetch(`${API_BASE}/chat`, { 
        method: "POST", 
        headers: { "Content-Type": "application/json" }, 
        body: JSON.stringify({ 
          message: text, 
          prediction_context: prediction, 
          history: formattedHistory
        }) 
      });
      
      if (!res.ok) {
        const ct = res.headers.get("content-type") ?? "";
        const errorData = ct.includes("application/json") ? await res.json().catch(() => ({})) : {};
        throw new Error(getChatErrorMessage(errorData, res.status));
      }
      
       const data = await safeJson<{ text: string }>(res);
       const aiMsg: ChatMessage = { id: generateMessageId("ai"), role: "assistant", text: data.text };
       setMessages(prev => [...prev, aiMsg]);
       
       if (resultSession > 0) {
        void fetch(`${API_BASE}/api/chat-sessions/${resultSession}/messages`, { 
           method: "POST", 
           headers: { "Content-Type": "application/json" }, 
           body: JSON.stringify({ sender: "ai", text: data.text }) 
         });
       }
    } catch (err) { 
      console.error("Chat Error:", err);
      const message = err instanceof Error ? err.message : "Maaf, layanan AI sedang tidak dapat dihubungi. Silakan coba lagi nanti.";
      setMessages(prev => [...prev, { id: generateMessageId("a"), role: "assistant", text: message }]); 
    } finally { 
      setIsTyping(false); 
    }
  }, [chatInput, prediction, messages, resultSession, generateMessageId]);

  const loadSession = async (id: number) => {
    const res = await fetch(`${API_BASE}/api/chat-sessions/${id}`);
    if (res.ok) {
      const data = await res.json() as { messages: Array<{ role: "user" | "assistant" | "system"; text: string; prediction?: PredictionResult; image?: string }> };
      setMessages(data.messages.map((m) => ({ id: Math.random().toString(), role: m.role, text: m.text, prediction: m.prediction, image: m.image })));
      const lastScan = [...data.messages].reverse().find((m) => m.prediction); setPrediction(lastScan?.prediction || null);
      setResultSession(id); setView("chat"); setScanSidebarOpen(false);
    }
  };

  const openDeleteDialog = useCallback((target: StoredChatSession) => {
    setDeleteError(null);
    setDeleteTarget({ id: target.id, title: target.title || target.diagnosis || "Sesi Chat" });
    setDeleteDialogOpen(true);
  }, []);

  const closeDeleteDialog = useCallback(() => {
    if (deleteBusy) return;
    setDeleteDialogOpen(false);
    setDeleteTarget(null);
    setDeleteError(null);
  }, [deleteBusy]);

  useEffect(() => {
    if (!deleteDialogOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeDeleteDialog();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [deleteDialogOpen, closeDeleteDialog]);

  const deleteSession = async (id: number) => {
    const email = session?.user?.email;
    if (!email) return;
    setDeleteBusy(true);
    setDeleteError(null);
    try {
      const res = await fetch(`${API_BASE}/api/chat-sessions/${id}?email=${encodeURIComponent(email)}`, { method: "DELETE" });
      if (!res.ok) throw new Error(`Delete failed: HTTP ${res.status}`);
      setSidebarSessions((prev) => prev.filter((s) => s.id !== id));
      if (resultSession === id) {
        setResultSession(0);
        setMessages([]);
        setPrediction(null);
        setView("home");
      }
      closeDeleteDialog();
    } catch (e) {
      console.error("Delete session error:", e);
      setDeleteError("Gagal menghapus riwayat chat. Silakan coba lagi.");
    } finally {
      setDeleteBusy(false);
    }
  };

  const handleCopy = (text: string, id: string) => { navigator.clipboard.writeText(text); setCopiedMessageId(id); setTimeout(() => setCopiedMessageId(null), 2000); };
  const startEditing = (msg: ChatMessage) => { setEditingMessageId(msg.id); setEditText(msg.text); };
  const handleEditSubmit = async (id: string) => { if (!editText.trim()) return; const index = messages.findIndex(m => m.id === id); if (index === -1) return; setMessages(messages.slice(0, index)); setEditingMessageId(null); sendChat(editText); };

  const renderView = view;

  return (
    <div 
      className="relative flex h-[100dvh] w-full overflow-hidden transition-colors duration-300 font-inter text-foreground bg-background"
      style={{ visibility: mounted ? "visible" : "hidden" }}
    >
      <div className="fixed inset-0 z-0 pointer-events-none">
        {mounted && (
          <NextImage
            src={theme === "light" ? "/img/background.jpg" : "/img/darkbg.jpg"}
            alt=""
            fill
            sizes="100vw"
            priority
            className="object-cover transition-opacity duration-700"
          />
        )}
        <div className="absolute inset-0" style={{ background: theme === "light" ? "rgba(242, 246, 234, 0.4)" : "rgba(15, 23, 42, 0.6)" }} />
      </div>
      <AnimatePresence>
        {scanSidebarOpen && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setScanSidebarOpen(false)} className="fixed inset-0 z-[140] bg-black/20 backdrop-blur-sm lg:hidden" />
        )}
      </AnimatePresence>
      
      <AnimatePresence>
        {deleteDialogOpen && deleteTarget && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[260] flex items-end sm:items-center justify-center p-4"
          >
            <motion.button
              type="button"
              aria-label="Tutup dialog"
              className="absolute inset-0 bg-black/40 backdrop-blur-sm"
              onClick={closeDeleteDialog}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-labelledby="cg-delete-title"
              aria-describedby="cg-delete-desc"
              initial={{ y: 18, opacity: 0, scale: 0.98 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: 18, opacity: 0, scale: 0.98 }}
              transition={{ type: "spring", stiffness: 320, damping: 26 }}
              className="relative w-full max-w-md rounded-2xl border shadow-2xl p-4 sm:p-5"
              style={{
                backgroundColor: theme === "light" ? "rgba(255,255,255,0.95)" : "rgba(30,41,59,0.95)",
                borderColor: theme === "light" ? "rgba(0,0,0,0.08)" : "rgba(255,255,255,0.12)",
              }}
            >
              <div className="flex items-start gap-3">
                <div
                  className="h-10 w-10 rounded-xl flex items-center justify-center shrink-0 border"
                  style={{
                    backgroundColor: theme === "light" ? "rgba(239,68,68,0.08)" : "rgba(239,68,68,0.12)",
                    borderColor: theme === "light" ? "rgba(239,68,68,0.22)" : "rgba(239,68,68,0.25)",
                  }}
                >
                  <Trash2 className="h-5 w-5" style={{ color: theme === "light" ? "#dc2626" : "#fca5a5" }} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 id="cg-delete-title" className="text-sm font-bold" style={{ color: theme === "light" ? "#0f172a" : "#f8fafc" }}>
                        Hapus riwayat chat?
                      </h3>
                      <p id="cg-delete-desc" className="mt-1 text-xs leading-relaxed" style={{ color: theme === "light" ? "#475569" : "#cbd5e1" }}>
                        Riwayat untuk <span className="font-semibold">{deleteTarget.title}</span> akan dihapus permanen dan tidak dapat dibatalkan.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={closeDeleteDialog}
                      disabled={deleteBusy}
                      className="p-2 rounded-lg transition-all opacity-60 hover:opacity-100 disabled:opacity-30"
                      aria-label="Tutup"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>

                  {deleteError && (
                    <div className="mt-3 text-xs font-medium rounded-lg border px-3 py-2"
                      style={{
                        color: theme === "light" ? "#b91c1c" : "#fecaca",
                        backgroundColor: theme === "light" ? "rgba(239,68,68,0.08)" : "rgba(239,68,68,0.12)",
                        borderColor: theme === "light" ? "rgba(239,68,68,0.22)" : "rgba(239,68,68,0.2)",
                      }}
                    >
                      {deleteError}
                    </div>
                  )}

                  <div className="mt-4 flex flex-col sm:flex-row gap-2 sm:justify-end">
                    <button
                      type="button"
                      onClick={closeDeleteDialog}
                      disabled={deleteBusy}
                      className="w-full sm:w-auto px-4 py-2.5 rounded-xl text-xs font-semibold border transition-all disabled:opacity-50"
                      style={{
                        backgroundColor: theme === "light" ? "rgba(255,255,255,0.9)" : "rgba(15,23,42,0.35)",
                        borderColor: theme === "light" ? "rgba(0,0,0,0.08)" : "rgba(255,255,255,0.12)",
                        color: theme === "light" ? "#0f172a" : "#e2e8f0",
                      }}
                    >
                      Batal
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteSession(deleteTarget.id)}
                      disabled={deleteBusy}
                      className="w-full sm:w-auto px-4 py-2.5 rounded-xl text-xs font-bold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                      style={{
                        backgroundColor: theme === "light" ? "#ef4444" : "rgba(239,68,68,0.95)",
                        color: "white",
                      }}
                    >
                      {deleteBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                      Hapus
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.aside 
        initial={false}
        animate={{ width: scanSidebarOpen ? 288 : 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="fixed inset-y-0 left-0 z-[150] lg:relative overflow-hidden backdrop-blur-md shrink-0" 
        style={{ background: theme === "light" ? "rgba(255, 255, 255, 0.85)" : "rgba(30, 41, 59, 0.85)", borderRight: `1.5px solid ${theme === "light" ? "rgba(107, 82, 41, 0.12)" : "rgba(255, 255, 255, 0.08)"}` }}
      >
        <div className="flex flex-col h-full w-72 shrink-0">
          <div className="flex h-14 shrink-0 items-center justify-between px-5 border-b" style={{ borderColor: theme === "light" ? "rgba(107, 82, 41, 0.08)" : "rgba(255, 255, 255, 0.05)" }}>
            <div className="flex items-center gap-3"><div className="relative h-7 w-7 pixelated"><NextImage src="/img/logo.png" alt="" fill sizes="28px" priority className="object-contain" /></div><span className="font-pixel text-[13px]" style={{ color: theme === "light" ? "#3a6219" : "#7cbd40" }}>CHILLIGUARD</span></div>
            <button onClick={() => setScanSidebarOpen(false)} className="lg:hidden transition-colors hover:opacity-70"><X className="h-5 w-5" /></button>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-4 font-inter">
            <button onClick={() => { resetToHome(); setResultSession(0); setMessages([]); setScanSidebarOpen(false); }} className="flex w-full items-center gap-2 p-2.5 rounded-lg border text-sm font-medium transition-all" style={{ background: theme === "light" ? "rgba(91, 158, 42, 0.08)" : "rgba(91, 158, 42, 0.2)", color: theme === "light" ? "#3a6219" : "#f3f9ec", borderColor: theme === "light" ? "rgba(91, 158, 42, 0.15)" : "rgba(91, 158, 42, 0.3)" }}><MessageSquare className="h-4 w-4" /><span>Chat Baru</span></button>
            <div className="space-y-1">
              <p className="px-3 font-pixel text-[10px] uppercase mb-2" style={{ opacity: theme === "light" ? 0.6 : 0.5, color: theme === "light" ? "#3a6219" : "inherit" }}>RIWAYAT</p>
              {sidebarSessions.map(s => {
                 const dateObj = new Date(s.created_at);
                 const formattedDate = !isNaN(dateObj.getTime()) 
                   ? dateObj.toLocaleDateString("id-ID", { day: 'numeric', month: 'short' })
                   : "";
                 const isActive = resultSession === s.id;
                 return (
                   <div key={s.id} className="flex items-stretch gap-1.5 group">
                     <button
                       onClick={() => loadSession(s.id)}
                       aria-current={isActive ? "page" : undefined}
                       className={`flex-1 w-full p-2.5 text-xs rounded-lg text-left transition-all flex flex-col gap-1 border ${isActive ? (theme === "light" ? "bg-primary-50 text-primary-700 shadow-sm border-primary-100" : "bg-primary-900/30 text-primary-200 border-primary-500/20") : "border-transparent hover:border-black/10 dark:hover:border-white/10 hover:bg-black/5 dark:hover:bg-white/5 opacity-70 hover:opacity-100"}`}
                     >
                       <div className="flex items-center justify-between w-full">
                         <div className="flex items-center truncate">
                           <Bot className="inline h-3.5 w-3.5 mr-2.5 opacity-40 shrink-0" />
                           <span className="truncate font-medium">{s.title || s.diagnosis || "Sesi Chat"}</span>
                         </div>
                         <span className="text-[9px] opacity-40 shrink-0 ml-2">{formattedDate}</span>
                       </div>
                     </button>
                     <button
                       type="button"
                       onClick={() => openDeleteDialog(s)}
                       className={`w-9 shrink-0 rounded-lg border flex items-center justify-center transition-all ${theme === "light" ? "border-transparent hover:border-red-200 hover:bg-red-50 text-slate-500 hover:text-red-600" : "border-transparent hover:border-red-500/20 hover:bg-red-500/10 text-slate-300 hover:text-red-300"} opacity-70 group-hover:opacity-100`}
                       aria-label="Hapus sesi chat"
                       title="Hapus sesi"
                     >
                       <Trash2 className="h-4 w-4" />
                     </button>
                   </div>
                 );
               })}
            </div>
          </div>
          <div className="p-4 border-t" style={{ borderColor: theme === "light" ? "rgba(107, 82, 41, 0.08)" : "rgba(255, 255, 255, 0.05)" }}>
            <div className="flex items-center gap-2.5 p-2 rounded-lg bg-black/5 transition-colors">
              <div className="h-8 w-8 rounded-lg overflow-hidden flex items-center justify-center font-bold text-xs bg-primary-100 text-primary-700 relative">
                {session?.user?.image ? (
                  <NextImage
 src={session.user.image} alt="" className="object-cover" referrerPolicy="no-referrer" fill sizes="32px" />
                ) : (
                  (session?.user?.name?.[0] || "U").toUpperCase()
                )}
              </div>
              <div className="flex-1 truncate text-xs font-semibold transition-colors" style={{ color: theme === "light" ? "#2d2118" : "#f1f5f9" }}>{session?.user?.name || "User"}</div>
              <button onClick={handleLogout} className="p-1.5 opacity-50 hover:opacity-100 transition-opacity"><LogOut className="h-3.5 w-3.5" /></button>
            </div>
          </div>
        </div>
      </motion.aside>
      
      <motion.button 
        initial={false}
        animate={{ x: scanSidebarOpen ? 288 : 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        onClick={() => setScanSidebarOpen(!scanSidebarOpen)} 
        className="fixed left-0 top-1/2 -translate-x-full lg:-translate-x-0 -translate-y-1/2 z-[160] hidden lg:flex h-16 w-8 items-center justify-center rounded-r-xl shadow-xl border border-l-0 transition-colors duration-300" 
        style={{ backgroundColor: theme === "light" ? "white" : "#1e293b", borderColor: theme === "light" ? "rgba(0,0,0,0.1)" : "rgba(255,255,255,0.1)" }}
      >
        <ChevronLeft className={`h-5 w-5 opacity-40 transition-transform duration-300 ${!scanSidebarOpen ? "rotate-180" : ""}`} />
      </motion.button>

      <div className="relative flex-1 flex flex-col overflow-hidden z-10">
        
        {/* Floating Hamburger for Mobile */}
        {!scanSidebarOpen && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            onClick={() => setScanSidebarOpen(true)}
            className="fixed top-3 left-3 z-[140] lg:hidden h-10 w-10 flex items-center justify-center rounded-xl shadow-xl backdrop-blur-md transition-all border"
            style={{ 
              backgroundColor: theme === "light" ? "rgba(255,255,255,0.8)" : "rgba(30, 41, 59, 0.8)",
              borderColor: theme === "light" ? "rgba(107, 82, 41, 0.15)" : "rgba(255, 255, 255, 0.1)"
            }}
          >
            <Menu className="h-5 w-5 text-foreground" />
          </motion.button>
        )}

        <main ref={mainScrollRef} className="flex-1 overflow-y-auto relative scroll-smooth">
          <AnimatePresence mode="wait">
            {renderView === "home" && <HomeView activeSection={activeSection} setView={setView} setMessages={setMessages} setPrediction={setPrediction} setScanFile={setScanFile} setScanPreviewUrl={setScanPreviewUrl} setResultSession={setResultSession} setScanSidebarOpen={setScanSidebarOpen} containerRef={mainScrollRef} />}
            {renderView === "chat" && (
              <motion.div key="chat" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mx-auto w-full max-w-3xl px-3 md:px-5 pt-4 md:pt-8 pb-24 md:pb-28 space-y-6 md:space-y-8 font-inter relative z-10">
                  {messages.map((m, idx) => {
                    const scanIndex = messages.filter((msg, i) => i <= idx && (msg.role === "system" || msg.prediction)).length;
                    return (
                      <div key={m.id} className={`flex flex-col gap-3 md:gap-4 ${m.role === "user" ? "items-end" : "items-start"}`}>
                        {/* Scan Divider */}
                        {m.prediction && (
                          <div className="w-full flex items-center gap-3 my-6 transition-opacity duration-500" style={{ opacity: theme === "light" ? 0.6 : 0.4 }}>
                            <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent via-black/10 to-transparent dark:via-white/10" />
                            <div className="font-pixel text-[8px] md:text-[9px] uppercase tracking-[0.2em] transition-colors" style={{ color: theme === "light" ? "#8b6e37" : "#9dd16b" }}>
                              SCAN #{scanIndex} • {m.prediction.label}
                            </div>
                            <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent via-black/10 to-transparent dark:via-white/10" />
                          </div>
                        )}
                        
                        <div className={`flex gap-3 md:gap-4 w-full ${m.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                          {/* Avatar */}
                           <div className={`h-8 w-8 md:h-10 md:w-10 shrink-0 overflow-hidden flex items-center justify-center rounded-xl shadow-sm transition-all border relative ${m.role === "user" ? "bg-primary-500 text-white border-primary-600" : ""}`} style={m.role !== "user" ? { backgroundColor: theme === "light" ? "white" : "#1e293b", borderColor: theme === "light" ? "rgba(0,0,0,0.05)" : "rgba(255,255,255,0.1)" } : {}}>
                             {m.role === "user" ? (
                               session?.user?.image ? (
                                 <NextImage
 src={session.user.image} alt="" className="object-cover" referrerPolicy="no-referrer" fill sizes="40px" />
                               ) : (
                                 <User className="w-4 h-4" />
                               )
                             ) : (
                               <div className="relative h-6 w-6 md:h-7 md:w-7 pixelated">
                                 <NextImage
 src="/img/iconchatbot.png" alt="AI" fill sizes="28px" />
                               </div>
                             )}
                           </div>

                          <div className={`flex-1 space-y-3 max-w-[85%] md:max-w-[80%] ${m.role === "user" ? "text-right" : ""}`}>
                             {/* Diagnosis Card */}
                             {m.prediction && (
                                <div className="cg-cozy-card overflow-hidden shadow-sm ring-1 ring-black/5 transition-all mb-4" style={{ backgroundColor: theme === "light" ? "white" : "#1e293b", borderColor: theme === "light" ? "rgba(0,0,0,0.05)" : "rgba(255,255,255,0.1)" }}>
                                   <div className="flex flex-col md:flex-row">
                                      {m.image && (
                                        <div className="relative w-full md:w-64 h-44 md:h-auto shrink-0 border-b md:border-b-0 md:border-r transition-colors" style={{ backgroundColor: theme === "light" ? "#f1f5f9" : "#0f172a", borderColor: theme === "light" ? "rgba(0,0,0,0.05)" : "rgba(255,255,255,0.05)" }}>
                                          <NextImage
 src={m.image} alt="" className="object-cover" fill sizes="(max-width: 768px) 100vw, 256px" />
                                        </div>
                                      )}
                                      <div className="flex-1 p-4 md:p-5 flex flex-col" style={{ backgroundColor: theme === "light" ? "white" : "#1e293b" }}>
                                         <div className="flex items-center gap-2 mb-2">
                                           <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase text-white transition-colors ${m.prediction.severity === "peringatan" ? "bg-amber-500" : "bg-primary-500"}`}>{m.prediction.severity}</span>
                                           <span className="text-[9px] font-bold tracking-wider opacity-40 uppercase" style={{ color: theme === "light" ? "inherit" : "#f1f5f9" }}>{m.prediction.confidence > 0 ? `${Math.round(m.prediction.confidence * 100)}% Match` : "Info"}</span>
                                         </div>
                                         <h3 className="text-base md:text-lg font-bold mb-1.5 transition-colors font-inter" style={{ color: theme === "light" ? "#2d2118" : "#f1f5f9" }}>{m.prediction.label}</h3>
                                         <p className="text-xs leading-relaxed mb-4 transition-colors" style={{ opacity: 0.8, color: theme === "light" ? "#4b3a2f" : "#cbd5e1" }}>{m.prediction.description}</p>
                                         <div className="h-1 w-full rounded-full overflow-hidden transition-colors" style={{ backgroundColor: theme === "light" ? "rgba(0,0,0,0.05)" : "rgba(255,255,255,0.05)" }}><div className="h-full bg-primary-500 transition-all duration-1000" style={{ width: `${m.prediction.confidence * 100}%` }} /></div>
                                      </div>
                                   </div>
                                   <div className="p-4 md:p-5 space-y-5 border-t transition-colors" style={{ backgroundColor: theme === "light" ? "rgba(0,0,0,0.02)" : "rgba(0,0,0,0.2)", borderColor: theme === "light" ? "rgba(0,0,0,0.05)" : "rgba(255,255,255,0.05)" }}>
                                      {m.prediction.symptoms?.length > 0 && (
                                        <div>
                                          <h4 className="text-[9px] font-bold uppercase tracking-widest mb-3 opacity-50" style={{ color: theme === "light" ? "#2d2118" : "#f1f5f9" }}>Gejala</h4>
                                          <div className="flex flex-wrap gap-1.5">
                                            {m.prediction.symptoms.map((s, i) => <span key={i} className="text-[10px] px-2.5 py-1 rounded-lg border shadow-sm transition-colors" style={{ backgroundColor: theme === "light" ? "white" : "#0f172a", borderColor: theme === "light" ? "rgba(0,0,0,0.05)" : "rgba(255,255,255,0.05)", color: theme === "light" ? "#2d2118" : "#f1f5f9" }}>{s}</span>)}
                                          </div>
                                        </div>
                                      )}
                                      {m.prediction.treatment?.length > 0 && (
                                        <div>
                                          <h4 className="text-[9px] font-bold uppercase tracking-widest mb-3 opacity-50" style={{ color: theme === "light" ? "#2d2118" : "#f1f5f9" }}>Penanganan</h4>
                                          <div className="space-y-2">
                                            {m.prediction.treatment.map((t, i) => <div key={i} className="flex gap-3 text-[11px] p-3 rounded-xl border transition-colors" style={{ backgroundColor: theme === "light" ? "#f7fee7" : "rgba(91,158,42,0.1)", borderColor: theme === "light" ? "#ecfccb" : "rgba(91,158,42,0.2)", color: theme === "light" ? "#2d2118" : "#f1f5f9" }}><div className="h-5 w-5 shrink-0 rounded-full bg-primary-500 text-white flex items-center justify-center text-[9px] font-bold shadow-sm">{i+1}</div><span className="leading-relaxed">{t}</span></div>)}
                                          </div>
                                        </div>
                                      )}
                                      {m.prediction.prevention?.length > 0 && (
                                        <div>
                                          <h4 className="text-[9px] font-bold uppercase tracking-widest mb-3 opacity-50" style={{ color: theme === "light" ? "#2d2118" : "#f1f5f9" }}>Pencegahan</h4>
                                          <div className="space-y-2">
                                            {m.prediction.prevention.map((p, i) => <div key={i} className="flex gap-2.5 text-[11px] items-start transition-colors" style={{ color: theme === "light" ? "#4b3a2f" : "#cbd5e1" }}><Check className="h-3.5 w-3.5 mt-0.5 text-primary-500 shrink-0" /><span className="leading-relaxed">{p}</span></div>)}
                                          </div>
                                        </div>
                                      )}
                                   </div>
                                </div>
                             )}

                             {/* Text Bubble */}
                             {m.text && (
                               <div className="group relative space-y-2">
                                  <div className={`inline-block px-4 py-3 md:px-5 md:py-4 rounded-2xl shadow-sm text-left transition-all ${m.role === "user" ? "bg-primary-500 text-white rounded-tr-none" : "rounded-tl-none border"}`} style={m.role !== "user" ? { backgroundColor: theme === "light" ? "white" : "#1e293b", borderColor: theme === "light" ? "rgba(0,0,0,0.1)" : "rgba(255,255,255,0.1)" } : {}}>
                                     {editingMessageId === m.id ? (
                                       <div className="flex flex-col gap-2 min-w-[200px] transition-all"><textarea value={editText} onChange={e => setEditText(e.target.value)} className="bg-transparent border-none outline-none resize-none w-full text-sm text-inherit" rows={2} autoFocus /><div className="flex justify-end gap-2 pt-2 border-t border-white/10"><button onClick={() => setEditingMessageId(null)} className="text-[9px] font-bold opacity-60 uppercase">Batal</button><button onClick={() => handleEditSubmit(m.id)} className="text-[9px] font-bold text-white uppercase flex items-center gap-1"><Check className="w-3 h-3" /> Simpan</button></div></div>
                                     ) : (
                                       <div className={`prose prose-sm max-w-none text-[13px] md:text-sm leading-relaxed transition-colors ${m.role === "user" ? "prose-invert text-white" : (theme === "dark" ? "prose-invert" : "")}`} style={m.role !== "user" ? { color: theme === "light" ? "#1e293b" : "#f1f5f9" } : {}}><ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown></div>
                                     )}
                                  </div>
                                  {!editingMessageId && (
                                    <div className={`flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-all duration-200 ${m.role === "user" ? "justify-end mr-1" : "justify-start ml-1"}`}>
                                      <button onClick={() => handleCopy(m.text, m.id)} className="text-[9px] font-bold tracking-widest opacity-40 hover:opacity-100 uppercase transition-all" style={{ color: theme === "light" ? "inherit" : "#94a3b8" }}>{copiedMessageId === m.id ? "Tersalin" : "Salin"}</button>
                                      {m.role === "user" && <button onClick={() => startEditing(m)} className="text-[9px] font-bold tracking-widest opacity-40 hover:opacity-100 uppercase transition-all" style={{ color: theme === "light" ? "inherit" : "#94a3b8" }}>Edit</button>}
                                    </div>
                                  )}
                               </div>
                             )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  <AnimatePresence mode="popLayout">
                    {isTyping && (
                      <motion.div 
                        key="typing"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 5 }}
                        className="flex items-start gap-3"
                      >
                        <div className="h-8 w-8 md:h-10 md:w-10 shrink-0 flex items-center justify-center rounded-xl shadow-sm border transition-all" style={{ backgroundColor: theme === "light" ? "white" : "#1e293b", borderColor: theme === "light" ? "rgba(0,0,0,0.05)" : "rgba(255,255,255,0.05)" }}>
                          <div className="relative h-6 w-6 md:h-7 md:w-7 pixelated animate-pulse">
                            <NextImage
 src="/img/iconchatbot.png" alt="AI" fill sizes="28px" />
                          </div>
                        </div>
                        <div className="px-4 py-3 rounded-2xl rounded-tl-none border shadow-sm transition-all flex items-center gap-1.5" style={{ backgroundColor: theme === "light" ? "white" : "#1e293b", borderColor: theme === "light" ? "rgba(0,0,0,0.05)" : "rgba(255,255,255,0.05)" }}>
                          <motion.div animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1, repeat: Infinity, delay: 0 }} className="w-1.5 h-1.5 rounded-full bg-primary-400" />
                          <motion.div animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1, repeat: Infinity, delay: 0.2 }} className="w-1.5 h-1.5 rounded-full bg-primary-400" />
                          <motion.div animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1, repeat: Infinity, delay: 0.4 }} className="w-1.5 h-1.5 rounded-full bg-primary-400" />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                  <div ref={chatEndRef} />
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        {renderView === "chat" && (
          <div className={`fixed bottom-0 inset-x-0 z-50 transition-all duration-300 pointer-events-none ${scanSidebarOpen ? "lg:pl-[304px]" : "pl-0"}`}>
             <div className="mx-auto w-full max-w-3xl flex flex-col items-center">
                <div className="w-full pointer-events-auto pb-6 md:pb-8 px-3 md:px-0">
                  <AnimatePresence>{showFAQ && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden mb-3">
                    <div className="flex flex-wrap gap-2 pb-2 overflow-x-auto no-scrollbar">
                      {QUICK_PROMPTS.map((p, i) => (
                        <button 
                          key={i} 
                          onClick={() => { sendChat(p); setShowFAQ(false); }} 
                          className="shrink-0 px-4 py-2 text-[11px] font-medium border rounded-xl shadow-sm transition-all whitespace-nowrap"
                          style={{ 
                            backgroundColor: theme === "light" ? "white" : "#1e293b", 
                            color: theme === "light" ? "#1e293b" : "#f1f5f9",
                            borderColor: theme === "light" ? "rgba(0,0,0,0.05)" : "rgba(255,255,255,0.1)"
                          }}
                        >
                          {p}
                        </button>
                      ))}
                    </div>
                  </motion.div>
                )}</AnimatePresence>
                  <div className="rounded-2xl shadow-[0_-10px_40px_rgba(0,0,0,0.1)] dark:shadow-[0_-10px_40px_rgba(0,0,0,0.3)] border p-1.5 md:p-2 flex items-center gap-1.5 md:gap-2 backdrop-blur-xl transition-colors" style={{ backgroundColor: theme === "light" ? "rgba(255,255,255,0.9)" : "rgba(30,41,59,0.9)", borderColor: theme === "light" ? "rgba(0,0,0,0.05)" : "rgba(255,255,255,0.1)" }}>
                     <button onClick={() => setShowFAQ(!showFAQ)} className={`w-9 h-9 md:w-10 md:h-10 flex items-center justify-center rounded-lg transition-colors ${showFAQ ? "bg-primary-100 text-primary-600" : "opacity-40 hover:opacity-100"}`}><HelpCircle className="h-5 w-5" /></button>
                     <button onClick={() => { setScanPreviewUrl(null); setView("scan"); }} className="w-9 h-9 md:w-10 md:h-10 flex items-center justify-center opacity-40 hover:opacity-100 transition-colors"><Camera className="h-5 w-5" /></button>
                     <button onClick={() => galleryInputRef.current?.click()} className="w-9 h-9 md:w-10 md:h-10 flex items-center justify-center opacity-40 hover:opacity-100 transition-colors"><Images className="h-5 w-5" /></button>
                     <textarea value={chatInput} onChange={e => setChatInput(e.target.value)} placeholder="Tanya sesuatu..." className="flex-1 bg-transparent outline-none resize-none text-sm py-2 placeholder:opacity-50 transition-colors" style={{ color: theme === "light" ? "#1e293b" : "white" }} rows={1} onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChat(); } }} />
                     <button onClick={() => sendChat()} className="w-9 h-9 md:w-10 md:h-10 flex items-center justify-center bg-primary-600 text-white rounded-xl shadow-lg hover:bg-primary-500 transition-all active:scale-95 shadow-primary-500/20"><Send className="h-4 w-4" /></button>
                  </div>
                </div>
             </div>
          </div>
        )}
      </div>

      <AnimatePresence>
        {view === "scan" && (
           <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[300] bg-black flex flex-col md:items-center md:justify-center md:p-4">
              
              {/* Close Button - Top Left on Mobile, Top Right inside container on Desktop */}
              <div className="absolute top-6 left-6 z-[310] md:hidden">
                 <button onClick={() => setView(prevViewRef.current)} className="p-3 bg-white/10 rounded-full text-white backdrop-blur-md hover:bg-white/20 transition-all border border-white/10"><X className="h-6 w-6" /></button>
              </div>

              {/* Camera Container */}
              <div className="relative flex-1 md:flex-none w-full md:max-w-2xl md:aspect-[4/3] bg-slate-900 md:rounded-[2rem] overflow-hidden shadow-2xl">
                 <video ref={videoRef} autoPlay playsInline muted className="h-full w-full object-cover" />
                 
                 {/* Visual Scan Guide Brackets */}
                 <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                   <div className="w-64 h-64 border-2 border-primary-500/30 rounded-3xl relative">
                     <div className="absolute -top-1 -left-1 w-8 h-8 border-t-4 border-l-4 border-primary-500 rounded-tl-xl" />
                     <div className="absolute -top-1 -right-1 w-8 h-8 border-t-4 border-r-4 border-primary-500 rounded-tr-xl" />
                     <div className="absolute -bottom-1 -left-1 w-8 h-8 border-b-4 border-l-4 border-primary-500 rounded-bl-xl" />
                     <div className="absolute -bottom-1 -right-1 w-8 h-8 border-b-4 border-r-4 border-primary-500 rounded-br-xl" />
                   </div>
                 </div>

                 {/* Desktop Only Buttons (Original Layout) */}
                 <div className="hidden md:block absolute top-6 right-6 flex items-center gap-3">
                   <button onClick={() => setView(prevViewRef.current)} className="p-3 bg-black/40 rounded-full text-white backdrop-blur-md hover:bg-black/60 transition-all"><X className="h-6 w-6" /></button>
                 </div>
                 <div className="hidden md:flex absolute bottom-10 inset-x-0 flex items-center justify-center gap-8">
                    <button onClick={() => galleryInputRef.current?.click()} className="p-4 bg-white/10 rounded-full text-white backdrop-blur-md hover:bg-white/20 transition-all"><Images className="h-7 w-7" /></button>
                    <button onClick={captureFromVideo} className="h-20 w-20 rounded-full bg-white border-[6px] border-white/20 active:scale-90 transition-transform shadow-2xl" />
                    <button onClick={() => setCameraFacingUser(!cameraFacingUser)} className="p-4 bg-white/10 rounded-full text-white backdrop-blur-md hover:bg-white/20 transition-all"><RefreshCw className="h-7 w-7" /></button>
                 </div>
              </div>

              {/* Mobile Only Controls Area (Bottom Area) */}
              <div className="md:hidden relative h-40 w-full flex items-center justify-center gap-8 px-6 bg-gradient-to-t from-black via-black/80 to-transparent pb-8">
                 <button onClick={() => galleryInputRef.current?.click()} className="p-4 bg-white/10 rounded-full text-white backdrop-blur-md hover:bg-white/20 transition-all border border-white/10"><Images className="h-6 w-6" /></button>
                 <button onClick={captureFromVideo} className="relative h-20 w-20 rounded-full bg-white flex items-center justify-center shadow-2xl active:scale-90 transition-transform group">
                    <div className="h-[72px] w-[72px] rounded-full border-4 border-black/5" />
                    <div className="absolute inset-0 rounded-full border-4 border-primary-500 opacity-0 group-active:opacity-100 transition-opacity" />
                 </button>
                 <button onClick={() => setCameraFacingUser(!cameraFacingUser)} className="p-4 bg-white/10 rounded-full text-white backdrop-blur-md hover:bg-white/20 transition-all border border-white/10"><RefreshCw className="h-6 w-6" /></button>
              </div>
           </motion.div>
        )}
        {view === "analyzing" && (
           <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[500] backdrop-blur-2xl flex flex-col items-center justify-center transition-colors" style={{ backgroundColor: theme === "light" ? "rgba(248,245,239,0.9)" : "rgba(15,23,42,0.9)" }}>
              <div className="relative group">
                {scanPreviewUrl && (
                  <div className="relative w-48 h-48 md:w-56 md:h-56 mb-10 rounded-3xl overflow-hidden shadow-xl border-2" style={{ borderColor: theme === "light" ? "white" : "rgba(255,255,255,0.1)" }}>
                    <NextImage
 src={scanPreviewUrl} alt="Analyzing" className="object-cover grayscale-[0.3] scale-105" fill sizes="224px" />
                    <div className="absolute inset-0 bg-primary-500/5 backdrop-brightness-90" />
                  </div>
                )}
                <div className="absolute -bottom-5 left-1/2 -translate-x-1/2">
                   <div
                     className="h-10 w-10 flex items-center justify-center rounded-2xl shadow-lg border transition-colors duration-300"
                     style={{
                       background: theme === "light" ? "rgba(255,255,255,0.92)" : "rgba(30,41,59,0.92)",
                       borderColor: theme === "light" ? "rgba(0,0,0,0.06)" : "rgba(255,255,255,0.12)",
                     }}
                   >
                      <Loader2
                        className="h-5 w-5 animate-spin"
                        style={{ color: theme === "light" ? "#5b9e2a" : "#9dd16b" }}
                      />
                   </div>
                </div>
              </div>
              <div className="mt-12 text-center">
                 <p className="font-pixel text-sm tracking-[0.3em] uppercase transition-colors" style={{ color: theme === "light" ? "#3a6219" : "#7cbd40" }}>Memproses Diagnosis</p>
                 <p
                   className="mt-2 text-[10px] font-bold tracking-widest uppercase transition-colors duration-300"
                   style={{ color: theme === "light" ? "rgba(107, 82, 41, 0.45)" : "rgba(148, 163, 184, 0.6)" }}
                 >
                   Kecerdasan Buatan Sedang Menganalisis...
                 </p>
              </div>
           </motion.div>
        )}
      </AnimatePresence>
      <input ref={galleryInputRef} type="file" accept="image/*" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) setImageFromFile(f); e.target.value = ""; }} />
    </div>
  );
}
