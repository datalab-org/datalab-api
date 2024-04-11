import time
from typing import Annotated, Optional

import typer
from click_shell import make_click_shell
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.pretty import pprint
from rich.table import Table

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
    animate_intro: bool = True,
):
    """Makes an interactive REPL-style interface using the subcommands below."""
    shell = make_click_shell(
        ctx,
        prompt="datalab > ",
    )

    animation_intro = _make_fancy_intro()
    if animate_intro:
        with Live(console=console, auto_refresh=False) as live:
            for frame in animation_intro:
                live._live_render.set_renderable(
                    Panel(
                        frame,
                        subtitle=app.info.epilog,
                        width=len(app.info.epilog) + 6,
                        highlight=False,
                    )
                )  # type: ignore
                console.print(live._live_render.position_cursor())
                time.sleep(0.05)

    console.print(
        Panel(animation_intro[-1], subtitle=app.info.epilog, width=len(app.info.epilog) + 6),
        highlight=False,
    )  # type: ignore
    console.print()
    console.print(
        Panel(
            "This CLI is an experimental work in progress and does not expose the full functionality of the underlying DatalabClient.",
            title="[red]WARNING![/red]",
            width=len(app.info.epilog) + 6,
        )
    )
    console.print()

    if instance_url:
        authenticate(ctx, instance_url)
    shell.cmdloop()


def _get_client(
    ctx: typer.Context,
    instance_url: Optional[str] = None,
    log_level: str = "WARNING",
):
    client = getattr(ctx, "client", None)
    if instance_url is None:
        instance_url = getattr(ctx, "instance_url", None)  # type: ignore
    if client is None:
        client = DatalabClient(datalab_api_url=instance_url, log_level=log_level)  # type: ignore
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
    instance_url: Annotated[Optional[str], typer.Argument()] = None,
    log_level: str = "WARNING",
):
    client = _get_client(ctx, instance_url, log_level)
    user = client.authenticate()
    console.print(
        f"Welcome [red]{user['display_name']}[/red]!\nSuccessfully authenticated at [blue]{client.datalab_api_url}[/blue]."
    )


@app.command()
def get(
    ctx: typer.Context,
    item_type: str,
    instance_url: Annotated[Optional[str], typer.Argument()] = None,
    page_limit: int = 10,
    log_level: str = "WARNING",
):
    """Get a table of items of the given type."""
    client = _get_client(ctx, instance_url, log_level)
    items = client.get_items(item_type)
    table = Table(title=f"/{item_type}/", show_lines=True)
    table.add_column("type", overflow="crop", justify="center")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("refcode", style="magenta", no_wrap=True)
    table.add_column("name", width=30, overflow="ellipsis", no_wrap=True)
    table.add_column("nblocks", justify="right")
    table.add_column("collections")
    table.add_column("creators")
    for item in items[:page_limit]:
        table.add_row(
            item["type"][0].upper(),
            item["item_id"],
            item["refcode"],
            item["name"],
            str(item["nblocks"]),
            ", ".join(d["collection_id"] for d in item["collections"]),
            ", ".join(d["display_name"] for d in item["creators"]),
            end_section=True,
        )
    console.print(table)


@app.command()
def info(ctx: typer.Context, instance_url: str, log_level: str = "WARNING"):
    """Print the server info."""
    client = _get_client(ctx, instance_url, log_level)
    pprint(client.get_info())


def _make_fancy_intro(animate=True):
    """Bit of fun, make an animated datalab logo intro to the CLI."""
    import random

    intro_ascii = """
              oooo              o8              o888             oooo
           ooooo888    ooooooo o888oo  ooooooo    888   ooooooo    888ooooo
         888    888    ooooo888 888    ooooo888   888   ooooo888   888    888
         888    888  888    888 888  888    888   888 888    888   888    888
           88ooo888o  88ooo88 8o 888o 88ooo88 8o o888o 88ooo88 8o o888ooo88
    """

    # Colour themes that should work in both light and dark terminals
    themes = [
        ["dark_orange", "salmon1", "light_coral", "pale_violet_red1", "orchid2", "orchid1"],
        ["dark_orange3", "indian_red", "hot_pink3", "hot_pink2", "orchid"],
        ["chartreuse4", "pale_turqoise4", "steel_blue", "steel_blue3", "cornflower_blue"],
    ]

    colours = random.choice(themes)
    random.shuffle(colours)
    colours.append("black")
    num_colours = len(colours)

    animation: list[str] = []
    colours_by_index: list[int] = [num_colours - 1] * len(intro_ascii)
    beta_1: float = 0.2
    beta_2: float = 0.6
    steps: int = 0
    max_steps: int = 50

    while max(colours_by_index) != 0:
        intro_fancy = ""
        for ind, char in enumerate(intro_ascii):
            if char == " ":
                colours_by_index[ind] = 0
                intro_fancy += " "
            else:
                if colours_by_index[ind] != 0 and random.random() < (steps / max_steps) * beta_1:
                    colours_by_index[ind] = 0
                elif colours_by_index[ind] != 0 and random.random() < (steps / max_steps) * beta_2:
                    colours_by_index[ind] = random.randint(1, num_colours - 2)
                intro_fancy += f"[{colours[colours_by_index[ind]]}]{char}[/]"

        animation.append(intro_fancy)
        steps += 1

    return animation


if __name__ == "__main__":
    app()
