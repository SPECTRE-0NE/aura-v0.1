export const isNonEmpty = (s?: string) => !!s && s.trim().length > 0;

export type KPI = { title: string; value: number | string; unit?: string };
