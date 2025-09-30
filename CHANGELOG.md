# Changelog

All notable changes to Discovery Engine 2-Cat will be documented in this file.

## [0.1.0] - 2024-12-19

### Added
- **Architecture unifiée v0.1** : Implémentation complète de l'architecture 2-catégorique
- **AE Next-Closure** : Exploration d'attributs avec boucles AE/CEGIS
- **E-graph canonicalization** : Anti-redondance structurelle avec témoins d'équivalence
- **PromptContract++** : Gouvernance des prompts avec contrats structurés
- **Sélection de politique** : Bandits contextuels + DPP pour la diversité
- **Demo RegTech** : Mini-benchmark RegTech/Code avec artefacts
- **Handlers d'incidents** : Transformation incident→règle avec mapping des raisons d'échec
- **CI/CD complet** : Installation OPA, attestations Cosign, journal Merkle
- **DomainSpec v0.1** : Spécification de domaine RegTech/Code
- **Journal Merkle** : Auditabilité complète avec hachage cryptographique

### Features
- **Exploration traçable** : DPP + e-graphs pour la non-redondance
- **PCAP/DCA appliqué** : Génération contrôlée avec validation
- **Antifragilité** : Incident→règle avec K↑ journalisé
- **Mesure unifiée V/δ** : Connectée aux incidents et à l'audit

### Technical Details
- **Langage** : Python 3.11+
- **Dépendances** : OPA, pytest, requirements.txt
- **CI/CD** : GitHub Actions avec workflows étendus
- **Sécurité** : Runner hermétique, SBOM, attestations

### Known Limitations
- **Déterminisme** : Variance V_actual peut dépasser 2% sur certains seeds
- **Performance** : Temps de réponse oracle peut varier selon la complexité
- **Couverture** : Exploration limitée aux domaines RegTech/Code v0.1
- **Scalabilité** : E-graph canonicalization O(n²) sur grandes structures

### Breaking Changes
- Aucune (première version)

### Migration Guide
- Installation : `make setup`
- Tests : `make test`
- Demo : `make demo`
- Bench : `make bench`

### Contributors
- Discovery Engine 2-Cat Team