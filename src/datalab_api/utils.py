import functools

from rich.console import Console
from rich.pretty import pprint
from rich.table import Table

__all__ = ("AutoPrettyPrint", "bokeh_from_json", "pretty_displayer")


def pretty_displayer(method):
    """A decorator which wraps a method with a 'display' kwarg, which will
    either pretty print a JSON response, display a Rich table, or render
    a bokeh plot from its JSON representation.
    """

    @functools.wraps(method)
    def rich_wrapper(self, *args, **kwargs):
        display = kwargs.pop("display", False)
        page_limit = kwargs.pop("page_limit", 10)
        result = method(self, *args, **kwargs)
        if display:
            blocks = None
            if isinstance(result, dict):
                if "blocks_obj" in result:
                    blocks = result["blocks_obj"]
                elif "blocktype" in result:
                    blocks = {result["block_id"]: result}
                    result = None
                if blocks:
                    for block in blocks.values():
                        if "bokeh_plot_data" in block:
                            bokeh_from_json(block)
                if result:
                    pprint(result, max_length=None, max_string=100, max_depth=3)
            elif isinstance(result, list):
                try:
                    table = Table(show_lines=True)
                    table.add_column("type", overflow="crop", justify="center")
                    table.add_column("ID", style="cyan", no_wrap=True)
                    table.add_column("refcode", style="magenta", no_wrap=True)
                    table.add_column("name", width=30, overflow="ellipsis", no_wrap=True)
                    for item in result[:page_limit]:
                        table.add_row(
                            item["type"][0].upper(),
                            item["item_id"],
                            item["refcode"],
                            item["name"],
                            end_section=True,
                        )
                    console = Console()
                    console.print(table)
                except Exception:
                    pprint(result, max_length=None, max_string=100, max_depth=3)

        return result

    return rich_wrapper


class AutoPrettyPrint(type):
    """A metaclass that automatically applies the pretty_displayer decorator."""

    def __new__(cls, name, bases, dct):
        for attr, value in dct.items():
            if callable(value) and not attr.startswith("__"):
                dct[attr] = pretty_displayer(value)
        return super().__new__(cls, name, bases, dct)


def bokeh_from_json(block_data, show=True):
    from bokeh.io import curdoc
    from bokeh.plotting import show as bokeh_show

    bokeh_plot_data = block_data.get("bokeh_plot_data", block_data)
    curdoc().replace_with_json(bokeh_plot_data["doc"])
    if show:
        bokeh_show(curdoc().roots[0])

    return curdoc()
