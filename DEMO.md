# 🚀 ProofEngine - Démonstration

## ✅ **Installation Réussie !**

Votre environnement ProofEngine est maintenant opérationnel avec :

- ✅ **LLM Integration** : OpenRouter + Grok 4 Fast
- ✅ **Cache Local** : Réponses LLM mises en cache
- ✅ **CLI Fonctionnel** : Commandes ping, plan, actions
- ✅ **JSON Strict** : Sorties LLM en JSON valide
- ✅ **Retry Logic** : Gestion des erreurs avec tenacity

## 🎯 **Commandes Disponibles**

### **Windows (PowerShell)**
```powershell
# Aide
.\run.ps1 help

# Test de connectivité
.\run.ps1 llm-ping

# Planification métacognitive
.\run.ps1 plan "Créer une fonction de validation d'email"

# Génération d'actions stochastiques
.\run.ps1 actions "Implémenter un rate limiter"
```

### **Linux/Mac (Make)**
```bash
# Test de connectivité
make llm-ping

# Planification métacognitive
make plan GOAL="Créer une fonction de validation d'email"

# Génération d'actions stochastiques
make actions TASK="Implémenter un rate limiter"
```

## 📊 **Résultats de Test**

### **1. Ping LLM** ✅
```json
{
    "ok": true,
    "ping": {
        "data": {"ok": true, "model": "GPT-4"},
        "meta": {
            "model": "x-ai/grok-4-fast:free",
            "latency_ms": 3314,
            "cache_hit": true
        }
    }
}
```

### **2. Plan Métacognitif** ✅
```json
{
  "plan": [
    "define_function_skeleton",
    "implement_regex_validation", 
    "add_basic_tests"
  ],
  "est_success": 0.95,
  "est_cost": 15,
  "notes": "Start with skeleton for structure..."
}
```

### **3. Actions Stochastiques** ✅
```json
[
  {
    "proposal": {
      "patch_unified": "--- /dev/null\n+++ utils.py\n@@ -0,0 +1,9 @@\n+import re\n+\n+def validate_email(email: str) -> bool:\n+    \"\"\"\n+    Validate an email address using a basic regex pattern.\n+    \"\"\"\n+    pattern = r'^+@+\\.{2,}$'\n+    return bool(re.match(pattern, email))\n+",
      "rationale": "Creates a new email validation function...",
      "risk_score": 0.1
    }
  }
]
```

## 🗂️ **Structure du Projet**

```
proof-engine-for-code/
├── .env                          # Configuration (clé API)
├── requirements.txt              # Dépendances Python
├── run.ps1                      # Script PowerShell (Windows)
├── Makefile                     # Commandes Make (Linux/Mac)
├── proofengine/
│   ├── core/
│   │   └── llm_client.py        # Client OpenRouter + cache
│   ├── planner/
│   │   ├── prompts.py           # Prompts planificateur
│   │   └── meta.py              # Planification métacognitive
│   ├── generator/
│   │   ├── prompts.py           # Prompts générateur
│   │   └── stochastic.py        # Génération stochastique
│   ├── runner/
│   │   └── cli.py               # Interface CLI
│   └── out/
│       └── llm_cache/           # Cache des réponses LLM
└── README.md                    # Documentation
```

## 🔧 **Configuration**

### **Variables d'Environnement (.env)**
```bash
OPENROUTER_API_KEY=sk-or-votre-cle
OPENROUTER_MODEL=x-ai/grok-4-fast:free
HTTP_REFERER=https://github.com/votre/repo
X_TITLE=ProofEngine Demo
OPENROUTER_TIMEOUT_SECS=60
```

### **Cache Local**
- **Emplacement** : `proofengine/out/llm_cache/`
- **Format** : JSON avec métadonnées
- **Avantage** : Reproductibilité et économie d'API

## 🎯 **Prochaines Étapes**

1. **Développement** : Ajouter les composants de validation déterministe
2. **PCAP** : Implémenter les Proof-Carrying Actions
3. **Rollback** : Mécanisme de retour arrière
4. **Métriques** : Calcul de la métrique δ (defect)
5. **Démo** : Cas d'usage complets avec rollback/replan

## 🏆 **Critères d'Acceptation - PHASE 1 ✅**

- ✅ `make llm-ping` retourne `ok:true`
- ✅ `make plan` retourne du JSON valide
- ✅ `make actions` retourne du JSON valide  
- ✅ Cache local créé et réutilisé
- ✅ Intégration OpenRouter + Grok 4 Fast fonctionnelle
- ✅ CLI minimal avec Typer
- ✅ Gestion d'erreurs et retry logic

**🎉 Phase 1 terminée avec succès !**
