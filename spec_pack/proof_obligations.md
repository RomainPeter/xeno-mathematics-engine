- PO-1 Minimalité
  Statement: "L’algorithme Evidence Selector produit un hitting-set minimal pour tout ensemble d’attributs."
  Method: "Preuve constructive + property-based tests + contre-exemples stockés"
  DependsOn: ["O-1","I-6","P-1","P-5"]
- PO-2 Monotonicité
  Statement: "Le meet contraint toujours l’extension (jamais élargit)."
  Method: "Preuve par ordre galoisien + tests de régression"
  DependsOn: ["I-1","P-1","P-5"]
- PO-3 Traçabilité bornée
  Statement: "Tout chemin de justification est ≤ K=10."
  Method: "Analyse de profondeur + vérifieur v_trace_bound"
  DependsOn: ["O-4","I-5","P-2","P-5"]
- PO-4 Append-only
  Statement: "Le journal est WORM; toute suppression est détectable."
  Method: "Merkle proofs + audit aléatoire"
  DependsOn: ["O-2","I-7","P-2","P-3"]
- PO-5 Déterminisme
  Statement: "Les opérateurs de requête sont déterministes."
  Method: "Runs répétés, stdev==0"
  DependsOn: ["O-6","I-3","P-1"]
- PO-6 Reversibilité mapping
  Statement: "Les mappings std↔obligations sont réversibles localement."
  Method: "Tests biunivoques sur échantillons"
  DependsOn: ["I-4","P-4"]
- PO-7 Audit 24h
  Statement: "Reconstruction complète < 24h sans réseau."
  Method: "Dry run sur 10 décisions; mesure temps"
  DependsOn: ["O-3","P-2","P-5"]
- PO-8 Non-réductibilité
  Statement: "Aucun homomorphisme vers RAG vectoriel ne conserve minimalité + traçabilité bornée sans réintroduire meet/closure."
  Method: "Module P-7 + argument formel"
  DependsOn: ["I-8","P-7"]
- PO-9 Deny-with-proof
  Statement: "Toute requête hors-scope est refusée avec preuve minimale."
  Method: "Tests noirs adversariaux"
  DependsOn: ["O-8","P-5"]
- PO-10 Réduction coût audit
  Statement: "Coût d’audit réduit de ≥ 30% vs baseline."
  Method: "Mesure avant/après sur cas représentatif"
  DependsOn: ["O-11"]
