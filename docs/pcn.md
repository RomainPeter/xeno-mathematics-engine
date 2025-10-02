# PCN - Proof-Carrying Notation

Le PCN (Proof-Carrying Notation) est un système de baptême contrôlé des symboles mathématiques avec preuves cryptographiques.

## 🎯 Vue d'ensemble

Le PCN permet de :
- **Baptiser** des symboles mathématiques avec des preuves
- **Vérifier** l'intégrité des symboles via des références de preuve
- **Contrôler** l'accès aux symboles via des embargos
- **Tracer** l'origine des symboles dans PCAP

## 📋 Format SymbolEntry

```python
class SymbolEntry(BaseModel):
    concept_id: str           # ID du concept (ex: "C42")
    symbol: str              # Symbole mathématique (ex: "Xi_1")
    version: int = 1         # Version du symbole
    proof_ref: Optional[str] # Référence de preuve (ex: "psp:proof123")
    created_at: str         # Timestamp de création
```

### Exemple

```json
{
  "concept_id": "C42",
  "symbol": "Xi_1",
  "version": 1,
  "proof_ref": "psp:proof123",
  "created_at": "2025-01-01T12:00:00Z"
}
```

## 🔐 Exigences de preuve

### Format des références de preuve

Les références de preuve suivent le format : `type:reference`

- **psp:proof123** : Preuve PSP avec ID "proof123"
- **pcap:run456** : Preuve PCAP avec run ID "run456"
- **merkle:hash789** : Preuve Merkle avec hash "hash789"

### Validation des preuves

```python
def validate_proof_ref(proof_ref: str) -> bool:
    """Valide le format d'une référence de preuve."""
    if not proof_ref:
        return False
    
    parts = proof_ref.split(":", 1)
    if len(parts) != 2:
        return False
    
    proof_type, reference = parts
    valid_types = ["psp", "pcap", "merkle", "signature"]
    
    return proof_type in valid_types and len(reference) > 0
```

## 🏗️ Symbol Store

### Structure des données

```json
{
  "symbols": [
    {
      "concept_id": "C42",
      "symbol": "Xi_1",
      "version": 1,
      "proof_ref": "psp:proof123",
      "created_at": "2025-01-01T12:00:00Z"
    }
  ]
}
```

### Opérations

```python
from xme.referee.pcn import SymbolStore

# Créer un store
store = SymbolStore(Path("artifacts/referee/symbols.json"))

# Proposer un symbole
entry = store.propose(
    concept_id="C42",
    symbol="Xi_1",
    proof_ref="psp:proof123"
)

# Lister les symboles
symbols = store.list()
for symbol in symbols:
    print(f"{symbol.symbol} -> {symbol.proof_ref}")
```

## 🚫 Contrôles d'accès

### Charset des symboles

Les symboles doivent respecter le charset : `^[A-Za-z0-9_]+$`

```python
import re

def is_valid_symbol(symbol: str) -> bool:
    """Vérifie si un symbole respecte le charset."""
    pattern = r"^[A-Za-z0-9_]+$"
    return bool(re.match(pattern, symbol))

# Exemples
assert is_valid_symbol("Xi_1")      # ✅ Valide
assert is_valid_symbol("alpha_2")   # ✅ Valide
assert not is_valid_symbol("Xi-1")  # ❌ Caractère invalide
assert not is_valid_symbol("Xi 1")  # ❌ Espace invalide
```

### Embargos

Les symboles ne peuvent être baptisés que si leur lineage n'est pas sous embargo :

```python
# Vérifier l'embargo
if reserve.is_embargoed(lineage_id):
    return {"ok": False, "reason": "embargoed"}

# Libérer l'embargo
reserve.release(lineage_id, "criteria met")
```

## 🔄 Workflow de baptême

### 1. Préparation

```bash
# Libérer le lineage de l'embargo
xme referee embargo-release --lineage X123 --reason "verification passed"
```

### 2. Baptême

```bash
# Baptiser le symbole
xme symbol baptize \
  --concept C42 \
  --symbol Xi_1 \
  --proof-ref "psp:proof123" \
  --lineage X123
```

### 3. Vérification

```bash
# Vérifier le statut
xme referee status
```

## 📊 Intégration PCAP

### Logging des baptêmes

```json
{
  "action": "symbol.baptize.accept",
  "obligations": {
    "pcn.proof_ref:exists": "true"
  },
  "psp_ref": "psp:proof123",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### Logging des refus

```json
{
  "action": "symbol.baptize.reject",
  "obligations": {
    "name.charset": "false"
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

## 🧪 Tests

### Test de baptême réussi

```python
def test_baptize_success():
    referee = Referee(cfg_path, reserve_path, symbols_path)
    
    # Libérer le lineage
    AlienReserve(reserve_path).release("X123", "init")
    
    # Baptiser
    verdict = referee.gate_baptism(
        lineage_id="X123",
        concept_id="C42",
        symbol="Xi_1",
        proof_ref="psp:proof123"
    )
    
    assert verdict["ok"]
    assert verdict["entry"]["symbol"] == "Xi_1"
```

### Test de refus d'embargo

```python
def test_baptize_embargoed():
    referee = Referee(cfg_path, reserve_path, symbols_path)
    
    # Mettre sous embargo
    AlienReserve(reserve_path).register("X123", {"area": "demo"})
    
    # Essayer de baptiser
    verdict = referee.gate_baptism(
        lineage_id="X123",
        concept_id="C42",
        symbol="Xi_1",
        proof_ref="psp:proof123"
    )
    
    assert not verdict["ok"]
    assert verdict["reason"] == "embargoed"
```

## 🔍 Dépannage

### Problèmes courants

1. **Symbole invalide** : Vérifier le charset (A-Za-z0-9_)
2. **Preuve manquante** : Fournir une référence de preuve valide
3. **Lineage sous embargo** : Libérer le lineage avec `embargo-release`
4. **Budget insuffisant** : Vérifier les quotas H/X

### Debug

```bash
# Voir tous les symboles
xme referee status | jq '.symbols'

# Vérifier les embargos
xme referee status | jq '.reserves'

# Tester un baptême
xme symbol baptize \
  --concept TEST \
  --symbol test_1 \
  --proof-ref "psp:test123" \
  --lineage XTEST
```

## 📚 Exemples d'usage

### Baptême en lot

```python
def batch_baptize(concepts, lineage_id, proof_refs):
    """Baptise plusieurs concepts en lot."""
    referee = Referee(cfg_path, reserve_path, symbols_path)
    
    results = []
    for concept, proof_ref in zip(concepts, proof_refs):
        verdict = referee.gate_baptism(
            lineage_id=lineage_id,
            concept_id=concept.id,
            symbol=concept.symbol,
            proof_ref=proof_ref
        )
        results.append(verdict)
    
    return results
```

### Vérification d'intégrité

```python
def verify_symbol_integrity(symbol_entry):
    """Vérifie l'intégrité d'un symbole."""
    if not symbol_entry.proof_ref:
        return False, "Missing proof reference"
    
    # Vérifier la preuve selon le type
    proof_type, reference = symbol_entry.proof_ref.split(":", 1)
    
    if proof_type == "psp":
        return verify_psp_proof(reference)
    elif proof_type == "pcap":
        return verify_pcap_proof(reference)
    else:
        return False, f"Unknown proof type: {proof_type}"
```
