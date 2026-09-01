import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ExperimentsPage } from '../pages/ExperimentsPage';
import { ExecutionMode } from '../types/api';
import * as experimentsApi from '../api/experiments';

vi.mock('../api/experiments', () => ({
  getExperiments: vi.fn(),
  getExperimentDetail: vi.fn()
}));

describe('ExperimentsPage Tests', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  const mockExperiments = [
    {
      experiment_id: 'EXP-1',
      title: 'Direct Prompt Injection Prevention',
      category: 'Core Security Experiments',
      description: 'Tests ASR against direct prompt injections.',
      execution_mode: ExecutionMode.REAL_RUNTIME,
      model_name: 'TinyLlama',
      primary_metric: { name: 'Protected ASR', value: 0, suffix: '%' }
    },
    {
      experiment_id: 'EXP-5',
      title: 'Behavioral Divergence Zero-Day',
      category: 'Core Security Experiments',
      description: 'Tests anomaly detection.',
      execution_mode: ExecutionMode.SYNTHETIC,
      model_name: null,
      primary_metric: { name: 'F1 Score', value: 0.99, suffix: '' }
    }
  ];

  it('renders experiment catalog and aggregate stats', async () => {
    vi.mocked(experimentsApi.getExperiments).mockResolvedValue({ experiments: mockExperiments });
    
    render(<ExperimentsPage />);
    
    expect(screen.getByText('Research Benchmark Results')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('EXP-1')).toBeInTheDocument();
      expect(screen.getByText('EXP-5')).toBeInTheDocument();
    });

    // Check aggregates
    expect(screen.getByText('2')).toBeInTheDocument(); // Total experiments
    expect(screen.getAllByText('1')[0]).toBeInTheDocument(); // Real LLM Evals (EXP-1)
  });

  it('filters experiments by category', async () => {
    vi.mocked(experimentsApi.getExperiments).mockResolvedValue({ experiments: mockExperiments });
    render(<ExperimentsPage />);
    
    await waitFor(() => screen.getByText('EXP-1'));
    
    // Simulate typing in search
    const searchInput = screen.getByPlaceholderText('Search experiments, models, or IDs...');
    fireEvent.change(searchInput, { target: { value: 'Divergence' } });

    expect(screen.queryByText('EXP-1')).not.toBeInTheDocument();
    expect(screen.getByText('EXP-5')).toBeInTheDocument();
  });

  it('fetches and displays experiment detail view', async () => {
    vi.mocked(experimentsApi.getExperiments).mockResolvedValue({ experiments: mockExperiments });
    vi.mocked(experimentsApi.getExperimentDetail).mockResolvedValue({
      ...mockExperiments[0],
      sample_size: 140,
      attack_success_rate: 0.0,
      baseline_metrics: { ASR: 34.16 },
      known_limitations: ["Small model capacity."],
      raw_artifact: { raw: "data" }
    });

    render(<ExperimentsPage />);
    
    await waitFor(() => screen.getByText('Direct Prompt Injection Prevention'));
    fireEvent.click(screen.getByText('Direct Prompt Injection Prevention'));

    const bannerText = await screen.findByText(/REAL LLM INFERENCE/i);
    expect(bannerText).toBeInTheDocument();
    
    expect(screen.getByText(/140/)).toBeInTheDocument(); // sample size
    expect(screen.getByText(/34\.16%/)).toBeInTheDocument(); // baseline ASR
    expect(screen.getAllByText(/0%/)[0]).toBeInTheDocument(); // protected ASR
    expect(screen.getByText('Small model capacity.')).toBeInTheDocument();
  });

  it('handles experiment comparison up to limit', async () => {
    vi.mocked(experimentsApi.getExperiments).mockResolvedValue({ experiments: mockExperiments });
    vi.mocked(experimentsApi.getExperimentDetail).mockResolvedValue({
      ...mockExperiments[0]
    });

    render(<ExperimentsPage />);
    
    await waitFor(() => screen.getByText('EXP-1'));
    
    // Find all 'Compare' buttons
    const compareButtons = screen.getAllByText('Compare');
    fireEvent.click(compareButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Comparing 1 Experiment')).toBeInTheDocument();
    });
    
    // Clear comparison
    fireEvent.click(screen.getByText('Clear Comparison'));
    expect(screen.queryByText('Comparing 1 Experiment')).not.toBeInTheDocument();
  });
});
