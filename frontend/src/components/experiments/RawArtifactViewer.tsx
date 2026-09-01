import React, { useState } from 'react';
import { Code, ChevronDown, ChevronUp } from 'lucide-react';

interface RawArtifactViewerProps {
  artifact: Record<string, any> | null;
}

export const RawArtifactViewer: React.FC<RawArtifactViewerProps> = ({ artifact }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!artifact) return null;

  return (
    <div className="mt-8 border border-gray-200 rounded-lg overflow-hidden">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center text-gray-700 font-medium">
          <Code className="w-4 h-4 mr-2" />
          Raw Experiment Artifact (summary.json)
        </div>
        {isOpen ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
      </button>
      
      {isOpen && (
        <div className="bg-gray-900 p-4 overflow-x-auto">
          <pre className="text-xs text-green-400 font-mono">
            {JSON.stringify(artifact, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
