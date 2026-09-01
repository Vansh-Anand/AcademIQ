import { useState, useCallback } from 'react';
import { runPipelineScenario } from '../api/pipeline';
import type { PipelineRunResponse } from '../types/api';
import type { LayerState } from '../types/pipeline';

interface PipelineDisplayState {
  L1: LayerState;
  L2: LayerState;
  L3: LayerState;
  L4: LayerState;
  L5: LayerState;
  L6: LayerState;
  L7: LayerState;
}

const INITIAL_LAYER_STATE: PipelineDisplayState = {
  L1: 'PENDING',
  L2: 'PENDING',
  L3: 'PENDING',
  L4: 'PENDING',
  L5: 'PENDING',
  L6: 'PENDING',
  L7: 'PENDING',
};

export const usePipelineExecution = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PipelineRunResponse | null>(null);
  const [layerStates, setLayerStates] = useState<PipelineDisplayState>(INITIAL_LAYER_STATE);
  const [currentLayer, setCurrentLayer] = useState<string | null>(null);

  const executeScenario = useCallback(async (scenarioId: string) => {
    setIsRunning(true);
    setError(null);
    setResult(null);
    setLayerStates({ ...INITIAL_LAYER_STATE });
    setCurrentLayer('L1');

    try {
      // 1. Fetch synchronous response from backend
      const response = await runPipelineScenario(scenarioId);
      
      // 2. Animate the visualization based on the response
      const layers: Array<keyof PipelineRunResponse> = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7'];
      let stopped = false;

      for (const layer of layers) {
        if (stopped) break;
        
        // Ensure layer is one of our PipelineDisplayState keys
        if (!Object.keys(INITIAL_LAYER_STATE).includes(layer)) continue;

        const layerKey = layer as keyof PipelineDisplayState;
        const outcome: any = response[layerKey];

        setCurrentLayer(layerKey);
        setLayerStates((prev) => ({ ...prev, [layerKey]: 'PROCESSING' }));

        // Simulate processing time for visualization
        await new Promise((resolve) => setTimeout(resolve, 500));

        let finalState: LayerState = 'UNAVAILABLE';
        
        if (layerKey === 'L1' || layerKey === 'L2') {
          if (!outcome || !outcome.decision) finalState = 'UNAVAILABLE';
          else finalState = outcome.decision;
        } else if (layerKey === 'L3' || layerKey === 'L4') {
            finalState = outcome ? 'ALLOW' : 'UNAVAILABLE';
        } else if (layerKey === 'L5') {
            finalState = outcome?.governance_state || 'UNAVAILABLE';
        } else if (layerKey === 'L6') {
            finalState = outcome?.chain_status === 'APPENDED' ? 'ALLOW' : 'UNAVAILABLE';
        } else if (layerKey === 'L7') {
            finalState = outcome?.isolation_status === 'UNAVAILABLE' ? 'UNAVAILABLE' : 'ALLOW';
        }

        setLayerStates((prev) => ({ ...prev, [layerKey]: finalState }));

        if (finalState === 'BLOCK' || finalState === 'FREEZE') {
          stopped = true;
        }
      }
      
      setCurrentLayer(null);
      setResult(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred during pipeline execution.');
      setLayerStates({ ...INITIAL_LAYER_STATE });
      setCurrentLayer(null);
    } finally {
      setIsRunning(false);
    }
  }, []);

  const reset = useCallback(() => {
    setIsRunning(false);
    setError(null);
    setResult(null);
    setLayerStates({ ...INITIAL_LAYER_STATE });
    setCurrentLayer(null);
  }, []);

  return {
    isRunning,
    error,
    result,
    layerStates,
    currentLayer,
    executeScenario,
    reset
  };
};
