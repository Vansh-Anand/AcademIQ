import React from 'react';
import type { ExperimentSummary } from '../../types/api';
import { ExecutionModeBadge } from '../common/ExecutionModeBadge';
import { Microchip } from 'lucide-react';

interface ExperimentCardProps {
  experiment: ExperimentSummary;
  isSelected: boolean;
  onSelect: (id: string) => void;
  onToggleCompare?: (id: string) => void;
  isCompared?: boolean;
}

export const ExperimentCard: React.FC<ExperimentCardProps> = ({ 
  experiment, 
  isSelected, 
  onSelect,
  onToggleCompare,
  isCompared = false
}) => {
  return (
    <div 
      className={`border rounded-xl p-5 transition-all duration-200 flex flex-col h-full bg-white relative ${
        isSelected ? 'ring-2 ring-blue-500 shadow-md border-transparent' : 'border-gray-200 hover:border-blue-300 hover:shadow-sm'
      }`}
    >
      <div 
        className="flex-grow cursor-pointer"
        onClick={() => onSelect(experiment.experiment_id)}
      >
        <div className="flex justify-between items-start mb-3">
          <div className="bg-gray-100 text-gray-700 text-xs font-bold px-2 py-1 rounded">
            {experiment.experiment_id}
          </div>
          <ExecutionModeBadge mode={experiment.execution_mode} />
        </div>
        
        <h3 className="font-bold text-gray-900 text-lg leading-tight mb-2">
          {experiment.title}
        </h3>
        
        <p className="text-gray-500 text-sm line-clamp-2 mb-4">
          {experiment.description}
        </p>

        {experiment.model_name && (
          <div className="flex items-center text-xs text-indigo-700 bg-indigo-50 px-2 py-1 rounded w-fit mb-4">
            <Microchip className="w-3 h-3 mr-1.5" />
            <span className="truncate max-w-[200px]">{experiment.model_name}</span>
          </div>
        )}
      </div>

      <div className="mt-auto pt-4 border-t border-gray-100 flex justify-between items-center">
        {experiment.primary_metric ? (
          <div>
            <div className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
              {experiment.primary_metric.name}
            </div>
            <div className="font-mono font-bold text-gray-900">
              {typeof experiment.primary_metric.value === 'number' && !Number.isInteger(experiment.primary_metric.value) 
                ? experiment.primary_metric.value.toFixed(2) 
                : experiment.primary_metric.value}
              {experiment.primary_metric.suffix}
            </div>
          </div>
        ) : (
          <div className="text-xs text-gray-400 italic">No primary metric</div>
        )}

        {onToggleCompare && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleCompare(experiment.experiment_id);
            }}
            className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors ${
              isCompared 
                ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' 
                : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border border-gray-200'
            }`}
          >
            {isCompared ? 'Compared' : 'Compare'}
          </button>
        )}
      </div>
    </div>
  );
};
