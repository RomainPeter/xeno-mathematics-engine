import typer
from rich import print

app = typer.Typer(help="BFK - minimal CLI for xeno mathematics engine")


@app.command()
def version():
    print("bfk 0.1.0")


@app.command()
def verify_vendor(
    zip_path: str = "vendor/2cat/pack.zip",
    sha256_path: str = "vendor/2cat/pack.sha256",
):
    import subprocess

    res = subprocess.run(
        [
            "python",
            "scripts/verify_2cat_pack.py",
            "--zip",
            zip_path,
            "--sha256",
            sha256_path,
        ],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise typer.Exit(code=res.returncode)
    print(res.stdout.strip())


if __name__ == "__main__":
    app()
