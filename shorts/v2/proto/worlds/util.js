// Shared helpers for the v2 worlds. Everything is deterministic: same inputs -> same pixels.
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const seg = (t, a, b) => clamp((t - a) / (b - a));
export const eInOut = x => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
export const eOutExpo = x => { x = clamp(x); return x >= 1 ? 1 : 1 - Math.pow(2, -10 * x); };
export const eOutCubic = x => 1 - Math.pow(1 - clamp(x), 3);
export const eOutBack = (x, c = 1.7) => { x = clamp(x); const c3 = c + 1; return 1 + c3 * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
export function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
export function vnoise(seed) { const r = rng(seed), P = Array.from({ length: 256 }, () => r()); return x => { const i = Math.floor(x), f = x - i, a = P[i & 255], b = P[(i + 1) & 255], u = f * f * (3 - 2 * f); return a + (b - a) * u; }; }
