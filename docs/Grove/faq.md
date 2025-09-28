# Discovery Engine 2‑Cat — FAQ

## Général

### Q: Qu'est-ce que Discovery Engine 2‑Cat ?
**R:** Discovery Engine 2‑Cat est un moteur de preuve pour le code génératif, basé sur la théorie des 2‑catégories et l'architecture PCAP/DCA. Il garantit que le code généré par les LLMs est non seulement syntaxiquement correct, mais aussi logiquement sound et conforme aux exigences réglementaires.

### Q: En quoi est-ce différent des systèmes de preuve traditionnels ?
**R:** Contrairement aux systèmes de preuve traditionnels qui sont rigides et manuels, Discovery Engine 2‑Cat est conçu pour travailler avec la nature stochastique des LLMs tout en maintenant des garanties déterministes. Il combine exploration non‑redondante, preuve portée par l'action, et apprentissage antifragile.

### Q: Qu'est-ce que la théorie des 2‑catégories apporte ?
**R:** La théorie des 2‑catégories fournit le fondement mathématique pour le raisonnement compositionnel sur des systèmes complexes. Elle permet de combiner de manière cohérente différentes opérations (Normalize, Verify, Meet) tout en maintenant les propriétés de cohérence.

## Technique

### Q: Comment fonctionne l'exploration non‑redondante ?
**R:** L'exploration non‑redondante est garantie par construction grâce aux e‑graphs et à la politique DPP (Diversity-Preserving Policy). Les e‑graphs maintiennent des classes d'équivalence, évitant la redondance, tandis que DPP assure que chaque exploration apporte de la nouveauté mesurable.

### Q: Qu'est-ce que PCAP/DCA ?
**R:** PCAP/DCA (Proof-Carrying Action/Deterministic Control Architecture) applique les principes de preuve formelle à la génération de code. Chaque action porte sa preuve, et l'architecture de contrôle déterministe garantit la cohérence globale.

### Q: Comment l'antifragilité fonctionne-t-elle ?
**R:** L'antifragilité se manifeste par le mécanisme incident→règle : chaque incident (violation de contrainte, timeout, etc.) génère automatiquement des règles qui enrichissent la base de connaissances K et améliorent la robustesse du système.

### Q: Qu'est-ce que la mesure V/δ ?
**R:** La variance V et l'effort δ sont des métriques quantifiées qui relient directement l'effort d'audit et le nombre d'incidents. V mesure la variabilité des résultats, δ mesure l'effort computationnel, et leur rapport indique l'efficacité du système.

## Performance

### Q: Quels sont les résultats de performance ?
**R:** Notre v0.1.0 démontre :
- **Coverage gain** : +20% vs baseline
- **Novelty average** : +22% vs baseline
- **Audit cost p95** : -15% vs baseline
- **Déterminisme** : 3 runs avec mêmes seeds → Merkle identique

### Q: Comment la reproductibilité est-elle garantie ?
**R:** La reproductibilité est garantie par :
- **Seeds déterministes** : Même graine → même résultat
- **Merkle attestation** : Preuve cryptographique de l'intégrité
- **SBOM** : Software Bill of Materials avec 0 vulnérabilités High/Critical
- **Bench Pack** : Suite de benchmark complète avec instructions de reproduction

### Q: Qu'est-ce que le Bench Pack ?
**R:** Le Bench Pack est un package public contenant :
- **summary.json** : Métriques agrégées
- **seeds** : Graines déterministes pour reproduction
- **merkle.txt** : Hash Merkle pour vérification d'intégrité
- **sbom.json** : Software Bill of Materials
- **reproduce.md** : Instructions de reproduction

## Intégration

### Q: Comment intégrer Discovery Engine 2‑Cat ?
**R:** L'intégration se fait en 4 étapes :
1. **Configuration** : Définir les contraintes et politiques
2. **Déploiement** : Intégrer dans le pipeline CI/CD
3. **Calibration** : Ajuster les budgets et timeouts
4. **Monitoring** : Surveiller les métriques et incidents

### Q: Quels sont les prérequis techniques ?
**R:** Les prérequis incluent :
- **Python 3.11+** : Runtime principal
- **Docker** : Pour l'environnement hermétique
- **SMT Solver** : Pour la vérification formelle
- **OPA** : Pour les politiques de compliance

### Q: Comment gérer les coûts computationnels ?
**R:** Les coûts sont optimisés par :
- **IDS/CVaR** : Optimisation information-théorique
- **Budget calibration** : Ajustement automatique des budgets
- **Parallel processing** : Traitement parallèle des vérifications
- **Caching** : Mise en cache des résultats de vérification

## Sécurité

### Q: Comment la sécurité est-elle garantie ?
**R:** La sécurité est garantie par :
- **SBOM** : Inventaire complet des dépendances
- **Vulnerability scanning** : Scan automatique des vulnérabilités
- **Hermetic runner** : Environnement isolé et déterministe
- **Cryptographic attestation** : Preuve cryptographique de l'intégrité

### Q: Qu'est-ce que l'environnement hermétique ?
**R:** L'environnement hermétique est un conteneur Docker isolé qui :
- **Fige les dépendances** : Versions exactes et vérifiées
- **Contrôle l'environnement** : Variables d'environnement déterministes
- **Garantit la reproductibilité** : Même environnement → même résultat
- **Assure la sécurité** : Isolation des processus et des données

## Business

### Q: Quel est le ROI attendu ?
**R:** Le ROI se manifeste par :
- **Réduction des coûts d'audit** : -15% du temps d'audit
- **Amélioration de la qualité** : +20% de couverture, +22% de nouveauté
- **Conformité réglementaire** : Preuves formelles pour les auditeurs
- **Time to market** : Déploiement plus rapide des systèmes conformes

### Q: Comment mesurer le succès ?
**R:** Les métriques de succès incluent :
- **Métriques techniques** : Coverage, novelty, audit cost
- **Métriques business** : ROI, compliance, time to market
- **Métriques utilisateur** : Satisfaction, adoption, retention

### Q: Quels sont les cas d'usage prioritaires ?
**R:** Les cas d'usage prioritaires sont :
- **Financial Services** : Algorithmes de trading conformes
- **Healthcare** : Systèmes d'IA médicaux audités
- **Legal Tech** : Automatisation de la compliance
- **Enterprise** : Systèmes d'IA d'entreprise avec garanties formelles

## Support

### Q: Comment obtenir du support ?
**R:** Le support est disponible via :
- **Documentation** : [Site officiel](https://your-org.github.io/discovery-engine-2cat/)
- **GitHub Issues** : [Issues GitHub](https://github.com/your-org/discovery-engine-2cat/issues)
- **Email** : [contact@your-org.com](mailto:contact@your-org.com)
- **Pilot Program** : Support dédié pour les pilotes

### Q: Qu'est-ce que le programme pilote ?
**R:** Le programme pilote est une évaluation de 4 semaines :
- **Semaine 1** : Intégration et configuration
- **Semaine 2** : Tests sur corpus RegTech
- **Semaine 3** : Optimisation et calibration
- **Semaine 4** : Rapport et recommandations

### Q: Comment participer au programme Grove ?
**R:** Pour participer au programme Grove :
1. **Soumettre l'application** : Formulaire Grove
2. **Démontrer l'impact** : Résultats quantifiés
3. **Proposer la collaboration** : Co‑développement du standard
4. **Engager les partenaires** : Pilotes et validation

---

*Discovery Engine 2‑Cat — Manufacturing proof for generative reasoning in code*
