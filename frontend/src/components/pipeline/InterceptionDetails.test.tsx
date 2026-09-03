import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { InterceptionDetails } from './InterceptionDetails';
import type { PipelineRunResponse } from '../../types/api';

const mockResult: PipelineRunResponse = {
  session_id: 'test-session-123',
  scenario_id: 'L2_BACKSLASH',
  overall_decision: 'BLOCK',
  stopping_layer: 'L2',
  total_latency_ns: 1500000, // 1.5ms
  L1: {
    decision: 'ALLOW',
    latency: 500000,
    metadata: {
      tool_name: 'execute_shell'
    }
  },
  L2: {
    decision: 'BLOCK',
    latency: 1000000,
    normalized_command: 'cat /etc/passwd',
    detection_reason: 'Restricted file access'
  },
  L3: undefined,
  L4: undefined,
  L5: undefined,
  L6: undefined,
  L7: undefined
};

describe('InterceptionDetails', () => {
  it('renders nothing if scenario is unknown', () => {
    const unknownResult = { ...mockResult, scenario_id: 'UNKNOWN' };
    const { container } = render(<InterceptionDetails result={unknownResult} selectedLayerId="L2" />);
    expect(container.firstChild).toBeNull();
  });

  it('renders blocking state correctly for L2', () => {
    render(<InterceptionDetails result={mockResult} selectedLayerId="L2" />);
    
    // Header
    expect(screen.getByText('🔴 BLOCKED AT L2')).toBeInTheDocument();
    
    // Details
    expect(screen.getByText('cat /etc/passwd')).toBeInTheDocument();
    expect(screen.getByText('Restricted file access')).toBeInTheDocument();
    
    // Expected match text
    expect(screen.getByText('✓ Expected interception confirmed')).toBeInTheDocument();
    
    // Forensic summary
    expect(screen.getByText('test-session-123')).toBeInTheDocument();
    expect(screen.getByText('1.50 ms')).toBeInTheDocument();
  });

  it('renders allowed state correctly for L1', () => {
    render(<InterceptionDetails result={mockResult} selectedLayerId="L1" />);
    
    // Header
    expect(screen.getByText('🟢 PASSED L1')).toBeInTheDocument();
    
    // Details
    expect(screen.getAllByText('Grammar-Constrained Decoding').length).toBeGreaterThan(0);
    expect(screen.getByText('execute_shell')).toBeInTheDocument();
    
    // Shouldn't show expected match text on a non-stopping layer
    expect(screen.queryByText('✓ Expected interception confirmed')).not.toBeInTheDocument();
  });

  it('renders unavailable state correctly for L3', () => {
    render(<InterceptionDetails result={mockResult} selectedLayerId="L3" />);
    
    // Header
    expect(screen.getByText('⚪ SKIPPED / UNAVAILABLE L3')).toBeInTheDocument();
  });
});
