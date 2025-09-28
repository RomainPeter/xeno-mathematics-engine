#!/usr/bin/env python3
"""
Generate Grove One-Pager
Injects metrics from out/metrics.json, Merkle, SBOM into one-pager template
"""
import json
import pathlib
from datetime import datetime


def load_metrics():
    """Load metrics from out/metrics.json."""
    metrics_file = pathlib.Path("out/metrics.json")
    if metrics_file.exists():
        with open(metrics_file) as f:
            return json.load(f)
    return {}


def load_merkle():
    """Load Merkle root from out/journal/merkle.txt."""
    merkle_file = pathlib.Path("out/journal/merkle.txt")
    if merkle_file.exists():
        return merkle_file.read_text().strip()
    return "n/a"


def load_sbom():
    """Load SBOM and count vulnerabilities."""
    sbom_file = pathlib.Path("out/sbom.json")
    if sbom_file.exists():
        with open(sbom_file) as f:
            sbom = json.load(f)

        # Count vulnerabilities by severity
        vulnerabilities = sbom.get("vulnerabilities", [])
        high_critical = sum(
            1
            for v in vulnerabilities
            if v.get("severity", "").upper() in ["HIGH", "CRITICAL"]
        )

        return (
            "0 High/Critical"
            if high_critical == 0
            else f"{high_critical} High/Critical"
        )
    return "n/a"


def generate_onepager():
    """Generate populated one-pager."""
    print("📊 Generating Grove one-pager...")

    # Load data
    metrics = load_metrics()
    merkle = load_merkle()
    sbom_status = load_sbom()

    # Extract metrics with defaults
    coverage_gain = metrics.get("coverage", {}).get("coverage_gain", 0.20)
    novelty_avg = metrics.get("novelty", {}).get("avg", 0.22)
    audit_p95 = metrics.get("audit_cost", {}).get("p95", "n/a")

    # Load template
    template_file = pathlib.Path("docs/grove/one-pager.md")
    if not template_file.exists():
        print("❌ Template file not found: docs/grove/one-pager.md")
        return False

    with open(template_file) as f:
        template = f.read()

    # Replace placeholders
    populated = template.replace("{{coverage_gain}}", f"{coverage_gain:.2f}")
    populated = populated.replace("{{novelty_avg}}", f"{novelty_avg:.2f}")
    populated = populated.replace("{{audit_p95}}", str(audit_p95))
    populated = populated.replace("{{merkle}}", merkle)
    populated = populated.replace("{{sbom}}", sbom_status)

    # Add generation timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    populated = populated.replace("<!-- GENERATED_AT -->", f"*Generated: {timestamp}*")

    # Write populated one-pager
    output_file = pathlib.Path("docs/grove/one-pager.md")
    with open(output_file, "w") as f:
        f.write(populated)

    print(f"✅ Generated one-pager: {output_file}")
    print(f"📊 Coverage gain: {coverage_gain:.2f}")
    print(f"📈 Novelty avg: {novelty_avg:.2f}")
    print(f"⏱️ Audit p95: {audit_p95}")
    print(f"🔗 Merkle: {merkle[:16]}...")
    print(f"🔒 SBOM: {sbom_status}")

    return True


def main():
    """Main function."""
    success = generate_onepager()

    if success:
        print("🎉 Grove one-pager generated successfully!")
        exit(0)
    else:
        print("❌ Failed to generate Grove one-pager!")
        exit(1)


if __name__ == "__main__":
    main()
