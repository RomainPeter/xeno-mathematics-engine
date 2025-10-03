from __future__ import annotations

import json
import logging
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pefc.pack.manifest_utils import load_manifest

log = logging.getLogger(__name__)


@dataclass
class OnePagerData:
    pack_version: str
    pack_name: str
    built_at: str
    merkle_root: Optional[str]
    merkle_reason: Optional[str]
    summary: Optional[dict]
    summary_reason: Optional[str]
    sbom: Optional[dict]
    sbom_reason: Optional[str]
    environment: dict


DEFAULT_TEMPLATE = """# {pack_name} — One-Pager (v{pack_version})
Built at: {built_at}

## Integrity
- Merkle root: {merkle_line}

## Metrics (summary)
{metrics_block}

## SBOM
{sbom_block}

## Environment
- Python: {py_version}
- Platform: {platform}
"""


def _fmt_metrics(summary: Optional[dict], reason: Optional[str]) -> str:
    """Format metrics section for markdown."""
    if summary is None:
        return f"- Unavailable: {reason}"

    o = summary.get("overall", {})
    by = summary.get("by_group", {})
    lines = []

    if o:
        lines.append(f"- Overall: n_runs={o.get('n_runs', 0)}, weight_sum={o.get('weight_sum', 0)}")
        if "metrics" in o and isinstance(o["metrics"], dict):
            for k, v in o["metrics"].items():
                lines.append(f"  - {k}: {v:.6f}")

    if by:
        lines.append("- By group:")
        for g, obj in by.items():
            s = f"  - {g}: n_runs={obj.get('n_runs', 0)}, weight_sum={obj.get('weight_sum', 0)}"
            lines.append(s)

    return "\n".join(lines) if lines else "- No metrics found"


def _fmt_sbom(sbom: Optional[dict], reason: Optional[str]) -> str:
    """Format SBOM section for markdown."""
    if sbom is None:
        return f"- Unavailable: {reason}"

    comp = sbom.get("components") or sbom.get("packages") or []
    return f"- Components/Packages: {len(comp)}"


def render_markdown(data: OnePagerData, template_text: Optional[str] = None) -> str:
    """Render one-pager markdown from data and template."""
    merkle_line = data.merkle_root if data.merkle_root else f"Unavailable: {data.merkle_reason}"
    metrics_block = _fmt_metrics(data.summary, data.summary_reason)
    sbom_block = _fmt_sbom(data.sbom, data.sbom_reason)
    templ = template_text or DEFAULT_TEMPLATE

    md = templ.format(
        pack_name=data.pack_name,
        pack_version=data.pack_version,
        built_at=data.built_at,
        merkle_line=merkle_line,
        metrics_block=metrics_block,
        sbom_block=sbom_block,
        py_version=data.environment.get("python"),
        platform=data.environment.get("platform"),
    )

    # Normaliser les fins de ligne pour reproductibilité
    return md.replace("\r\n", "\n").replace("\r", "\n")


def build_onepager(cfg, out_dir: Path) -> Path:
    """Build one-pager markdown file."""
    # Collect manifest/merkle
    manifest_path = out_dir / "manifest.json"
    merkle_root = None
    merkle_reason = None
    if manifest_path.exists():
        try:
            manifest = load_manifest(manifest_path)
            merkle_root = manifest.get("merkle_root")
        except Exception as e:
            merkle_reason = f"manifest invalid: {e}"
    else:
        merkle_reason = "manifest.json not found"

    # Load summary
    summary_path = out_dir / "summary.json"
    summary = None
    summary_reason = None
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception as e:
            summary_reason = f"summary unreadable: {e}"
    else:
        summary_reason = "summary.json not found"

    # SBOM
    from pefc.sbom import find_sbom

    sbom, sbom_reason = find_sbom(out_dir, getattr(cfg.sbom, "path", None))

    data = OnePagerData(
        pack_version=cfg.pack.version,
        pack_name=cfg.pack.pack_name,
        built_at=datetime.now(timezone.utc).isoformat(),
        merkle_root=merkle_root,
        merkle_reason=merkle_reason,
        summary=summary,
        summary_reason=summary_reason,
        sbom=sbom,
        sbom_reason=sbom_reason,
        environment={
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
    )

    # Template
    template_text = None
    if cfg.docs.onepager.template_path:
        tpath = Path(cfg.docs.onepager.template_path)
        if not tpath.is_absolute():
            tpath = (Path(cfg._base_dir) / tpath).resolve()
        if tpath.exists():
            template_text = tpath.read_text(encoding="utf-8")
        else:
            log.warning("onepager: template not found, using default: %s", tpath)

    md = render_markdown(data, template_text=template_text)
    out_file = Path(cfg.pack.out_dir) / cfg.docs.onepager.output_file
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(md, encoding="utf-8", newline="\n")
    log.info("onepager: written %s", out_file)
    return out_file
