// Electron main process — VULCAN-2D desktop app.
// Spawns the bundled Python engine sidecar (PyInstaller binary) on startup,
// waits until it answers /health, then opens the UI window. Kills it on quit.
const { app, BrowserWindow } = require('electron')
const path = require('path')
const fs = require('fs')
const http = require('http')
const { spawn } = require('child_process')

const ENGINE_PORT = 8000
let engineProc = null

function enginePath() {
  // Packaged: resources/engine/vulcan-engine ; Dev: the PyInstaller output.
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'engine', 'vulcan-engine')
  }
  return path.join(__dirname, '..', 'engine-dist', 'vulcan-engine', 'vulcan-engine')
}

function startEngine() {
  const exe = enginePath()
  if (!fs.existsSync(exe)) {
    console.warn('[vulcan] engine binary not found at', exe, '— expecting an external engine on :' + ENGINE_PORT)
    return
  }
  engineProc = spawn(exe, [], { stdio: 'ignore' })
  engineProc.on('error', (e) => console.error('[vulcan] engine spawn error:', e))
  engineProc.on('exit', (code) => console.log('[vulcan] engine exited:', code))
}

function waitForEngine(done, tries = 80) {
  const attempt = (n) => {
    const req = http.get({ host: '127.0.0.1', port: ENGINE_PORT, path: '/health', timeout: 1000 }, (res) => {
      res.resume()
      done(true)
    })
    req.on('error', () => {
      if (n <= 0) return done(false)
      setTimeout(() => attempt(n - 1), 300)
    })
    req.on('timeout', () => req.destroy())
  }
  attempt(tries)
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1480,
    height: 920,
    minWidth: 1100,
    minHeight: 720,
    backgroundColor: '#090a0d',
    title: 'VULCAN-2D',
    webPreferences: { contextIsolation: true, nodeIntegration: false },
  })
  const devUrl = process.env.VULCAN_DEV_URL
  if (devUrl) {
    win.loadURL(devUrl)
  } else {
    win.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }
}

function stopEngine() {
  if (engineProc) {
    try { engineProc.kill() } catch (_) { /* ignore */ }
    engineProc = null
  }
}

app.whenReady().then(() => {
  startEngine()
  waitForEngine(() => createWindow()) // open the window whether or not the engine answered
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  stopEngine()
  if (process.platform !== 'darwin') app.quit()
})
app.on('before-quit', stopEngine)
app.on('quit', stopEngine)
process.on('exit', stopEngine)
