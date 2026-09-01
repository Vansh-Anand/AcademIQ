import React from 'react';
import type { VerifyResponse } from '../../types/api';
import { ShieldCheck, ShieldAlert, Loader2, Play } from 'lucide-react';

interface ChainVerificationPanelProps {
  onVerify: () => void;
  result: VerifyResponse | null;
  isLoading: boolean;
  error: string | null;
}

export const ChainVerificationPanel: React.FC<ChainVerificationPanelProps> = ({ onVerify, result, isLoading, error }) => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Chain Verification</h3>
        <button
          onClick={onVerify}
          disabled={isLoading}
          className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium disabled:opacity-50 transition-colors"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          <span>Verify Chain</span>
        </button>
      </div>
      
      <p className="text-sm text-gray-600 mb-6">
        Cryptographically validates the hash chain from genesis through all sequence records. This process runs on the backend to guarantee integrity.
      </p>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-200 text-sm">
          Chain verification is currently unavailable. {error}
        </div>
      )}

      {result && (
        <div className={`p-6 rounded-lg border ${result.valid ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}`}>
          <div className="flex items-center space-x-4 mb-4">
            {result.valid ? (
              <ShieldCheck className="w-10 h-10 text-emerald-500" />
            ) : (
              <ShieldAlert className="w-10 h-10 text-red-500" />
            )}
            <div>
              <h4 className={`text-xl font-bold uppercase tracking-wider ${result.valid ? 'text-emerald-700' : 'text-red-700'}`}>
                {result.valid ? 'Chain Verified' : 'Chain Integrity Failure'}
              </h4>
              <p className={`text-sm ${result.valid ? 'text-emerald-600' : 'text-red-600'}`}>
                {result.valid 
                  ? 'All cryptographic links are valid. No evidence tampering detected.' 
                  : `Verification detected a broken hash relationship. Reason: ${result.failure || 'UNKNOWN'}`}
              </p>
            </div>
          </div>
          
          <div className={`text-sm font-mono p-3 rounded ${result.valid ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
            Records Checked: {result.records_checked}
          </div>
        </div>
      )}
      
      {!result && !error && !isLoading && (
        <div className="bg-gray-50 border border-gray-200 rounded p-4 text-center text-sm text-gray-500">
          Click "Verify Chain" to perform cryptographic validation.
        </div>
      )}
    </div>
  );
};
