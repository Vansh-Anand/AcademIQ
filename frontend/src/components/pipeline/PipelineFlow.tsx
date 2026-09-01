import React from 'react';
import { PipelineLayerCard } from './PipelineLayerCard';
import { usePipelineExecution } from '../../hooks/usePipelineExecution';
import { ShieldAlert, ArrowDown } from 'lucide-react';
import { ExecutionModeBadge } from '../common/ExecutionModeBadge';

interface PipelineFlowProps {
  execution: ReturnType<typeof usePipelineExecution>;
}

export const PipelineFlow: React.FC<PipelineFlowProps> = ({ execution }) => {
  const { isRunning, layerStates, result } = execution;
  
  const showInterceptBanner = result && result.overall_decision === 'BLOCK';

  const formatLatency = (ns?: number) => ns ? `${(ns / 1_000_000).toFixed(2)} ms` : 'N/A';

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Live Pipeline Execution</h3>
        {isRunning && <span className="text-sm font-medium text-blue-600 animate-pulse">Running simulation...</span>}
      </div>

      <div className="relative space-y-2">
        <PipelineLayerCard
          id="L1"
          name="Grammar-Constrained Decoding"
          state={layerStates.L1}
          executionMode={result?.L1?.latency ? result.L3?.execution_mode : undefined} // Infer mode if executed
          details={result?.L1?.metadata ? 
            <div className="space-y-1">
              <div><span className="font-semibold text-gray-700">Tool Evaluated:</span> {result.L1.metadata.tool_name}</div>
              <div><span className="font-semibold text-gray-700">Latency:</span> {formatLatency(result.L1.latency)}</div>
            </div> : null
          }
        />

        <div className="flex justify-center py-1">
          <ArrowDown className="w-5 h-5 text-gray-300" />
        </div>

        <PipelineLayerCard
          id="L2"
          name="Semantic Deobfuscation Network"
          state={layerStates.L2}
          executionMode={result?.L2?.latency ? result.L3?.execution_mode : undefined}
          details={result?.L2 ? 
            <div className="space-y-1">
              {result.L2.normalized_command && <div><span className="font-semibold text-gray-700">Canonical:</span> <code className="bg-gray-100 px-1 rounded">{result.L2.normalized_command}</code></div>}
              {result.L2.detection_reason && <div><span className="font-semibold text-gray-700">Reason:</span> {result.L2.detection_reason}</div>}
              {result.L2.latency && <div><span className="font-semibold text-gray-700">Latency:</span> {formatLatency(result.L2.latency)}</div>}
            </div> : null
          }
        />

        <div className="flex justify-center py-1">
          <ArrowDown className="w-5 h-5 text-gray-300" />
        </div>

        <PipelineLayerCard
          id="L3"
          name="Runtime Telemetry Correlation"
          state={layerStates.L3}
          executionMode={result?.L3?.execution_mode}
          details={result?.L3?.event_count ? 
            <div className="space-y-1">
              <div><span className="font-semibold text-gray-700">Events Captured:</span> {result.L3.event_count}</div>
              <div><span className="font-semibold text-gray-700">Anomalies Detected:</span> {result.L3.anomalies}</div>
            </div> : null
          }
        />

        <div className="flex justify-center py-1">
          <ArrowDown className="w-5 h-5 text-gray-300" />
        </div>

        <PipelineLayerCard
          id="L4"
          name="Behavioral Divergence"
          state={layerStates.L4}
          executionMode={result?.L4?.execution_mode}
          details={result?.L4?.ensemble_score ? 
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div><span className="font-semibold text-gray-700">IsoForest:</span> {result.L4.isolation_forest_score?.toFixed(3)}</div>
              <div><span className="font-semibold text-gray-700">Siamese:</span> {result.L4.siamese_score?.toFixed(3)}</div>
              <div className="col-span-2"><span className="font-semibold text-gray-700">Ensemble:</span> {result.L4.ensemble_score?.toFixed(3)} ({result.L4.drift_state})</div>
            </div> : null
          }
        />

        <div className="flex justify-center py-1">
          <ArrowDown className="w-5 h-5 text-gray-300" />
        </div>

        <PipelineLayerCard
          id="L5"
          name="RiskChain Governance"
          state={layerStates.L5}
          executionMode={result?.L4?.execution_mode}
          details={result?.L5?.bayesian_probability ? 
            <div className="space-y-1">
              <div><span className="font-semibold text-gray-700">Bayesian Risk:</span> {(result.L5.bayesian_probability * 100).toFixed(1)}%</div>
              <div><span className="font-semibold text-gray-700">Cross-Session:</span> {result.L5.cross_session_status}</div>
            </div> : null
          }
        />

        <div className="flex justify-center py-1">
          <ArrowDown className="w-5 h-5 text-gray-300" />
        </div>

        <PipelineLayerCard
          id="L6"
          name="ECES Evidence"
          state={layerStates.L6}
          executionMode={result?.L3?.execution_mode}
          details={result?.L6?.evidence_chain_reference ? 
            <div className="space-y-1">
              <div><span className="font-semibold text-gray-700">Chain Ref:</span> <span className="font-mono text-xs">{result.L6.evidence_chain_reference}</span></div>
              <div><span className="font-semibold text-gray-700">Backend:</span> {result.L6.storage_backend} ({result.L6.chain_status})</div>
            </div> : null
          }
        />

        <div className="flex justify-center py-1">
          <ArrowDown className="w-5 h-5 text-gray-300" />
        </div>

        <PipelineLayerCard
          id="L7"
          name="Agent Isolation"
          state={layerStates.L7}
          executionMode={result?.L3?.execution_mode}
          details={result?.L7?.isolation_status ? 
            <div className="space-y-1">
              <div><span className="font-semibold text-gray-700">Status:</span> {result.L7.isolation_status}</div>
            </div> : null
          }
        />

        {showInterceptBanner && !isRunning && (
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none z-10 bg-white/60 backdrop-blur-[2px] rounded-lg">
            <div className="bg-red-900 border-4 border-red-500 shadow-2xl rounded-xl p-8 max-w-lg w-full transform -translate-y-12 pointer-events-auto text-center">
              <div className="flex justify-center mb-4">
                <div className="bg-red-500 p-3 rounded-full animate-pulse">
                  <ShieldAlert className="w-12 h-12 text-white" />
                </div>
              </div>
              <h2 className="text-3xl font-black text-white tracking-widest mb-2 uppercase">Attack Intercepted</h2>
              <div className="bg-red-950 p-4 rounded-lg border border-red-800 text-left space-y-2 mt-6">
                <div className="flex justify-between items-center border-b border-red-800 pb-2">
                  <span className="text-red-300 text-sm uppercase tracking-wider font-semibold">Stopping Layer</span>
                  <span className="text-white font-bold text-lg">{result.stopping_layer}</span>
                </div>
                <div className="flex justify-between items-center border-b border-red-800 pb-2 pt-2">
                  <span className="text-red-300 text-sm uppercase tracking-wider font-semibold">Total Latency</span>
                  <span className="text-white font-mono">{formatLatency(result.total_latency_ns)}</span>
                </div>
                <div className="flex justify-between items-center pt-2">
                  <span className="text-red-300 text-sm uppercase tracking-wider font-semibold">Execution Mode</span>
                  <ExecutionModeBadge mode={result.L3?.execution_mode || result.L4?.execution_mode || 'UNAVAILABLE'} className="bg-red-800 text-white border-red-700" />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
