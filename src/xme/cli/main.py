import typer
from rich import print

app = typer.Typer(help="XME — Xeno-Math Engine CLI")


@app.callback()
def main():
    print("[bold cyan]XME CLI[/bold cyan]")


if __name__ == "__main__":
    app()
