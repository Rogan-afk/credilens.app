import { createServer } from 'vite'

async function main() {
  try {
    const server = await createServer({
      configFile: 'vite.config.mjs', // ensure we load the clean config above
    })
    await server.listen()
    server.printUrls()
    console.log('\nVite dev server is running. Press Ctrl+C to stop.\n')

    // Keep process alive and close gracefully
    const close = async () => {
      try { await server.close() } finally { process.exit(0) }
    }
    process.on('SIGINT', close)
    process.on('SIGTERM', close)
    process.on('uncaughtException', (e) => { console.error(e); close() })
  } catch (err) {
    console.error('Failed to start Vite:', err)
    // Keep process open so you can read the error instead of the window closing
    setInterval(() => {}, 1 << 30)
  }
}
main()
