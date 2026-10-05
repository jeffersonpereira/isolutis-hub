import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vitest/config";

const apiAlvo = process.env.VITE_API_PROXY ?? "http://127.0.0.1:8000";

export default defineConfig({
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  server: {
    port: 5173,
    // Em desenvolvimento a API e o WebSocket passam pelo mesmo endereço do front (sem CORS).
    proxy: { "/api": { target: apiAlvo, ws: true, changeOrigin: true } },
  },
  build: { outDir: "dist", sourcemap: true },
  test: { environment: "jsdom", include: ["src/**/*.test.ts"] },
});
