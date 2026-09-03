import { renderHook, act } from '@testing-library/react';
import { useDemoOrchestrator } from '../hooks/useDemoOrchestrator';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import type { PipelineRunResponse } from '../types/api';

describe('useDemoOrchestrator', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
  });

  it('initializes in IDLE state', () => {
    const { result } = renderHook(() => useDemoOrchestrator({
      executeScenario: vi.fn(),
      result: null,
      error: null
    }));

    expect(result.current.demoState).toBe('IDLE');
    expect(result.current.currentScenarioIndex).toBe(0);
  });

  it('transitions to RUNNING and executes first scenario on startDemo', () => {
    const executeScenario = vi.fn().mockResolvedValue(undefined);
    
    const { result } = renderHook(() => useDemoOrchestrator({
      executeScenario,
      result: null,
      error: null
    }));

    act(() => {
      result.current.startDemo();
    });

    expect(result.current.demoState).toBe('RUNNING');
    expect(executeScenario).toHaveBeenCalledWith('SAFE_FILE_READ');
  });

  it('pauses between scenarios and advances to the next', () => {
    const executeScenario = vi.fn().mockResolvedValue(undefined);
    
    const hookOptions = {
      executeScenario,
      result: null as PipelineRunResponse | null,
      error: null
    };

    const { result, rerender } = renderHook(() => useDemoOrchestrator(hookOptions));

    act(() => {
      result.current.startDemo();
    });

    // Simulate completion of first scenario (SAFE_FILE_READ)
    hookOptions.result = {
      session_id: 'sess-1',
      scenario_id: 'SAFE_FILE_READ',
      overall_decision: 'ALLOW',
      stopping_layer: 'L7',
      total_latency_ns: 1000
    } as any;
    
    rerender();

    expect(result.current.demoState).toBe('PAUSED_BETWEEN');
    expect(result.current.demoResults).toHaveLength(1);

    // Fast-forward 2 seconds
    act(() => {
      vi.advanceTimersByTime(2000);
    });

    expect(result.current.demoState).toBe('RUNNING');
    expect(result.current.currentScenarioIndex).toBe(1);
    expect(executeScenario).toHaveBeenCalledWith('L1_GRAMMAR');
  });
  
  it('goes to COMPLETE state after the final scenario', () => {
    const executeScenario = vi.fn().mockResolvedValue(undefined);
    
    const hookOptions = {
      executeScenario,
      result: null as PipelineRunResponse | null,
      error: null
    };

    const { result, rerender } = renderHook(() => useDemoOrchestrator(hookOptions));

    // Force state to the last scenario
    act(() => {
      result.current.startDemo();
    });
    
    // complete 1
    hookOptions.result = { session_id: 'sess-1', scenario_id: 'SAFE_FILE_READ' } as any;
    rerender();
    act(() => vi.advanceTimersByTime(2000));
    
    // complete 2
    hookOptions.result = { session_id: 'sess-2', scenario_id: 'L1_GRAMMAR' } as any;
    rerender();
    act(() => vi.advanceTimersByTime(2000));
    
    // complete 3
    hookOptions.result = { session_id: 'sess-3', scenario_id: 'L2_BACKSLASH' } as any;
    rerender();
    act(() => vi.advanceTimersByTime(2000));
    
    // complete 4
    hookOptions.result = { session_id: 'sess-4', scenario_id: 'L5_TEMPORAL' } as any;
    rerender();
    
    // No pause needed after the last one
    expect(result.current.demoState).toBe('COMPLETE');
    expect(result.current.demoResults).toHaveLength(4);
  });
});
