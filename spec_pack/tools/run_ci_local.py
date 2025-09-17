import sys
import tempfile
import shutil
import os
import subprocess

def run_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"--- STDOUT ---\n{result.stdout}", file=sys.stderr)
        print(f"--- STDERR ---\n{result.stderr}", file=sys.stderr)
        sys.exit(result.returncode)
    print(result.stdout)

def main():
    original_dir = os.getcwd()
    tmp_dir = tempfile.mkdtemp()
    print(f"[CI local] Created temp sandbox: {tmp_dir}")

    try:
        spec_pack_src = os.path.join(original_dir, 'spec_pack')
        spec_pack_dst = os.path.join(tmp_dir, 'spec_pack')
        shutil.copytree(spec_pack_src, spec_pack_dst)
        os.chdir(tmp_dir)

        print("[CI local] S1…")
        run_command(['python', os.path.join('spec_pack', 'tools', 'run_s1.py')])

        print("[CI local] S2 sandbox…")
        run_command(['python', os.path.join('spec_pack', 'tools', 's2_contradiction.py')])
        run_command(['python', os.path.join('spec_pack', 'tools', 's2_check.py')])

    finally:
        os.chdir(original_dir)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        print(f"[CI local] Cleaned up sandbox: {tmp_dir}")

    print("[CI local] OK: S1+S2 PASS")

if __name__ == "__main__":
    main()
