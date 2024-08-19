import random
from pathlib import Path

from datalab_api import DatalabClient, DuplicateItemError


def import_cheminventory(filename: Path, client: DatalabClient):
    """Helper function to import a ChemInventory xlsx export into datalab, using the
    'starting_materials' item type.

    Migrated from the original version in the main datalab repository:
        https://github.com/the-grey-group/datalab/blob/43764fb494c2cc1bf9f7dc90c25594aeb79d5767/pydatalab/tasks.py#L350-L413

    """

    def _generate_random_startingmaterial_id():
        """Generate 'XX' + a random 15-length string for use as an id for starting materials
        that don't have a barcode.
        """
        yield "".join(["XX"] + random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=15))

    try:
        import pandas as pd

        inventory_df = pd.read_excel(filename)
    except ImportError as exc:
        raise ImportError(
            "Please install pandas + openpyxl to use this helper function, via `pip install datalab-api[cheminventory-helper]`"
        ) from exc
    inventory_df["type"] = "starting_materials"
    inventory_df["item_id"] = inventory_df["Barcode"]
    # Fill missing barcodes
    inventory_df["item_id"] = inventory_df["item_id"].fillna(
        inventory_df["item_id"].apply(lambda _: next(_generate_random_startingmaterial_id()))
    )
    inventory_df["Molecular Weight"] = inventory_df["Molecular Weight"].replace(" ", float("nan"))

    counts = {"success": 0, "duplicate": 0, "failed": 0}

    for item in inventory_df.to_dict(orient="records"):
        try:
            client.create_item(
                item["item_id"], item["type"], item, collection_id="jul24-inventory-import"
            )
            counts["success"] += 1
        except DuplicateItemError:
            counts["duplicate"] += 1
        except Exception as exc:
            counts["failed"] += 1
            print(f"Failed to import item: {item}. Error: {exc}")
            continue

    print(f"Done: {counts=}")
