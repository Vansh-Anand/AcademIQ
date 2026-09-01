import React from 'react';

interface BaselineComparisonProps {
  metricName: string;
  baselineValue: number | null | undefined;
  protectedValue: number | null | undefined;
  suffix?: string;
  lowerIsBetter?: boolean;
}

export const BaselineComparison: React.FC<BaselineComparisonProps> = ({ 
  metricName, 
  baselineValue, 
  protectedValue,
  suffix = '%',
  lowerIsBetter = true
}) => {
  if (baselineValue === null && protectedValue === null) {
    return null;
  }

  const formatValue = (val: number | null | undefined) => {
    if (val === null || val === undefined) return 'N/A';
    return Number.isInteger(val) ? val.toString() : val.toFixed(2);
  };

  const getBarColor = (val: number | null | undefined, isProtected: boolean) => {
    if (val === null || val === undefined) return 'bg-gray-200';
    if (isProtected) {
      if (lowerIsBetter) {
        return val < (baselineValue || 0) ? 'bg-emerald-500' : 'bg-blue-500';
      } else {
        return val > (baselineValue || 0) ? 'bg-emerald-500' : 'bg-blue-500';
      }
    }
    return 'bg-gray-400';
  };

  // Safe percentage calculation for width
  const maxVal = Math.max(baselineValue || 0, protectedValue || 0, 100);
  const baselineWidth = baselineValue != null ? Math.max((baselineValue / maxVal) * 100, 2) : 0;
  const protectedWidth = protectedValue != null ? Math.max((protectedValue / maxVal) * 100, 2) : 0;

  return (
    <div className="mb-4">
      <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
        {metricName}
      </div>
      
      <div className="space-y-3">
        {/* Baseline */}
        <div className="flex items-center">
          <div className="w-24 text-xs text-gray-600 font-medium">Baseline</div>
          <div className="flex-grow flex items-center h-5">
            {baselineValue !== null ? (
              <div 
                className={`h-full ${getBarColor(baselineValue, false)} rounded-r transition-all duration-500`} 
                style={{ width: `${baselineWidth}%` }}
              ></div>
            ) : (
              <span className="text-xs text-gray-400 italic">Unavailable</span>
            )}
            {baselineValue !== null && (
              <span className="ml-2 text-xs font-mono font-bold text-gray-700">
                {formatValue(baselineValue)}{suffix}
              </span>
            )}
          </div>
        </div>

        {/* Protected */}
        <div className="flex items-center">
          <div className="w-24 text-xs text-blue-700 font-bold">AcademIQ</div>
          <div className="flex-grow flex items-center h-5">
            {protectedValue !== null ? (
              <div 
                className={`h-full ${getBarColor(protectedValue, true)} rounded-r transition-all duration-500`} 
                style={{ width: `${protectedWidth}%` }}
              ></div>
            ) : (
              <span className="text-xs text-gray-400 italic">Unavailable</span>
            )}
            {protectedValue !== null && (
              <span className="ml-2 text-xs font-mono font-bold text-blue-800">
                {formatValue(protectedValue)}{suffix}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
