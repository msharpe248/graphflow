import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  // Determine certificate directory
  const certDir = env.GRAPHFLOW_CERT_DIR || path.resolve(__dirname, '../../.certs')

  // Check if we should use HTTPS
  const useHttps = env.GRAPHFLOW_HTTPS === 'true' || (
    fs.existsSync(path.join(certDir, 'graphflow.key')) &&
    fs.existsSync(path.join(certDir, 'graphflow.crt'))
  )

  // Configure HTTPS if certificates exist
  let httpsConfig: boolean | { key: Buffer; cert: Buffer } = false
  if (useHttps) {
    const keyPath = path.join(certDir, 'graphflow.key')
    const certPath = path.join(certDir, 'graphflow.crt')

    if (fs.existsSync(keyPath) && fs.existsSync(certPath)) {
      httpsConfig = {
        key: fs.readFileSync(keyPath),
        cert: fs.readFileSync(certPath),
      }
    }
  }

  // Determine runtime URL based on HTTPS setting
  const runtimeUrl = env.GRAPHFLOW_RUNTIME_URL || (useHttps ? 'https://localhost:8000' : 'http://localhost:8000')

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 3000,
      https: httpsConfig,
      proxy: {
        '/api': {
          target: runtimeUrl,
          changeOrigin: true,
          secure: false, // Allow self-signed certificates
        },
      },
    },
  }
})
