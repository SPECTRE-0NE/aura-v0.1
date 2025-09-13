'use client';

import { useState } from 'react';
import { Card, Button } from '@aura/ui';

type Plan = {
  workflows: { name: string; cadence?: string; description?: string }[];
  tasks: { title: string; assignee?: string; dueAt?: string; status?: string }[];
  widgets: { title: string; query: string; unit?: string }[];
};

export default function HomePage() {
  const [prompt, setPrompt] = useState('Set a weekly ops check‑in with finance and logistics; track SLA and stockouts.');
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loading, setLoading] = useState(false);

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
