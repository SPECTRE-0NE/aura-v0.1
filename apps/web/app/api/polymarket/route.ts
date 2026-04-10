import { NextResponse } from 'next/server';

type PolyMarket = {
  id: string;
  question: string;
  slug?: string;
  endDate?: string;
  outcomes?: string;
  outcomePrices?: string;
};

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const query = searchParams.get('query') ?? 'bitcoin 5 minute up or down';
  const limit = Number(searchParams.get('limit') ?? '6');

  const upstream = `https://gamma-api.polymarket.com/markets?limit=${Math.min(50, Math.max(1, limit))}&active=true&closed=false&query=${encodeURIComponent(query)}`;

  try {
    const response = await fetch(upstream, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
      next: { revalidate: 0 },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: `Polymarket upstream request failed (${response.status})`, markets: [] },
        { status: 502 },
      );
    }

    const markets = (await response.json()) as PolyMarket[];

    return NextResponse.json({
      markets: markets.map((m) => ({
        id: m.id,
        question: m.question,
        slug: m.slug,
        endDate: m.endDate,
        outcomes: m.outcomes,
        outcomePrices: m.outcomePrices,
      })),
    });
  } catch {
    return NextResponse.json({ error: 'Failed to connect to Polymarket API', markets: [] }, { status: 502 });
  }
}
