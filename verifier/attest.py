"""
Système d'attestation pour le Proof Engine for Code v0.
Gère la signature et la vérification des attestations.
"""

import hashlib
import json
import time
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from proofengine.core.schemas import Attestation


class AttestationManager:
    """Gestionnaire d'attestations avec signature."""

    def __init__(self, private_key_path: Optional[str] = None):
        """
        Initialise le gestionnaire d'attestations.

        Args:
            private_key_path: Chemin vers la clé privée (optionnel)
        """
        self.private_key = None
        self.public_key = None

        if private_key_path and os.path.exists(private_key_path):
            self._load_keys(private_key_path)
        else:
            self._generate_keys()

    def _load_keys(self, private_key_path: str) -> None:
        """Charge les clés depuis un fichier."""
        try:
            with open(private_key_path, "rb") as f:
                self.private_key = serialization.load_pem_private_key(f.read(), password=None)
            self.public_key = self.private_key.public_key()
        except Exception as e:
            print(f"Error loading keys: {e}")
            self._generate_keys()

    def _generate_keys(self) -> None:
        """Génère une nouvelle paire de clés."""
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

    def sign_attestation(self, attestation: Attestation) -> str:
        """
        Signe une attestation avec Ed25519.

        Args:
            attestation: Attestation à signer

        Returns:
            str: Signature en base64
        """
        if not self.private_key:
            return ""

        # Sérialiser l'attestation
        attestation_data = json.dumps(attestation.model_dump(), sort_keys=True)

        # Signer
        signature = self.private_key.sign(attestation_data.encode())

        # Encoder en base64
        import base64

        return base64.b64encode(signature).decode()

    def verify_attestation(self, attestation: Attestation, signature: str) -> bool:
        """
        Vérifie la signature d'une attestation.

        Args:
            attestation: Attestation à vérifier
            signature: Signature à vérifier

        Returns:
            bool: True si la signature est valide
        """
        if not self.public_key or not signature:
            return False

        try:
            # Sérialiser l'attestation
            attestation_data = json.dumps(attestation.model_dump(), sort_keys=True)

            # Décoder la signature
            import base64

            signature_bytes = base64.b64decode(signature)

            # Vérifier
            self.public_key.verify(signature_bytes, attestation_data.encode())
            return True

        except Exception:
            return False

    def create_attestation(self, pcap_count: int, verdicts: list, sign: bool = True) -> Attestation:
        """
        Crée une attestation complète.

        Args:
            pcap_count: Nombre de PCAPs
            verdicts: Liste des verdicts
            sign: Signer l'attestation

        Returns:
            Attestation: Attestation créée
        """
        # Créer l'attestation
        attestation = Attestation(
            ts=time.time(),
            pcap_count=pcap_count,
            verdicts=verdicts,
            digest=hashlib.sha256(json.dumps(verdicts, sort_keys=True).encode()).hexdigest(),
        )

        # Signer si demandé
        if sign and self.private_key:
            attestation.signature = self.sign_attestation(attestation)

        return attestation

    def save_keys(self, private_key_path: str, public_key_path: str) -> None:
        """
        Sauvegarde les clés dans des fichiers.

        Args:
            private_key_path: Chemin pour la clé privée
            public_key_path: Chemin pour la clé publique
        """
        if self.private_key:
            # Sauvegarder la clé privée
            private_pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            with open(private_key_path, "wb") as f:
                f.write(private_pem)

        if self.public_key:
            # Sauvegarder la clé publique
            public_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            with open(public_key_path, "wb") as f:
                f.write(public_pem)

    def get_public_key_pem(self) -> str:
        """Retourne la clé publique en format PEM."""
        if not self.public_key:
            return ""

        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return public_pem.decode()

    def verify_attestation_file(self, attestation_file: str) -> Dict[str, Any]:
        """
        Vérifie un fichier d'attestation.

        Args:
            attestation_file: Chemin du fichier d'attestation

        Returns:
            Dict[str, Any]: Résultats de la vérification
        """
        try:
            with open(attestation_file, "r") as f:
                data = json.load(f)

            attestation = Attestation(**data)

            # Vérifier la signature si présente
            signature_valid = True
            if attestation.signature:
                signature_valid = self.verify_attestation(attestation, attestation.signature)

            # Vérifier le digest
            expected_digest = hashlib.sha256(
                json.dumps(attestation.verdicts, sort_keys=True).encode()
            ).hexdigest()
            digest_valid = attestation.digest == expected_digest

            return {
                "valid": signature_valid and digest_valid,
                "signature_valid": signature_valid,
                "digest_valid": digest_valid,
                "attestation": attestation.model_dump(),
            }

        except Exception as e:
            return {"valid": False, "error": str(e), "attestation": None}


def create_simple_attestation(pcap_count: int, verdicts: list) -> Dict[str, Any]:
    """
    Crée une attestation simple sans signature.

    Args:
        pcap_count: Nombre de PCAPs
        verdicts: Liste des verdicts

    Returns:
        Dict[str, Any]: Attestation simple
    """
    return {
        "ts": time.time(),
        "pcap_count": pcap_count,
        "verdicts": verdicts,
        "digest": hashlib.sha256(json.dumps(verdicts, sort_keys=True).encode()).hexdigest(),
        "signature": None,
    }


def verify_attestation_integrity(attestation_data: Dict[str, Any]) -> bool:
    """
    Vérifie l'intégrité d'une attestation.

    Args:
        attestation_data: Données de l'attestation

    Returns:
        bool: True si l'attestation est intègre
    """
    try:
        # Vérifier les champs requis
        required_fields = ["ts", "pcap_count", "verdicts", "digest"]
        if not all(field in attestation_data for field in required_fields):
            return False

        # Vérifier le digest
        expected_digest = hashlib.sha256(
            json.dumps(attestation_data["verdicts"], sort_keys=True).encode()
        ).hexdigest()

        return attestation_data["digest"] == expected_digest

    except Exception:
        return False
