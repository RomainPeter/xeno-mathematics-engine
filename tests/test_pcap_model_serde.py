from __future__ import annotations
from pefc.pcap.model import PCAP, VVector, ProofSpec


def test_pcap_model_creation():
    """Test PCAP model creation."""
    v = VVector(time=1.0, audit_cost=0.5, extra={"custom": 0.3})
    proof = ProofSpec(type="test", args={"param": "value"}, expect={"result": True})
    pcap = PCAP(
        action="test.action",
        context_hash="abc123",
        obligations=["ob1", "ob2"],
        justification=v,
        proofs=[proof],
        meta={"key": "value"},
    )

    assert pcap.action == "test.action"
    assert pcap.context_hash == "abc123"
    assert pcap.obligations == ["ob1", "ob2"]
    assert pcap.justification.time == 1.0
    assert pcap.justification.audit_cost == 0.5
    assert pcap.justification.extra["custom"] == 0.3
    assert len(pcap.proofs) == 1
    assert pcap.proofs[0].type == "test"
    assert pcap.meta["key"] == "value"


def test_pcap_model_dump():
    """Test PCAP model serialization."""
    v = VVector(time=1.0, audit_cost=0.5)
    proof = ProofSpec(type="test", args={"param": "value"})
    pcap = PCAP(
        action="test.action",
        context_hash="abc123",
        justification=v,
        proofs=[proof],
    )

    data = pcap.model_dump()
    assert data["action"] == "test.action"
    assert data["context_hash"] == "abc123"
    assert data["justification"]["time"] == 1.0
    assert data["justification"]["audit_cost"] == 0.5
    assert len(data["proofs"]) == 1
    assert data["proofs"][0]["type"] == "test"


def test_pcap_model_dump_json():
    """Test PCAP model JSON serialization."""
    v = VVector(time=1.0, audit_cost=0.5)
    proof = ProofSpec(type="test", args={"param": "value"})
    pcap = PCAP(
        action="test.action",
        context_hash="abc123",
        justification=v,
        proofs=[proof],
    )

    json_str = pcap.model_dump_json()
    assert isinstance(json_str, str)
    assert "test.action" in json_str
    assert "abc123" in json_str


def test_pcap_model_parse():
    """Test PCAP model deserialization."""
    data = {
        "action": "test.action",
        "context_hash": "abc123",
        "obligations": ["ob1", "ob2"],
        "justification": {
            "time": 1.0,
            "audit_cost": 0.5,
            "extra": {"custom": 0.3},
        },
        "proofs": [
            {
                "type": "test",
                "args": {"param": "value"},
                "expect": {"result": True},
            }
        ],
        "meta": {"key": "value"},
    }

    pcap = PCAP.model_validate(data)
    assert pcap.action == "test.action"
    assert pcap.context_hash == "abc123"
    assert pcap.obligations == ["ob1", "ob2"]
    assert pcap.justification.time == 1.0
    assert pcap.justification.audit_cost == 0.5
    assert pcap.justification.extra["custom"] == 0.3
    assert len(pcap.proofs) == 1
    assert pcap.proofs[0].type == "test"
    assert pcap.proofs[0].args["param"] == "value"
    assert pcap.proofs[0].expect["result"] is True
    assert pcap.meta["key"] == "value"


def test_pcap_model_roundtrip():
    """Test PCAP model roundtrip serialization."""
    v = VVector(time=1.0, audit_cost=0.5, extra={"custom": 0.3})
    proof = ProofSpec(type="test", args={"param": "value"}, expect={"result": True})
    original = PCAP(
        action="test.action",
        context_hash="abc123",
        obligations=["ob1", "ob2"],
        justification=v,
        proofs=[proof],
        meta={"key": "value"},
    )

    # Serialize and deserialize
    data = original.model_dump()
    restored = PCAP.model_validate(data)

    assert restored.action == original.action
    assert restored.context_hash == original.context_hash
    assert restored.obligations == original.obligations
    assert restored.justification.time == original.justification.time
    assert restored.justification.audit_cost == original.justification.audit_cost
    assert restored.justification.extra == original.justification.extra
    assert len(restored.proofs) == len(original.proofs)
    assert restored.proofs[0].type == original.proofs[0].type
    assert restored.proofs[0].args == original.proofs[0].args
    assert restored.proofs[0].expect == original.proofs[0].expect
    assert restored.meta == original.meta


def test_vvector_defaults():
    """Test VVector with default values."""
    v = VVector()
    assert v.time is None
    assert v.audit_cost is None
    assert v.security_risk is None
    assert v.tech_debt is None
    assert v.extra == {}


def test_proofspec_defaults():
    """Test ProofSpec with default values."""
    proof = ProofSpec(type="test")
    assert proof.type == "test"
    assert proof.args == {}
    assert proof.expect == {}
