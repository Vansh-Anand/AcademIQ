import React from 'react';
import type { ExperimentNormalized } from '../../types/api';
import { ExecutionModeBadge } from '../common/ExecutionModeBadge';
import { BaselineComparison } from './BaselineComparison';
import { RawArtifactViewer } from './RawArtifactViewer';
import { ShieldAlert, Info, Database, AlertTriangle } from 'lucide-react';

interface ExperimentDetailProps {
  experiment: ExperimentNormalized;
}

export const ExperimentDetail: React.FC<ExperimentDetailProps> = ({ experiment }) => {
  const isRealModel = experiment.execution_mode === 'REAL_RUNTIME';
  const isSynthetic = experiment.execution_mode === 'SYNTHETIC';
  const isSimulated = experiment.execution_mode === 'SIMULATED';

  // Helper to extract baseline ASR safely across heterogeneous schemas
  const getBaselineASR = () => {
    if (experiment.baseline_metrics) {
      if ('ASR' in experiment.baseline_metrics) return experiment.baseline_metrics.ASR as number;
      if ('asr' in experiment.baseline_metrics) return experiment.baseline_metrics.asr as number;
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gray-50 border-b border-gray-200 p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded">
                {experiment.experiment_id}
              </span>
              <ExecutionModeBadge mode={experiment.execution_mode} />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">{experiment.title}</h2>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500 font-medium">{experiment.category}</div>
          </div>
        </div>
        
        <p className="text-gray-600 max-w-3xl">{experiment.description}</p>
        
        <div className="mt-6 flex flex-wrap gap-4">
          {experiment.model_name && (
            <div className="flex items-center bg-white border border-gray-200 rounded px-3 py-1.5 text-sm">
              <Database className="w-4 h-4 text-gray-400 mr-2" />
              <span className="text-gray-500 mr-1">Model:</span>
              <span className="font-semibold text-gray-900">{experiment.model_name}</span>
            </div>
          )}
          {experiment.sample_size !== null && experiment.sample_size !== undefined && (
            <div className="flex items-center bg-white border border-gray-200 rounded px-3 py-1.5 text-sm">
              <Info className="w-4 h-4 text-gray-400 mr-2" />
              <span className="text-gray-500 mr-1">Sample Size:</span>
              <span className="font-semibold text-gray-900">{experiment.sample_size}</span>
            </div>
          )}
        </div>
      </div>

      <div className="p-6 space-y-10">
        {/* Context Truthfulness Banner */}
        <div className={`p-4 rounded-lg border flex items-start ${
          isRealModel ? 'bg-emerald-50 border-emerald-200' :
          isSynthetic ? 'bg-purple-50 border-purple-200' :
          'bg-amber-50 border-amber-200'
        }`}>
          <ShieldAlert className={`w-5 h-5 mr-3 mt-0.5 ${
            isRealModel ? 'text-emerald-500' :
            isSynthetic ? 'text-purple-500' :
            'text-amber-500'
          }`} />
          <div>
            <h4 className={`text-sm font-bold uppercase tracking-wider mb-1 ${
              isRealModel ? 'text-emerald-800' :
              isSynthetic ? 'text-purple-800' :
              'text-amber-800'
            }`}>
              Data / Execution Context: {
                isRealModel ? 'REAL LLM INFERENCE' :
                isSynthetic ? 'SYNTHETIC BEHAVIORAL DATASET' :
                isSimulated ? 'SIMULATED TELEMETRY REPLAY' :
                'BENCHMARK ENVIRONMENT'
              }
            </h4>
            <p className={`text-sm ${
              isRealModel ? 'text-emerald-700' :
              isSynthetic ? 'text-purple-700' :
              'text-amber-700'
            }`}>
              {isRealModel && "Metrics derived from live inference against an actual LLM weights/endpoint."}
              {isSynthetic && "Metrics derived from synthetically generated anomaly datasets."}
              {isSimulated && "Metrics derived from replaying captured telemetry rather than live OS execution."}
              {!isRealModel && !isSynthetic && !isSimulated && "Standard benchmark execution environment."}
            </p>
          </div>
        </div>

        {/* Security Performance Grid */}
        <div>
          <h3 className="text-lg font-bold text-gray-900 mb-6 border-b border-gray-100 pb-2">Security Performance</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
            <BaselineComparison 
              metricName="Attack Success Rate (ASR)" 
              baselineValue={getBaselineASR()} 
              protectedValue={experiment.attack_success_rate} 
              lowerIsBetter={true}
            />
            
            <BaselineComparison 
              metricName="Detection Rate" 
              baselineValue={
                experiment.baseline_metrics?.detection_rate ?? 
                experiment.baseline_metrics?.DR ?? 
                null
              } 
              protectedValue={experiment.detection_rate} 
              lowerIsBetter={false}
            />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {experiment.precision !== null && experiment.precision !== undefined && (
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Precision</div>
                <div className="text-xl font-bold font-mono text-gray-900">{experiment.precision.toFixed(3)}</div>
              </div>
            )}
            {experiment.recall !== null && experiment.recall !== undefined && (
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Recall</div>
                <div className="text-xl font-bold font-mono text-gray-900">{experiment.recall.toFixed(3)}</div>
              </div>
            )}
            {experiment.f1_score !== null && experiment.f1_score !== undefined && (
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">F1 Score</div>
                <div className="text-xl font-bold font-mono text-blue-600">{experiment.f1_score.toFixed(3)}</div>
              </div>
            )}
            {experiment.false_positive_rate !== null && experiment.false_positive_rate !== undefined && (
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">False Positive Rate</div>
                <div className="text-xl font-bold font-mono text-red-600">{experiment.false_positive_rate.toFixed(2)}%</div>
              </div>
            )}
          </div>
        </div>

        {/* Latency */}
        {experiment.latency_metrics && (
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-4 border-b border-gray-100 pb-2">Latency Overhead</h3>
            <div className="flex flex-wrap gap-4">
              {Object.entries(experiment.latency_metrics).map(([key, val]) => (
                <div key={key} className="bg-white border border-gray-200 rounded p-3 min-w-[120px]">
                  <div className="text-xs text-gray-500 uppercase">{key}</div>
                  <div className="text-lg font-mono font-medium text-gray-900">
                    {typeof val === 'number' && !Number.isInteger(val) ? val.toFixed(2) : val}
                    <span className="text-xs text-gray-400 ml-1">ms</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Limitations */}
        {experiment.known_limitations && experiment.known_limitations.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-5">
            <h3 className="text-sm font-bold text-red-800 uppercase tracking-wider flex items-center mb-3">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Known Scientific Limitations
            </h3>
            <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
              {experiment.known_limitations.map((limit, idx) => (
                <li key={idx}>{limit}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Raw Artifact */}
        <RawArtifactViewer artifact={experiment.raw_artifact || null} />
      </div>
    </div>
  );
};
