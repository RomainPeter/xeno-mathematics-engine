import json
import typer
from rich import print
from proofengine.core.llm_client import LLMClient, LLMError
from proofengine.planner.meta import propose_plan
from proofengine.generator.stochastic import propose_actions

app = typer.Typer(no_args_is_help=True)

@app.command("ping")
def ping():
    try:
        client = LLMClient()
        res = client.ping()
        print({"ok": True, "ping": res})
    except LLMError as e:
        print({"ok": False, "error": str(e)})

@app.command("propose-plan")
def cli_propose_plan(
    goal: str = typer.Option(..., "--goal"),
    x_summary: str = typer.Option("{}", "--x-summary"),
    obligations: str = typer.Option("[]", "--obligations"),
    history: str = typer.Option("[]", "--history"),
):
    res = propose_plan(goal, x_summary, obligations, history)
    print(json.dumps(res, ensure_ascii=False, indent=2))

@app.command("propose-actions")
def cli_propose_actions(
    task: str = typer.Option(..., "--task"),
    context: str = typer.Option("", "--context"),
    obligations: str = typer.Option("[]", "--obligations"),
    k: int = typer.Option(3, "--k"),
):
    res = propose_actions(task, context, obligations, k=k, temperature=0.8)
    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    app()
