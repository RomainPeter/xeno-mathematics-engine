import subprocess, tempfile, shutil, os, uuid, sys

class Workspace:
    def __init__(self, base_dir="demo_repo"):
        self.base_dir = base_dir
        self.work_dir = os.path.join(".work", str(uuid.uuid4())[:8])
        shutil.copytree(base_dir, self.work_dir)

    def apply_unified_diff(self, patch_text: str) -> bool:
        if not patch_text.strip():
            return False
        # try git apply
        try:
            p = subprocess.run(["git", "apply", "-p0", "-"], input=patch_text.encode("utf-8"),
                               cwd=self.work_dir, capture_output=True, check=True)
            return True
        except Exception:
            # naive fallback: no-op
            return False

    def cleanup(self):
        shutil.rmtree(self.work_dir, ignore_errors=True)
