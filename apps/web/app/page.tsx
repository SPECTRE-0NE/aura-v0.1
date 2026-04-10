'use client';

import { useEffect, useState } from 'react';
import { Card, Button } from '@aura/ui';

type Plan = {
  workflows: { name: string; cadence?: string; description?: string }[];
  tasks: { title: string; assignee?: string; dueAt?: string; status?: string }[];
  widgets: { title: string; query: string; unit?: string }[];
};

type SignalDirection = 'UP' | 'DOWN' | 'NEUTRAL';

type TimeframeKey = '5s' | '30s' | '1m' | '5m';

type TimeframeSignal = {
  interval: TimeframeKey;
  signal: SignalDirection;
  strength: number;
  changePct: number;
  buyPressurePct: number;
};

type Trade = {
  id: number;
  price: string;
  qty: string;
  quoteQty: string;
  time: number;
  isBuyerMaker: boolean;
  isBestMatch: boolean;
};

type Kline = [number, string, string, string, string, string, ...string[]];

type PolyMarket = {
  id: string;
  question: string;
  slug?: string;
  endDate?: string;
  outcomes?: string;
  outcomePrices?: string;
};

type MarketSnapshot = {
  price: number;
  signals: TimeframeSignal[];
  updatedAt: string;
};

function signalColor(signal: SignalDirection): string {
  if (signal === 'UP') return 'text-emerald-600';
  if (signal === 'DOWN') return 'text-rose-600';
  return 'text-amber-600';
}

function normalizeStrength(score: number): number {
  return Math.min(99, Math.round(Math.abs(score)));
}

function deriveSignal(score: number): SignalDirection {
  if (score > 15) return 'UP';
  if (score < -15) return 'DOWN';
  return 'NEUTRAL';
}

function evaluateWindow(curr: Trade[], prev: Trade[]): { score: number; changePct: number; buyPressurePct: number } {
  const currNotional = curr.reduce((sum, t) => sum + Number(t.price) * Number(t.qty), 0);
  const prevNotional = prev.reduce((sum, t) => sum + Number(t.price) * Number(t.qty), 0);
  const changePct = prevNotional > 0 ? (currNotional - prevNotional) / prevNotional : 0;

  const buyerAggressorNotional = curr.reduce((sum, t) => {
    const notional = Number(t.price) * Number(t.qty);
    return !t.isBuyerMaker ? sum + notional : sum;
  }, 0);

  const buyPressurePct = currNotional > 0 ? buyerAggressorNotional / currNotional : 0.5;
  const pressureScore = (buyPressurePct - 0.5) * 120;
  const changeScore = changePct * 900;

  return {
    score: pressureScore + changeScore,
    changePct,
    buyPressurePct,
  };
}

function parsePolyOutcomePrices(market: PolyMarket): string {
  if (!market.outcomePrices) return 'n/a';

  try {
    const outcomes = market.outcomes ? (JSON.parse(market.outcomes) as string[]) : [];
    const prices = JSON.parse(market.outcomePrices) as string[];

    if (outcomes.length === prices.length && outcomes.length > 0) {
      return outcomes.map((name, i) => `${name}: ${(Number(prices[i]) * 100).toFixed(1)}%`).join(' • ');
    }

    return prices.map((p, i) => `Outcome ${i + 1}: ${(Number(p) * 100).toFixed(1)}%`).join(' • ');
  } catch {
    return market.outcomePrices;
  }
}

export default function HomePage() {
  const [prompt, setPrompt] = useState('Set a weekly ops check‑in with finance and logistics; track SLA and stockouts.');
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loading, setLoading] = useState(false);

  const [snapshot, setSnapshot] = useState<MarketSnapshot | null>(null);
  const [indicatorLoading, setIndicatorLoading] = useState(false);
  const [indicatorError, setIndicatorError] = useState<string | null>(null);

  const [polyMarkets, setPolyMarkets] = useState<PolyMarket[]>([]);
  const [polyError, setPolyError] = useState<string | null>(null);

  async function generate() {
    setLoading(true);
    try {
      const r = await fetch('http://localhost:4000/ai/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      const data = await r.json();
      setPlan(data.plan);
    } finally {
      setLoading(false);
    }
  }

  async function loadPolyMarkets() {
    setPolyError(null);
    try {
      const response = await fetch('/api/polymarket?query=bitcoin 5 minute up or down&limit=6');
      const data = (await response.json()) as { markets?: PolyMarket[]; error?: string };
      if (!response.ok) throw new Error(data.error ?? 'Could not load Polymarket markets');
      setPolyMarkets(data.markets ?? []);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Could not load Polymarket markets';
      setPolyError(message);
    }
  }

  async function loadBtcSignals() {
    setIndicatorLoading(true);
    setIndicatorError(null);

    try {
      const [priceResponse, tradesResponse, klinesResponse] = await Promise.all([
        fetch('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT'),
        fetch('https://api.binance.com/api/v3/trades?symbol=BTCUSDT&limit=1000'),
        fetch('https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=180'),
      ]);

      if (!priceResponse.ok || !tradesResponse.ok || !klinesResponse.ok) {
        throw new Error('Unable to fetch BTC market data');
      }

      const priceData = (await priceResponse.json()) as { price: string };
      const trades = (await tradesResponse.json()) as Trade[];
      const klines = (await klinesResponse.json()) as Kline[];

      const now = Date.now();

      const windowSignals: TimeframeSignal[] = [
        { interval: '5s', ms: 5_000 },
        { interval: '30s', ms: 30_000 },
      ].map(({ interval, ms }) => {
        const current = trades.filter((t) => t.time >= now - ms);
        const previous = trades.filter((t) => t.time < now - ms && t.time >= now - ms * 2);
        const { score, changePct, buyPressurePct } = evaluateWindow(current, previous);
        return {
          interval,
          signal: deriveSignal(score),
          strength: normalizeStrength(score),
          changePct,
          buyPressurePct,
        } as TimeframeSignal;
      });

      const closes = klines.map((k) => Number(k[4]));
      const close1m = closes.at(-1) ?? 0;
      const closePrev1m = closes.at(-2) ?? close1m;
      const closePrev5m = closes.at(-6) ?? close1m;

      const oneMinuteChange = closePrev1m > 0 ? (close1m - closePrev1m) / closePrev1m : 0;
      const fiveMinuteChange = closePrev5m > 0 ? (close1m - closePrev5m) / closePrev5m : 0;

      const oneMinuteScore = oneMinuteChange * 7000;
      const fiveMinuteScore = fiveMinuteChange * 3000;

      const minuteSignals: TimeframeSignal[] = [
        {
          interval: '1m',
          signal: deriveSignal(oneMinuteScore),
          strength: normalizeStrength(oneMinuteScore),
          changePct: oneMinuteChange,
          buyPressurePct: 0.5,
        },
        {
          interval: '5m',
          signal: deriveSignal(fiveMinuteScore),
          strength: normalizeStrength(fiveMinuteScore),
          changePct: fiveMinuteChange,
          buyPressurePct: 0.5,
        },
      ];

      setSnapshot({
        price: Number(priceData.price),
        signals: [...windowSignals, ...minuteSignals],
        updatedAt: new Date().toLocaleTimeString(),
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Signal calculation failed';
      setIndicatorError(message);
    } finally {
      setIndicatorLoading(false);
    }
  }

  useEffect(() => {
    void loadBtcSignals();
    void loadPolyMarkets();

    const interval = window.setInterval(() => {
      void loadBtcSignals();
      void loadPolyMarkets();
    }, 5_000);

    return () => {
      window.clearInterval(interval);
    };
  }, []);

  return (
    <main className="mx-auto max-w-5xl p-6 space-y-6">
      <h1 className="text-3xl font-semibold">Aura</h1>
      <p className="opacity-70">Type operations in natural language. Aura scaffolds workflows, tasks, and widgets.</p>

      <Card title="Planner">
        <div className="flex gap-2">
          <input
            className="w-full rounded-xl border px-3 py-2"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe what you want to set up…"
          />
          <Button onClick={generate} disabled={loading}>{loading ? 'Thinking…' : 'Generate'}</Button>
        </div>
      </Card>

      <Card title="BTC Live Momentum Panel + Polymarket">
        <div className="space-y-3">
          <p className="text-sm opacity-80">
            Refreshes every 5 seconds and tracks BTC directional pressure for 5s, 30s, 1m and 5m windows. Not financial advice.
          </p>

          <div className="flex items-center gap-3">
            <Button onClick={loadBtcSignals} disabled={indicatorLoading}>
              {indicatorLoading ? 'Refreshing…' : 'Refresh now'}
            </Button>
            {snapshot && <span className="text-sm opacity-70">BTC: ${snapshot.price.toFixed(2)} • Updated: {snapshot.updatedAt}</span>}
          </div>

          {indicatorError && <p className="text-sm text-rose-600">{indicatorError}</p>}

          {snapshot && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {snapshot.signals.map((row) => (
                <div key={row.interval} className="rounded-xl border p-3">
                  <p className="text-xs uppercase opacity-60">{row.interval}</p>
                  <p className={`text-base font-semibold ${signalColor(row.signal)}`}>{row.signal}</p>
                  <p className="text-xs opacity-70">Strength: {row.strength}%</p>
                  <p className="text-xs opacity-70">Move: {(row.changePct * 100).toFixed(3)}%</p>
                  <p className="text-xs opacity-70">Buy pressure: {(row.buyPressurePct * 100).toFixed(1)}%</p>
                </div>
              ))}
            </div>
          )}

          <div className="rounded-xl border p-4 space-y-2">
            <p className="font-medium">Polymarket: BTC 5m up/down related markets</p>
            {polyError && <p className="text-sm text-rose-600">{polyError}</p>}
            {!polyError && polyMarkets.length === 0 && <p className="text-sm opacity-70">No markets returned for this query.</p>}
            <ul className="space-y-2 text-sm">
              {polyMarkets.map((market) => (
                <li key={market.id} className="rounded-lg border p-2">
                  <p className="font-medium">{market.question}</p>
                  <p className="opacity-70">{parsePolyOutcomePrices(market)}</p>
                  {market.endDate && <p className="opacity-60">Ends: {new Date(market.endDate).toLocaleString()}</p>}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Card>

      {plan && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card title="Workflows">
            <ul className="list-disc ml-4 space-y-1">
              {plan.workflows.map((w, i) => (
                <li key={i}><b>{w.name}</b>{w.cadence ? ` • ${w.cadence}` : ''}{w.description ? ` — ${w.description}` : ''}</li>
              ))}
            </ul>
          </Card>

          <Card title="Tasks">
            <ul className="list-disc ml-4 space-y-1">
              {plan.tasks.map((t, i) => (
                <li key={i}>{t.title}{t.assignee ? ` — @${t.assignee}` : ''}</li>
              ))}
            </ul>
          </Card>

          <Card title="Widgets">
            <ul className="list-disc ml-4 space-y-1">
              {plan.widgets.map((k, i) => (
                <li key={i}><b>{k.title}</b> • <code className="opacity-70">{k.query}</code>{k.unit ? ` (${k.unit})` : ''}</li>
              ))}
            </ul>
          </Card>
        </div>
      )}
    </main>
  );
}
