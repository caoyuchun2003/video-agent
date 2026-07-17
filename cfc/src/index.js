/**
 * 百度 CFC 网关 — video-agent
 *
 * path 白名单转发 + 注入 X-Gateway-Token。千帆 Key 不经过这里。
 *
 * 环境变量:
 *   BACKEND_URL   - 例如 http://180.76.180.105/video
 *   GATEWAY_TOKEN - 与服务器 .env 一致
 *   ALLOW_ORIGIN  - 例如 https://video.yuchuntest.com
 *
 * 触发器:HTTP GET+POST+OPTIONS,不认证;超时建议 90 秒(含文生图)。
 */
'use strict';

const http = require('http');
const https = require('https');
const { URL } = require('url');

const BACKEND_URL = process.env.BACKEND_URL || '';
const GATEWAY_TOKEN = process.env.GATEWAY_TOKEN || '';
// 逗号分隔白名单；证书未就绪时需同时放行 http + https
const ALLOW_ORIGINS = String(process.env.ALLOW_ORIGIN || '*')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean);

const ROUTES = {
  '/prompt/polish': 'POST',
  '/video/create': 'POST',
  '/video/status': 'GET',
};

function corsHeaders(event) {
  const reqOrigin = (event && event.headers && (event.headers.origin || event.headers.Origin)) || '';
  let allow = ALLOW_ORIGINS[0] || '*';
  if (ALLOW_ORIGINS.includes('*')) {
    allow = reqOrigin || '*';
  } else if (reqOrigin && ALLOW_ORIGINS.includes(reqOrigin)) {
    allow = reqOrigin;
  }
  return {
    'Access-Control-Allow-Origin': allow,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    Vary: 'Origin',
  };
}

function respond(event, statusCode, bodyObj) {
  return {
    isBase64Encoded: false,
    statusCode,
    headers: { 'Content-Type': 'application/json; charset=utf-8', ...corsHeaders(event) },
    body: typeof bodyObj === 'string' ? bodyObj : JSON.stringify(bodyObj),
  };
}

function targetUrl(path, query) {
  const base = String(BACKEND_URL || '').replace(/\/$/, '');
  const url = new URL(base + path);
  for (const [k, v] of Object.entries(query || {})) {
    if (v != null) url.searchParams.set(k, v);
  }
  return url;
}

function forward(method, path, query, body) {
  return new Promise((resolve, reject) => {
    const url = targetUrl(path, query);
    const lib = url.protocol === 'https:' ? https : http;
    const headers = {
      'Content-Type': 'application/json',
      'X-Gateway-Token': GATEWAY_TOKEN,
    };
    if (method === 'POST') headers['Content-Length'] = Buffer.byteLength(body);
    const req = lib.request(url, { method, headers, timeout: 85000 }, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () =>
        resolve({ statusCode: res.statusCode, body: Buffer.concat(chunks).toString('utf-8') })
      );
    });
    req.on('timeout', () => req.destroy(new Error('后端响应超时')));
    req.on('error', reject);
    if (method === 'POST') req.write(body);
    req.end();
  });
}

exports.handler = async (event) => {
  const method = (event.httpMethod || '').toUpperCase();
  const rawPath = event.path || '/';
  const path = Object.keys(ROUTES).find((p) => rawPath === p || rawPath.endsWith(p));

  if (method === 'OPTIONS') {
    return { isBase64Encoded: false, statusCode: 204, headers: corsHeaders(event), body: '' };
  }
  if (!path) {
    return respond(event, 404, { error: '未知路径' });
  }
  if (method !== ROUTES[path]) {
    return respond(event, 405, { error: `该路径仅支持 ${ROUTES[path]}` });
  }
  if (!BACKEND_URL || !GATEWAY_TOKEN) {
    return respond(event, 500, { error: '网关未配置 BACKEND_URL / GATEWAY_TOKEN' });
  }

  let body = event.body || '';
  if (event.isBase64Encoded) {
    body = Buffer.from(body, 'base64').toString('utf-8');
  }
  if (Buffer.byteLength(body) > 64 * 1024) {
    return respond(event, 413, { error: '请求体过大' });
  }

  try {
    const upstream = await forward(method, path, event.queryStringParameters, body);
    return respond(event, upstream.statusCode || 502, upstream.body);
  } catch (err) {
    return respond(event, 502, { error: `网关转发失败:${err.message}` });
  }
};
