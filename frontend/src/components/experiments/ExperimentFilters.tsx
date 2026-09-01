import React from 'react';
import { Search } from 'lucide-react';
import type { ExecutionModeType } from '../../types/api';
import { ExecutionMode } from '../../types/api';

export interface FilterState {
  search: string;
  category: string | null;
  executionMode: ExecutionModeType | null;
}

interface ExperimentFiltersProps {
  filters: FilterState;
  onFilterChange: (filters: FilterState) => void;
  categories: string[];
}

export const ExperimentFilters: React.FC<ExperimentFiltersProps> = ({ filters, onFilterChange, categories }) => {
  const modes = [
    ExecutionMode.REAL_RUNTIME,
    ExecutionMode.BENCHMARK,
    ExecutionMode.SIMULATED,
    ExecutionMode.SYNTHETIC
  ];

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex flex-col md:flex-row gap-4 items-start md:items-center">
      <div className="relative flex-grow w-full md:w-auto">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-gray-400" />
        </div>
        <input
          type="text"
          placeholder="Search experiments, models, or IDs..."
          value={filters.search}
          onChange={(e) => onFilterChange({ ...filters, search: e.target.value })}
          className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
      </div>
      
      <div className="flex gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
        <select
          value={filters.category || ''}
          onChange={(e) => onFilterChange({ ...filters, category: e.target.value || null })}
          className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md border"
        >
          <option value="">All Categories</option>
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>

        <select
          value={filters.executionMode || ''}
          onChange={(e) => onFilterChange({ ...filters, executionMode: (e.target.value as ExecutionModeType) || null })}
          className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md border"
        >
          <option value="">All Modes</option>
          {modes.map(mode => (
            <option key={mode} value={mode}>{mode.replace('_', ' ')}</option>
          ))}
        </select>
      </div>
    </div>
  );
};
