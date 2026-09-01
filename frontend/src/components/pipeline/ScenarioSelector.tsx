import React from 'react';
import { AVAILABLE_SCENARIOS } from '../../types/pipeline';

interface ScenarioSelectorProps {
  onSelect: (scenarioId: string) => void;
  isRunning: boolean;
}

export const ScenarioSelector: React.FC<ScenarioSelectorProps> = ({ onSelect, isRunning }) => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Select Execution Scenario</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {AVAILABLE_SCENARIOS.map((scenario) => (
          <button
            key={scenario.id}
            onClick={() => onSelect(scenario.id)}
            disabled={isRunning}
            className="flex flex-col text-left p-4 border rounded-lg transition-colors border-gray-200 hover:border-blue-400 hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <div className="flex justify-between items-start w-full mb-2">
              <span className="font-medium text-gray-900 group-hover:text-blue-700">{scenario.label}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                scenario.category === 'Safe' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
              }`}>
                {scenario.category}
              </span>
            </div>
            <span className="text-sm text-gray-500 line-clamp-2">{scenario.description}</span>
          </button>
        ))}
      </div>
    </div>
  );
};
