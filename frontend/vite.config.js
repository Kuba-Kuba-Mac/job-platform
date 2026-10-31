import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// В dev-режиме запросы /api и /media проксируются на Django
const backend = process.env.VITE_PROXY_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": backend,
      "/media": backend,
    },
  },
});
