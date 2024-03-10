from typing import Optional, Annotated

import typer
import time
from rich.pretty import pprint
from rich.console import Console
from rich.live import Live
from click_shell import make_click_shell

from datalab_api import DatalabClient

app = typer.Typer(
    name="datalab",
    help="A command-line interface for the Datalab API.",
    epilog="Copyright (c) 2020-2024 Matthew Evans, Joshua Bocarsly & the Datalab Development Team.",
)

console = Console()


@app.callback(invoke_without_command=True)
def launch(
    ctx: typer.Context,
    instance_url: Annotated[Optional[str], typer.Argument()] = None,
    animate_intro: bool = False,
):
    """Makes an interactive REPL-style interface using the subcommands below."""
    shell = make_click_shell(
        ctx,
        prompt="datalab > ",
    )

    if animate_intro:
        animation_intro = _make_fancy_intro(steps=50)
        with Live(console=console, screen=True, auto_refresh=False) as live:
            for frame in animation_intro:
                console.print(frame, highlight=False)
                time.sleep(0.02)
    else:
        animation_intro = _make_fancy_intro(steps=1)
        console.print(animation_intro[-1], highlight=False)
    console.print()
    console.print(app.info.epilog, highlight=False)
    console.print()

    if instance_url:
        authenticate(ctx, instance_url)
    shell.cmdloop()


def _get_client(
    ctx: typer.Context,
    instance_url: Optional[str] = None,
    api_key: Optional[str] = None,
    log_level: str = "WARNING",
):
    client = getattr(ctx, "client", None)
    if instance_url is None:
        instance_url = getattr(ctx, "instance_url", None)
    if client is None:
        client = DatalabClient(datalab_api_url=instance_url, api_key=api_key, log_level=log_level)
    ctx.client = client
    ctx.instance_url = client.datalab_api_url
    return ctx.client


def _get_instance_url(ctx: typer.Context):
    instance_url = getattr(ctx, "instance_url", None)
    if instance_url is None:
        raise ValueError("No Datalab API URL provided.")
    return instance_url


@app.command()
def authenticate(
    ctx: typer.Context,
    instance_url: Annotated[str, typer.Argument()],
    api_key: Optional[str] = None,
    log_level: str = "WARNING",
):
    client = _get_client(ctx, instance_url, api_key, log_level)
    user = client.authenticate()
    console.print(
        f"Welcome [red]{user['display_name']}[/red]! Successfully authenticated at [blue]{client.datalab_api_url}[/blue]."
    )


@app.command()
def info(
    ctx: typer.Context, instance_url: str, api_key: Optional[str] = None, log_level: str = "WARNING"
):
    """Print the server info."""
    client = _get_client(ctx, instance_url, api_key, log_level)
    pprint(client.get_info())


def _make_fancy_intro(steps=50):
    """Bit of fun, make an animated datalab logo intro to the CLI."""
    import random

    intro_ascii = """
        oooo              o8              o888             oooo
     ooooo888    ooooooo o888oo  ooooooo    888   ooooooo    888ooooo
   888    888    ooooo888 888    ooooo888   888   ooooo888   888    888
   888    888  888    888 888  888    888   888 888    888   888    888
     88ooo888o  88ooo88 8o 888o 88ooo88 8o o888o 88ooo88 8o o888ooo88"""

    colours = [
        "medium_purple1",
        "dark_slate_gray3",
        "medium_orchid",
        "dark_red",
        "dodger_blue3",
        "turquoise2",
        "plum4",
    ]
    colours.insert(0, random.choice(colours))
    num_colours = len(colours)

    animation = []
    step = 0
    colours_by_index: list[int] = [-1] * len(intro_ascii)
    while step < steps:
        intro_fancy = ""
        for ind, char in enumerate(intro_ascii):
            if char != " ":
                if random.random() < float(step + 1) / steps:
                    colours_by_index[ind] = 0
                elif colours_by_index[ind] == -1:
                    colours_by_index[ind] = random.randint(0, num_colours - 1)
                intro_fancy += f"[{colours[colours_by_index[ind]]}]{char}[/]"
            else:
                intro_fancy += " "
        animation.append(intro_fancy)
        step += 1

    return animation


if __name__ == "__main__":
    app()
