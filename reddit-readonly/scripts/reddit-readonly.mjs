#!/usr/bin/env node

/**
 * reddit-readonly.mjs
 *
 * Read-only Reddit CLI using public JSON endpoints.
 *
 * Commands output JSON to stdout:
 * - Success: { ok: true, data: ... }
 * - Failure: { ok: false, error: { message, details? } }
 */

const BASE_URL = 'https://www.reddit.com';

const DEFAULTS = {
  minDelayMs: parseInt(process.env.REDDIT_RO_MIN_DELAY_MS || '500', 10),
  maxDelayMs: parseInt(process.env.REDDIT_RO_MAX_DELAY_MS || '1500', 10),
  timeoutMs: parseInt(process.env.REDDIT_RO_TIMEOUT_MS || '20000', 10),
  userAgent: process.env.REDDIT_RO_USER_AGENT || 'script:clawdbot-reddit-readonly:v1.0.0',
  maxChars: 1000,
};

function nowMs() { return Date.now(); }
function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }
function randInt(min, max) {
  const lo = Math.min(min, max), hi = Math.max(min, max);
  return lo + Math.floor(Math.random() * (hi - lo + 1));
}
function toIsoFromUtcSeconds(sec) { return new Date(sec * 1000).toISOString(); }
function clampInt(n, lo, hi, fallback) { const x = Number.isFinite(n) ? n : fallback; return Math.max(lo, Math.min(hi, x)); }
function parseCommaList(s) { if (!s) return []; return String(s).split(',').map((x) => x.trim()).filter(Boolean); }

function parseArgs(argv) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next && !next.startsWith('--')) { out[key] = next; i++; }
      else { out[key] = true; }
    } else { out._.push(a); }
  }
  return out;
}

function ok(data) { process.stdout.write(JSON.stringify({ ok: true, data }, null, 2) + '\n'); }
function fail(message, details) {
  const error = { message };
  if (details) error.details = details;
  process.stdout.write(JSON.stringify({ ok: false, error }, null, 2) + '\n');
  process.exitCode = 1;
}

async function fetchJson(url, { timeoutMs } = {}) {
  if (typeof fetch !== 'function') throw new Error('Requires Node.js 18+');
  await sleep(randInt(DEFAULTS.minDelayMs, DEFAULTS.maxDelayMs));
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs || DEFAULTS.timeoutMs);
  try {
    const res = await fetch(url, { headers: { 'User-Agent': DEFAULTS.userAgent, 'Accept': 'application/json' }, signal: controller.signal });
    const text = await res.text();
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${text.slice(0, 300)}`);
    if (text.trim().startsWith('<')) throw new Error('Reddit returned HTML. Try again later.');
    return JSON.parse(text);
  } finally { clearTimeout(t); }
}

async function fetchJsonWithRetry(url, { retries = 3 } = {}) {
  let attempt = 0, lastErr = null;
  while (attempt <= retries) {
    try { return await fetchJson(url); }
    catch (e) {
      lastErr = e;
      const msg = String(e && e.message ? e.message : e);
      const isRetryable = msg.includes('HTTP 429') || msg.includes('HTTP 5') || msg.includes('aborted') || msg.includes('HTML');
      if (!isRetryable || attempt === retries) break;
      await sleep(600 * Math.pow(2, attempt) + randInt(0, 400));
      attempt++;
    }
  }
  throw lastErr || new Error('Request failed');
}

function buildUrl(pathWithQuery) {
  if (/^https?:\/\//i.test(pathWithQuery)) return pathWithQuery;
  const [path, qs] = String(pathWithQuery).split('?');
  const jsonPath = path.endsWith('.json') ? path : `${path}.json`;
  return qs ? `${BASE_URL}${jsonPath}?${qs}` : `${BASE_URL}${jsonPath}`;
}

function extractPostId(input) {
  const s = String(input || '').trim();
  if (!s) return null;
  if (/^[a-z0-9]{5,10}$/i.test(s)) return s;
  const m = s.match(/comments\/([a-z0-9]{5,10})/i);
  return m ? m[1] : null;
}

function normalisePermalink(permalink) {
  if (!permalink) return null;
  if (permalink.startsWith('http')) return permalink;
  return permalink.startsWith('/') ? `${BASE_URL}${permalink}` : `${BASE_URL}/${permalink}`;
}

function normalisePost(p) {
  const d = p && p.data ? p.data : p;
  const cu = d.created_utc || 0;
  return { id: d.id, fullname: d.name || (d.id ? `t3_${d.id}` : null), subreddit: d.subreddit, title: d.title, author: d.author,
    score: d.score, num_comments: d.num_comments, created_utc: cu, created_iso: cu ? toIsoFromUtcSeconds(cu) : null,
    permalink: normalisePermalink(d.permalink), url: d.url, is_self: d.is_self, over_18: d.over_18, flair: d.link_flair_text || null,
    selftext_snippet: d.selftext ? String(d.selftext).slice(0, 800) : null };
}

function normaliseComment(c, { depth, parentFullname, maxChars }) {
  const d = c && c.data ? c.data : c;
  const cu = d.created_utc || 0;
  const body = d.body || '';
  return { id: d.id, fullname: d.name || (d.id ? `t1_${d.id}` : null), author: d.author, score: d.score,
    created_utc: cu, created_iso: cu ? toIsoFromUtcSeconds(cu) : null, depth,
    parent_fullname: parentFullname || d.parent_id || null, permalink: normalisePermalink(d.permalink),
    body_snippet: body ? String(body).slice(0, maxChars) : null };
}

function parseCommentsTree(children, { depth = 0, parentFullname = null, maxDepth = 8, includeDeleted = false, maxChars = 1000 }) {
  const out = []; let moreCount = 0;
  if (!Array.isArray(children)) return { comments: out, moreCount };
  for (const node of children) {
    if (!node) continue;
    if (node.kind === 'more') { moreCount += (node?.data?.count || 0); continue; }
    if (node.kind !== 't1') continue;
    const author = node?.data?.author; const body = node?.data?.body;
    if (!(author === '[deleted]' || body === '[deleted]' || body === '[removed]' || body == null))
      out.push(normaliseComment(node, { depth, parentFullname, maxChars }));
    if (depth < maxDepth) {
      const replies = node?.data?.replies;
      const rcpp = replies && replies.data && Array.isArray(replies.data.children) ? replies.data.children : null;
      if (rcpp) {
        const parsed = parseCommentsTree(rcpp, { depth: depth + 1, parentFullname: node?.data?.name || (node?.data?.id ? `t1_${node.data.id}` : parentFullname), maxDepth, includeDeleted, maxChars });
        out.push(...parsed.comments); moreCount += parsed.moreCount;
      }
    }
  }
  return { comments: out, moreCount };
}

function keywordHits(text, keywords) {
  const t = String(text || '').toLowerCase();
  return keywords.filter(kw => String(kw).toLowerCase() && t.includes(String(kw).toLowerCase()));
}
function hoursAgo(cu) { return cu ? (Date.now() - cu * 1000) / 3600000 : Number.POSITIVE_INFINITY; }

async function cmdPosts(subreddit, args) {
  const sort = String(args.sort || 'hot'), time = String(args.time || 'day');
  const limit = clampInt(parseInt(args.limit || '25', 10), 1, 100, 25);
  const after = args.after ? String(args.after) : null;
  const qs = new URLSearchParams({ limit: String(limit) });
  if ((sort === 'top' || sort === 'controversial') && time) qs.set('t', time);
  if (after) qs.set('after', after);
  const listing = await fetchJsonWithRetry(buildUrl(`/r/${subreddit}/${sort}?${qs}`));
  ok({ subreddit, sort, time: (sort === 'top' || sort === 'controversial') ? time : null, limit, after: listing?.data?.after || null, before: listing?.data?.before || null,
    posts: (listing?.data?.children || []).filter(x => x?.kind === 't3').map(x => normalisePost(x)) });
}

async function cmdSearch(scope, query, args) {
  const sort = String(args.sort || 'relevance'), time = String(args.time || 'all');
  const limit = clampInt(parseInt(args.limit || '25', 10), 1, 100, 25);
  const after = args.after ? String(args.after) : null;
  const qs = new URLSearchParams({ q: query, sort, t: time, limit: String(limit) });
  if (after) qs.set('after', after);
  const path = scope === 'all' ? `/search?${qs}` : (qs.set('restrict_sr', 'on'), `/r/${scope}/search?${qs}`);
  const listing = await fetchJsonWithRetry(buildUrl(path));
  ok({ scope, query, sort, time, limit, after: listing?.data?.after || null, before: listing?.data?.before || null,
    posts: (listing?.data?.children || []).filter(x => x?.kind === 't3').map(x => normalisePost(x)) });
}

async function cmdRecentComments(subreddit, args) {
  const limit = clampInt(parseInt(args.limit || '25', 10), 1, 100, 25);
  const listing = await fetchJsonWithRetry(buildUrl(`/r/${subreddit}/comments?limit=${limit}`));
  ok({ subreddit, limit, comments: (listing?.data?.children || []).filter(x => x?.kind === 't1').map(x => {
    const d = x.data; return { id: d.id, fullname: d.name || (d.id ? `t1_${d.id}` : null), subreddit: d.subreddit, author: d.author, score: d.score,
      created_utc: d.created_utc, created_iso: d.created_utc ? toIsoFromUtcSeconds(d.created_utc) : null,
      permalink: normalisePermalink(d.permalink), link_id: d.link_id || null, link_title: d.link_title || null,
      link_permalink: d.link_permalink ? normalisePermalink(d.link_permalink) : null,
      body_snippet: d.body ? String(d.body).slice(0, clampInt(parseInt(args.maxChars || '1000', 10), 50, 5000, 1000)) : null };
  }) });
}

async function cmdComments(postIdOrUrl, args) {
  const postId = extractPostId(postIdOrUrl); if (!postId) throw new Error('Could not parse post id.');
  const limit = clampInt(parseInt(args.limit || '50', 10), 1, 500, 50);
  const maxDepth = clampInt(parseInt(args.depth || '8', 10), 0, 20, 8);
  const maxChars = clampInt(parseInt(args.maxChars || '1000', 10), 50, 20000, 1000);
  const data = await fetchJsonWithRetry(buildUrl(`/comments/${postId}?limit=${limit}`));
  const children = (Array.isArray(data) ? data[1] : null)?.data?.children || [];
  ok({ post_id: postId, limit, max_depth: maxDepth, max_chars: maxChars,
    more_count_estimate: parseCommentsTree(children, { maxDepth, maxChars }).moreCount,
    comments: parseCommentsTree(children, { maxDepth, maxChars }).comments });
}

async function cmdThread(postIdOrUrl, args) {
  const postId = extractPostId(postIdOrUrl); if (!postId) throw new Error('Could not parse post id.');
  const commentLimit = clampInt(parseInt(args.commentLimit || args.limit || '50', 10), 1, 500, 50);
  const maxDepth = clampInt(parseInt(args.depth || '8', 10), 0, 20, 8);
  const maxChars = clampInt(parseInt(args.maxChars || '1000', 10), 50, 20000, 1000);
  const data = await fetchJsonWithRetry(buildUrl(`/comments/${postId}?limit=${commentLimit}`));
  const [pl, cl] = Array.isArray(data) ? data : [null, null];
  const postChild = pl?.data?.children?.find(x => x?.kind === 't3');
  const children = cl?.data?.children || [];
  ok({ post: postChild ? normalisePost(postChild) : null,
    comments: parseCommentsTree(children, { maxDepth, maxChars }).comments,
    more_count_estimate: parseCommentsTree(children, { maxDepth, maxChars }).moreCount });
}

async function cmdFind(args) {
  const subreddits = parseCommaList(args.subreddits || args.subreddit);
  if (subreddits.length === 0) throw new Error('find requires --subreddits');
  const query = String(args.query || ''), include = parseCommaList(args.include), exclude = parseCommaList(args.exclude);
  const minScore = args.minScore != null ? parseInt(args.minScore, 10) : 0;
  const maxAgeHours = args.maxAgeHours != null ? parseFloat(args.maxAgeHours) : null;
  const perSubLimit = clampInt(parseInt(args.perSubredditLimit || '25', 10), 1, 100, 25);
  const maxResults = clampInt(parseInt(args.maxResults || '10', 10), 1, 100, 10);
  const rank = String(args.rank || 'new');
  const collected = [], perSub = {};
  for (const sub of subreddits) {
    let posts;
    if (query) {
      const listing = await fetchJsonWithRetry(buildUrl(`/r/${sub}/search?q=${encodeURIComponent(query)}&restrict_sr=on&sort=new&t=all&limit=${perSubLimit}`));
      posts = (listing?.data?.children || []).filter(x => x?.kind === 't3').map(x => normalisePost(x));
    } else {
      const listing = await fetchJsonWithRetry(buildUrl(`/r/${sub}/new?limit=${perSubLimit}`));
      posts = (listing?.data?.children || []).filter(x => x?.kind === 't3').map(x => normalisePost(x));
    }
    perSub[sub] = posts.length;
    for (const p of posts) {
      const text = `${p.title || ''}\n${p.selftext_snippet || ''}`;
      const hits = keywordHits(text, include), exHits = keywordHits(text, exclude);
      if (include.length > 0 && hits.length === 0) continue;
      if (exclude.length > 0 && exHits.length > 0) continue;
      if (typeof minScore === 'number' && (p.score || 0) < minScore) continue;
      if (maxAgeHours != null && hoursAgo(p.created_utc) > maxAgeHours) continue;
      const reason = []; if (query) reason.push(`query:${query}`); if (hits.length) reason.push(`include:${hits.join(',')}`);
      if (maxAgeHours != null) reason.push(`age_h:${hoursAgo(p.created_utc).toFixed(1)}`);
      if (minScore) reason.push(`minScore:${minScore}`);
      collected.push({ ...p, reason, match_score: hits.length });
    }
  }
  const ranked = collected.slice().sort((a, b) => {
    if (rank === 'score') return (b.score || 0) - (a.score || 0);
    if (rank === 'comments') return (b.num_comments || 0) - (a.num_comments || 0);
    if (rank === 'match') return (b.match_score || 0) - (a.match_score || 0);
    return (b.created_utc || 0) - (a.created_utc || 0);
  });
  ok({ criteria: { subreddits, query: query || null, include, exclude, minScore, maxAgeHours, perSubredditLimit: perSubLimit, maxResults, rank },
    meta: { fetched_per_subreddit: perSub, candidates: collected.length, returned: Math.min(maxResults, ranked.length) },
    results: ranked.slice(0, maxResults) });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const [cmd, ...rest] = args._;
  try {
    switch (cmd) {
      case 'posts': { const [s] = rest; if (!s) throw new Error('Usage: posts <subreddit>'); await cmdPosts(s, args); break; }
      case 'search': { const [s, ...q] = rest; const query = q.join(' ').trim(); if (!s || !query) throw new Error('Usage: search <subreddit|all> <query>'); await cmdSearch(s, query, args); break; }
      case 'comments': { const [u] = rest; if (!u) throw new Error('Usage: comments <post_id|url>'); await cmdComments(u, args); break; }
      case 'recent-comments': { const [s] = rest; if (!s) throw new Error('Usage: recent-comments <subreddit>'); await cmdRecentComments(s, args); break; }
      case 'thread': { const [u] = rest; if (!u) throw new Error('Usage: thread <post_id|url>'); await cmdThread(u, args); break; }
      case 'find': { await cmdFind(args); break; }
      default: throw new Error(usage());
    }
  } catch (e) { fail(String(e?.message || e)); }
}
function usage() { return 'Commands: posts <sub> [--sort hot|new|top|controversial|rising] [--time day|week|month|year|all] [--limit N]\n  search <sub|all> <query> [--sort relevance|top|new|comments] [--time all|day|week|month|year] [--limit N]\n  comments <post_id|url> [--limit N] [--depth N] [--maxChars N]\n  recent-comments <sub> [--limit N]\n  thread <post_id|url> [--commentLimit N] [--depth N] [--maxChars N]\n  find --subreddits "a,b" [--query "..."] [--include "k1,k2"] [--exclude "k3"] [--minScore N] [--maxAgeHours H] [--perSubredditLimit N] [--maxResults N] [--rank new|score|comments|match]'; }
main();
