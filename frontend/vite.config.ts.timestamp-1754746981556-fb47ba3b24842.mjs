// vite.config.ts
import { defineConfig } from "file:///Users/jeonmingyu/Desktop/lvlup-ai-core/frontend/node_modules/.pnpm/vite@5.4.19_@types+node@20.19.9/node_modules/vite/dist/node/index.js";
import react from "file:///Users/jeonmingyu/Desktop/lvlup-ai-core/frontend/node_modules/.pnpm/@vitejs+plugin-react@4.7.0_vite@5.4.19_@types+node@20.19.9_/node_modules/@vitejs/plugin-react/dist/index.js";
import compression from "file:///Users/jeonmingyu/Desktop/lvlup-ai-core/frontend/node_modules/.pnpm/vite-plugin-compression@0.5.1_vite@5.4.19_@types+node@20.19.9_/node_modules/vite-plugin-compression/dist/index.mjs";
import path from "node:path";
import { fileURLToPath } from "node:url";
var __vite_injected_original_import_meta_url = "file:///Users/jeonmingyu/Desktop/lvlup-ai-core/frontend/vite.config.ts";
var __dirname = path.dirname(fileURLToPath(__vite_injected_original_import_meta_url));
var vite_config_default = defineConfig({
  plugins: [react(), compression({ algorithm: "brotliCompress", deleteOriginFile: false })],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src")
    }
  },
  server: {
    port: 5173
  },
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom"],
          vendor: ["axios", "@tanstack/react-query", "recharts"]
        }
      }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvVXNlcnMvamVvbm1pbmd5dS9EZXNrdG9wL2x2bHVwLWFpLWNvcmUvZnJvbnRlbmRcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIi9Vc2Vycy9qZW9ubWluZ3l1L0Rlc2t0b3AvbHZsdXAtYWktY29yZS9mcm9udGVuZC92aXRlLmNvbmZpZy50c1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vVXNlcnMvamVvbm1pbmd5dS9EZXNrdG9wL2x2bHVwLWFpLWNvcmUvZnJvbnRlbmQvdml0ZS5jb25maWcudHNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJztcbmltcG9ydCByZWFjdCBmcm9tICdAdml0ZWpzL3BsdWdpbi1yZWFjdCc7XG4vLyBAdHMtZXhwZWN0LWVycm9yIHR5cGVzXG5pbXBvcnQgY29tcHJlc3Npb24gZnJvbSAndml0ZS1wbHVnaW4tY29tcHJlc3Npb24nO1xuLy8gQHRzLWV4cGVjdC1lcnJvciBidWlsdC1pbiB0eXBlcyB2aWEgbm9kZVxuaW1wb3J0IHBhdGggZnJvbSAnbm9kZTpwYXRoJztcbi8vIEB0cy1leHBlY3QtZXJyb3IgYnVpbHQtaW4gdHlwZXMgdmlhIG5vZGVcbmltcG9ydCB7IGZpbGVVUkxUb1BhdGggfSBmcm9tICdub2RlOnVybCc7XG5cbi8vIEVTTSBfX2Rpcm5hbWUgcG9seWZpbGxcbi8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBAdHlwZXNjcmlwdC1lc2xpbnQvYmFuLXRzLWNvbW1lbnRcbi8vIEB0cy1pZ25vcmVcbmNvbnN0IF9fZGlybmFtZSA9IHBhdGguZGlybmFtZShmaWxlVVJMVG9QYXRoKGltcG9ydC5tZXRhLnVybCkpO1xuXG4vLyBodHRwczovL3ZpdGVqcy5kZXYvY29uZmlnL1xuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcbiAgcGx1Z2luczogW3JlYWN0KCksIGNvbXByZXNzaW9uKHsgYWxnb3JpdGhtOiAnYnJvdGxpQ29tcHJlc3MnLCBkZWxldGVPcmlnaW5GaWxlOiBmYWxzZSB9KV0sXG4gIHJlc29sdmU6IHtcbiAgICBhbGlhczoge1xuICAgICAgJ0AnOiBwYXRoLnJlc29sdmUoX19kaXJuYW1lLCAnLi9zcmMnKSxcbiAgICB9LFxuICB9LFxuICBzZXJ2ZXI6IHtcbiAgICBwb3J0OiA1MTczLFxuICB9LFxuICBidWlsZDoge1xuICAgIGNodW5rU2l6ZVdhcm5pbmdMaW1pdDogNjAwLFxuICAgIHJvbGx1cE9wdGlvbnM6IHtcbiAgICAgIG91dHB1dDoge1xuICAgICAgICBtYW51YWxDaHVua3M6IHtcbiAgICAgICAgICByZWFjdDogWydyZWFjdCcsICdyZWFjdC1kb20nXSxcbiAgICAgICAgICB2ZW5kb3I6IFsnYXhpb3MnLCAnQHRhbnN0YWNrL3JlYWN0LXF1ZXJ5JywgJ3JlY2hhcnRzJ10sXG4gICAgICAgIH0sXG4gICAgICB9LFxuICAgIH0sXG4gIH0sXG59KTsgIl0sCiAgIm1hcHBpbmdzIjogIjtBQUFrVSxTQUFTLG9CQUFvQjtBQUMvVixPQUFPLFdBQVc7QUFFbEIsT0FBTyxpQkFBaUI7QUFFeEIsT0FBTyxVQUFVO0FBRWpCLFNBQVMscUJBQXFCO0FBUDBLLElBQU0sMkNBQTJDO0FBWXpQLElBQU0sWUFBWSxLQUFLLFFBQVEsY0FBYyx3Q0FBZSxDQUFDO0FBRzdELElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzFCLFNBQVMsQ0FBQyxNQUFNLEdBQUcsWUFBWSxFQUFFLFdBQVcsa0JBQWtCLGtCQUFrQixNQUFNLENBQUMsQ0FBQztBQUFBLEVBQ3hGLFNBQVM7QUFBQSxJQUNQLE9BQU87QUFBQSxNQUNMLEtBQUssS0FBSyxRQUFRLFdBQVcsT0FBTztBQUFBLElBQ3RDO0FBQUEsRUFDRjtBQUFBLEVBQ0EsUUFBUTtBQUFBLElBQ04sTUFBTTtBQUFBLEVBQ1I7QUFBQSxFQUNBLE9BQU87QUFBQSxJQUNMLHVCQUF1QjtBQUFBLElBQ3ZCLGVBQWU7QUFBQSxNQUNiLFFBQVE7QUFBQSxRQUNOLGNBQWM7QUFBQSxVQUNaLE9BQU8sQ0FBQyxTQUFTLFdBQVc7QUFBQSxVQUM1QixRQUFRLENBQUMsU0FBUyx5QkFBeUIsVUFBVTtBQUFBLFFBQ3ZEO0FBQUEsTUFDRjtBQUFBLElBQ0Y7QUFBQSxFQUNGO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
