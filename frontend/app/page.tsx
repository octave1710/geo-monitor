'use client';
import { useState, useEffect, useRef } from 'react';

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

/* ─── Types ─── */
type QueryResult = {
  query: string;
  mentioned: boolean;
  snippet: string | null;
};

type PlatformResult = {
  platform: string;
  brand: string;
  mention_rate: number;
  sentiment: string;
  context: string;
  snippet: string | null;
  queries_tested: number;
  queries_with_mention: number;
  query_results?: QueryResult[];
};

type PlatformAnalysis = {
  platform: string;
  verdict: string;
  analysis: string;
};

type ScoreData = {
  visibility_score: number;
  summary: string;
  geo_recommendations: string[];
  dominant_sentiment: string;
  platform_analyses?: PlatformAnalysis[];
};

type ScanResult = {
  score: ScoreData;
  platforms: PlatformResult[];
  queries: string[];
};

/* ─── SVG Icons ─── */
const SearchIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" />
  </svg>
);

const BoltIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z" />
  </svg>
);

const CheckIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-green)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
    <path d="m5 12 5 5L20 7" />
  </svg>
);

const XIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
    <path d="m18 6-12 12" /><path d="m6 6 12 12" />
  </svg>
);

const ChevronIcon = ({ open }: { open: boolean }) => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
    style={{ transition: 'transform 0.25s cubic-bezier(0.16, 1, 0.3, 1)', transform: open ? 'rotate(180deg)' : 'rotate(0)' }}>
    <path d="m6 9 6 6 6-6" />
  </svg>
);

/* ─── Platform Badge ─── */
const platformMeta: Record<string, { color: string; label: string }> = {
  perplexity: { color: '#20B2AA', label: 'Perplexity' },
  chatgpt: { color: '#10A37F', label: 'ChatGPT' },
  bing: { color: '#00809D', label: 'Bing' },
};

const PlatformIcon = ({ platform, size = 28 }: { platform: string; size?: number }) => {
  const meta = platformMeta[platform] || { color: '#666', label: '?' };
  return (
    <div style={{
      width: size, height: size, borderRadius: 8,
      background: `${meta.color}18`, border: `1px solid ${meta.color}40`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: size * 0.45, fontWeight: 800, color: meta.color,
      flexShrink: 0,
    }}>
      {meta.label[0]}
    </div>
  );
};

/* ─── Animated Progress Ring ─── */
const ProgressRing = ({ value, size = 56, strokeWidth = 4 }: { value: number; size?: number; strokeWidth?: number }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;
  const color = value >= 60 ? 'var(--accent-green)' : value >= 30 ? 'var(--accent-amber)' : 'var(--accent-red)';

  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)', flexShrink: 0 }}>
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none"
        stroke="rgba(255,255,255,0.04)" strokeWidth={strokeWidth} />
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none"
        stroke={color} strokeWidth={strokeWidth}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        className="progress-ring-circle" />
    </svg>
  );
};

/* ─── Animated Counter ─── */
const AnimatedNumber = ({ target, duration = 1400 }: { target: number; duration?: number }) => {
  const [value, setValue] = useState(0);

  useEffect(() => {
    const startTime = performance.now();
    const animate = (now: number) => {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 4);
      setValue(Math.round(eased * target));
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [target, duration]);

  return <>{value}</>;
};

/* ─── Animated Bar ─── */
const AnimatedBar = ({ value, color, delay = 0 }: { value: number; color: string; delay?: number }) => (
  <div style={{ height: 6, background: 'rgba(255,255,255,0.04)', borderRadius: 3, overflow: 'hidden', flex: 1 }}>
    <div className="bar-fill" style={{
      height: '100%', width: `${value}%`, background: color, borderRadius: 3,
      animationDelay: `${delay}s`,
    }} />
  </div>
);

/* ─── Orbital Scanner ─── */
const OrbitalScanner = ({ label, active }: { label: string; active: boolean }) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
    <div style={{ position: 'relative', width: 48, height: 48, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <PlatformIcon platform={label} size={28} />
      {active && (
        <div className="orbit-container" style={{ position: 'absolute', inset: 0 }}>
          <div style={{
            position: 'absolute', top: 0, left: '50%', transform: 'translateX(-50%)',
            width: 6, height: 6, borderRadius: '50%',
            background: platformMeta[label]?.color || '#06B6D4',
            boxShadow: `0 0 8px ${platformMeta[label]?.color || '#06B6D4'}`,
          }} />
        </div>
      )}
    </div>
    <span style={{ fontSize: 11, color: active ? 'var(--text-secondary)' : 'var(--text-muted)', textTransform: 'capitalize', fontWeight: 500 }}>
      {label}
    </span>
  </div>
);

/* ─── Skeleton Card ─── */
const SkeletonCard = () => (
  <div className="glass animate-border-pulse" style={{ padding: 24, minHeight: 180 }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
      <div className="skeleton" style={{ width: 28, height: 28, borderRadius: 8 }} />
      <div className="skeleton" style={{ width: 70, height: 14 }} />
    </div>
    <div className="skeleton" style={{ width: '100%', height: 6, marginBottom: 16, borderRadius: 3 }} />
    <div className="skeleton" style={{ width: '55%', height: 12, marginBottom: 10 }} />
    <div className="skeleton" style={{ width: '75%', height: 12, marginBottom: 10 }} />
    <div className="skeleton" style={{ width: '35%', height: 12 }} />
  </div>
);

/* ─── Helpers ─── */
const sentimentColor = (s: string) =>
  s === 'positive' ? 'var(--accent-green)' : s === 'neutral' ? 'var(--accent-amber)' : 'var(--accent-red)';

const scoreColor = (n: number) =>
  n >= 60 ? 'var(--accent-green)' : n >= 30 ? 'var(--accent-amber)' : 'var(--accent-red)';

const scoreColorRaw = (n: number) =>
  n >= 60 ? '#10B981' : n >= 30 ? '#F59E0B' : '#EF4444';

const verdictStyle = (v: string) => {
  const map: Record<string, { bg: string; color: string; label: string }> = {
    strong: { bg: 'rgba(16,185,129,0.12)', color: 'var(--accent-green)', label: 'Strong' },
    moderate: { bg: 'rgba(245,158,11,0.12)', color: 'var(--accent-amber)', label: 'Moderate' },
    weak: { bg: 'rgba(239,68,68,0.12)', color: 'var(--accent-red)', label: 'Weak' },
  };
  return map[v] || map.moderate;
};

/* ═══════════════════════════════════════════
   Main Component
   ═══════════════════════════════════════════ */
export default function Home() {
  const [brand, setBrand] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [result, setResult] = useState<ScanResult | null>(null);
  const [platforms, setPlatforms] = useState<PlatformResult[]>([]);
  const [queries, setQueries] = useState<string[]>([]);
  const [expandedPlatform, setExpandedPlatform] = useState<string | null>(null);
  const [showScore, setShowScore] = useState(false);
  const scoreRef = useRef<HTMLDivElement>(null);

  const scan = async (demo = false) => {
    const effectiveBrand = brand.trim() || (demo ? 'Nike' : '');
    if (!effectiveBrand) return;
    if (demo && !brand.trim()) setBrand('Nike');
    setLoading(true);
    setResult(null);
    setPlatforms([]);
    setQueries([]);
    setExpandedPlatform(null);
    setShowScore(false);
    setStatus(demo ? 'Running demo scan...' : 'Generating search queries...');

    let totalPlatforms = 3;
    let receivedComplete = false;

    try {
      const url = `${BACKEND}/api/scan/${encodeURIComponent(effectiveBrand)}${demo ? '?demo=true' : ''}`;
      const res = await fetch(url);
      if (!res.ok || !res.body) {
        setStatus(`Server error (${res.status})`);
        setLoading(false);
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      const collectedPlatforms: PlatformResult[] = [];
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';
        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.replace('data: ', ''));
            if (data.type === 'started') {
              totalPlatforms = data.platforms?.length || 3;
              setStatus('Scanning AI platforms...');
            }
            if (data.type === 'queries') {
              setQueries(data.queries);
              setStatus(`Testing ${data.queries.length} queries across platforms...`);
            }
            if (data.type === 'platform_done') {
              collectedPlatforms.push(data.result);
              setPlatforms([...collectedPlatforms]);
              setStatus(`${collectedPlatforms.length}/${totalPlatforms} platforms complete`);
            }
            if (data.type === 'complete') {
              receivedComplete = true;
              setResult({ score: data.score, platforms: collectedPlatforms, queries: [] });
              setStatus('');
              setTimeout(() => {
                setShowScore(true);
                scoreRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }, 300);
            }
          } catch { /* skip malformed SSE events */ }
        }
      }
      if (!receivedComplete) {
        setStatus('Connection lost during scan. Please try again.');
      }
    } catch {
      setStatus('Connection error — check backend is running');
    }
    setLoading(false);
  };

  const allPlatformKeys = ['perplexity', 'chatgpt', 'bing'];
  const pendingPlatforms = loading
    ? allPlatformKeys.filter(p => !platforms.find(r => r.platform === p))
    : [];

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-deep)', color: 'var(--text-primary)', position: 'relative', overflow: 'hidden' }}>

      {/* Ambient background */}
      <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0 }}>
        <div style={{ position: 'absolute', top: -300, right: -300, width: 800, height: 800, borderRadius: '50%', background: 'radial-gradient(circle, rgba(6,182,212,0.05) 0%, transparent 70%)' }} />
        <div style={{ position: 'absolute', bottom: -400, left: -300, width: 900, height: 900, borderRadius: '50%', background: 'radial-gradient(circle, rgba(139,92,246,0.04) 0%, transparent 70%)' }} />
      </div>

      <div style={{ maxWidth: 920, margin: '0 auto', padding: '48px 24px', position: 'relative', zIndex: 1 }}>

        {/* ─── Header ─── */}
        <header className="animate-fade-in-up" style={{ marginBottom: 48 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-green)', boxShadow: '0 0 12px var(--accent-green)' }} />
            <span style={{ fontSize: 11, color: 'var(--text-muted)', letterSpacing: 3, textTransform: 'uppercase', fontWeight: 600 }}>GEO Monitor</span>
          </div>
          <h1 style={{ fontSize: 42, fontWeight: 800, margin: 0, letterSpacing: -1.5, lineHeight: 1.1 }}>
            <span className="gradient-text">Brand Visibility</span>
            <br />
            <span style={{ color: 'var(--text-primary)' }}>in AI Search</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: 12, fontSize: 15, lineHeight: 1.6, maxWidth: 480 }}>
            Track how your brand appears organically across AI platforms with per-query analysis.
          </p>
        </header>

        {/* ─── Input ─── */}
        <div className="animate-fade-in-up delay-1" style={{ display: 'flex', gap: 10, marginBottom: 40 }}>
          <div className="glass" style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 12, padding: '0 18px', transition: 'border-color 0.2s ease' }}>
            <span style={{ color: 'var(--text-muted)', display: 'flex' }}><SearchIcon /></span>
            <input
              value={brand}
              onChange={e => setBrand(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && scan()}
              placeholder="Enter brand name (e.g. Nike, Apple, Notion...)"
              aria-label="Brand name"
              style={{ flex: 1, padding: '16px 0', background: 'none', border: 'none', color: 'var(--text-primary)', fontSize: 15, outline: 'none', fontFamily: 'inherit' }}
            />
          </div>
          <button onClick={() => scan(false)} disabled={loading} aria-label="Scan brand"
            style={{
              padding: '0 28px', borderRadius: 16, border: 'none',
              background: loading ? 'var(--bg-card)' : 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))',
              color: '#fff', fontWeight: 600, fontSize: 15, cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease', fontFamily: 'inherit', opacity: loading ? 0.5 : 1,
            }}>
            {loading ? 'Scanning...' : 'Scan'}
          </button>
          <button onClick={() => scan(true)} disabled={loading} aria-label="Run demo"
            style={{
              padding: '0 22px', borderRadius: 16, border: '2px solid var(--accent-green)',
              background: 'rgba(16,185,129,0.06)', color: 'var(--accent-green)', fontWeight: 600, fontSize: 15,
              cursor: loading ? 'not-allowed' : 'pointer', transition: 'all 0.2s ease', fontFamily: 'inherit',
              display: 'flex', alignItems: 'center', gap: 7, opacity: loading ? 0.5 : 1,
            }}>
            <BoltIcon /> Demo
          </button>
        </div>

        {/* ─── Scanning Animation ─── */}
        {loading && pendingPlatforms.length > 0 && (
          <div className="animate-fade-in" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 40, marginBottom: 32, padding: '20px 0' }}>
            {['perplexity', 'chatgpt', 'bing'].map(p => {
              const done = platforms.find(r => r.platform === p);
              const active = !done && pendingPlatforms.includes(p);
              return (
                <div key={p} style={{ opacity: done ? 0.4 : 1, transition: 'opacity 0.3s ease' }}>
                  <OrbitalScanner label={p} active={active} />
                  {done && <div style={{ textAlign: 'center', marginTop: 4 }}><CheckIcon /></div>}
                </div>
              );
            })}
          </div>
        )}

        {/* ─── Status ─── */}
        {status && (
          <div className="animate-fade-in" style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24, justifyContent: 'center' }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-cyan)', animation: 'pulseGlow 1.5s ease-in-out infinite' }} />
            <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{status}</span>
          </div>
        )}

        {/* ─── Queries Tested ─── */}
        {queries.length > 0 && !loading && (
          <div className="animate-fade-in" style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: 2.5, textTransform: 'uppercase', fontWeight: 600, marginBottom: 10 }}>Queries Tested</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {queries.map((q, i) => (
                <span key={i} className="glass-subtle animate-slide-up" style={{ padding: '6px 14px', fontSize: 12, color: 'var(--text-secondary)', fontStyle: 'italic', animationDelay: `${i * 0.08}s` }}>
                  &ldquo;{q}&rdquo;
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ─── Platform Cards ─── */}
        {(platforms.length > 0 || pendingPlatforms.length > 0) && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 28 }}>
            {platforms.map((p, idx) => (
              <div key={p.platform} className="glass animate-fade-in-up"
                style={{
                  padding: 22, animationDelay: `${idx * 0.12}s`,
                  cursor: p.query_results ? 'pointer' : 'default',
                  transition: 'border-color 0.2s ease, transform 0.2s ease',
                }}
                onClick={() => p.query_results && setExpandedPlatform(expandedPlatform === p.platform ? null : p.platform)}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--glass-border)'; e.currentTarget.style.transform = 'translateY(0)'; }}
              >
                {/* Header row */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <PlatformIcon platform={p.platform} />
                    <span style={{ fontWeight: 600, fontSize: 14 }}>{platformMeta[p.platform]?.label || p.platform}</span>
                  </div>
                  <ProgressRing value={p.mention_rate} size={44} strokeWidth={3.5} />
                </div>

                {/* Bar + rate */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                  <AnimatedBar value={p.mention_rate} color={scoreColorRaw(p.mention_rate)} delay={idx * 0.15} />
                  <span style={{ fontSize: 18, fontWeight: 800, color: scoreColor(p.mention_rate), minWidth: 42, textAlign: 'right' }}>
                    {p.mention_rate}%
                  </span>
                </div>

                {/* Sentiment pill */}
                <div style={{
                  display: 'inline-flex', alignItems: 'center', gap: 5,
                  padding: '3px 10px', borderRadius: 20,
                  background: `color-mix(in srgb, ${sentimentColor(p.sentiment)} 10%, transparent)`,
                  marginBottom: 12,
                }}>
                  <div style={{ width: 5, height: 5, borderRadius: '50%', background: sentimentColor(p.sentiment) }} />
                  <span style={{ fontSize: 11, color: sentimentColor(p.sentiment), textTransform: 'capitalize', fontWeight: 500 }}>
                    {p.sentiment}
                  </span>
                </div>

                {/* Snippet */}
                {p.snippet && (
                  <div style={{
                    fontSize: 11.5, color: 'var(--text-secondary)', fontStyle: 'italic', lineHeight: 1.6,
                    borderLeft: `2px solid ${platformMeta[p.platform]?.color || 'var(--accent-cyan)'}`,
                    paddingLeft: 10, marginBottom: 10,
                  }}>
                    &ldquo;{p.snippet.length > 90 ? p.snippet.slice(0, 90) + '...' : p.snippet}&rdquo;
                  </div>
                )}

                {/* Expand toggle */}
                {p.query_results && (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 10, borderTop: '1px solid var(--border-subtle)' }}>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {p.queries_with_mention}/{p.queries_tested} queries matched
                    </span>
                    <ChevronIcon open={expandedPlatform === p.platform} />
                  </div>
                )}
              </div>
            ))}

            {pendingPlatforms.map(p => <SkeletonCard key={p} />)}
          </div>
        )}

        {/* ─── Query Breakdown (expanded) ─── */}
        {expandedPlatform && (() => {
          const p = platforms.find(x => x.platform === expandedPlatform);
          if (!p?.query_results) return null;
          return (
            <div className="glass animate-fade-in" style={{ padding: 22, marginBottom: 28, marginTop: -12 }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: 2.5, textTransform: 'uppercase', fontWeight: 600, marginBottom: 14 }}>
                Query Breakdown — <span style={{ color: platformMeta[p.platform]?.color }}>{platformMeta[p.platform]?.label}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {p.query_results.map((qr, i) => (
                  <div key={i} className="glass-subtle animate-slide-in-left"
                    style={{ padding: '12px 14px', display: 'flex', gap: 10, alignItems: 'flex-start', animationDelay: `${i * 0.08}s` }}>
                    <div style={{ marginTop: 2 }}>{qr.mentioned ? <CheckIcon /> : <XIcon />}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 500, marginBottom: 3 }}>
                        &ldquo;{qr.query}&rdquo;
                      </div>
                      <div style={{ fontSize: 11.5, color: qr.mentioned ? 'var(--text-secondary)' : 'var(--text-muted)', fontStyle: qr.mentioned ? 'italic' : 'normal', lineHeight: 1.5 }}>
                        {qr.mentioned && qr.snippet ? qr.snippet : 'Brand not found in results'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })()}

        {/* ─── Comparison Heatmap ─── */}
        {platforms.length === 3 && platforms.some(p => p.query_results && p.query_results.length > 0) && (
          <div className="glass animate-fade-in-up delay-2" style={{ padding: 24, marginBottom: 28 }}>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: 2.5, textTransform: 'uppercase', fontWeight: 600, marginBottom: 18 }}>
              Visibility Matrix
            </div>

            {/* Header row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr repeat(3, 80px)', gap: 8, marginBottom: 10 }}>
              <div />
              {platforms.map(p => (
                <div key={p.platform} style={{ textAlign: 'center', fontSize: 11, color: platformMeta[p.platform]?.color, fontWeight: 600 }}>
                  {platformMeta[p.platform]?.label}
                </div>
              ))}
            </div>

            {/* Query rows */}
            {(platforms[0]?.query_results || []).map((_, qi) => {
              const query = platforms[0]?.query_results?.[qi]?.query || '';
              return (
                <div key={qi} className="animate-slide-in-left"
                  style={{ display: 'grid', gridTemplateColumns: '1fr repeat(3, 80px)', gap: 8, alignItems: 'center', padding: '8px 0', borderTop: qi > 0 ? '1px solid var(--border-subtle)' : 'none', animationDelay: `${0.3 + qi * 0.1}s` }}>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontStyle: 'italic', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    &ldquo;{query}&rdquo;
                  </div>
                  {platforms.map(p => {
                    const qr = p.query_results?.[qi];
                    const mentioned = qr?.mentioned || false;
                    return (
                      <div key={p.platform} style={{ display: 'flex', justifyContent: 'center' }}>
                        <div style={{
                          width: 32, height: 32, borderRadius: 8,
                          background: mentioned ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.06)',
                          border: `1px solid ${mentioned ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.04)'}`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          transition: 'all 0.3s ease',
                        }}>
                          {mentioned ? <CheckIcon /> : <XIcon />}
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        )}

        {/* ─── Score Reveal ─── */}
        {result?.score && showScore && (
          <div ref={scoreRef}>
            {/* Score card */}
            <div className="glass glow-cyan animate-scale-reveal" style={{ padding: 36, marginBottom: 20, position: 'relative', overflow: 'hidden' }}>
              {/* Radial burst behind score */}
              <div style={{
                position: 'absolute', top: '50%', left: 120, transform: 'translate(-50%, -50%)',
                width: 300, height: 300, borderRadius: '50%',
                background: `radial-gradient(circle, ${scoreColorRaw(result.score.visibility_score)}12 0%, transparent 70%)`,
                pointerEvents: 'none',
              }} />

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28, position: 'relative' }}>
                <div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: 2.5, textTransform: 'uppercase', fontWeight: 600, marginBottom: 8 }}>
                    Visibility Score
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                    <span style={{ fontSize: 72, fontWeight: 800, color: scoreColor(result.score.visibility_score), lineHeight: 1, letterSpacing: -3 }}>
                      <AnimatedNumber target={result.score.visibility_score} duration={1600} />
                    </span>
                    <span style={{ fontSize: 22, color: 'var(--text-muted)', fontWeight: 300 }}>/100</span>
                  </div>
                </div>

                <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <ProgressRing value={result.score.visibility_score} size={110} strokeWidth={6} />
                  <span style={{
                    position: 'absolute', fontSize: 11, fontWeight: 600,
                    color: sentimentColor(result.score.dominant_sentiment),
                    textTransform: 'capitalize',
                  }}>
                    {result.score.dominant_sentiment}
                  </span>
                </div>
              </div>

              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: 14, margin: 0, position: 'relative' }}>
                {result.score.summary}
              </p>
            </div>

            {/* ─── Platform Analyses ─── */}
            {result.score.platform_analyses && result.score.platform_analyses.length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: 2.5, textTransform: 'uppercase', fontWeight: 600, marginBottom: 14, paddingLeft: 4 }}>
                  Platform Analysis
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {result.score.platform_analyses.map((pa, i) => {
                    const badge = verdictStyle(pa.verdict);
                    return (
                      <div key={pa.platform} className="glass animate-slide-up" style={{ padding: '18px 22px', animationDelay: `${0.2 + i * 0.12}s` }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                          <PlatformIcon platform={pa.platform} />
                          <span style={{ fontWeight: 600, fontSize: 14, flex: 1 }}>{platformMeta[pa.platform]?.label || pa.platform}</span>
                          <span style={{
                            padding: '3px 12px', borderRadius: 20, fontSize: 10, fontWeight: 700,
                            background: badge.bg, color: badge.color, textTransform: 'uppercase', letterSpacing: 1.5,
                          }}>
                            {badge.label}
                          </span>
                        </div>
                        <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.7, margin: 0 }}>
                          {pa.analysis}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* ─── Recommendations ─── */}
            {result.score.geo_recommendations && result.score.geo_recommendations.length > 0 && (
              <div className="glass animate-fade-in-up delay-5" style={{ padding: 26 }}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: 2.5, textTransform: 'uppercase', fontWeight: 600, marginBottom: 18 }}>
                  GEO Recommendations
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  {result.score.geo_recommendations.map((r, i) => (
                    <div key={i} className="animate-slide-up" style={{ display: 'flex', gap: 14, alignItems: 'flex-start', animationDelay: `${0.6 + i * 0.1}s` }}>
                      <div style={{
                        width: 26, height: 26, borderRadius: 8, flexShrink: 0,
                        background: 'rgba(6,182,212,0.08)', border: '1px solid rgba(6,182,212,0.2)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 11, fontWeight: 700, color: 'var(--accent-cyan)',
                      }}>
                        {i + 1}
                      </div>
                      <span style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, paddingTop: 3 }}>
                        {r}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ─── Empty state ─── */}
        {!loading && !result && platforms.length === 0 && (
          <div className="animate-fade-in delay-3" style={{ textAlign: 'center', padding: '80px 20px' }}>
            <div style={{ color: 'var(--text-muted)', opacity: 0.3, marginBottom: 16, display: 'flex', justifyContent: 'center' }}>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: 14, maxWidth: 340, margin: '0 auto', lineHeight: 1.6 }}>
              Enter a brand name and hit Scan to analyze visibility, or try the Demo for a sample report.
            </p>
          </div>
        )}

      </div>
    </div>
  );
}
