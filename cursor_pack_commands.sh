#!/usr/bin/env bash
# Cursor Pack - Commandes immédiates à exécuter

echo "🚀 Cursor Pack - Exécution des commandes immédiates"

# 1) Définir la variable repo
export REPO=RomainPeter/discovery-engine-2cat
echo "✅ REPO défini: $REPO"

# 2) Protéger main (required checks + CODEOWNERS)
echo "🔒 Configuration de la protection de branche..."
bash scripts/protect_main.sh
echo "✅ Protection de branche configurée"

# 3) Lancer un Nightly Bench manuel
echo "🌙 Lancement du Nightly Bench manuel..."
gh workflow run "Nightly Bench"
echo "✅ Nightly Bench lancé"

# 4) Déclencher le fire-drill Incident→Rule
echo "🔥 Fire-drill Incident→Rule..."
make fire-drill
echo "✅ Fire-drill terminé"

# 5) Lancer le sweep IDS/CVaR et publier les defaults
echo "📊 Sweep IDS/CVaR..."
make sweep-ids-cvar
echo "✅ Sweep IDS/CVaR terminé"

echo "🎉 Cursor Pack exécuté avec succès !"
echo ""
echo "📋 Prochaines étapes:"
echo "1. Vérifier que les workflows sont visibles dans Branch Protection"
echo "2. Créer une PR de test pour valider Gate Merge"
echo "3. Vérifier les artifacts générés dans out/"
echo "4. Consulter les métriques dans out/sweep_ids_cvar.json"
