class IDSSampler:
    def __init__(self, lambda_cost=0.1):
        self.lambda_cost = lambda_cost

    def score(self, candidate):
        # candidate: dict with keys {'info_gain','var','cost'}
        ig = max(candidate.get("info_gain", 0.0), 0.0)
        var = max(candidate.get("var", 1e-6), 1e-6)
        cost = max(candidate.get("cost", 0.0), 0.0)
        return (ig**2) / (var + self.lambda_cost * cost + 1e-9)

    def select(self, candidates, k=1):
        return sorted(candidates, key=self.score, reverse=True)[:k]
