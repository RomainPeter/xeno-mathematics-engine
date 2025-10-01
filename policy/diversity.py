"""
Diversity selection using DPP (Determinantal Point Process) for Discovery Engine 2-Cat.
Submodular diversity selection algorithms.
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
    diversity_key: str
    metadata: Dict[str, Any]
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class DiversitySelection:
    """Result of diversity selection."""

    selected_items: List[DiversityItem]
    diversity_score: float
    selection_method: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class DPPSelector:
    """Determinantal Point Process selector for diversity."""

    def __init__(self, lambda_param: float = 1.0, kernel_type: str = "rbf"):
        """
        Initialize DPP selector.

        Args:
            lambda_param: DPP parameter
            kernel_type: Kernel type for similarity
        """
        self.lambda_param = lambda_param
        self.kernel_type = kernel_type

        # Statistics
        self.total_selections = 0
        self.diversity_scores: List[float] = []
        self.selection_history: List[Dict[str, Any]] = []

    def select_diverse_items(
        self, items: List[DiversityItem], k: int, diversity_key: str = None
    ) -> DiversitySelection:
        """Select k diverse items using DPP."""
        if not items:
            raise ValueError("No items provided")

        if k <= 0 or k > len(items):
            raise ValueError(f"Invalid k: {k}, must be 1 <= k <= {len(items)}")

        # Filter by diversity key if specified
        if diversity_key:
            filtered_items = [item for item in items if item.diversity_key == diversity_key]
            if not filtered_items:
                # Fallback to all items if no items match diversity key
                filtered_items = items
        else:
            filtered_items = items

        # Calculate similarity matrix
        similarity_matrix = self._calculate_similarity_matrix(filtered_items)

        # Apply DPP selection
        selected_indices = self._dpp_select(similarity_matrix, k)

        # Create selected items
        selected_items = [filtered_items[i] for i in selected_indices]

        # Calculate diversity score
        diversity_score = self._calculate_diversity_score(selected_items, similarity_matrix)

        # Create selection result
        selection = DiversitySelection(
            selected_items=selected_items,
            diversity_score=diversity_score,
            selection_method="DPP",
        )

        # Record selection
        self.total_selections += 1
        self.diversity_scores.append(diversity_score)
        self.selection_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "k": k,
                "diversity_key": diversity_key,
                "diversity_score": diversity_score,
                "selected_item_ids": [item.id for item in selected_items],
                "total_items": len(filtered_items),
            }
        )

        return selection

    def _calculate_similarity_matrix(self, items: List[DiversityItem]) -> np.ndarray:
        """Calculate similarity matrix for items."""
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
        features1 = np.array(item1.features)
        features2 = np.array(item2.features)

        # Ensure same dimension
        if len(features1) != len(features2):
            min_len = min(len(features1), len(features2))
            features1 = features1[:min_len]
            features2 = features2[:min_len]

        if self.kernel_type == "rbf":
            # RBF kernel
            gamma = 1.0 / len(features1)
            distance = np.linalg.norm(features1 - features2)
            similarity = np.exp(-gamma * distance**2)
        elif self.kernel_type == "linear":
            # Linear kernel
            similarity = np.dot(features1, features2) / (
                np.linalg.norm(features1) * np.linalg.norm(features2)
            )
        else:
            # Default: cosine similarity
            similarity = np.dot(features1, features2) / (
                np.linalg.norm(features1) * np.linalg.norm(features2)
            )

        return max(0.0, similarity)  # Ensure non-negative

    def _dpp_select(self, similarity_matrix: np.ndarray, k: int) -> List[int]:
        """Select k items using DPP."""
        n = similarity_matrix.shape[0]

        if k >= n:
            return list(range(n))

        # Greedy DPP selection
        selected_indices = []
        remaining_indices = list(range(n))

        # Initialize with highest quality item
        quality_scores = np.diag(similarity_matrix)
        initial_idx = np.argmax(quality_scores)
        selected_indices.append(initial_idx)
        remaining_indices.remove(initial_idx)

        # Greedy selection
        for _ in range(k - 1):
            best_idx = None
            best_score = -np.inf

            for idx in remaining_indices:
                # Calculate marginal gain
                marginal_gain = self._calculate_marginal_gain(
                    selected_indices, idx, similarity_matrix
                )

                if marginal_gain > best_score:
                    best_score = marginal_gain
                    best_idx = idx

            if best_idx is not None:
                selected_indices.append(best_idx)
                remaining_indices.remove(best_idx)

        return selected_indices

    def _calculate_marginal_gain(
        self,
        selected_indices: List[int],
        candidate_idx: int,
        similarity_matrix: np.ndarray,
    ) -> float:
        """Calculate marginal gain of adding candidate to selection."""
        if not selected_indices:
            return similarity_matrix[candidate_idx, candidate_idx]

        # Calculate determinant of selected items
        selected_matrix = similarity_matrix[np.ix_(selected_indices, selected_indices)]
        current_det = np.linalg.det(selected_matrix)

        # Calculate determinant with candidate added
        extended_indices = selected_indices + [candidate_idx]
        extended_matrix = similarity_matrix[np.ix_(extended_indices, extended_indices)]
        extended_det = np.linalg.det(extended_matrix)

        # Marginal gain
        marginal_gain = extended_det - current_det

        return marginal_gain

    def _calculate_diversity_score(
        self, selected_items: List[DiversityItem], similarity_matrix: np.ndarray
    ) -> float:
        """Calculate diversity score for selected items."""
        if not selected_items:
            return 0.0

        # Get indices of selected items
        selected_indices = [i for i, item in enumerate(selected_items)]

        # Calculate determinant (diversity score)
        selected_matrix = similarity_matrix[np.ix_(selected_indices, selected_indices)]
        diversity_score = np.linalg.det(selected_matrix)

        return max(0.0, diversity_score)  # Ensure non-negative

    def get_statistics(self) -> Dict[str, Any]:
        """Get selector statistics."""
        if not self.diversity_scores:
            return {
                "total_selections": 0,
                "average_diversity_score": 0.0,
                "max_diversity_score": 0.0,
                "min_diversity_score": 0.0,
                "selection_history_length": 0,
            }

        return {
            "total_selections": self.total_selections,
            "average_diversity_score": np.mean(self.diversity_scores),
            "max_diversity_score": np.max(self.diversity_scores),
            "min_diversity_score": np.min(self.diversity_scores),
            "diversity_score_std": np.std(self.diversity_scores),
            "selection_history_length": len(self.selection_history),
            "lambda_param": self.lambda_param,
            "kernel_type": self.kernel_type,
        }


class SubmodularSelector:
    """Submodular diversity selector."""

    def __init__(self, alpha: float = 1.0, beta: float = 0.5):
        """
        Initialize submodular selector.

        Args:
            alpha: Coverage parameter
            beta: Diversity parameter
        """
        self.alpha = alpha
        self.beta = beta

        # Statistics
        self.total_selections = 0
        self.diversity_scores: List[float] = []
        self.selection_history: List[Dict[str, Any]] = []

    def select_diverse_items(
        self, items: List[DiversityItem], k: int, diversity_key: str = None
    ) -> DiversitySelection:
        """Select k diverse items using submodular optimization."""
        if not items:
            raise ValueError("No items provided")

        if k <= 0 or k > len(items):
            raise ValueError(f"Invalid k: {k}, must be 1 <= k <= {len(items)}")

        # Filter by diversity key if specified
        if diversity_key:
            filtered_items = [item for item in items if item.diversity_key == diversity_key]
            if not filtered_items:
                filtered_items = items
        else:
            filtered_items = items

        # Greedy submodular selection
        selected_items = self._greedy_submodular_selection(filtered_items, k)

        # Calculate diversity score
        diversity_score = self._calculate_submodular_score(selected_items)

        # Create selection result
        selection = DiversitySelection(
            selected_items=selected_items,
            diversity_score=diversity_score,
            selection_method="Submodular",
        )

        # Record selection
        self.total_selections += 1
        self.diversity_scores.append(diversity_score)
        self.selection_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "k": k,
                "diversity_key": diversity_key,
                "diversity_score": diversity_score,
                "selected_item_ids": [item.id for item in selected_items],
                "total_items": len(filtered_items),
            }
        )

        return selection

    def _greedy_submodular_selection(
        self, items: List[DiversityItem], k: int
    ) -> List[DiversityItem]:
        """Greedy submodular selection."""
        selected_items = []
        remaining_items = items.copy()

        for _ in range(k):
            best_item = None
            best_score = -np.inf

            for item in remaining_items:
                # Calculate marginal gain
                marginal_gain = self._calculate_marginal_gain(selected_items, item)

                if marginal_gain > best_score:
                    best_score = marginal_gain
                    best_item = item

            if best_item is not None:
                selected_items.append(best_item)
                remaining_items.remove(best_item)

        return selected_items

    def _calculate_marginal_gain(
        self, selected_items: List[DiversityItem], candidate_item: DiversityItem
    ) -> float:
        """Calculate marginal gain of adding candidate to selection."""
        if not selected_items:
            return self.alpha * self._item_quality(candidate_item)

        # Coverage gain
        coverage_gain = self.alpha * self._coverage_gain(selected_items, candidate_item)

        # Diversity gain
        diversity_gain = self.beta * self._diversity_gain(selected_items, candidate_item)

        return coverage_gain + diversity_gain

    def _item_quality(self, item: DiversityItem) -> float:
        """Calculate item quality."""
        # Simple quality based on features
        features = np.array(item.features)
        return np.sum(features**2)  # L2 norm squared

    def _coverage_gain(
        self, selected_items: List[DiversityItem], candidate_item: DiversityItem
    ) -> float:
        """Calculate coverage gain."""
        # Coverage based on feature diversity
        selected_features = [np.array(item.features) for item in selected_items]
        candidate_features = np.array(candidate_item.features)

        # Calculate minimum distance to selected items
        min_distance = (
            min([np.linalg.norm(candidate_features - features) for features in selected_features])
            if selected_features
            else 0.0
        )

        return min_distance

    def _diversity_gain(
        self, selected_items: List[DiversityItem], candidate_item: DiversityItem
    ) -> float:
        """Calculate diversity gain."""
        # Diversity based on diversity key
        selected_keys = [item.diversity_key for item in selected_items]
        candidate_key = candidate_item.diversity_key

        # Count unique keys
        unique_keys = set(selected_keys + [candidate_key])
        diversity_gain = len(unique_keys) - len(set(selected_keys))

        return diversity_gain

    def _calculate_submodular_score(self, selected_items: List[DiversityItem]) -> float:
        """Calculate submodular score for selected items."""
        if not selected_items:
            return 0.0

        # Coverage score
        coverage_score = self.alpha * sum(self._item_quality(item) for item in selected_items)

        # Diversity score
        diversity_score = self.beta * len(set(item.diversity_key for item in selected_items))

        return coverage_score + diversity_score

    def get_statistics(self) -> Dict[str, Any]:
        """Get selector statistics."""
        if not self.diversity_scores:
            return {
                "total_selections": 0,
                "average_diversity_score": 0.0,
                "max_diversity_score": 0.0,
                "min_diversity_score": 0.0,
                "selection_history_length": 0,
            }

        return {
            "total_selections": self.total_selections,
            "average_diversity_score": np.mean(self.diversity_scores),
            "max_diversity_score": np.max(self.diversity_scores),
            "min_diversity_score": np.min(self.diversity_scores),
            "diversity_score_std": np.std(self.diversity_scores),
            "selection_history_length": len(self.selection_history),
            "alpha": self.alpha,
            "beta": self.beta,
        }


# Convenience functions
def dpp_select(
    candidates: List[Dict[str, Any]], keys: List[str], k: int, lambda_param: float = 1.0
) -> List[Dict[str, Any]]:
    """DPP selection convenience function."""
    # Convert candidates to DiversityItems
    items = []
    for i, candidate in enumerate(candidates):
        item = DiversityItem(
            id=candidate.get("id", f"item_{i}"),
            features=candidate.get("features", [0.0] * 10),
            diversity_key=candidate.get("diversity_key", "default"),
            metadata=candidate.get("metadata", {}),
        )
        items.append(item)

    # Create selector and select
    selector = DPPSelector(lambda_param=lambda_param)
    selection = selector.select_diverse_items(items, k)

    # Convert back to original format
    return [item.__dict__ for item in selection.selected_items]


def submodular_select(
    candidates: List[Dict[str, Any]],
    keys: List[str],
    k: int,
    alpha: float = 1.0,
    beta: float = 0.5,
) -> List[Dict[str, Any]]:
    """Submodular selection convenience function."""
    # Convert candidates to DiversityItems
    items = []
    for i, candidate in enumerate(candidates):
        item = DiversityItem(
            id=candidate.get("id", f"item_{i}"),
            features=candidate.get("features", [0.0] * 10),
            diversity_key=candidate.get("diversity_key", "default"),
            metadata=candidate.get("metadata", {}),
        )
        items.append(item)

    # Create selector and select
    selector = SubmodularSelector(alpha=alpha, beta=beta)
    selection = selector.select_diverse_items(items, k)

    # Convert back to original format
    return [item.__dict__ for item in selection.selected_items]
