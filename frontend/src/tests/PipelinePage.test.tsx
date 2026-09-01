import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PipelinePage } from '../pages/PipelinePage';
import { ExecutionMode } from '../types/api';
import * as pipelineApi from '../api/pipeline';

vi.mock('../api/pipeline', () => ({
  runPipelineScenario: vi.fn(),
}));

describe('PipelinePage Tests', () => {
  it('renders Pipeline Idle state initially', () => {
    render(<PipelinePage />);
    expect(screen.getByText('Pipeline Idle')).toBeInTheDocument();
    expect(screen.getAllByText('AcademIQ Security Pipeline').length).toBeGreaterThan(0);
  });

  it('renders scenarios from the selector', () => {
    render(<PipelinePage />);
    expect(screen.getByText('Select Execution Scenario')).toBeInTheDocument();
    expect(screen.getByText('Safe file read')).toBeInTheDocument();
    expect(screen.getByText('Forbidden tool invocation')).toBeInTheDocument();
  });

  it('handles scenario execution simulation', async () => {
    const mockResponse = {
      session_id: 'test-session',
      scenario_id: 'SAFE_READ',
      overall_decision: 'ALLOW',
      stopping_layer: 'L5',
      total_latency_ns: 1000000,
      L1: { decision: 'ALLOW', latency: 1000, metadata: { tool_name: 'read_file' } },
      L2: { decision: 'UNAVAILABLE', normalized_command: null, detection_reason: null, latency: null },
      L3: { status: 'MOCKED', event_count: 5, anomalies: 0, execution_mode: ExecutionMode.SIMULATED },
      L4: { isolation_forest_score: 0.1, siamese_score: 0.1, ensemble_score: 0.1, drift_state: 'NOMINAL', execution_mode: ExecutionMode.SIMULATED },
      L5: { bayesian_probability: 0.05, governance_state: 'ALLOW', highest_risk_path: 'N/A', cross_session_status: 'CLEAN' },
      L6: { evidence_chain_reference: 'chain-1', chain_status: 'APPENDED', storage_backend: 'SQLite' },
      L7: { isolation_status: 'UNAVAILABLE', scope_information: null }
    };

    vi.mocked(pipelineApi.runPipelineScenario).mockResolvedValue(mockResponse as any);

    render(<PipelinePage />);
    
    // Click Safe file read
    fireEvent.click(screen.getByText('Safe file read'));
    
    // Expect the state to change from idle to pipeline flow
    expect(screen.queryByText('Pipeline Idle')).not.toBeInTheDocument();
    expect(screen.getByText('Live Pipeline Execution')).toBeInTheDocument();

    // The execution hook steps through with 500ms delays, so we wait for the final results to settle.
    // L1 should be ALLOW after a bit
    await waitFor(() => {
      expect(screen.getAllByText('ALLOW').length).toBeGreaterThan(0);
    }, { timeout: 4000 });
  });
});
