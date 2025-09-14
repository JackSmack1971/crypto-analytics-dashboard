import { readFileSync } from 'fs';
import { join } from 'path';
import { randomBytes } from 'crypto';

const FIXTURE_ROOT = join(__dirname, '..', 'fixtures');

export function readFixture(relativePath: string): any {
  const fullPath = join(FIXTURE_ROOT, relativePath);
  if (fullPath.endsWith('.b64')) {
    const encoded = readFileSync(fullPath, 'utf-8');
    return Buffer.from(encoded, 'base64');
  }
  const isBinary = fullPath.endsWith('.parquet');
  const data = readFileSync(fullPath, isBinary ? undefined : 'utf-8');
  if (!isBinary && fullPath.endsWith('.json')) {
    return JSON.parse(data as string);
  }
  return data;
}

export function generateUuid7(): string {
  const unixMs = BigInt(Date.now());
  const tsHex = unixMs.toString(16).padStart(15, "0");
  const timeHigh = tsHex.slice(0, 8);
  const timeMid = tsHex.slice(8, 12);
  const timeLow = tsHex.slice(12, 15);
  const randHex = randomBytes(10).toString("hex");
  const variant = "8";
  return `${timeHigh}-${timeMid}-7${timeLow}-${variant}${randHex.slice(0, 3)}-${randHex.slice(3, 15)}`;
}

export function simulateRedisState(initial: Record<string, string> = {}) {
  return new Map(Object.entries(initial));
}

export function simulateDbState<T extends Record<string, unknown>>(
  initial: T,
): T {
  return { ...initial };
}
