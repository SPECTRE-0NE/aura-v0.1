import 'dotenv/config';
import express from 'express';
import type { Request, Response } from 'express';
import { planOpsFromPrompt } from '@aura/ai';
import { z } from 'zod';
import crypto from 'crypto';

const app = express();
app.use(express.json({ limit: '1mb' }));

const PORT = process.env.PORT || 4000;

// Health
app.get('/health', (_req, res) => res.json({ ok: true }));

// AI planner (stub → replace with OpenAI call as needed)
const PlanBody = z.object({ prompt: z.string().min(3) });
app.post('/ai/plan', async (req: Request, res: Response) => {
  const parsed = PlanBody.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  const plan = await planOpsFromPrompt(parsed.data.prompt);
  res.json({ plan });
});

// Slack command (signature verification minimal)
app.post('/slack/command', express.raw({ type: '*/*' }), (req: Request, res: Response) => {
  const signingSecret = process.env.SLACK_SIGNING_SECRET;
  if (!signingSecret) return res.status(500).send('Slack not configured');

  const ts = req.headers['x-slack-request-timestamp'] as string;
  const sig = req.headers['x-slack-signature'] as string;
  const fiveMinutesAgo = Math.floor(Date.now() / 1000) - 60 * 5;
  if (!ts || parseInt(ts) < fiveMinutesAgo) return res.status(400).send('Stale');

  const body = (req as any).body as Buffer;
  const hmac = crypto.createHmac('sha256', signingSecret);
  const basestring = `v0:${ts}:${body.toString()}`;
  const mySig = 'v0=' + hmac.update(basestring).digest('hex');
  if (sig !== mySig) return res.status(401).send('Bad signature');

  const text = new URLSearchParams(body.toString()).get('text') || '';
  res.json({
    response_type: 'ephemeral',
    text: `Aura plan (draft): ${text}`
  });
});

app.listen(PORT, () => console.log(`API on :${PORT}`));
