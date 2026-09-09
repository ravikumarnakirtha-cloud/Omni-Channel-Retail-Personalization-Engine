/**
 * API Gateway
 * Routes requests to microservices with caching (Redis simulation) and rate limiting
 */
const express = require('express');
const axios = require('axios');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');

const app = express();
app.use(express.json());
app.use(cors());
app.use(morgan('combined'));

// ── Service URLs ────────────────────────────────
const SERVICES = {
  recommendation: process.env.REC_SERVICE_URL  || 'http://localhost:8000',
  ingestion:      process.env.ING_SERVICE_URL  || 'http://localhost:8001',
  feature:        process.env.FEAT_SERVICE_URL || 'http://localhost:8002',
  notification:   process.env.NOTIF_SERVICE_URL|| 'http://localhost:8003',
};

// ── Simple In-Memory Cache (Redis simulation) ──
const CACHE = new Map();
const CACHE_TTL = 30_000; // 30 seconds

function cacheGet(key) {
  const item = CACHE.get(key);
  if (!item) return null;
  if (Date.now() - item.ts > CACHE_TTL) { CACHE.delete(key); return null; }
  return item.value;
}
function cacheSet(key, value) {
  CACHE.set(key, { value, ts: Date.now() });
}

// ── Rate Limiter ────────────────────────────────
const limiter = rateLimit({
  windowMs: 60_000,
  max: 100,
  message: { error: 'Too many requests, please slow down.' },
});
app.use('/api/', limiter);

// ── Request Logger ──────────────────────────────
const requestLog = [];
app.use((req, _res, next) => {
  requestLog.push({ method: req.method, path: req.path, ts: new Date().toISOString() });
  if (requestLog.length > 500) requestLog.shift();
  next();
});

// ── Proxy Helper ────────────────────────────────
async function proxy(serviceUrl, path, method = 'GET', body = null) {
  const url = `${serviceUrl}${path}`;
  const cfg = { method, url, headers: { 'Content-Type': 'application/json' }, timeout: 10000 };
  if (body) cfg.data = body;
  const resp = await axios(cfg);
  return resp.data;
}

// ════════════════════════════════════════════════
// GATEWAY ROUTES
// ════════════════════════════════════════════════

app.get('/', (_req, res) => {
  res.json({
    service: 'API Gateway',
    version: '1.0.0',
    uptime: process.uptime(),
    routes: [
      'GET  /api/health',
      'GET  /api/recommend/:userId',
      'GET  /api/segment/:userId',
      'POST /api/ingest/event',
      'POST /api/ingest/transaction',
      'POST /api/trigger-offer',
      'GET  /api/analytics/summary',
      'GET  /api/analytics/segments',
      'GET  /api/products',
      'GET  /api/users',
      'POST /api/notify',
      'GET  /api/gateway/stats',
    ],
  });
});

// ── Health ──────────────────────────────────────
app.get('/api/health', async (_req, res) => {
  const checks = {};
  for (const [name, url] of Object.entries(SERVICES)) {
    try {
      await axios.get(`${url}/health`, { timeout: 3000 });
      checks[name] = 'healthy';
    } catch {
      try {
        await axios.get(`${url}/`, { timeout: 3000 });
        checks[name] = 'healthy';
      } catch {
        checks[name] = 'unreachable';
      }
    }
  }
  res.json({ gateway: 'healthy', services: checks, ts: new Date().toISOString() });
});

// ── Recommend ───────────────────────────────────
app.get('/api/recommend/:userId', async (req, res) => {
  const { userId } = req.params;
  const topN = req.query.top_n || 5;
  const cacheKey = `rec:${userId}:${topN}`;
  const cached = cacheGet(cacheKey);
  if (cached) return res.json({ ...cached, _cached: true });

  try {
    const data = await proxy(SERVICES.recommendation, '/recommend', 'POST', { user_id: userId, top_n: Number(topN) });
    cacheSet(cacheKey, data);
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: 'Recommendation service unavailable', details: err.message });
  }
});

// ── Segment ─────────────────────────────────────
app.get('/api/segment/:userId', async (req, res) => {
  const cacheKey = `seg:${req.params.userId}`;
  const cached = cacheGet(cacheKey);
  if (cached) return res.json({ ...cached, _cached: true });

  try {
    const data = await proxy(SERVICES.recommendation, `/get-segment/${req.params.userId}`);
    cacheSet(cacheKey, data);
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: 'Segment service unavailable', details: err.message });
  }
});

// ── Ingest Event ────────────────────────────────
app.post('/api/ingest/event', async (req, res) => {
  try {
    const data = await proxy(SERVICES.ingestion, '/ingest/event', 'POST', req.body);
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: 'Ingestion service unavailable', details: err.message });
  }
});

// ── Ingest Transaction ──────────────────────────
app.post('/api/ingest/transaction', async (req, res) => {
  try {
    const data = await proxy(SERVICES.ingestion, '/ingest/transaction', 'POST', req.body);
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: 'Ingestion service unavailable', details: err.message });
  }
});

// ── Trigger Offer ───────────────────────────────
app.post('/api/trigger-offer', async (req, res) => {
  try {
    const data = await proxy(SERVICES.recommendation, '/trigger-offer', 'POST', req.body);
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: 'Offer service unavailable', details: err.message });
  }
});

// ── Notify ──────────────────────────────────────
app.post('/api/notify', async (req, res) => {
  try {
    const data = await proxy(SERVICES.notification, '/send', 'POST', req.body);
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: 'Notification service unavailable', details: err.message });
  }
});

// ── Analytics ───────────────────────────────────
app.get('/api/analytics/summary', async (_req, res) => {
  const cacheKey = 'analytics:summary';
  const cached = cacheGet(cacheKey);
  if (cached) return res.json({ ...cached, _cached: true });

  try {
    const data = await proxy(SERVICES.recommendation, '/segments/summary');
    cacheSet(cacheKey, data);
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: 'Analytics unavailable', details: err.message });
  }
});

app.get('/api/analytics/segments', async (_req, res) => {
  try {
    const data = await proxy(SERVICES.recommendation, '/segments/distribution');
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: 'Analytics unavailable', details: err.message });
  }
});

app.get('/api/products', async (_req, res) => {
  const cached = cacheGet('products');
  if (cached) return res.json(cached);
  try {
    const data = await proxy(SERVICES.feature, '/channel/usage');
    cacheSet('products', data);
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: 'Service unavailable', details: err.message });
  }
});

app.get('/api/users', async (req, res) => {
  try {
    const data = await proxy(SERVICES.recommendation, `/users?limit=${req.query.limit || 20}`);
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: 'Service unavailable', details: err.message });
  }
});

app.get('/api/simulate/stream', async (req, res) => {
  try {
    const data = await proxy(SERVICES.ingestion, `/simulate/stream?n=${req.query.n || 20}`, 'POST');
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: 'Simulation failed', details: err.message });
  }
});

// ── Gateway Stats ────────────────────────────────
app.get('/api/gateway/stats', (_req, res) => {
  res.json({
    total_requests: requestLog.length,
    cache_size: CACHE.size,
    uptime_seconds: Math.round(process.uptime()),
    recent_requests: requestLog.slice(-20),
  });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`🚀 API Gateway running on http://localhost:${PORT}`));
