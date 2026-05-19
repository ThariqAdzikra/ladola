export type StoredChatMessage = {
  role: "user" | "assistant" | "system";
  text: string;
  image?: string;
  prediction?: Record<string, unknown>;
};

export type StoredChatSession = {
  id: string;
  updatedAt: string;
  diagnosis: string;
  messages?: StoredChatMessage[];
  prediction?: Record<string, unknown>;
};

const BASE_KEY = "cg_chat_sessions_v2";
const OLD_KEY = "cg_chat_sessions_v1";

function getStorageKey(userId: string) {
  return `${BASE_KEY}_${userId}`;
}

export function loadChatSessions(userId?: string): StoredChatSession[] {
  if (typeof window === "undefined" || !userId) return [];
  const key = getStorageKey(userId);
  try {
    let raw = localStorage.getItem(key);
    
    // Migration: If new key is empty, check old key
    if (!raw) {
      const oldRaw = localStorage.getItem(OLD_KEY);
      if (oldRaw) {
        localStorage.setItem(key, oldRaw);
        // localStorage.removeItem(OLD_KEY); // Optional: Keep for safety for now
        raw = oldRaw;
      }
    }

    if (!raw) return [];
    const parsed = JSON.parse(raw) as StoredChatSession[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function upsertChatSession(session: StoredChatSession, userId?: string): void {
  if (typeof window === "undefined" || !userId) return;
  const all = loadChatSessions(userId);
  const i = all.findIndex((s) => s.id === session.id);
  
  // Create updated session object with fresh timestamp
  const next = { 
    ...session, 
    updatedAt: new Date().toISOString() 
  };
  
  if (i >= 0) {
    // If it exists, remove it from current position
    all.splice(i, 1);
  }
  
  // Always add the most recently updated session to the top
  all.unshift(next);
  
  localStorage.setItem(getStorageKey(userId), JSON.stringify(all.slice(0, 40)));
}
