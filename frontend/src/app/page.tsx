"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { signIn } from "next-auth/react";
import Image from "next/image";
import { useTheme } from "@/context/ThemeContext";

function TwinkleStar({ x, y, delay = 0 }: { x: string; y: string; delay?: number }) {
  const { theme } = useTheme();
  return (
    <motion.span
      className="absolute pointer-events-none select-none text-[10px]"
      style={{ left: x, top: y, color: theme === "light" ? "#c9a227" : "#64b4dc" }}
      animate={{ opacity: [0.2, 0.7, 0.2], scale: [0.8, 1.1, 0.8] }}
      transition={{ duration: 2.8, repeat: Infinity, delay, ease: "easeInOut" }}
    >
      ✦
    </motion.span>
  );
}

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const { theme } = useTheme();

  const signInWithGoogle = () => {
    setIsLoading(true);
    signIn("google", { callbackUrl: "/dashboard" });
  };

  return (
    <div
      className="relative flex min-h-[100dvh] flex-col items-center justify-center overflow-hidden px-6 transition-colors duration-500"
      style={{ fontFamily: "Inter, system-ui, sans-serif" }}
    >
      {/* Background Image */}
      <div className="fixed inset-0 z-[-2] pointer-events-none">
        <Image 
          src={theme === "light" ? "/img/background.jpg" : "/img/darkbg.jpg"} 
          alt="" 
          fill 
          sizes="100vw"
          priority
          className="object-cover transition-opacity duration-700" 
          quality={90} 
        />
        {/* Tint overlay */}
        <div 
          className="absolute inset-0 z-[-1] transition-colors duration-500"
          style={{ background: theme === "light" ? "rgba(240, 244, 232, 0.15)" : "rgba(15, 23, 42, 0.4)" }}
        />
      </div>
      {/* Very subtle pixel grid */}
      <div className="cg-pixel-grid pointer-events-none absolute inset-0 opacity-20 z-0" />

      {/* Twinkling stars */}
      <TwinkleStar x="8%" y="15%" delay={0} />
      <TwinkleStar x="88%" y="10%" delay={0.8} />
      <TwinkleStar x="12%" y="78%" delay={1.5} />
      <TwinkleStar x="85%" y="75%" delay={0.4} />
      <TwinkleStar x="50%" y="6%" delay={1.1} />

      {/* Main card */}
      <motion.div
        initial={{ opacity: 0, y: 16, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 w-[90vw] max-w-[400px] overflow-hidden transition-all duration-300 mx-auto"
        style={{
          background: theme === "light" ? "#ffffff" : "#1e293b",
          borderRadius: "16px",
          border: theme === "light" ? "1.5px solid rgba(107, 82, 41, 0.14)" : "1.5px solid rgba(255, 255, 255, 0.1)",
          boxShadow: theme === "light" 
            ? "0 4px 6px rgba(45, 33, 24, 0.06), 0 12px 40px rgba(45, 33, 24, 0.08), 0 3px 0 rgba(107, 82, 41, 0.1)"
            : "0 4px 20px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.05)",
        }}
      >
        {/* Thin warm top accent */}
        <div style={{ height: "3px", background: "linear-gradient(90deg, #5b9e2a, #c9a227, #5b9e2a)" }} />

        <div className="px-6 py-8 md:px-8">
          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mb-7 flex flex-col items-center gap-3"
          >
            <div
              className="cg-float relative h-20 w-20 md:h-28 md:w-28 overflow-hidden mb-3 mx-auto"
              style={{ imageRendering: "pixelated" }}
            >
              <Image 
                src="/img/logo.png" 
                alt="ChilliGuard" 
                fill 
                sizes="(max-width: 768px) 80px, 112px"
                className="object-contain drop-shadow-md" 
                priority 
                loading="eager"
              />
            </div>
            <div className="text-center">
              <h1 className="font-pixel text-2xl text-center tracking-wide transition-colors duration-300" style={{ color: theme === "light" ? "#3a6219" : "#7cbd40" }}>
                ChilliGuard
              </h1>
              <p className="mt-1.5 text-xs font-pixel tracking-widest text-center transition-colors duration-300" style={{ color: theme === "light" ? "#8b6e37" : "#9dd16b" }}>
                ✦ ASISTEN PETANI CABAI ✦
              </p>
            </div>
          </motion.div>

          {/* Divider */}
          <div className="my-6 flex items-center gap-3">
            <div className="flex-1 h-0.5" style={{ background: theme === "light" ? "rgba(107, 82, 41, 0.15)" : "rgba(255, 255, 255, 0.1)" }} />
            <span className="text-[10px] font-pixel transition-colors duration-300" style={{ color: theme === "light" ? "rgba(107, 82, 41, 0.5)" : "rgba(255, 255, 255, 0.4)" }}>START</span>
            <div className="flex-1 h-0.5" style={{ background: theme === "light" ? "rgba(107, 82, 41, 0.15)" : "rgba(255, 255, 255, 0.1)" }} />
          </div>

          {/* Google Button */}
          <motion.button
            type="button"
            onClick={signInWithGoogle}
            disabled={isLoading}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            className="w-full flex items-center justify-center gap-2.5 py-3 px-4 text-base md:text-sm font-medium transition-all"
            style={{
              background: isLoading ? (theme === "light" ? "#f0f4e8" : "#1e293b") : "#5b9e2a",
              color: "#ffffff",
              borderRadius: "10px",
              border: "1.5px solid rgba(91, 158, 42, 0.3)",
              boxShadow: "0 2px 0 rgba(45, 90, 20, 0.25), 0 4px 12px rgba(91, 158, 42, 0.2)",
              fontFamily: "Inter, sans-serif",
              cursor: isLoading ? "not-allowed" : "pointer",
              opacity: isLoading ? 0.7 : 1,
            }}
          >
            {isLoading ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            ) : (
              <>
                <svg className="h-4 w-4 shrink-0" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Masuk dengan Google
              </>
            )}
          </motion.button>

          {/* Footer */}
          <p className="mt-5 text-center text-xs md:text-[10px] px-4 transition-colors duration-300" style={{ color: theme === "light" ? "#a89080" : "#94a3b8", fontFamily: "Inter, sans-serif" }}>
            Dengan masuk, Anda menyetujui{" "}
            <a href="#" className="underline underline-offset-2 hover:text-primary-600 transition-colors">Ketentuan</a>
            {" "}dan{" "}
            <a href="#" className="underline underline-offset-2 hover:text-primary-600 transition-colors">Privasi</a>
          </p>
        </div>
      </motion.div>

      {/* Version */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        className="relative z-10 mt-5 font-pixel text-[8px] transition-colors duration-300"
        style={{ color: theme === "light" ? "rgba(107, 82, 41, 0.4)" : "rgba(255, 255, 255, 0.3)" }}
      >
        ChilliGuard v1.0 ✦ AI Petani Cabai
      </motion.p>
    </div>
  );
}
