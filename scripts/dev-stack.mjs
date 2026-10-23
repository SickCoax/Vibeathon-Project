import { spawn } from 'node:child_process';
import net from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createInterface } from 'node:readline';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const host = '127.0.0.1';
const owned = [];
let shuttingDown = false;

function log(message) {
  process.stdout.write(`[VibeShift] ${message}\n`);
}

function expectedHealth(value) {
  return value && value.application === 'vibeshift-ai' && Number.isInteger(value.backend_port) && value.status === 'ok' && typeof value.provider_configured === 'boolean' &&
    (value.provider === 'gemini' || value.provider === 'openai-compatible');
}

async function fetchJson(url, timeoutMs = 900) {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });
    if (!response.ok) return null;
    const value = await response.json();
    return expectedHealth(value) ? value : null;
  } catch {
    return null;
  }
}

function portIsFree(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', () => resolve(false));
    server.listen({ host, port, exclusive: true }, () => {
      server.close(() => resolve(true));
    });
  });
}


function forwardLines(stream, label) {
  const lines = createInterface({ input: stream });
  lines.on('line', (line) => process.stdout.write(`[${label}] ${line}\n`));
}

function launch(command, args, options, label) {
  const child = spawn(command, args, { ...options, stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true });
  const record = { child, label, exited: false, exitCode: null };
  owned.push(record);
  forwardLines(child.stdout, label);
  forwardLines(child.stderr, label);
  child.once('error', (error) => {
    record.exited = true;
    log(`${label} failed to start: ${error.message}`);
  });
  child.once('exit', (code) => {
    record.exited = true;
    record.exitCode = code;
    if (!shuttingDown) log(`${label} stopped unexpectedly (exit ${code ?? 'unknown'}).`);
  });
  return record;
}

async function waitFor(check, record, label, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  let lastError = '';
  while (Date.now() < deadline) {
    if (record?.exited) throw new Error(`${label} exited before becoming ready (exit ${record.exitCode ?? 'unknown'}).`);
    try {
      const result = await check();
      if (result) return result;
    } catch (error) {
      lastError = error.message;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`${label} did not become ready within ${timeoutMs / 1000}s${lastError ? `: ${lastError}` : '.'}`);
}

async function selectBackend() {
  for (let port = 5001; port <= 5015; port += 1) {
    const url = `http://${host}:${port}`;
    const existing = await fetchJson(`${url}/api/health`);
    if (existing) {
      log(`Reusing the verified project Flask API on ${url} (provider configured: ${existing.provider_configured}).`);
      return { port, reused: true, health: existing };
    }
    if (await portIsFree(port)) return { port, reused: false };
    log(`Port ${port} is occupied by a service that did not identify as the VibeShift API; leaving it untouched.`);
  }
  throw new Error('No available backend port found in 5001-5015. No existing process was stopped.');
}

async function selectFrontend(backendPort) {
  for (let port = 5173; port <= 5190; port += 1) {
    const url = `http://${host}:${port}`;
    try {
      const page = await fetch(url, { signal: AbortSignal.timeout(700) });
      if (page.ok) {
        const html = await page.text();
        if (html.includes('VibeShift AI')) {
          const health = await fetchJson(`${url}/api/health`);
          if (health && health.backend_port === backendPort) {
            log(`Reusing the verified project Vite preview on ${url}; its API proxy is healthy (provider configured: ${health.provider_configured}).`);
            return { port, reused: true };
          }
          if (health) {
            log(`VibeShift preview on port ${port} targets Flask port ${health.backend_port}; expected ${backendPort}. Leaving it untouched.`);
          } else {
            log(`A VibeShift page is already on port ${port}, but its API proxy is not healthy; leaving it untouched.`);
          }
        }
      }
    } catch {
      // The port may be free or a listener may not be reachable from this host.
    }
    if (await portIsFree(port)) return { port, reused: false };
    log(`Port ${port} is occupied; leaving its listener untouched.`);
  }
  throw new Error('No available frontend port found in 5173-5190. No existing process was stopped.');
}

function stopOwned() {
  if (shuttingDown) return;
  shuttingDown = true;
  for (const { child, label } of owned.reverse()) {
    if (!child.killed && child.exitCode === null) {
      log(`Stopping this launcher's ${label} process.`);
      child.kill();
    }
  }
}

process.once('SIGINT', () => { stopOwned(); process.exitCode = 0; });
process.once('SIGTERM', () => { stopOwned(); process.exitCode = 0; });

try {
  const python = path.join(root, '.venv', 'Scripts', 'python.exe');
  const viteCli = path.join(root, 'node_modules', 'vite', 'bin', 'vite.js');
  const deps = path.join(root, 'work', 'python_deps');
  const backend = await selectBackend();

  if (!backend.reused) {
    log(`Starting Flask on ${host}:${backend.port}; backend/.env is loaded by backend/app.py from its own directory.`);
    const pythonPath = [deps, process.env.PYTHONPATH].filter(Boolean).join(path.delimiter);
    const record = launch(python, [path.join(root, 'backend', 'app.py')], {
      cwd: root,
      env: { ...process.env, PYTHONPATH: pythonPath, PORT: String(backend.port) },
    }, 'Flask');
    backend.health = await waitFor(() => fetchJson(`http://${host}:${backend.port}/api/health`, 1200), record, 'Flask health endpoint');
    backend.record = record;
    log(`Flask health check passed (provider configured: ${backend.health.provider_configured}).`);
  }

  const frontend = await selectFrontend(backend.port);
  if (!frontend.reused) {
    log(`Starting Vite on ${host}:${frontend.port}, proxying /api to Flask on ${host}:${backend.port}.`);
    const record = launch(process.execPath, [viteCli, '--host', host, '--port', String(frontend.port), '--strictPort'], {
      cwd: root,
      env: { ...process.env, VIBESHIFT_BACKEND_URL: `http://${host}:${backend.port}` },
    }, 'Vite');
    frontend.record = record;
    await waitFor(async () => {
      try {
        const page = await fetch(`http://${host}:${frontend.port}`, { signal: AbortSignal.timeout(1200) });
        const html = page.ok ? await page.text() : '';
        if (!page.ok || !html.includes('VibeShift AI')) return null;
        const health = await fetchJson(`http://${host}:${frontend.port}/api/health`, 1500);
        return health ? { health } : null;
      } catch {
        return null;
      }
    }, record, 'Vite page and API proxy');
  }

  const frontendUrl = `http://${host}:${frontend.port}/`;
  const proxiedHealth = await fetchJson(`http://${host}:${frontend.port}/api/health`, 2500);
  if (!proxiedHealth) throw new Error('Frontend loaded, but /api/health through the Vite proxy did not return the VibeShift health JSON.');

  log(`READY: ${frontendUrl}`);
  log(`API proxy health: ok; provider configured: ${proxiedHealth.provider_configured}.`);
  log('Use this URL in the Codex preview. Keep this terminal session open; press Ctrl+C to stop only processes started here.');

  const watched = owned.filter(({ child }) => child.exitCode === null);
  if (watched.length === 0) {
    log('Both project services were already running; no new processes were started.');
  } else {
    await Promise.race(watched.map(({ child, label }) => new Promise((resolve) => child.once('exit', () => resolve(label)))));
  }
  if (watched.length > 0 && !shuttingDown) {
    log('A managed service exited; stopping the other service started by this launcher.');
    stopOwned();
    process.exitCode = 1;
  }
} catch (error) {
  log(`Startup failed: ${error.message}`);
  stopOwned();
  process.exitCode = 1;
}
