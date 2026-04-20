/**
 * Per-persona color via deterministic name hashing. Every persona
 * gets its own distinct hue across the entire app — graph nodes,
 * avatars, action cards, sheets — so the same persona reads as the
 * same person wherever they appear.
 *
 * Archetype color (lib/archetypes.ts) is kept for badges/chips that
 * label *what kind of agent* this is — that's grouping info, not
 * identity.
 */

const cache = new Map<string, string>();

export function personaColor(name: string | undefined | null): string {
  const key = (name || "").trim().toLowerCase();
  if (!key) return "hsl(220, 12%, 60%)"; // neutral slate fallback
  const cached = cache.get(key);
  if (cached) return cached;

  let h = 5381;
  for (let i = 0; i < key.length; i++) {
    h = ((h << 5) + h + key.charCodeAt(i)) | 0;
  }
  // Golden-angle (137.508°) hue distribution → maximally distinct
  const hue = ((Math.abs(h) * 137.508) % 360 + 360) % 360;
  // Deterministic but varied saturation/lightness too — avoids the
  // "all colors look the same brightness" feeling.
  const sat = 55 + ((Math.abs(h >> 8)) % 20); // 55-74
  const light = 58 + ((Math.abs(h >> 16)) % 8); // 58-65
  const c = `hsl(${hue.toFixed(0)}, ${sat}%, ${light}%)`;
  cache.set(key, c);
  return c;
}
