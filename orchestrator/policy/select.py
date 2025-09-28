import json
from pathlib import Path
from methods.ids.ids_sampler import IDSSampler
from orchestrator.policy.cvar import risk_adjusted_utility


class Selector:
    def __init__(
        self, bandit, diversity, ids_lambda=None, cvar_alpha=None, overrides_file=None
    ):
        self.bandit = bandit
        self.diversity = diversity

        # Load overrides if provided
        if overrides_file and Path(overrides_file).exists():
            with open(overrides_file) as f:
                overrides = json.load(f)
                ids_lambda = overrides.get("ids", {}).get("lambda", ids_lambda)
                cvar_alpha = overrides.get("risk_policy", {}).get(
                    "cvar_alpha", cvar_alpha
                )

        # Use defaults if not provided
        self.ids_lambda = ids_lambda or 0.6
        self.cvar_alpha = cvar_alpha or 0.9

        self.ids = IDSSampler(lambda_cost=self.ids_lambda)
        self.overrides_file = overrides_file

    def rank(self, candidates):
        # candidates: [{'id', 'V_hat', 'S_hat', 'info_gain','var','cost', 'diversity_key', ...}]
        diverse = self.diversity.select(candidates)
        # IDS re-scoring
        for c in diverse:
            c["ids_score"] = self.ids.score(
                {
                    "info_gain": c.get("info_gain", 0.0),
                    "var": c.get("var", 0.25),
                    "cost": c.get("V_hat", {}).get("time_ms", 0.0),
                }
            )
        diverse.sort(
            key=lambda x: (x.get("ids_score", 0.0), x.get("S_hat", 0.0)), reverse=True
        )
        return diverse

    def update(self, cand_id, reward_samples, cost_samples):
        u = risk_adjusted_utility(reward_samples, cost_samples, alpha=self.cvar_alpha)
        self.bandit.update(cand_id, u)

    def get_scores(self, candidates):
        """Get IDS and CVaR scores for candidates."""
        scores = []
        for c in candidates:
            ids_score = self.ids.score(
                {
                    "info_gain": c.get("info_gain", 0.0),
                    "var": c.get("var", 0.25),
                    "cost": c.get("V_hat", {}).get("time_ms", 0.0),
                }
            )

            # Calculate CVaR score
            reward_samples = c.get("reward_samples", [0.0])
            cost_samples = c.get("cost_samples", [0.0])
            cvar_score = risk_adjusted_utility(
                reward_samples, cost_samples, alpha=self.cvar_alpha
            )

            scores.append(
                {
                    "candidate_id": c.get("id"),
                    "ids_score": ids_score,
                    "cvar_score": cvar_score,
                    "ids_lambda": self.ids_lambda,
                    "cvar_alpha": self.cvar_alpha,
                }
            )

        return scores

    def get_config(self):
        """Get current configuration."""
        return {
            "ids_lambda": self.ids_lambda,
            "cvar_alpha": self.cvar_alpha,
            "overrides_file": self.overrides_file,
        }
