import { useState, useEffect, useCallback, useRef } from 'react';
import type { PipelineRunResponse } from '../types/api';

export type DemoState = 'IDLE' | 'RUNNING' | 'PAUSED_BETWEEN' | 'COMPLETE' | 'CANCELLED' | 'ERROR';

interface DemoOrchestratorOptions {
  executeScenario: (scenarioId: string) => Promise<void>;
  result: PipelineRunResponse | null;
  error: string | null;
}

const DEMO_SEQUENCE = ['SAFE_FILE_READ', 'L1_GRAMMAR', 'L2_BACKSLASH', 'L5_TEMPORAL'];
const PAUSE_DURATION_MS = 2000;

export const useDemoOrchestrator = ({ executeScenario, result, error }: DemoOrchestratorOptions) => {
  const [demoState, setDemoState] = useState<DemoState>('IDLE');
  const [currentScenarioIndex, setCurrentScenarioIndex] = useState<number>(0);
  const [demoResults, setDemoResults] = useState<PipelineRunResponse[]>([]);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const startDemo = useCallback(() => {
    if (demoState === 'RUNNING' || demoState === 'PAUSED_BETWEEN') return;
    setDemoState('RUNNING');
    setCurrentScenarioIndex(0);
    setDemoResults([]);
    executeScenario(DEMO_SEQUENCE[0]);
  }, [demoState, executeScenario]);

  const stopDemo = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setDemoState('CANCELLED');
  }, []);

  const resetDemo = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setDemoState('IDLE');
    setCurrentScenarioIndex(0);
    setDemoResults([]);
  }, []);

  // Handle pipeline errors during demo
  useEffect(() => {
    if ((demoState === 'RUNNING' || demoState === 'PAUSED_BETWEEN') && error) {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      setDemoState('ERROR');
    }
  }, [error, demoState]);

  // Handle scenario completion and transition
  useEffect(() => {
    if (demoState !== 'RUNNING' || !result) return;
    
    // Check if the current result matches the scenario we are orchestrating
    const currentScenarioId = DEMO_SEQUENCE[currentScenarioIndex];
    if (result.scenario_id !== currentScenarioId) return;

    // A scenario just finished completely (including UI animations because result is populated)
    setDemoResults(prev => {
      // Prevent duplicate results if useEffect fires multiple times with same result reference
      if (prev.find(r => r.session_id === result.session_id)) return prev;
      return [...prev, result];
    });

    const isLastScenario = currentScenarioIndex === DEMO_SEQUENCE.length - 1;

    if (isLastScenario) {
      setDemoState('COMPLETE');
    } else {
      setDemoState('PAUSED_BETWEEN');
      timeoutRef.current = setTimeout(() => {
        setDemoState('RUNNING');
        setCurrentScenarioIndex(prev => {
          const nextIdx = prev + 1;
          executeScenario(DEMO_SEQUENCE[nextIdx]);
          return nextIdx;
        });
      }, PAUSE_DURATION_MS);
    }
    // Do NOT clear timeout on effect cleanup, as demoState change causes a re-render and cleanup execution
  }, [result, demoState, currentScenarioIndex, executeScenario]);

  // Global cleanup
  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  return {
    demoState,
    currentScenarioIndex,
    demoResults,
    currentScenarioId: DEMO_SEQUENCE[currentScenarioIndex],
    sequenceCount: DEMO_SEQUENCE.length,
    startDemo,
    stopDemo,
    resetDemo
  };
};
