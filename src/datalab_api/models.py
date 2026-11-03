# This file was edited with the assistance of an AI model and requires human review from the contributor.
"""Object-oriented models for *datalab* entries, generated at runtime from the
JSON schemas that a *datalab* instance advertises at `/info/types`.

Since *datalab* v0.8.0, deployments can register their own custom item types
(served with a leading underscore, e.g., `_my_samples`), so the set of models
cannot be known ahead of time. Instead, each client builds a set of
[pydantic](https://docs.pydantic.dev) models from the server's schemas, which
are available via `DatalabClient.models`:

```python
with DatalabClient("https://demo-api.datalab-org.io") as client:
    Sample = client.models.Sample
    sample = Sample(item_id="my-sample", name="My sample", chemform="NaCl")
    sample.create()

    sample.description = "Updated description"
    sample.save()
```

The models can also be built without a client, e.g., from a saved copy of the
`/info/types` response, using [`build_item_models`][datalab_api.models.build_item_models].

"""

from __future__ import annotations

import copy
import datetime as dt
import json
import keyword
import re
import warnings
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, ValidationError, create_model

if TYPE_CHECKING:
    from . import DatalabClient

__all__ = (
    "DatalabItem",
    "DatalabModel",
    "ItemModels",
    "build_item_models",
    "model_from_schema",
)

_MODEL_CONFIG = ConfigDict(
    # Keep any fields the server sends that are not in the schema (e.g., `nblocks`
    # in summaries, or block-specific data), so that nothing is lost on a round-trip.
    extra="allow",
    populate_by_name=True,
    protected_namespaces=(),
    # Server-side patterns are Python regexes; the default Rust engine
    # does not support every construct (e.g., lookarounds).
    regex_engine="python-re",
    validate_assignment=True,
    arbitrary_types_allowed=True,
)


class DatalabModel(BaseModel):
    """The base class for all generated models (including nested ones, e.g.,
    `File`, `Constituent`).

    For backwards-compatibility with the dictionary-based API, fields can also be
    accessed by key, e.g., `item["item_id"]` or `item.get("name")`, using their
    original (server) names.

    """

    model_config = _MODEL_CONFIG

    datalab_schema: ClassVar[dict[str, Any]] = {}
    """The JSON schema that this model was generated from."""

    def _python_name(self, key: str) -> str | None:
        for name, field in type(self).model_fields.items():
            if key in (name, field.alias):
                return name
        if self.__pydantic_extra__ and key in self.__pydantic_extra__:
            return key
        return None

    def __getitem__(self, key: str) -> Any:
        name = self._python_name(key)
        if name is None:
            raise KeyError(key)
        if name not in type(self).model_fields:
            # Extra fields could be shadowed by properties of the same name, e.g., `blocks`
            return self.__pydantic_extra__[name]  # type: ignore[index]
        return getattr(self, name)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, self._python_name(key) or key, value)

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and self._python_name(key) is not None

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value of the field `key` (by its server name), or `default`."""
        try:
            return self[key]
        except KeyError:
            return default

    def to_dict(self, **kwargs) -> dict[str, Any]:
        """Return a JSON-compatible dictionary of the model, using the server's field names.

        Any keyword arguments are passed through to `model_dump`.

        """
        kwargs.setdefault("mode", "json")
        kwargs.setdefault("by_alias", True)
        return self.model_dump(**kwargs)


class DatalabItem(DatalabModel):
    """The base class for all generated *datalab* item models (samples, cells,
    starting materials, equipment and any custom item types).

    Item models generated from a client are bound to it, so that instances can be
    created, saved and refreshed directly. Each model also carries the metadata
    that the server advertises for its type (see class attributes below).

    """

    item_type: ClassVar[str] = ""
    """The *datalab* `type` of this model, e.g., `samples` or `_my_samples`."""

    base_type: ClassVar[str | None] = None
    """For custom item types, the built-in type that the model extends
    (or `"items"` if it extends the generic `Item` model directly)."""

    base_fields: ClassVar[list[str]] = []
    """For custom item types, the fields inherited from the base type."""

    hidden_fields: ClassVar[list[str]] = []
    """Fields that the *datalab* UI hides for this type."""

    ui_color: ClassVar[str | None] = None
    """The accent colour used for this type in the *datalab* UI, if any."""

    datalab_client: ClassVar[DatalabClient | None] = None
    """The client that this model was generated from, if any."""

    _bound_client: Any = PrivateAttr(default=None)
    _synced_state: dict[str, Any] | None = PrivateAttr(default=None)

    @property
    def is_custom_type(self) -> bool:
        """Whether this is a deployment-specific custom item type."""
        return self.item_type.startswith("_")

    @property
    def client(self) -> DatalabClient:
        """The client that this item will use to talk to the server."""
        client = self._bound_client or type(self).datalab_client
        if client is None:
            raise RuntimeError(
                f"{type(self).__name__} is not bound to a `DatalabClient`; "
                "use the models from `client.models` to interact with a server."
            )
        return client

    @classmethod
    def from_api(cls, data: dict[str, Any], client: DatalabClient | None = None) -> DatalabItem:
        """Construct an instance from JSON data returned by the server.

        If the data does not validate against the schema (e.g., for legacy
        entries), a warning is raised and the model is constructed without
        validation, so that the data is still accessible.

        Parameters:
            data: The JSON data for the item, e.g., as returned by `get_item`.
            client: The client to bind the instance to (defaults to the client
                the model was generated from).

        """
        try:
            instance = cls.model_validate(data)
        except ValidationError as exc:
            warnings.warn(
                f"Data for item {data.get('item_id')!r} does not validate against the "
                f"{cls.__name__} schema; constructing without validation:\n{exc}"
            )
            instance = cls.model_construct(**data)
        instance._bind(client)
        instance._mark_synced()
        return instance

    def _bind(self, client: DatalabClient | None) -> None:
        if client is not None:
            self._bound_client = client

    def _mark_synced(self) -> None:
        """Record the current state as the last-known server state, used to compute `changes()`."""
        self._synced_state = self.to_dict()

    @property
    def is_synced(self) -> bool:
        """Whether this item has been loaded from, or created on, the server."""
        return self._synced_state is not None

    def changes(self) -> dict[str, Any]:
        """Return the fields (by server name) whose values differ from the last-known server state.

        For an item that has not been loaded from the server, all explicitly-set fields are returned.

        """
        self.validate()
        synced = self._synced_state
        if synced is None:
            return self.to_dict(exclude_unset=True)
        current = self.to_dict()
        return {k: v for k, v in current.items() if k not in synced or synced[k] != v}

    def validate(self) -> None:
        """Re-validate the item in place against its schema.

        Assigning to a field is validated immediately, but in-place mutations
        (e.g., appending a dictionary to `synthesis_constituents`) are not; this
        method is called before any data is sent to the server, so that such
        errors are raised locally.

        Raises:
            pydantic.ValidationError: If the item is not valid.

        """
        data = self.model_dump(by_alias=True, exclude_unset=True, warnings=False)
        validated = type(self).model_validate(data)
        for attr in ("__dict__", "__pydantic_extra__"):
            object.__setattr__(self, attr, getattr(validated, attr))

    def _update_from(self, other: DatalabItem) -> None:
        """Update this instance in place with the state of `other`."""
        for attr in ("__dict__", "__pydantic_extra__", "__pydantic_fields_set__"):
            object.__setattr__(self, attr, copy.copy(getattr(other, attr)))

    def create(
        self,
        collection_ids: str | list[str] | None = None,
        group_ids: str | list[str] | None = None,
    ) -> DatalabItem:
        """Create this item on the server, updating it in place with the
        server's response (e.g., generated `refcode`, `item_id` and `immutable_id`).

        If `item_id` is unset, the server will generate one.

        Parameters:
            collection_ids: The ID or IDs of the collection(s) to add the item to (optional).
            group_ids: The ID or IDs of the group(s) to share the item with (optional).

        Returns:
            The item itself.

        """
        if self.is_synced:
            raise RuntimeError(
                f"Item {self.get('item_id')!r} already exists on the server; use `save()` instead."
            )
        if isinstance(collection_ids, str):
            collection_ids = [collection_ids]
        if isinstance(group_ids, str):
            group_ids = [group_ids]
        created = self.client.create_item(
            item_data=self,
            collection_ids=collection_ids,
            group_ids=group_ids,
            as_model=False,
        )
        self._update_from(type(self).from_api(created))
        self._mark_synced()
        return self

    def save(self) -> dict[str, Any]:
        """Save any changes to this item back to the server.

        Only the fields that have changed since the item was last loaded or saved
        are sent; the server merges them into the stored entry.

        Returns:
            The fields that were sent to the server (empty if nothing had changed).

        """
        if not self.is_synced:
            raise RuntimeError(
                "This item has not been created on the server yet; use `create()` instead."
            )
        changes = self.changes()
        if not changes:
            return {}
        response = self.client.update_item(item_id=self["item_id"], item_data=changes)
        if "last_modified" in type(self).model_fields and response.get("last_modified"):
            self.last_modified = response["last_modified"]
        self._mark_synced()
        return changes

    def refresh(self, load_blocks: bool = False) -> DatalabItem:
        """Reload this item from the server in place, discarding any unsaved changes.

        Parameters:
            load_blocks: Whether to also load (i.e., re-render) the item's blocks.

        Returns:
            The item itself.

        """
        data = self.client.get_item(
            item_id=self["item_id"], load_blocks=load_blocks, as_model=False
        )
        self._update_from(type(self).from_api(data))
        self._mark_synced()
        return self

    @property
    def blocks(self) -> list[Any]:
        """The item's blocks, in display order."""
        blocks_obj = self.get("blocks_obj") or {}
        order = self.get("display_order") or list(blocks_obj)
        return [blocks_obj[block_id] for block_id in order if block_id in blocks_obj]

    def upload_file(
        self, file_path: Path | str, replace_file_id: str | None = None
    ) -> dict[str, Any]:
        """Upload a file and attach it to this item.

        The item is refreshed from the server afterwards so that its `files` are up to date
        (discarding any unsaved changes).

        Parameters:
            file_path: The path to the file to upload.
            replace_file_id: The ID of an existing file to replace with the uploaded file, if any.

        Returns:
            The uploaded file data (see `DatalabClient.upload_file`).

        """
        response = self.client.upload_file(
            item_id=self["item_id"], file_path=file_path, replace_file_id=replace_file_id
        )
        self.refresh()
        return response

    def add_block(self, block_type: str, file_ids: str | list[str] | None = None) -> Any:
        """Add a data block to this item, optionally attached to some already uploaded file(s).

        The item is refreshed from the server afterwards (discarding any unsaved changes).

        Parameters:
            block_type: The type of block to create, e.g., `"xrd"`; see `client.block_info`.
            file_ids: The ID(s) of file(s) attached to this item to attach to the block.

        Returns:
            The created block data.

        """
        block = self.client.create_data_block(
            item_id=self["item_id"], block_type=block_type, file_ids=file_ids
        )
        self.refresh()
        return block

    def __repr_args__(self):
        # Only show fields with non-default values to keep reprs readable for large models
        for name, value in super().__repr_args__():
            field = type(self).model_fields.get(name) if name else None
            if (
                field is not None
                and not field.is_required()
                and value == field.get_default(call_default_factory=True)
            ):
                continue
            yield name, value


def _identifier(name: str, fallback: str = "Model") -> str:
    """Turn an arbitrary string into a valid Python class name."""
    words = re.split(r"[^0-9a-zA-Z]+", name)
    ident = "".join(w[:1].upper() + w[1:] for w in words if w)
    if not ident:
        ident = fallback
    if ident[0].isdigit():
        ident = f"{fallback}{ident}"
    return ident


_RESERVED_NAMES = frozenset(dir(DatalabItem)) | frozenset(DatalabItem.__private_attributes__)


def _field_name(name: str, taken: set[str]) -> str:
    """Return a valid, non-clashing Python attribute name for a schema property."""
    pyname = re.sub(r"\W", "_", name).lstrip("_") or "field"
    if pyname[0].isdigit():
        pyname = f"field_{pyname}"
    while keyword.iskeyword(pyname) or pyname in _RESERVED_NAMES or pyname in taken:
        pyname = f"{pyname}_"
    return pyname


_STRING_FORMATS: dict[str, Any] = {
    "date-time": dt.datetime,
    "datetime": dt.datetime,
    "date": dt.date,
    "time": dt.time,
}


class _ModelBuilder:
    """Translates (the subset of) JSON Schema emitted by pydantic into pydantic models.

    Models for shared `$defs` (e.g., `File`, `Constituent`) are cached by content,
    so that the same definition used in multiple item schemas maps to a single class.

    """

    def __init__(self, module: str = __name__):
        self.module = module
        self._def_cache: dict[str, Any] = {}
        self._in_progress: dict[str, str] = {}
        self.models: dict[str, type[BaseModel]] = {}

    def _def_key(self, name: str, schema: dict) -> str:
        return f"{name}:{json.dumps(schema, sort_keys=True, default=str)}"

    def _resolve_ref(self, ref: str, defs: dict[str, Any]) -> Any:
        if not ref.startswith("#/$defs/"):
            raise ValueError(f"Unsupported JSON schema reference {ref!r}")
        name = ref.rsplit("/", 1)[-1]
        schema = defs[name]
        key = self._def_key(name, schema)
        if key in self._def_cache:
            return self._def_cache[key]
        if key in self._in_progress:
            # Recursive reference: return a forward reference to be resolved by `rebuild`
            return self._in_progress[key]
        class_name = _identifier(schema.get("title", name))
        self._in_progress[key] = class_name
        try:
            annotation = self.annotation(schema, defs, name_hint=class_name, is_def=True)
        finally:
            self._in_progress.pop(key)
        self._def_cache[key] = annotation
        return annotation

    def annotation(
        self, schema: dict | bool, defs: dict, name_hint: str = "Model", is_def: bool = False
    ) -> Any:
        """Return a type annotation for the given (sub)schema."""
        if schema is True or schema == {}:
            return Any
        if schema is False:
            return None
        if "$ref" in schema:
            return self._resolve_ref(schema["$ref"], defs)
        for combiner in ("anyOf", "oneOf"):
            if combiner in schema:
                members = [
                    self.annotation(s, defs, name_hint=f"{name_hint}{i}")
                    for i, s in enumerate(schema[combiner])
                ]
                non_null = [m for m in members if m is not type(None) and m is not None]
                if not non_null:
                    return type(None)
                union = non_null[0] if len(non_null) == 1 else Union[tuple(non_null)]  # noqa: UP007
                return Optional[union] if len(non_null) < len(members) else union  # noqa: UP045
        if "allOf" in schema:
            if len(schema["allOf"]) == 1:
                return self.annotation(schema["allOf"][0], defs, name_hint=name_hint)
            return Any
        if "const" in schema:
            return Literal[schema["const"]]
        if "enum" in schema:
            return Literal[tuple(schema["enum"])]

        type_ = schema.get("type")
        if isinstance(type_, list):
            return self.annotation(
                {"anyOf": [{**schema, "type": t} for t in type_]}, defs, name_hint=name_hint
            )
        if type_ == "string":
            if schema.get("format") in _STRING_FORMATS:
                return _STRING_FORMATS[schema["format"]]
            return self._constrained(str, schema, ("minLength", "maxLength", "pattern"))
        if type_ == "integer":
            return self._constrained(int, schema)
        if type_ == "number":
            return self._constrained(float, schema)
        if type_ == "boolean":
            return bool
        if type_ == "null":
            return type(None)
        if type_ == "array":
            if "prefixItems" in schema:
                prefix = tuple(self.annotation(s, defs, name_hint) for s in schema["prefixItems"])
                return tuple[prefix]  # type: ignore[valid-type]
            item = self.annotation(schema.get("items", {}), defs, f"{name_hint}Item")
            return list[item]  # type: ignore[valid-type]
        if type_ == "object" or "properties" in schema:
            if schema.get("properties"):
                return self.model(schema, defs, name=name_hint)
            additional = schema.get("additionalProperties", True)
            value = self.annotation(additional, defs, f"{name_hint}Value")
            return dict[str, value]  # type: ignore[valid-type]
        return Any

    _CONSTRAINTS: ClassVar[dict[str, str]] = {
        "minLength": "min_length",
        "maxLength": "max_length",
        "pattern": "pattern",
        "minimum": "ge",
        "maximum": "le",
        "exclusiveMinimum": "gt",
        "exclusiveMaximum": "lt",
        "multipleOf": "multiple_of",
    }

    def _constrained(self, base: type, schema: dict, keys: tuple[str, ...] | None = None) -> Any:
        keys = keys or ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf")
        constraints = {self._CONSTRAINTS[k]: schema[k] for k in keys if k in schema}
        if not constraints:
            return base
        return Annotated[base, Field(**constraints)]

    def fields(
        self, schema: dict, defs: dict, name: str, optional: frozenset[str] = frozenset()
    ) -> dict[str, Any]:
        """Return the `create_model` field definitions for an object schema."""
        required = set(schema.get("required", [])) - optional
        fields: dict[str, Any] = {}
        taken: set[str] = set()
        for prop, prop_schema in schema.get("properties", {}).items():
            pyname = _field_name(prop, taken)
            taken.add(pyname)
            annotation = self.annotation(prop_schema, defs, name_hint=_identifier(f"{name}_{prop}"))
            kwargs: dict[str, Any] = {}
            if pyname != prop:
                kwargs["alias"] = prop
            if prop_schema.get("description"):
                kwargs["description"] = prop_schema["description"]
            if prop_schema.get("title"):
                kwargs["title"] = prop_schema["title"]
            extra = {k: v for k, v in prop_schema.items() if k.startswith("datalab_")}
            if extra:
                kwargs["json_schema_extra"] = extra

            if "default" in prop_schema:
                default = prop_schema["default"]
                if isinstance(default, (list, dict)):
                    kwargs["default_factory"] = lambda d=default: copy.deepcopy(d)
                else:
                    kwargs["default"] = default
            elif prop in required:
                kwargs["default"] = ...
            elif prop_schema.get("type") == "array":
                # Fields with a `default_factory` on the server have no default in the schema
                kwargs["default_factory"] = list
            elif prop_schema.get("type") == "object":
                kwargs["default_factory"] = dict
            else:
                kwargs["default"] = None
            if kwargs.get("default") is not ...:
                # Be lenient with optional fields: the server's own models may coerce
                # `null` into e.g., an empty list, so its responses can contain `null`
                # where the schema does not allow it.
                annotation = Optional[annotation]  # noqa: UP045
            fields[pyname] = (annotation, Field(**kwargs))
        return fields

    def model(
        self,
        schema: dict,
        defs: dict,
        name: str,
        base: type[BaseModel] = DatalabModel,
        optional: frozenset[str] = frozenset(),
        class_vars: dict[str, Any] | None = None,
    ) -> type[BaseModel]:
        """Create a pydantic model from an object schema."""
        config = None
        if schema.get("additionalProperties") is False:
            config = ConfigDict(extra="forbid")
        model = create_model(  # type: ignore[call-overload]
            name,
            __base__=base,
            __module__=self.module,
            __doc__=schema.get("description"),
            **self.fields(schema, defs, name, optional=optional),
        )
        if config:
            model.model_config.update(config)
            model.model_rebuild(force=True)
        model.datalab_schema = schema
        for attr, value in (class_vars or {}).items():
            setattr(model, attr, value)
        self.models[name] = model
        return model

    def rebuild(self) -> None:
        """Resolve any forward references between the generated models."""
        namespace = dict(self.models)
        for model in self.models.values():
            if not model.__pydantic_complete__:
                model.model_rebuild(_types_namespace=namespace)


def model_from_schema(
    schema: dict[str, Any], name: str | None = None, base: type[BaseModel] = DatalabModel
) -> type[BaseModel]:
    """Create a pydantic model from a single (pydantic-generated) JSON schema.

    Parameters:
        schema: The JSON schema of an object, optionally with local `$defs`.
        name: The name of the model class (defaults to the schema's title).
        base: The base class of the generated model.

    Returns:
        The generated model class.

    """
    builder = _ModelBuilder()
    model = builder.model(
        schema,
        schema.get("$defs", {}),
        name=name or _identifier(schema.get("title", "Model")),
        base=base,
    )
    builder.rebuild()
    return model


class ItemModels(Mapping[str, type[DatalabItem]]):
    """A collection of generated item models, keyed by *datalab* item type.

    Models can be retrieved by type (`models["samples"]`, `models["_my_samples"]`)
    or by class name as an attribute (`models.Sample`, `models.MySample`).
    Shared nested models (e.g., `File`, `Constituent`) are also available as
    attributes.

    """

    def __init__(
        self,
        models: dict[str, type[DatalabItem]],
        nested: dict[str, type[BaseModel]] | None = None,
    ):
        self._models = models
        self._by_name = {**(nested or {}), **{m.__name__: m for m in models.values()}}

    def __getitem__(self, item_type: str) -> type[DatalabItem]:
        try:
            return self._models[item_type]
        except KeyError:
            raise KeyError(
                f"No model for item type {item_type!r}; available types: {list(self._models)}"
            ) from None

    def __iter__(self) -> Iterator[str]:
        return iter(self._models)

    def __len__(self) -> int:
        return len(self._models)

    def __getattr__(self, name: str) -> type[BaseModel]:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._by_name[name]
        except KeyError:
            raise AttributeError(
                f"No model named {name!r}; available item models: "
                f"{[m.__name__ for m in self._models.values()]}"
            ) from None

    def __dir__(self) -> list[str]:
        return sorted(set(super().__dir__()) | set(self._by_name))

    @property
    def custom_types(self) -> dict[str, type[DatalabItem]]:
        """The deployment-specific custom item types."""
        return {t: m for t, m in self._models.items() if t.startswith("_")}

    def for_data(self, data: dict[str, Any]) -> type[DatalabItem]:
        """Return the model for some item data, based on its `type`."""
        return self[data["type"]]

    def __repr__(self) -> str:
        return f"ItemModels({', '.join(f'{t!r}: {m.__name__}' for t, m in self._models.items())})"


def _normalise_types_data(types_data: Any) -> list[dict[str, Any]]:
    """Accept either the `/info/types` response (or its `data` list), or a plain
    mapping from item type to JSON schema, and return a list of `{id, attributes}` dicts."""
    if isinstance(types_data, dict) and "data" in types_data:
        types_data = types_data["data"]
    if isinstance(types_data, dict):
        return [{"id": t, "attributes": {"schema": s}} for t, s in types_data.items()]
    return list(types_data)


def build_item_models(
    types_data: Any, client: DatalabClient | None = None, module: str = __name__
) -> ItemModels:
    """Build item models from the schemas advertised by a *datalab* instance.

    Parameters:
        types_data: The response from the `/info/types` endpoint (or its `data` list),
            or a mapping from item type to JSON schema.
        client: The client to bind the generated models to, if any.
        module: The module name to assign to the generated classes.

    Returns:
        An `ItemModels` collection of the generated models.

    """
    entries = _normalise_types_data(types_data)
    builder = _ModelBuilder(module=module)
    models: dict[str, type[DatalabItem]] = {}

    # Build built-in types first, so that custom types can subclass them
    entries.sort(key=lambda entry: entry["id"].startswith("_"))
    for entry in entries:
        item_type = entry["id"]
        attributes = entry.get("attributes", {})
        schema = attributes["schema"]
        base_type = attributes.get("base_type")
        base = models.get(base_type, DatalabItem) if base_type else DatalabItem

        name = _identifier(schema.get("title") or item_type, fallback="Item")
        if name in {m.__name__ for m in models.values()} or name in _RESERVED_NAMES:
            name = _identifier(item_type, fallback="Item")

        models[item_type] = builder.model(  # type: ignore[assignment]
            schema,
            schema.get("$defs", {}),
            name=name,
            base=base,
            # Allow items to be created locally without an ID, for the server to generate one
            optional=frozenset({"item_id"}),
            class_vars={
                "item_type": item_type,
                "base_type": base_type,
                "base_fields": list(attributes.get("base_fields") or []),
                "hidden_fields": list(attributes.get("hidden_fields") or []),
                "ui_color": attributes.get("ui_color"),
                "datalab_client": client,
            },
        )

    builder.rebuild()
    nested = {name: m for name, m in builder.models.items() if not issubclass(m, DatalabItem)}
    return ItemModels(models, nested=nested)
