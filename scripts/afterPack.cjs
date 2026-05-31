// electron-builder afterPack hook — ad-hoc code-sign the macOS app.
// Apple Silicon refuses to run unsigned arm64 binaries (immediate SIGKILL), so
// even without a paid Developer ID we must ad-hoc sign ("-"). The bundled
// PyInstaller engine is already ad-hoc signed; this signs the Electron app.
const { execSync } = require('child_process')
const path = require('path')

exports.default = async function afterPack(context) {
  if (context.electronPlatformName !== 'darwin') return
  const appName = context.packager.appInfo.productFilename
  const appPath = path.join(context.appOutDir, `${appName}.app`)
  console.log('[afterPack] clearing xattrs + ad-hoc signing:', appPath)
  execSync(`xattr -cr "${appPath}"`, { stdio: 'inherit' })
  execSync(`codesign --force --deep --sign - "${appPath}"`, { stdio: 'inherit' })
  console.log('[afterPack] ad-hoc signature applied')
}
