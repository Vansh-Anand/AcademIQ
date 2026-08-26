import yaml
from typing import Dict, List
from common.events.schemas import BayesianRiskResult

class BayesianRiskModel:
    """Mathematically explicit Bayesian risk model."""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._load_config()
        
    def _load_config(self):
        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f)
            
        self.prior_attack = data.get('prior_attack_probability', 0.05)
        self.cpts = data.get('cpts', {})
        self.version = data.get('model_version', '1.0')
        
    def evaluate(self, evidence: Dict[str, bool]) -> BayesianRiskResult:
        """
        Evaluates P(Attack | Evidence) using a Naive Bayes assumption 
        (conditional independence of evidence variables given the Attack state).
        
        P(Attack | E) = [ P(E | Attack) * P(Attack) ] / [ P(E) ]
        """
        p_attack = self.prior_attack
        p_normal = 1.0 - p_attack
        
        p_e_given_attack = 1.0
        p_e_given_normal = 1.0
        
        contributing = []
        
        for feature, is_present in evidence.items():
            if feature not in self.cpts:
                continue
                
            prob_if_attack = self.cpts[feature]['attack']
            prob_if_normal = self.cpts[feature]['normal']
            
            if is_present:
                p_e_given_attack *= prob_if_attack
                p_e_given_normal *= prob_if_normal
                contributing.append(feature)
            else:
                p_e_given_attack *= (1.0 - prob_if_attack)
                p_e_given_normal *= (1.0 - prob_if_normal)
                
        # Denominator P(E)
        p_e = (p_e_given_attack * p_attack) + (p_e_given_normal * p_normal)
        
        if p_e == 0:
            # Prevent division by zero if probabilities are 0
            posterior = p_attack
        else:
            posterior = (p_e_given_attack * p_attack) / p_e
            
        return BayesianRiskResult(
            attack_probability=float(posterior),
            prior=float(self.prior_attack),
            evidence=evidence,
            model_version=self.version,
            confidence=0.9, # Confidence derived from telemetry quality in upper layers
            contributing_variables=contributing
        )
