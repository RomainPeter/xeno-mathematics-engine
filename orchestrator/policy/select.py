from methods.ids.ids_sampler import IDSSampler
from orchestrator.policy.cvar import risk_adjusted_utility


class Selector:
    def __init__(self, bandit, diversity, ids_lambda=0.1, cvar_alpha=0.9):
        self.bandit = bandit
        self.diversity = diversity
        self.ids = IDSSampler(lambda_cost=ids_lambda)
        self.cvar_alpha = cvar_alpha

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
