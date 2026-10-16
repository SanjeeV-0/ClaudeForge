"""ClaudeForge command-line interface."""

import typer
from rich.console import Console

app = typer.Typer(
    name="claudeforge",
    help="A reliable, resumable AI software engineering framework.",
    no_args_is_help=True,
)

console = Console()


@app.command()
def version() -> None:
    """Display the installed ClaudeForge version."""
    from claudeforge import __version__

    console.print(f"ClaudeForge v{__version__}")


@app.command()
def status() -> None:
    """Display the initial framework status."""
    console.print("[bold]ClaudeForge[/bold]")
    console.print("Project foundation initialized.")
    console.print("Agent orchestration: not implemented yet.")
    console.print("Persistent project state: not implemented yet.")
    console.print("Verification engine: not implemented yet.")


if __name__ == "__main__":
    app()
