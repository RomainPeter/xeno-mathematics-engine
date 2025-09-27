"""Patch workspace utilities used by controller tests."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import uuid
from typing import Any, Dict, List


class Workspace:
    """Isolated copy of a repository where patches can be applied."""

    def __init__(self, base_dir: str = "demo_repo"):
        if not os.path.exists(base_dir):
            raise ValueError(f"Base directory {base_dir} does not exist")
        self.base_dir = base_dir
        self.work_dir = os.path.join(".work", str(uuid.uuid4())[:8])
        shutil.copytree(base_dir, self.work_dir)

    def apply_unified_diff(self, patch_text: str) -> bool:
        if not patch_text.strip():
            return False
        try:
            subprocess.run(
                ["git", "apply", "-p0", "-"],
                input=patch_text.encode("utf-8"),
                cwd=self.work_dir,
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return self._apply_with_patch(patch_text)

    def _apply_with_patch(self, patch_text: str) -> bool:
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".patch", delete=False
            ) as handle:
                handle.write(patch_text)
                temp_patch = handle.name
            subprocess.run(
                ["patch", "-p0", "-i", temp_patch],
                cwd=self.work_dir,
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False
        finally:
            if "temp_patch" in locals():
                os.unlink(temp_patch)

    def get_changed_files(self) -> List[str]:
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            return [line for line in result.stdout.splitlines() if line]
        except subprocess.CalledProcessError:
            return []

    def get_diff(self) -> str:
        try:
            result = subprocess.run(
                ["git", "diff"],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def get_status(self) -> Dict[str, Any]:
        return {
            "work_dir": self.work_dir,
            "base_dir": self.base_dir,
            "changed_files": self.get_changed_files(),
            "diff": self.get_diff(),
        }

    def cleanup(self) -> None:
        shutil.rmtree(self.work_dir, ignore_errors=True)

    def __enter__(self) -> "Workspace":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()


class PatchManager:
    """High level patch management utilities."""

    def __init__(self, base_dir: str = "demo_repo"):
        self.base_dir = base_dir

    def validate_patch(self, patch_text: str) -> Dict[str, Any]:
        result = {"valid": False, "errors": [], "warnings": []}
        if not patch_text.strip():
            result["errors"].append("Empty patch")
            return result

        lines = patch_text.splitlines()
        if not any(line.startswith(("---", "+++")) for line in lines):
            result["errors"].append("Invalid patch format")
            return result

        python_targets = [
            line.split()[-1]
            for line in lines
            if line.startswith("+++") and line.endswith(".py")
        ]
        if python_targets:
            result["warnings"].append(f"Python files affected: {python_targets}")

        result["valid"] = True
        return result

    def apply_patch(self, patch_text: str) -> Dict[str, Any]:
        validation = self.validate_patch(patch_text)
        if not validation["valid"]:
            return {"success": False, "validation": validation}
        with Workspace(self.base_dir) as workspace:
            if workspace.apply_unified_diff(patch_text):
                return {
                    "success": True,
                    "workspace": workspace.get_status(),
                    "validation": validation,
                }
        return {
            "success": False,
            "validation": validation,
            "error": "Patch application failed",
        }

    def get_patch_info(self, patch_text: str) -> Dict[str, Any]:
        lines = patch_text.splitlines()
        added = sum(
            1 for line in lines if line.startswith("+") and not line.startswith("+++")
        )
        removed = sum(
            1 for line in lines if line.startswith("-") and not line.startswith("---")
        )
        files = set()
        for line in lines:
            if line.startswith(("---", "+++")):
                parts = line.split()
                if len(parts) >= 2:
                    path = parts[-1]
                    if path != "/dev/null":
                        files.add(path)
        return {
            "total_lines": len(lines),
            "added_lines": added,
            "removed_lines": removed,
            "files_affected": sorted(files),
            "size": len(patch_text),
            "complexity": (added + removed) / max(1, len(files)),
        }
