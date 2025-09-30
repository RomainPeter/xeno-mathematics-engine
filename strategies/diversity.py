"""
Diversity strategies for Discovery Engine 2-Cat.
Migrated from proof-engine-for-code.
"""

import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DiversityItem:
    """Item for diversity selection."""

    id: str
    features: List[float]
    metadata: Dict[str, Any]
    diversity_score: float = 0.0


class DiversityStrategy:
    """Diversity strategy for exploration."""

    def __init__(self, lambda_param: float = 0.5):
        self.lambda_param = lambda_param  # Diversity weight
        self.selected_items: List[DiversityItem] = []
        self.feature_matrix: List[List[float]] = []
        self.diversity_history: List[Dict[str, Any]] = []

    def select_diverse_items(self, items: List[Dict[str, Any]], k: int) -> List[DiversityItem]:
        """Select k diverse items from the list."""
        if not items:
            return []

        # Convert items to DiversityItem objects
        diversity_items = []
        for item in items:
            diversity_item = DiversityItem(
                id=item.get("id", str(len(diversity_items))),
                features=item.get("features", []),
                metadata=item,
            )
            diversity_items.append(diversity_item)

        # Select diverse items using DPP
        selected = self._dpp_selection(diversity_items, k)

        # Update diversity history
        self.diversity_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "total_items": len(items),
                "selected_count": len(selected),
                "diversity_scores": [item.diversity_score for item in selected],
            }
        )

        return selected

    def _dpp_selection(self, items: List[DiversityItem], k: int) -> List[DiversityItem]:
        """Select items using Determinantal Point Process (DPP)."""
        if len(items) <= k:
            return items

        # Calculate similarity matrix
        similarity_matrix = self._calculate_similarity_matrix(items)

        # Calculate DPP scores
        dpp_scores = self._calculate_dpp_scores(similarity_matrix)

        # Select top k items based on DPP scores
        scored_items = list(zip(items, dpp_scores))
        scored_items.sort(key=lambda x: x[1], reverse=True)

        selected = []
        for item, score in scored_items[:k]:
            item.diversity_score = score
            selected.append(item)

        # Update selected items
        self.selected_items.extend(selected)

        return selected

    def _calculate_similarity_matrix(self, items: List[DiversityItem]) -> np.ndarray:
        """Calculate similarity matrix between items."""
        n = len(items)
        similarity_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i == j:
                    similarity_matrix[i, j] = 1.0
                else:
                    similarity = self._calculate_similarity(items[i], items[j])
                    similarity_matrix[i, j] = similarity

        return similarity_matrix

    def _calculate_similarity(self, item1: DiversityItem, item2: DiversityItem) -> float:
        """Calculate similarity between two items."""
        if not item1.features or not item2.features:
            return 0.0

        # Ensure same length
        min_len = min(len(item1.features), len(item2.features))
        features1 = item1.features[:min_len]
        features2 = item2.features[:min_len]

        # Calculate cosine similarity
        dot_product = np.dot(features1, features2)
        norm1 = np.linalg.norm(features1)
        norm2 = np.linalg.norm(features2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return max(0.0, similarity)  # Ensure non-negative

    def _calculate_dpp_scores(self, similarity_matrix: np.ndarray) -> List[float]:
        """Calculate DPP scores for items."""
        n = similarity_matrix.shape[0]
        dpp_scores = []

        for i in range(n):
            # Calculate DPP score for item i
            # DPP score is related to the determinant of the submatrix
            score = self._calculate_dpp_score(similarity_matrix, i)
            dpp_scores.append(score)

        return dpp_scores

    def _calculate_dpp_score(self, matrix: np.ndarray, item_idx: int) -> float:
        """Calculate DPP score for a specific item."""
        # Simplified DPP score calculation
        # In practice, this would involve more complex matrix operations

        # Calculate the sum of similarities to other items
        similarities = matrix[item_idx, :]
        total_similarity = np.sum(similarities) - similarities[item_idx]  # Exclude self-similarity

        # DPP score is inversely related to total similarity
        dpp_score = 1.0 / (1.0 + total_similarity)

        return dpp_score

    def calculate_diversity_metrics(self, items: List[DiversityItem]) -> Dict[str, float]:
        """Calculate diversity metrics for a set of items."""
        if len(items) < 2:
            return {"diversity": 0.0, "coverage": 0.0, "balance": 0.0}

        # Calculate pairwise distances
        distances = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                distance = self._calculate_distance(items[i], items[j])
                distances.append(distance)

        # Diversity metrics
        diversity = np.mean(distances) if distances else 0.0
        coverage = self._calculate_coverage(items)
        balance = self._calculate_balance(items)

        return {"diversity": diversity, "coverage": coverage, "balance": balance}

    def _calculate_distance(self, item1: DiversityItem, item2: DiversityItem) -> float:
        """Calculate distance between two items."""
        if not item1.features or not item2.features:
            return 1.0

        # Ensure same length
        min_len = min(len(item1.features), len(item2.features))
        features1 = item1.features[:min_len]
        features2 = item2.features[:min_len]

        # Calculate Euclidean distance
        distance = np.linalg.norm(np.array(features1) - np.array(features2))
        return distance

    def _calculate_coverage(self, items: List[DiversityItem]) -> float:
        """Calculate coverage of the feature space."""
        if not items or not items[0].features:
            return 0.0

        # Calculate the span of features
        feature_matrix = np.array([item.features for item in items if item.features])
        if feature_matrix.size == 0:
            return 0.0

        # Calculate the range of each feature dimension
        feature_ranges = np.ptp(feature_matrix, axis=0)  # Peak-to-peak (max - min)
        coverage = np.mean(feature_ranges)

        return coverage

    def _calculate_balance(self, items: List[DiversityItem]) -> float:
        """Calculate balance of the selection."""
        if not items:
            return 0.0

        # Calculate the variance of diversity scores
        scores = [item.diversity_score for item in items]
        if not scores:
            return 0.0

        balance = 1.0 / (1.0 + np.var(scores))  # Higher variance = lower balance
        return balance

    def get_diversity_stats(self) -> Dict[str, Any]:
        """Get diversity strategy statistics."""
        return {
            "total_selections": len(self.selected_items),
            "diversity_history": self.diversity_history,
            "average_diversity": (
                np.mean([item.diversity_score for item in self.selected_items])
                if self.selected_items
                else 0.0
            ),
        }
