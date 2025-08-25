'use server';

import { NextRequest, NextResponse } from 'next/server';

type NominatimItem = {
  display_name: string;
  lat: string;
  lon: string;
  class?: string;
  type?: string;
  address?: { country?: string };
};

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const q = (searchParams.get('q') || '').trim();
  if (!q) {
    return NextResponse.json({ error: 'Missing q' }, { status: 400 });
  }

  const queries = [q, `${q} port`, `${q} harbour`, `${q} harbor`];

  const headers: HeadersInit = {
    'User-Agent': 'MaritimeAssistant/1.0 (contact: local-app)'
  };

  const results: Array<{ name: string; country: string; lat: number; lng: number; type: string; details: Record<string, any> }> = [];

  for (const term of queries) {
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(term)}&limit=20&dedupe=1&extratags=1&addressdetails=1`;
    try {
      const res = await fetch(url, { headers, next: { revalidate: 3600 } });
      if (!res.ok) continue;
      const data = (await res.json()) as NominatimItem[];
      for (const item of data) {
        // Heuristic: prefer items that look like ports/harbours/marinas
        const label = `${item.class || ''}/${item.type || ''}`.toLowerCase();
        const name = item.display_name?.split(',')[0]?.trim() || 'Unknown Port';
        const country = item.address?.country || '';
        const lat = parseFloat(item.lat);
        const lng = parseFloat(item.lon);
        const isPortLike = /port|harbour|harbor|marina|seaport|dock|quay|terminal/.test(label + ' ' + name.toLowerCase());
        if (!Number.isFinite(lat) || !Number.isFinite(lng) || !isPortLike) continue;

        results.push({
          name,
          country,
          lat,
          lng,
          type: 'port',
          details: { source: 'nominatim', label, display_name: item.display_name }
        });
      }
    } catch {
      // ignore and try next
    }
  }

  // Dedupe by name+country and by coordinate rounding
  const seen = new Set<string>();
  const deduped = results.filter((r) => {
    const key = `${r.name.toLowerCase()}|${r.country.toLowerCase()}|${Math.round(r.lat * 1000)}|${Math.round(r.lng * 1000)}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  return NextResponse.json(deduped.slice(0, 50));
}
