import numpy as np


def cvar(values, alpha=0.9):
    if not values:
        return 0.0
    q = np.quantile(values, alpha)
    tail = [v for v in values if v >= q]
    return float(np.mean(tail)) if tail else float(q)


def risk_adjusted_utility(utility_samples, cost_samples, alpha=0.9, w_util=1.0, w_cost=1.0):
    # maximize expected utility, penalize CVaR cost
    eu = float(np.mean(utility_samples)) if utility_samples else 0.0
    rc = cvar(cost_samples, alpha=alpha) if cost_samples else 0.0
    return w_util * eu - w_cost * rc
