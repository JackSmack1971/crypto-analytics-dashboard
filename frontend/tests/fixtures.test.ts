import { describe, expect, test } from 'vitest';
import {
  generateUuid7,
  readFixture,
  simulateDbState,
  simulateRedisState,
} from '../../tests/utils';

describe('shared test fixtures', () => {
  test('reads provider fixture', () => {
    const data = readFixture('providers/etherscan_rate_limit.json');
    expect(data.message).toBe('NOTOK');
  });

  test('reads csv fixture', () => {
    const content = readFixture('csv/transactions_dst.csv') as string;
    expect(content).toContain('2021-03-14T01:30:00-05:00');
  });

  test('reads parquet fixture', () => {
    const buf = readFixture('parquet/dst_transition.parquet.b64') as Buffer;
    expect(buf.length).toBeGreaterThan(0);
  });

  test('generates uuid7', () => {
    const id = generateUuid7();
    expect(id).toHaveLength(36);
    expect(id[14]).toBe('7');
  });

  test('simulates states', () => {
    const redis = simulateRedisState({ a: '1' });
    const db = simulateDbState({ records: [] });
    expect(redis.get('a')).toBe('1');
    expect(db.records).toEqual([]);
  });
});
