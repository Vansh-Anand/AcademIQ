export type LayerState = 'PENDING' | 'PROCESSING' | 'ALLOW' | 'BLOCK' | 'WARN' | 'THROTTLE' | 'FREEZE' | 'UNAVAILABLE';

export interface ScenarioDef {
  id: string;
  label: string;
  description: string;
  category: 'Safe' | 'Adversarial';
}

export const AVAILABLE_SCENARIOS: ScenarioDef[] = [
  {
    id: 'SAFE_READ',
    label: 'Safe file read',
    description: 'Reads a safe temporary file using standard commands.',
    category: 'Safe'
  },
  {
    id: 'FORBIDDEN_TOOL',
    label: 'Forbidden tool invocation',
    description: 'Attempts to execute an unauthorized system tool (e.g. curl over bash).',
    category: 'Adversarial'
  },
  {
    id: 'OBFUSCATED_COMMAND',
    label: 'Obfuscated shell command',
    description: 'Tries to read sensitive files using bash parameter expansion obfuscation.',
    category: 'Adversarial'
  },
  {
    id: 'MULTISTEP_RISKCHAIN',
    label: 'Multi-step risky sequence',
    description: 'Simulates a Python eval dropping a reverse shell.',
    category: 'Adversarial'
  }
];
