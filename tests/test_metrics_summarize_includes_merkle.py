"""
Tests pour la synthèse des métriques incluant merkle_root et incidents.
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from xme.pcap.store import PCAPStore
from xme.pcap.model import PCAPEntry
from xme.metrics.summarize import summarize_run, summarize_multiple_runs, compare_summaries


def test_summarize_run_includes_merkle():
    """Test que le résumé inclut le merkle_root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_path = Path(tmpdir) / "test_run.jsonl"
        store = PCAPStore(run_path)
        
        # Ajouter des entrées avec merkle_root
        entry1 = PCAPEntry(
            action="test_action_1",
            actor="test",
            level="S0",
            obligations={},
            deltas={"delta_test": 0.5},
            timestamp=datetime.now(timezone.utc)
        )
        store.append(entry1)
        
        entry2 = PCAPEntry(
            action="merkle_computed",
            actor="test",
            level="S0",
            obligations={},
            deltas={"merkle_root": 0.3, "delta_merkle": 0.3},
            timestamp=datetime.now(timezone.utc)
        )
        store.append(entry2)
        
        # Générer le résumé
        summary = summarize_run(run_path)
        
        # Vérifier que merkle_root est inclus
        assert "merkle_root" in summary
        assert summary["merkle_root"] == 0.3  # Dernier merkle_root trouvé


def test_summarize_run_includes_incidents():
    """Test que le résumé inclut les incidents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_path = Path(tmpdir) / "test_run.jsonl"
        store = PCAPStore(run_path)
        
        # Ajouter des entrées normales
        entry1 = PCAPEntry(
            action="normal_action",
            actor="test",
            level="S0",
            obligations={},
            deltas={},
            timestamp=datetime.now(timezone.utc)
        )
        store.append(entry1)
        
        # Ajouter un incident (timeout)
        entry2 = PCAPEntry(
            action="ae_timeout",
            actor="test",
            level="S0",
            obligations={},
            deltas={},
            timestamp=datetime.now(timezone.utc)
        )
        store.append(entry2)
        
        # Ajouter un incident (verification failure)
        entry3 = PCAPEntry(
            action="verification_verdict",
            actor="test",
            level="S0",
            obligations={"psp_acyclic": "False"},
            deltas={},
            timestamp=datetime.now(timezone.utc)
        )
        store.append(entry3)
        
        # Ajouter un incident (error)
        entry4 = PCAPEntry(
            action="error_occurred",
            actor="test",
            level="S0",
            obligations={},
            deltas={},
            timestamp=datetime.now(timezone.utc)
        )
        store.append(entry4)
        
        # Générer le résumé
        summary = summarize_run(run_path)
        
        # Vérifier que les incidents sont inclus
        assert "incidents" in summary
        incidents = summary["incidents"]
        assert len(incidents) == 3  # 3 incidents détectés
        
        # Vérifier les types d'incidents
        incident_types = [incident["type"] for incident in incidents]
        assert "timeout" in incident_types
        assert "verification_failure" in incident_types
        assert "error" in incident_types
        
        # Vérifier la structure des incidents
        for incident in incidents:
            assert "timestamp" in incident
            assert "action" in incident
            assert "type" in incident
            assert "details" in incident


def test_summarize_run_includes_actions():
    """Test que le résumé inclut le comptage des actions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_path = Path(tmpdir) / "test_run.jsonl"
        store = PCAPStore(run_path)
        
        # Ajouter des actions variées
        actions = ["action1", "action2", "action1", "action3", "action2", "action2"]
        for i, action in enumerate(actions):
            entry = PCAPEntry(
                action=action,
                actor="test",
                level="S0",
                obligations={},
                deltas={},
                timestamp=datetime.now(timezone.utc)
            )
            store.append(entry)
        
        # Générer le résumé
        summary = summarize_run(run_path)
        
        # Vérifier le comptage des actions
        assert "actions" in summary
        actions_count = summary["actions"]
        assert actions_count["action1"] == 2
        assert actions_count["action2"] == 3
        assert actions_count["action3"] == 1


def test_summarize_run_includes_deltas():
    """Test que le résumé inclut les δ."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_path = Path(tmpdir) / "test_run.jsonl"
        store = PCAPStore(run_path)
        
        # Ajouter des entrées avec δ
        entry1 = PCAPEntry(
            action="ae_psp_emitted",
            actor="test",
            level="S0",
            obligations={},
            deltas={"delta_ae": 0.3, "delta_run": 0.2},
            timestamp=datetime.now(timezone.utc)
        )
        store.append(entry1)
        
        entry2 = PCAPEntry(
            action="cegis_start",
            actor="test",
            level="S0",
            obligations={},
            deltas={"delta_cegis": 0.5},
            timestamp=datetime.now(timezone.utc)
        )
        store.append(entry2)
        
        # Générer le résumé
        summary = summarize_run(run_path)
        
        # Vérifier que les δ sont inclus
        assert "deltas" in summary
        deltas = summary["deltas"]
        assert "delta_run" in deltas
        assert "deltas_by_phase" in deltas
        assert "phase_weights" in deltas
        
        # Vérifier que δ_run est borné
        assert 0.0 <= deltas["delta_run"] <= 1.0


def test_summarize_run_includes_performance():
    """Test que le résumé inclut les métriques de performance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_path = Path(tmpdir) / "test_run.jsonl"
        store = PCAPStore(run_path)
        
        # Ajouter des entrées
        for i in range(5):
            entry = PCAPEntry(
                action=f"action_{i}",
                actor="test",
                level="S0",
                obligations={},
                deltas={},
                timestamp=datetime.now(timezone.utc)
            )
            store.append(entry)
        
        # Ajouter un incident
        incident_entry = PCAPEntry(
            action="error_occurred",
            actor="test",
            level="S0",
            obligations={},
            deltas={},
            timestamp=datetime.now(timezone.utc)
        )
        store.append(incident_entry)
        
        # Générer le résumé
        summary = summarize_run(run_path)
        
        # Vérifier les métriques de performance
        assert "performance" in summary
        performance = summary["performance"]
        assert "total_actions" in performance
        assert "unique_actions" in performance
        assert "incident_rate" in performance
        assert "delta_run" in performance
        
        assert performance["total_actions"] == 6
        assert performance["unique_actions"] == 6
        assert performance["incident_rate"] == 1/6  # 1 incident sur 6 actions


def test_summarize_multiple_runs():
    """Test la synthèse de plusieurs runs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Créer plusieurs runs
        run_paths = []
        for i in range(3):
            run_path = Path(tmpdir) / f"run_{i}.jsonl"
            store = PCAPStore(run_path)
            
            # Ajouter des entrées avec δ différents
            entry = PCAPEntry(
                action="test_action",
                actor="test",
                level="S0",
                obligations={},
                deltas={"delta_run": 0.1 * (i + 1)},  # δ différents
                timestamp=datetime.now(timezone.utc)
            )
            store.append(entry)
            run_paths.append(run_path)
        
        # Générer le résumé agrégé
        summary = summarize_multiple_runs(run_paths)
        
        # Vérifier l'agrégation
        assert "runs_processed" in summary
        assert "total_entries" in summary
        assert "deltas" in summary
        
        assert summary["runs_processed"] == 3
        assert summary["total_entries"] == 3
        
        deltas = summary["deltas"]
        assert "average" in deltas
        assert "minimum" in deltas
        assert "maximum" in deltas
        assert "all_values" in deltas
        
        # Vérifier les bornes
        assert 0.0 <= deltas["average"] <= 1.0
        assert 0.0 <= deltas["minimum"] <= 1.0
        assert 0.0 <= deltas["maximum"] <= 1.0


def test_compare_summaries():
    """Test la comparaison de résumés."""
    summary1 = {
        "total_entries": 10,
        "incidents": [{"type": "error"}],
        "deltas": {"delta_run": 0.3}
    }
    
    summary2 = {
        "total_entries": 15,
        "incidents": [{"type": "error"}, {"type": "timeout"}],
        "deltas": {"delta_run": 0.1}
    }
    
    comparison = compare_summaries(summary1, summary2)
    
    # Vérifier la structure de comparaison
    assert "delta_comparison" in comparison
    assert "entries_comparison" in comparison
    assert "incidents_comparison" in comparison
    assert "summary" in comparison
    
    # Vérifier les comparaisons
    delta_comp = comparison["delta_comparison"]
    assert delta_comp["summary1"] == 0.3
    assert delta_comp["summary2"] == 0.1
    assert abs(delta_comp["difference"] - (-0.2)) < 0.001
    assert delta_comp["improvement"] == True  # 0.3 > 0.1, donc amélioration
    
    entries_comp = comparison["entries_comparison"]
    assert entries_comp["summary1"] == 10
    assert entries_comp["summary2"] == 15
    assert entries_comp["difference"] == 5
    
    incidents_comp = comparison["incidents_comparison"]
    assert incidents_comp["summary1"] == 1
    assert incidents_comp["summary2"] == 2
    assert incidents_comp["difference"] == 1


def test_summarize_run_empty():
    """Test la synthèse d'un run vide."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_path = Path(tmpdir) / "empty_run.jsonl"
        store = PCAPStore(run_path)
        
        # Générer le résumé d'un run vide
        summary = summarize_run(run_path)
        
        # Vérifier la structure pour un run vide
        assert "run_path" in summary
        assert "total_entries" in summary
        assert "actions" in summary
        assert "incidents" in summary
        assert "deltas" in summary
        assert "merkle_root" in summary
        assert "summary" in summary
        
        assert summary["total_entries"] == 0
        assert summary["actions"] == {}
        assert summary["incidents"] == []
        assert summary["merkle_root"] is None
        assert "Empty run" in summary["summary"]


def test_summarize_run_error_handling():
    """Test la gestion d'erreur dans la synthèse."""
    # Tester avec un fichier inexistant
    fake_path = Path("nonexistent_run.jsonl")
    summary = summarize_run(fake_path)
    
    # Vérifier que l'erreur est gérée
    assert "error" in summary or "Empty run" in summary["summary"] or "Error processing run" in summary["summary"]
