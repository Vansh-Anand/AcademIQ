import React from 'react';
import type { ExperimentNormalized } from '../../types/api';
import { X } from 'lucide-react';

interface ExperimentComparisonProps {
  experiments: ExperimentNormalized[];
  onRemove: (id: string) => void;
  onClear: () => void;
}

export const ExperimentComparison: React.FC<ExperimentComparisonProps> = ({ experiments, onRemove, onClear }) => {
  if (experiments.length === 0) return null;

  const metricsToCompare = [
    { label: 'Execution Mode', key: 'execution_mode' },
    { label: 'Model', key: 'model_name' },
    { label: 'Sample Size', key: 'sample_size' },
    { label: 'Detection Rate', key: 'detection_rate', suffix: '%' },
    { label: 'Protected ASR', key: 'attack_success_rate', suffix: '%' },
    { label: 'False Positive Rate', key: 'false_positive_rate', suffix: '%' },
    { label: 'Precision', key: 'precision' },
    { label: 'Recall', key: 'recall' },
    { label: 'F1 Score', key: 'f1_score' },
  ];

  const formatValue = (val: any, suffix?: string) => {
    if (val === null || val === undefined) return <span className="text-gray-300">—</span>;
    if (typeof val === 'number') {
      return (
        <span className="font-mono font-semibold">
          {Number.isInteger(val) ? val : val.toFixed(2)}{suffix || ''}
        </span>
      );
    }
    return <span className="text-gray-900">{val}</span>;
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.1)] z-50 animate-in slide-in-from-bottom-full duration-300">
      <div className="max-w-7xl mx-auto p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-bold text-gray-900">Comparing {experiments.length} Experiment{experiments.length > 1 ? 's' : ''}</h3>
          <button onClick={onClear} className="text-sm text-red-600 hover:text-red-800 font-medium px-3 py-1 rounded hover:bg-red-50 transition-colors">
            Clear Comparison
          </button>
        </div>

        <div className="overflow-x-auto pb-4">
          <table className="w-full text-sm text-left">
            <thead>
              <tr>
                <th className="px-4 py-3 bg-gray-50 border-b border-gray-200 text-gray-500 font-medium w-48">Metric</th>
                {experiments.map(exp => (
                  <th key={exp.experiment_id} className="px-4 py-3 bg-gray-50 border-b border-gray-200 font-bold text-gray-900 min-w-[200px]">
                    <div className="flex justify-between items-start">
                      <div className="pr-4">
                        <div className="text-xs text-blue-600 mb-1">{exp.experiment_id}</div>
                        <div className="line-clamp-1" title={exp.title}>{exp.title}</div>
                      </div>
                      <button onClick={() => onRemove(exp.experiment_id)} className="text-gray-400 hover:text-red-500">
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {metricsToCompare.map(metric => (
                <tr key={metric.key} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-2.5 font-medium text-gray-600 bg-gray-50/50">{metric.label}</td>
                  {experiments.map(exp => (
                    <td key={exp.experiment_id} className="px-4 py-2.5">
                      {formatValue((exp as any)[metric.key], metric.suffix)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
