// Read-only inspection using an independent browser profile; never attaches to the shared MCP browser.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright-core');
const config = require('./resources.json');

async function main() {
  const directory = path.join(__dirname, '.browser-proof');
  fs.mkdirSync(directory, { recursive: true });
  process.env.TEMP = directory;
  process.env.TMP = directory;
  process.env.TMPDIR = directory;
  const context = await chromium.launchPersistentContext(path.join(directory, 'profile'), {
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: !process.argv.includes('--visible'),
    downloadsPath: path.join(directory, 'downloads'),
    tracesDir: path.join(directory, 'traces')
  });
  try {
    const page = context.pages()[0] || await context.newPage();
    const failures = [];
    const errors = [];
    page.on('requestfailed', request => {
      if (failures.length < 12) failures.push({origin: new URL(request.url()).origin, error: request.failure()?.errorText});
    });
    page.on('pageerror', error => { if (errors.length < 8) errors.push(error.message.replace(/https?:\/\/\S+/g, '[URL omitted]')); });
    const studioHost = process.argv.includes('--preview') ? 'copilotstudio.preview.microsoft.com' : 'copilotstudio.microsoft.com';
    await page.goto(`https://${studioHost}/environments/${config.environmentId}/bots/${config.agentId}/overview`, {
      waitUntil: 'domcontentloaded', timeout: 60000
    });
    let bodyRendered = true;
    try {
      await page.waitForFunction(() => document.body && document.body.innerText.trim().length > 0, null, { timeout: 60000 });
    } catch {
      bodyRendered = false;
    }
    const location = new URL(page.url());
    const loginFields = await page.locator('input[type="email"], input[type="password"]').count();
    const pageStates = [];
    for (const current of context.pages()) {
      const text = (await current.locator('body').innerText()).slice(0, 1800)
        .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '[account]')
        .replace(/\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b/gi, '[identifier]');
      pageStates.push({origin: new URL(current.url()).origin, path: new URL(current.url()).pathname.replace(/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}/gi, '[identifier]'), title: await current.title(), pageText: text,
        frameOrigins: current.frames().map(frame => { try { return new URL(frame.url()).origin; } catch { return 'none'; } })});
    }
    console.log(JSON.stringify({
      independentProfile: true, origin: location.origin, title: await page.title(),
      bodyRendered, failures, errors,
      signInFieldsPresent: loginFields > 0,
      interactiveSignInRequired: /login\.microsoftonline\.com|login\.live\.com/.test(location.hostname) || loginFields > 0 ? true : null,
      authenticationState: 'Not established by this inspection',
      studioTestPanePresent: await page.getByRole('button', { name: /^Test$/i }).count() > 0,
      credentialsEntered: false, sharedBrowserAccessed: false, screenshotsCaptured: false
    }));
    console.log('Independent-page diagnostics:', JSON.stringify(pageStates));
  } finally {
    await context.close();
  }
}

main().catch(error => { console.error('Independent Studio inspection failed:', error.message.replace(/https?:\/\/\S+/g, '[URL omitted]')); process.exitCode = 1; });
