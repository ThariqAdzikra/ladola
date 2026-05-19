"use client";

import { useTheme } from "@/context/ThemeContext";
import { motion, AnimatePresence } from "framer-motion";
import { Sun, Moon } from "lucide-react";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="fixed top-3 right-3 md:top-6 md:right-6 z-[200]">
      <motion.button
        onClick={toggleTheme}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        className="relative h-10 w-10 md:h-12 md:w-12 flex items-center justify-center rounded-xl md:rounded-2xl overflow-hidden transition-colors duration-300"
        style={{ 
          background: "transparent",
          backdropFilter: "blur(4px)",
          border: theme === "light" ? "1.5px solid #8b6e37" : "1.5px solid #7cbd40"
        }}
      >
        <AnimatePresence mode="wait">
          {theme === "light" ? (
            <motion.div
              key="sun"
              initial={{ y: 20, opacity: 0, rotate: -45 }}
              animate={{ y: 0, opacity: 1, rotate: 0 }}
              exit={{ y: -20, opacity: 0, rotate: 45 }}
              transition={{ duration: 0.3 }}
            >
              <Sun className="h-6 w-6 text-[#8b6e37]" strokeWidth={2} />
            </motion.div>
          ) : (
            <motion.div
              key="moon"
              initial={{ y: 20, opacity: 0, rotate: 45 }}
              animate={{ y: 0, opacity: 1, rotate: 0 }}
              exit={{ y: -20, opacity: 0, rotate: -45 }}
              transition={{ duration: 0.3 }}
            >
              <Moon className="h-6 w-6 text-[#7cbd40]" strokeWidth={2} />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>
    </div>
  );
}
