import time
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from typing import Dict, List, Any, Optional

from common.events.schemas import GovernanceDecision

class GovernanceEngine:
    """Neuro-Fuzzy Governance Engine based on Mamdani inference."""
    
    def __init__(self, policy_version: str = "1.0"):
        self.policy_version = policy_version
        self._build_system()
        
        # Simple state tracking for hysteresis (in-memory mock for now)
        self._last_decisions: Dict[str, str] = {}
        self._last_decision_times: Dict[str, int] = {}
        self.cooldown_ns = 5_000_000_000 # 5 seconds
        
    def _build_system(self):
        # Antecedents (Inputs)
        self.risk = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'risk')
        self.divergence = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'divergence')
        self.chain_severity = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'chain_severity')
        
        # Consequent (Output)
        self.action = ctrl.Consequent(np.arange(0, 101, 1), 'action')
        
        # Membership Functions for Risk
        self.risk['LOW'] = fuzz.trimf(self.risk.universe, [0, 0, 0.3])
        self.risk['MEDIUM'] = fuzz.trimf(self.risk.universe, [0.2, 0.5, 0.7])
        self.risk['HIGH'] = fuzz.trimf(self.risk.universe, [0.6, 0.8, 0.95])
        self.risk['CRITICAL'] = fuzz.trapmf(self.risk.universe, [0.85, 0.95, 1.0, 1.0])
        
        # Membership Functions for Divergence
        self.divergence['LOW'] = fuzz.trimf(self.divergence.universe, [0, 0, 0.4])
        self.divergence['MEDIUM'] = fuzz.trimf(self.divergence.universe, [0.3, 0.5, 0.7])
        self.divergence['HIGH'] = fuzz.trapmf(self.divergence.universe, [0.6, 0.8, 1.0, 1.0])
        
        # Membership Functions for Chain Severity
        self.chain_severity['LOW'] = fuzz.trimf(self.chain_severity.universe, [0, 0, 0.4])
        self.chain_severity['MEDIUM'] = fuzz.trimf(self.chain_severity.universe, [0.3, 0.5, 0.7])
        self.chain_severity['HIGH'] = fuzz.trapmf(self.chain_severity.universe, [0.6, 0.8, 1.0, 1.0])
        self.chain_severity['CRITICAL'] = fuzz.trapmf(self.chain_severity.universe, [0.85, 0.95, 1.0, 1.0])
        
        # Membership Functions for Action (ALLOW, WARN, THROTTLE, FREEZE)
        self.action['ALLOW'] = fuzz.trimf(self.action.universe, [0, 0, 30])
        self.action['WARN'] = fuzz.trimf(self.action.universe, [20, 40, 60])
        self.action['THROTTLE'] = fuzz.trimf(self.action.universe, [50, 70, 90])
        self.action['FREEZE'] = fuzz.trapmf(self.action.universe, [80, 95, 100, 100])
        
        # Rules
        rules = [
            # ALLOW Rules
            ctrl.Rule(self.risk['LOW'] & self.divergence['LOW'] & self.chain_severity['LOW'], self.action['ALLOW']),
            
            # WARN Rules
            ctrl.Rule(self.risk['MEDIUM'] | self.divergence['MEDIUM'], self.action['WARN']),
            
            # THROTTLE Rules
            ctrl.Rule(self.risk['HIGH'] & self.chain_severity['HIGH'], self.action['THROTTLE']),
            ctrl.Rule(self.risk['CRITICAL'] & self.chain_severity['LOW'], self.action['THROTTLE']),
            
            # FREEZE Rules
            ctrl.Rule(self.risk['CRITICAL'] & self.chain_severity['MEDIUM'], self.action['FREEZE']),
            ctrl.Rule(self.risk['CRITICAL'] & self.divergence['HIGH'], self.action['FREEZE']),
            ctrl.Rule(self.risk['HIGH'] & self.divergence['HIGH'] & self.chain_severity['HIGH'], self.action['FREEZE']),
            ctrl.Rule(self.risk['CRITICAL'] & self.chain_severity['HIGH'], self.action['FREEZE']),
            ctrl.Rule(self.chain_severity['CRITICAL'], self.action['FREEZE']),
        ]
        
        self.ctrl_system = ctrl.ControlSystem(rules)
        self.simulator = ctrl.ControlSystemSimulation(self.ctrl_system)

    def _map_crisp_to_decision(self, crisp_value: float) -> str:
        if crisp_value >= 85:
            return "FREEZE"
        elif crisp_value >= 65:
            return "THROTTLE"
        elif crisp_value >= 35:
            return "WARN"
        else:
            return "ALLOW"
            
    def _apply_hysteresis(self, agent_id: str, new_decision: str) -> str:
        current_time = time.time_ns()
        
        last_decision = self._last_decisions.get(agent_id, "ALLOW")
        last_time = self._last_decision_times.get(agent_id, 0)
        
        severity_map = {"ALLOW": 0, "WARN": 1, "THROTTLE": 2, "FREEZE": 3}
        
        # If escalating, allow immediately
        if severity_map[new_decision] > severity_map[last_decision]:
            self._last_decisions[agent_id] = new_decision
            self._last_decision_times[agent_id] = current_time
            return new_decision
            
        # If de-escalating, enforce cooldown
        if current_time - last_time < self.cooldown_ns:
            return last_decision
            
        # Cooldown expired, allow de-escalation
        self._last_decisions[agent_id] = new_decision
        self._last_decision_times[agent_id] = current_time
        return new_decision

    def evaluate(self, agent_id: str, risk_prob: float, divergence: float, chain_score: float, telemetry_confidence: float) -> GovernanceDecision:
        # Penalize confidence if telemetry is bad (simplified conservative behavior)
        if telemetry_confidence < 0.8:
            risk_prob = min(1.0, risk_prob + 0.2) # Shift risk up if blind
            
        self.simulator.input['risk'] = np.clip(risk_prob, 0, 1)
        self.simulator.input['divergence'] = np.clip(divergence, 0, 1)
        self.simulator.input['chain_severity'] = np.clip(chain_score, 0, 1)
        
        try:
            self.simulator.compute()
            crisp_action = self.simulator.output['action']
        except ValueError:
            # If rules don't cover the space fully
            crisp_action = 0.0
            
        raw_decision = self._map_crisp_to_decision(crisp_action)
        final_decision = self._apply_hysteresis(agent_id, raw_decision)
        
        # Explanation logic
        explanation = f"Fuzzy inference generated raw score {crisp_action:.2f}. "
        if final_decision != raw_decision:
            explanation += f"Hysteresis held decision at {final_decision}. "
        explanation += f"Inputs: Risk={risk_prob:.2f}, Div={divergence:.2f}, Chain={chain_score:.2f}."
            
        return GovernanceDecision(
            decision=final_decision,
            risk_probability=risk_prob,
            divergence_score=divergence,
            chain_score=chain_score,
            telemetry_confidence=telemetry_confidence,
            fuzzy_activation={"action_score": float(crisp_action)},
            rule_ids=[], # Can extract activated rules with more skfuzzy introspect
            explanation=explanation,
            policy_version=self.policy_version,
            timestamp_ns=time.time_ns()
        )
