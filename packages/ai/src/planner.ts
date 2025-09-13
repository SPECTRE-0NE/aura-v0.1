import { z } from 'zod';

export const PlanSchema = z.object({
  workflows: z.array(z.object({
    name: z.string(),
    cadence: z.string().optional(),
    description: z.string().optional(),
  })).default([]),
  tasks: z.array(z.object({
    title: z.string(),
    assignee: z.string().optional(),
    dueAt: z.string().optional(),
    status: z.string().optional(),
  })).default([]),
  widgets: z.array(z.object({
    title: z.string(),
    query: z.string(),
    unit: z.string().optional(),
  })).default([]),
});

export type Plan = z.infer<typeof PlanSchema>;

export async function planOpsFromPrompt(prompt: string): Promise<Plan> {
  // Stub: deterministic rules for demo; replace with OpenAI call in apps/api
  const lower = prompt.toLowerCase();
  const workflows = [{
    name: 'Weekly Ops Check‑In',
    cadence: 'weekly',
    description: '15‑min cross‑functional standup for finance + logistics'
  }];
  const tasks = [
    { title: 'Create Slack channel #ops-weekly', assignee: 'ops' },
    { title: 'Set recurring calendar event (Fri 09:00)', assignee: 'ops' },
    { title: 'Prepare SLA + stockout snapshot', assignee: 'finance' },
  ];
  const widgets = [
    { title: 'SLA % (last 7d)', query: 'sheets:KPI!sla_last_7d', unit: '%' },
    { title: 'Stockouts (QTD)', query: 'clickup:list:stockouts_qtd' },
  ];

  if (lower.includes('month') or lower.includes('monthly')) {
    workflows[0].cadence = 'monthly';
  }

  return { workflows, tasks, widgets };
}
