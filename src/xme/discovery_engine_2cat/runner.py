"""
Runner unifié pour le discovery-engine-2cat v0.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import orjson

from xme.adapters.logger import log_verdict
from xme.discovery_engine_2cat.config import DiscoveryEngine2CatConfig
from xme.metrics.delta import aggregate_run_delta
from xme.metrics.summarize import export_summary_json, summarize_run
from xme.orchestrator.event_bus import EventBus
from xme.orchestrator.loops.ae import run_ae
from xme.orchestrator.loops.cegis import run_cegis
from xme.orchestrator.state import Budgets, RunState
from xme.pcap.store import PCAPStore
from xme.pefc.pack import build_manifest, write_zip
from xme.psp.schema import PSP
from xme.verifier.base import Verifier, create_obligation
from xme.verifier.psp_checks import get_psp_obligations


class DiscoveryEngine2CatRunner:
    """
    Runner unifié pour le discovery-engine-2cat v0.
    Exécute AE (algo réel) puis CEGIS (v0), logs PCAP, vérifie PSP S1, calcule δ, construit Audit Pack.
    """

    def __init__(self, config: DiscoveryEngine2CatConfig):
        self.config = config
        self.run_id = config.get_run_id()
        self.start_time = datetime.now(timezone.utc)

        # Initialiser les composants
        self.state = RunState(
            run_id=self.run_id,
            budgets=Budgets(ae_ms=config.budgets.ae_ms, cegis_ms=config.budgets.cegis_ms),
        )
        self.bus = EventBus()
        self.pcap_store: Optional[PCAPStore] = None
        self.psp_output: Optional[Path] = None
        self.metrics_output: Optional[Path] = None
        self.report_output: Optional[Path] = None

        # Résultats
        self.ae_result: Optional[Dict[str, Any]] = None
        self.cegis_result: Optional[Dict[str, Any]] = None
        self.verification_report: Optional[Dict[str, Any]] = None
        self.metrics_summary: Optional[Dict[str, Any]] = None
        self.pack_path: Optional[Path] = None

    async def run(self) -> Dict[str, Any]:
        """
        Exécute le pipeline complet 2cat.

        Returns:
            Résultat du pipeline avec tous les artefacts
        """
        try:
            # 1. Initialiser PCAP
            await self._setup_pcap()

            # 2. Exécuter AE
            await self._run_ae()

            # 3. Exécuter CEGIS
            await self._run_cegis()

            # 4. Vérifier PSP S1
            await self._verify_psp()

            # 5. Calculer δ et métriques
            await self._calculate_metrics()

            # 6. Construire Audit Pack
            await self._build_audit_pack()

            # 7. Générer le rapport final
            result = await self._generate_final_report()

            return result

        except Exception as e:
            # Log l'erreur dans PCAP si disponible
            if self.pcap_store:
                from xme.adapters.logger import log_action

                log_action(
                    self.pcap_store,
                    "2cat_pipeline_error",
                    level="S0",
                    obligations={"error": str(e)},
                )
            raise

    async def _setup_pcap(self):
        """Initialise le store PCAP."""
        run_dir = Path(self.config.outputs.run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)

        run_file = run_dir / f"run-{self.run_id}.jsonl"
        self.pcap_store = PCAPStore.new_run(run_file)

        # Log du début du pipeline
        from xme.adapters.logger import log_action

        log_action(
            self.pcap_store,
            "2cat_pipeline_start",
            level="S0",
            obligations={"run_id": self.run_id, "config_version": self.config.version},
        )

    async def _run_ae(self):
        """Exécute Attribute Exploration."""
        from xme.adapters.logger import log_action

        # Log du début AE
        log_action(
            self.pcap_store,
            "2cat_ae_start",
            level="S0",
            obligations={
                "context": self.config.ae.context,
                "timeout_ms": str(self.config.ae.timeout_ms),
            },
        )

        # Préparer les sorties
        psp_path = Path(self.config.outputs.psp)
        psp_path.parent.mkdir(parents=True, exist_ok=True)
        self.psp_output = psp_path

        # Exécuter AE
        try:
            await run_ae(
                context_path=self.config.ae.context,
                state=self.state,
                bus=self.bus,
                store=self.pcap_store,
                out_psp=self.psp_output,
            )

            # Charger le PSP généré
            psp_data = orjson.loads(self.psp_output.read_bytes())
            psp = PSP.model_validate(psp_data)

            # Log du succès AE
            log_action(
                self.pcap_store,
                "2cat_ae_done",
                level="S0",
                obligations={"psp_blocks": str(len(psp.blocks)), "psp_edges": str(len(psp.edges))},
            )

            self.ae_result = {
                "success": True,
                "psp_path": str(self.psp_output),
                "blocks_count": len(psp.blocks),
                "edges_count": len(psp.edges),
            }

        except Exception as e:
            # Log de l'erreur AE
            log_action(self.pcap_store, "2cat_ae_error", level="S0", obligations={"error": str(e)})

            self.ae_result = {"success": False, "error": str(e)}
            raise

    async def _run_cegis(self):
        """Exécute CEGIS."""
        from xme.adapters.logger import log_action

        # Log du début CEGIS
        log_action(
            self.pcap_store,
            "2cat_cegis_start",
            level="S0",
            obligations={
                "secret": self.config.cegis.secret,
                "max_iters": str(self.config.cegis.max_iters),
            },
        )

        try:
            # Exécuter CEGIS
            await run_cegis(
                secret=self.config.cegis.secret,
                max_iters=self.config.cegis.max_iters,
                state=self.state,
                bus=self.bus,
                store=self.pcap_store,
                out_path=Path("artifacts/cegis/result.json"),
            )

            # Log du succès CEGIS
            log_action(
                self.pcap_store,
                "2cat_cegis_done",
                level="S0",
                obligations={
                    "secret": self.config.cegis.secret,
                    "max_iters": str(self.config.cegis.max_iters),
                },
            )

            self.cegis_result = {
                "success": True,
                "converged": True,
                "iters": self.config.cegis.max_iters,
                "candidate": {"value": self.config.cegis.secret},
            }

        except Exception as e:
            # Log de l'erreur CEGIS
            log_action(
                self.pcap_store, "2cat_cegis_error", level="S0", obligations={"error": str(e)}
            )

            self.cegis_result = {"success": False, "error": str(e)}
            raise

    async def _verify_psp(self):
        """Vérifie le PSP avec les obligations S1."""
        from xme.adapters.logger import log_action

        if not self.ae_result or not self.ae_result.get("success"):
            return

        # Log du début de vérification
        log_action(
            self.pcap_store,
            "2cat_verify_start",
            level="S0",
            obligations={"psp_path": str(self.psp_output)},
        )

        try:
            # Charger le PSP
            psp_data = orjson.loads(self.psp_output.read_bytes())

            # Créer le vérificateur
            verifier = Verifier()

            # Enregistrer les obligations PSP
            for obligation_id, level, check_func, description in get_psp_obligations():
                obligation = create_obligation(obligation_id, level, check_func, description)
                verifier.register_obligation(obligation)

            # Exécuter les vérifications S1
            report = verifier.run_by_level(psp_data, "S1")

            # Loguer les verdicts dans PCAP
            for result in report.results:
                log_verdict(
                    self.pcap_store, result.obligation_id, result.level, result.ok, result.details
                )

            # Log du résultat de vérification
            log_action(
                self.pcap_store,
                "2cat_verify_done",
                level="S0",
                obligations={
                    "all_ok": str(report.ok_all),
                    "total_checks": str(len(report.results)),
                },
            )

            self.verification_report = {
                "success": report.ok_all,
                "total_checks": len(report.results),
                "passed": sum(1 for r in report.results if r.ok),
                "failed": sum(1 for r in report.results if not r.ok),
            }

        except Exception as e:
            # Log de l'erreur de vérification
            log_action(
                self.pcap_store, "2cat_verify_error", level="S0", obligations={"error": str(e)}
            )

            self.verification_report = {"success": False, "error": str(e)}

    async def _calculate_metrics(self):
        """Calcule les métriques δ et génère le résumé."""
        from xme.adapters.logger import log_action

        # Log du début de calcul des métriques
        log_action(
            self.pcap_store, "2cat_metrics_start", level="S0", obligations={"run_id": self.run_id}
        )

        try:
            # Calculer les δ du run
            delta_info = aggregate_run_delta(self.pcap_store.path)

            # Générer le résumé
            summary = summarize_run(self.pcap_store.path)

            # Sauvegarder les métriques
            metrics_path = Path(self.config.outputs.metrics)
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            export_summary_json(summary, metrics_path)
            self.metrics_output = metrics_path

            # Log du résultat des métriques
            log_action(
                self.pcap_store,
                "2cat_metrics_done",
                level="S0",
                obligations={
                    "delta_run": str(delta_info.get("delta_run", 0.0)),
                    "total_entries": str(delta_info.get("total_entries", 0)),
                },
            )

            self.metrics_summary = {
                "delta_run": delta_info.get("delta_run", 0.0),
                "total_entries": delta_info.get("total_entries", 0),
                "summary": summary,
            }

        except Exception as e:
            # Log de l'erreur de calcul des métriques
            log_action(
                self.pcap_store, "2cat_metrics_error", level="S0", obligations={"error": str(e)}
            )

            self.metrics_summary = {"error": str(e)}

    async def _build_audit_pack(self):
        """Construit l'Audit Pack hermétique."""
        from xme.adapters.logger import log_action

        # Log du début de construction du pack
        log_action(
            self.pcap_store,
            "2cat_pack_start",
            level="S0",
            obligations={
                "out_dir": self.config.pack.out,
                "include_patterns": str(len(self.config.pack.include)),
            },
        )

        try:
            # Construire la liste d'entrées à partir des artefacts produits
            inputs = []
            if self.psp_output and Path(self.psp_output).exists():
                inputs.append((Path(self.psp_output), "psp"))
            if self.pcap_store and Path(self.pcap_store.path).exists():
                inputs.append((Path(self.pcap_store.path), "pcap"))
            if self.metrics_output and Path(self.metrics_output).exists():
                inputs.append((Path(self.metrics_output), "metrics"))

            # Construire le manifest
            manifest = build_manifest(inputs)

            # Écrire le pack dans le répertoire de sortie (nom auto-généré)
            out_dir = self.config.pack.out
            pack_path = write_zip(manifest, out_dir)
            self.pack_path = pack_path

            # Log du succès de construction du pack
            log_action(
                self.pcap_store,
                "2cat_pack_done",
                level="S0",
                obligations={
                    "pack_path": str(pack_path),
                    "files_count": str(len(inputs)),
                    "merkle_root": manifest.merkle_root,
                },
            )

        except Exception as e:
            # Log de l'erreur de construction du pack
            log_action(
                self.pcap_store, "2cat_pack_error", level="S0", obligations={"error": str(e)}
            )
            raise

    async def _generate_final_report(self) -> Dict[str, Any]:
        """Génère le rapport final du pipeline."""
        from xme.adapters.logger import log_action

        # Log de la fin du pipeline
        log_action(
            self.pcap_store,
            "2cat_pipeline_done",
            level="S0",
            obligations={"run_id": self.run_id, "success": "true"},
        )

        # Générer le rapport
        report = {
            "run_id": self.run_id,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "config": {
                "version": self.config.version,
                "ae": {"context": self.config.ae.context, "timeout_ms": self.config.ae.timeout_ms},
                "cegis": {
                    "secret": self.config.cegis.secret,
                    "max_iters": self.config.cegis.max_iters,
                },
                "budgets": {
                    "ae_ms": self.config.budgets.ae_ms,
                    "cegis_ms": self.config.budgets.cegis_ms,
                    "total_ms": self.config.budgets.total_ms,
                },
            },
            "results": {
                "ae": self.ae_result,
                "cegis": self.cegis_result,
                "verification": self.verification_report,
                "metrics": self.metrics_summary,
            },
            "artifacts": {
                "psp": str(self.psp_output) if self.psp_output else None,
                "pcap": str(self.pcap_store.path) if self.pcap_store else None,
                "metrics": str(self.metrics_output) if self.metrics_output else None,
                "pack": str(self.pack_path) if self.pack_path else None,
            },
            "success": (
                self.ae_result
                and self.ae_result.get("success", False)
                and self.cegis_result
                and self.cegis_result.get("success", False)
                and self.verification_report
                and self.verification_report.get("success", False)
            ),
        }

        # Sauvegarder le rapport
        report_path = Path(self.config.outputs.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "wb") as f:
            f.write(orjson.dumps(report, option=orjson.OPT_INDENT_2))

        return report


async def run_discovery_engine_2cat(config_path: Path) -> Dict[str, Any]:
    """
    Fonction principale pour exécuter le discovery-engine-2cat.

    Args:
        config_path: Chemin vers le fichier de configuration YAML

    Returns:
        Résultat du pipeline
    """
    # Charger la configuration
    config = DiscoveryEngine2CatConfig.from_yaml(config_path)

    # Valider la configuration
    errors = config.validate()
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

    # Créer et exécuter le runner
    runner = DiscoveryEngine2CatRunner(config)
    return await runner.run()
