import { defineConfig } from "vite";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
const root = dirname(fileURLToPath(import.meta.url));
export default defineConfig({ resolve: { alias: { "@": resolve(root, "src") } }, build: { outDir: "dist", emptyOutDir: true } });
