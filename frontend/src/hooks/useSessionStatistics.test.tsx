import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSessionStatistics } from './useSessionStatistics';
import * as evidenceApi from '../api/evidence';
import type { PipelineRunResponse } from '../types/api';

vi.mock('../api/evidence', () => ({
  getEvidenceSessions: vi.fn()
}));

const mockGetEvidenceSessions = evidenceApi.getEvidenceSessions as any;

describe('useSessionStatistics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetEvidenceSessions.mockResolvedValue({ sessions: [] });
  });

  const createMockResult = (id: string, decision: string, layer: string, latency: number): PipelineRunResponse => ({
    session_id: id,
    scenario_id: 'TEST_SCENARIO',
    overall_decision: decision,
    stopping_layer: layer,
    total_latency_ns: latency * 1_000_000,
  });

  it('initializes with zero values and fetches initial ECES count', async () => {
    mockGetEvidenceSessions.mockResolvedValueOnce({ sessions: [1, 2, 3] });
    
    const { result } = renderHook(() => useSessionStatistics(null));

    expect(result.current.attacksRun).toBe(0);
    expect(result.current.blocked).toBe(0);
    expect(result.current.frozen).toBe(0);
    expect(result.current.allowed).toBe(0);
    expect(result.current.cumulativeLatency).toBe(0);

    // Wait for the async effect
    await vi.waitFor(() => {
      expect(result.current.ecesCount).toBe(3);
    });
  });

  it('handles 404 from ECES count gracefully as 0', async () => {
    mockGetEvidenceSessions.mockRejectedValueOnce({ response: { status: 404 } });
    
    const { result } = renderHook(() => useSessionStatistics(null));

    await vi.waitFor(() => {
      expect(result.current.ecesCount).toBe(0);
    });
  });

  it('increments ALLOWED execution', () => {
    const { result, rerender } = renderHook(({ res }) => useSessionStatistics(res), {
      initialProps: { res: null as PipelineRunResponse | null }
    });

    act(() => {
      rerender({ res: createMockResult('s1', 'ALLOW', 'L7', 150) });
    });

    expect(result.current.attacksRun).toBe(1);
    expect(result.current.allowed).toBe(1);
    expect(result.current.blocked).toBe(0);
    expect(result.current.frozen).toBe(0);
    expect(result.current.cumulativeLatency).toBe(150);
  });

  it('increments BLOCKED execution (L1 or L2)', () => {
    const { result, rerender } = renderHook(({ res }) => useSessionStatistics(res), {
      initialProps: { res: null as PipelineRunResponse | null }
    });

    act(() => {
      rerender({ res: createMockResult('s1', 'BLOCK', 'L2', 25) });
    });

    expect(result.current.attacksRun).toBe(1);
    expect(result.current.blocked).toBe(1);
    expect(result.current.allowed).toBe(0);
  });

  it('increments FROZEN execution', () => {
    const { result, rerender } = renderHook(({ res }) => useSessionStatistics(res), {
      initialProps: { res: null as PipelineRunResponse | null }
    });

    act(() => {
      rerender({ res: createMockResult('s1', 'FREEZE', 'L5', 200) });
    });

    expect(result.current.attacksRun).toBe(1);
    expect(result.current.frozen).toBe(1);
  });

  it('does not incorrectly classify WARN/THROTTLE as ALLOWED or BLOCKED', () => {
    const { result, rerender } = renderHook(({ res }) => useSessionStatistics(res), {
      initialProps: { res: null as PipelineRunResponse | null }
    });

    act(() => {
      rerender({ res: createMockResult('s1', 'WARN', 'L5', 100) });
    });

    expect(result.current.attacksRun).toBe(1);
    expect(result.current.allowed).toBe(0);
    expect(result.current.blocked).toBe(0);
    expect(result.current.frozen).toBe(0);
  });

  it('ignores duplicate executions', () => {
    const { result, rerender } = renderHook(({ res }) => useSessionStatistics(res), {
      initialProps: { res: null as PipelineRunResponse | null }
    });

    const mockObj = createMockResult('s1', 'ALLOW', 'L7', 100);

    act(() => {
      rerender({ res: mockObj });
    });

    expect(result.current.attacksRun).toBe(1);

    // Re-render with same object/session
    act(() => {
      rerender({ res: mockObj });
    });

    expect(result.current.attacksRun).toBe(1);
  });

  it('accumulates latency properly', () => {
    const { result, rerender } = renderHook(({ res }) => useSessionStatistics(res), {
      initialProps: { res: null as PipelineRunResponse | null }
    });

    act(() => {
      rerender({ res: createMockResult('s1', 'ALLOW', 'L7', 100) });
    });
    expect(result.current.cumulativeLatency).toBe(100);

    act(() => {
      rerender({ res: createMockResult('s2', 'BLOCK', 'L1', 50.5) });
    });
    expect(result.current.cumulativeLatency).toBe(150.5);
  });
});
