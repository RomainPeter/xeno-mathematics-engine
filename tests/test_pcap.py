"""
Tests pour le système PCAP.
"""

import pytest
import json
import os
import tempfile
import shutil
from proofengine.core.schemas import PCAP, VJustification
from proofengine.core.pcap import now_iso, merkle_of, write_pcap, read_pcap, list_pcaps, verify_pcap_chain


class TestPCAPSchemas:
    """Tests pour les schémas PCAP."""
    
    def test_vjustification_creation(self):
        """Test de création d'une VJustification."""
        justification = VJustification(
            time_ms=1000,
            backtracks=2,
            audit_cost_ms=500,
            tech_debt=1,
            llm_time_ms=800,
            model="grok-2-fast"
        )
        
        assert justification.time_ms == 1000
        assert justification.backtracks == 2
        assert justification.audit_cost_ms == 500
        assert justification.tech_debt == 1
        assert justification.llm_time_ms == 800
        assert justification.model == "grok-2-fast"
    
    def test_pcap_creation(self):
        """Test de création d'un PCAP."""
        justification = VJustification(time_ms=1000)
        
        pcap = PCAP(
            ts="2024-01-01T00:00:00Z",
            operator="plan",
            case_id="test_case",
            pre={"state": "initial"},
            post={"state": "planned"},
            obligations=["tests_ok", "lint_ok"],
            justification=justification,
            proof_state_hash="abc123",
            toolchain={"python": "3.11"},
            verdict="pass"
        )
        
        assert pcap.ts == "2024-01-01T00:00:00Z"
        assert pcap.operator == "plan"
        assert pcap.case_id == "test_case"
        assert pcap.verdict == "pass"
        assert len(pcap.obligations) == 2
    
    def test_pcap_validation(self):
        """Test de validation d'un PCAP."""
        # PCAP valide
        justification = VJustification(time_ms=1000)
        pcap = PCAP(
            ts="2024-01-01T00:00:00Z",
            operator="plan",
            case_id="test_case",
            pre={},
            post={},
            obligations=[],
            justification=justification,
            proof_state_hash="abc123",
            toolchain={}
        )
        
        assert pcap.model_validate(pcap.model_dump()) == pcap
        
        # PCAP avec verdict
        pcap_with_verdict = pcap.model_copy(update={"verdict": "pass"})
        assert pcap_with_verdict.verdict == "pass"


class TestPCAPUtils:
    """Tests pour les utilitaires PCAP."""
    
    def test_now_iso(self):
        """Test de génération du timestamp ISO."""
        timestamp = now_iso()
        assert isinstance(timestamp, str)
        assert "T" in timestamp
        assert timestamp.endswith("Z")
    
    def test_merkle_of(self):
        """Test de calcul du hash Merkle."""
        obj1 = {"a": 1, "b": 2}
        obj2 = {"b": 2, "a": 1}  # Même contenu, ordre différent
        
        hash1 = merkle_of(obj1)
        hash2 = merkle_of(obj2)
        
        assert hash1 == hash2  # Hash indépendant de l'ordre
        assert len(hash1) == 64  # SHA256 hex
        
        # Test avec des objets différents
        obj3 = {"a": 1, "b": 3}
        hash3 = merkle_of(obj3)
        assert hash1 != hash3
    
    def test_write_read_pcap(self):
        """Test d'écriture et lecture d'un PCAP."""
        with tempfile.TemporaryDirectory() as temp_dir:
            justification = VJustification(time_ms=1000)
            pcap = PCAP(
                ts="2024-01-01T00:00:00Z",
                operator="plan",
                case_id="test_case",
                pre={"state": "initial"},
                post={"state": "planned"},
                obligations=["tests_ok"],
                justification=justification,
                proof_state_hash="abc123",
                toolchain={"python": "3.11"},
                verdict="pass"
            )
            
            # Écrire le PCAP
            filepath = write_pcap(pcap, temp_dir)
            assert os.path.exists(filepath)
            assert filepath.endswith('.json')
            
            # Lire le PCAP
            read_pcap_obj = read_pcap(filepath)
            assert read_pcap_obj.ts == pcap.ts
            assert read_pcap_obj.operator == pcap.operator
            assert read_pcap_obj.case_id == pcap.case_id
            assert read_pcap_obj.verdict == pcap.verdict
    
    def test_list_pcaps(self):
        """Test de liste des PCAPs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Créer des fichiers de test
            test_files = [
                "1234567890_abc123.json",
                "1234567891_def456.json",
                "not_a_pcap.txt"
            ]
            
            for filename in test_files:
                with open(os.path.join(temp_dir, filename), 'w') as f:
                    f.write('{"test": "data"}')
            
            pcap_files = list_pcaps(temp_dir)
            assert len(pcap_files) == 2
            assert all(f.endswith('.json') for f in pcap_files)
            assert all('abc123' in f or 'def456' in f for f in pcap_files)
    
    def test_verify_pcap_chain_empty(self):
        """Test de vérification d'une chaîne vide."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = verify_pcap_chain(temp_dir)
            assert result["status"] == "empty"
            assert result["count"] == 0
    
    def test_verify_pcap_chain_valid(self):
        """Test de vérification d'une chaîne valide."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Créer des PCAPs valides
            justification = VJustification(time_ms=1000)
            pcap1 = PCAP(
                ts="2024-01-01T00:00:00Z",
                operator="plan",
                case_id="test_case",
                pre={},
                post={},
                obligations=[],
                justification=justification,
                proof_state_hash="abc123",
                toolchain={}
            )
            
            pcap2 = PCAP(
                ts="2024-01-01T00:01:00Z",
                operator="verify",
                case_id="test_case",
                pre={},
                post={},
                obligations=[],
                justification=justification,
                proof_state_hash="def456",
                toolchain={}
            )
            
            # Écrire les PCAPs
            write_pcap(pcap1, temp_dir)
            write_pcap(pcap2, temp_dir)
            
            # Vérifier la chaîne
            result = verify_pcap_chain(temp_dir)
            assert result["status"] == "ok"
            assert result["count"] == 2
            assert len(result["files"]) == 2
    
    def test_verify_pcap_chain_invalid(self):
        """Test de vérification d'une chaîne invalide."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Créer un fichier JSON invalide
            invalid_file = os.path.join(temp_dir, "invalid.json")
            with open(invalid_file, 'w') as f:
                f.write('{"invalid": "json"')
            
            result = verify_pcap_chain(temp_dir)
            assert result["status"] == "error"
            assert len(result["errors"]) > 0


class TestPCAPIntegration:
    """Tests d'intégration pour le système PCAP."""
    
    def test_full_pcap_workflow(self):
        """Test du workflow complet PCAP."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Créer une séquence de PCAPs
            justification = VJustification(time_ms=1000, backtracks=0)
            
            # PCAP 1: Planification
            pcap1 = PCAP(
                ts="2024-01-01T00:00:00Z",
                operator="plan",
                case_id="test_case",
                pre={"state": "initial"},
                post={"plan": ["step1", "step2"]},
                obligations=["tests_ok"],
                justification=justification,
                proof_state_hash="abc123",
                toolchain={"python": "3.11"},
                verdict="pass"
            )
            
            # PCAP 2: Génération
            pcap2 = PCAP(
                ts="2024-01-01T00:01:00Z",
                operator="generate",
                case_id="test_case",
                pre={"plan": ["step1", "step2"]},
                post={"patch": "diff content"},
                obligations=["tests_ok"],
                justification=justification,
                proof_state_hash="def456",
                toolchain={"python": "3.11"},
                verdict="pass"
            )
            
            # PCAP 3: Vérification
            pcap3 = PCAP(
                ts="2024-01-01T00:02:00Z",
                operator="verify",
                case_id="test_case",
                pre={"patch": "diff content"},
                post={"result": "success"},
                obligations=["tests_ok"],
                justification=justification,
                proof_state_hash="ghi789",
                toolchain={"python": "3.11"},
                verdict="pass"
            )
            
            # Écrire tous les PCAPs
            file1 = write_pcap(pcap1, temp_dir)
            file2 = write_pcap(pcap2, temp_dir)
            file3 = write_pcap(pcap3, temp_dir)
            
            # Vérifier que tous les fichiers existent
            assert os.path.exists(file1)
            assert os.path.exists(file2)
            assert os.path.exists(file3)
            
            # Lister les PCAPs
            pcap_files = list_pcaps(temp_dir)
            assert len(pcap_files) == 3
            
            # Vérifier la chaîne
            chain_result = verify_pcap_chain(temp_dir)
            assert chain_result["status"] == "ok"
            assert chain_result["count"] == 3
            
            # Lire et vérifier chaque PCAP
            for pcap_file in pcap_files:
                read_pcap_obj = read_pcap(pcap_file)
                assert read_pcap_obj.case_id == "test_case"
                assert read_pcap_obj.verdict == "pass"
    
    def test_pcap_serialization(self):
        """Test de sérialisation/désérialisation des PCAPs."""
        justification = VJustification(time_ms=1000)
        pcap = PCAP(
            ts="2024-01-01T00:00:00Z",
            operator="plan",
            case_id="test_case",
            pre={"state": "initial"},
            post={"state": "planned"},
            obligations=["tests_ok"],
            justification=justification,
            proof_state_hash="abc123",
            toolchain={"python": "3.11"},
            verdict="pass"
        )
        
        # Sérialiser en JSON
        json_str = pcap.model_dump_json()
        assert isinstance(json_str, str)
        
        # Désérialiser depuis JSON
        pcap_dict = json.loads(json_str)
        pcap_from_json = PCAP.model_validate(pcap_dict)
        
        assert pcap_from_json.ts == pcap.ts
        assert pcap_from_json.operator == pcap.operator
        assert pcap_from_json.case_id == pcap.case_id
        assert pcap_from_json.verdict == pcap.verdict


if __name__ == "__main__":
    pytest.main([__file__])
