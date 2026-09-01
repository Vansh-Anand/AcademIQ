import React from 'react';
import { ScenarioSelector } from '../components/pipeline/ScenarioSelector';
import { PipelineFlow } from '../components/pipeline/PipelineFlow';
import { usePipelineExecution } from '../hooks/usePipelineExecution';
import { ErrorState } from '../components/common/ErrorState';
import { Shield } from 'lucide-react';

export const PipelinePage: React.FC = () => {
  const execution = usePipelineExecution();

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          <Shield className="w-6 h-6 mr-2 text-blue-600" />
          AcademIQ Security Pipeline
        </h2>
        <p className="mt-2 text-gray-600">Simulate and visualize adversarial scenarios through the L1-L7 defense layers in real-time.</p>
      </div>
      
      {execution.error && (
        <ErrorState title="Execution Failed" message={execution.error} className="mb-6" />
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-1 space-y-6">
          <ScenarioSelector 
            onSelect={execution.executeScenario} 
            isRunning={execution.isRunning} 
          />
          
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 text-sm text-gray-600 space-y-4">
            <h4 className="font-semibold text-gray-900 border-b border-gray-200 pb-2">Execution Notes</h4>
            <p>
              Scenarios are processed synchronously by the backend orchestrator. The pipeline flow animation is a UI visualization of the returned event trace, not a WebSocket stream.
            </p>
            <p>
              On Windows/Mock environments, kernel telemetry (L3) and container isolation (L7) are clearly marked as <strong>SIMULATED</strong> or <strong>UNAVAILABLE</strong> in adherence to truthfulness requirements.
            </p>
          </div>
        </div>

        <div className="xl:col-span-2">
          {(!execution.result && !execution.isRunning && execution.currentLayer === null) ? (
            <div className="bg-white p-12 rounded-lg shadow-sm border border-gray-200 border-dashed flex flex-col items-center justify-center text-center h-full min-h-[400px]">
              <Shield className="w-16 h-16 text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900">Pipeline Idle</h3>
              <p className="mt-2 text-sm text-gray-500 max-w-sm">Select a scenario from the left panel to begin execution simulation through the defense layers.</p>
            </div>
          ) : (
            <PipelineFlow execution={execution} />
          )}
        </div>
      </div>
    </div>
  );
};
