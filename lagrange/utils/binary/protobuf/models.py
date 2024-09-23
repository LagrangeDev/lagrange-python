import sys
from dataclasses import MISSING
from types import GenericAlias
from typing import cast, TypeVar, Union, Any, Callable, overload, get_origin, ForwardRef, get_args
from collections.abc import Mapping
from typing_extensions import Self, TypeAlias, dataclass_transform
from typing import Optional, ClassVar

from .coder import Proto, proto_decode, proto_encode

_ProtoTypes = Union[str, list, dict, bytes, int, float, bool, "ProtoStruct"]

T = TypeVar("T", bound=_ProtoTypes)
V = TypeVar("V")
NT: TypeAlias = dict[int, Union[_ProtoTypes, "NT"]]
NoneType = type(None)


class ProtoField:
    name: str
    type: Any

    def __init__(self, tag: int, default: Any, default_factory: Any):
        if tag <= 0:
            raise ValueError("Tag must be a positive integer")
        self.tag = tag
        self._default = default
        self._default_factory = default_factory

    def ensure_annotation(self, name: str, type_: Any) -> None:
        self.name = name
        self.type = type_

    def get_default(self) -> Any:
        if self._default is not MISSING:
            return self._default
        elif self._default_factory is not MISSING:
            return self._default_factory()
        return MISSING

    @property
    def type_without_optional(self) -> Any:
        if get_origin(self.type) is Union:
            return get_args(self.type)[0]
        return self.type


@overload  # `default` and `default_factory` are optional and mutually exclusive.
def proto_field(
    tag: int,
    *,
    default: Optional[T],
    init: bool = True,
    repr: bool = True,
    metadata: Optional[Mapping[Any, Any]] = None,
    kw_only: bool = ...,
) -> T:
    ...


@overload
def proto_field(
    tag: int,
    *,
    default_factory: Callable[[], T],
    init: bool = True,
    repr: bool = True,
    metadata: Optional[Mapping[Any, Any]] = None,
    kw_only: bool = ...,
) -> T:
    ...


@overload
def proto_field(
    tag: int,
    *,
    init: bool = True,
    repr: bool = True,
    metadata: Optional[Mapping[Any, Any]] = None,
    kw_only: bool = ...,
) -> Any:
    ...


def proto_field(
    tag: int,
    *,
    default: Optional[Any] = MISSING,
    default_factory: Optional[Any] = MISSING,
    init: bool = True,
    repr: bool = True,
    metadata: Optional[Mapping[Any, Any]] = None,
    kw_only: bool = False,
) -> "Any":
    return ProtoField(tag, default, default_factory)


@dataclass_transform(kw_only_default=True, field_specifiers=(proto_field,))
class ProtoStruct:
    __fields__: ClassVar[dict[str, ProtoField]]
    __proto_debug__: ClassVar[bool]
    __proto_evaluated__: ClassVar[bool] = False

    def check_type(self, value: Any, typ: Any) -> bool:
        if typ is Any:
            return True
        if typ is list:
            return isinstance(value, list)
        if typ is dict:
            return isinstance(value, dict)
        if isinstance(typ, GenericAlias):
            if get_origin(typ) is list:
                return all(self.check_type(v, get_args(typ)[0]) for v in value)
            if get_origin(typ) is dict:
                return all(self.check_type(k, get_args(typ)[0]) and self.check_type(v, get_args(typ)[1]) for k, v in value.items())
            return False
        if get_origin(typ) is Union:  # Should Only be Optional
            return self.check_type(value, get_args(typ)[0]) if value is not None else True
        if isinstance(value, typ):
            return True
        return False  # or True if value is None else False

    def _evaluate(self):
        for base in reversed(self.__class__.__mro__):
            if base in (ProtoStruct, object):
                continue
            if getattr(base, '__proto_evaluated__', False):
                continue
            base_globals = getattr(sys.modules.get(base.__module__, None), '__dict__', {})
            base_locals = dict(vars(base))
            base_globals, base_locals = base_locals, base_globals
            for field in base.__fields__.values():
                if isinstance(field.type, str):
                    field.type = ForwardRef(field.type, is_argument=False, is_class=True)._evaluate(
                        base_globals, base_locals, recursive_guard=frozenset()
                    )
            base.__proto_evaluated__ = True

    def __init__(self, **kwargs):
        undefined_params: list[str] = []
        self._evaluate()
        for name, field in self.__fields__.items():
            if name in kwargs:
                value = kwargs.pop(name)
                if not self.check_type(value, field.type):
                    raise TypeError(
                        f"'{value}' is not a instance of type '{field.type}'"
                    )
                setattr(self, name, value)
            else:
                if (de := field.get_default()) is not MISSING:
                    setattr(self, name, de)
                else:
                    undefined_params.append(name)
        if undefined_params:
            raise AttributeError(
                f"Undefined parameters in '{self}': {undefined_params}"
            )
        super().__init__(**kwargs)

    @classmethod
    def _process_field(cls):
        fields = {}
        cls_annotations = cls.__dict__.get('__annotations__', {})
        cls_fields: list[ProtoField] = []
        for name, typ in cls_annotations.items():
            field = getattr(cls, name, MISSING)
            if field is MISSING:
                raise TypeError(f'{name!r} should define its proto_field!')
            field.ensure_annotation(name, typ)
            cls_fields.append(field)

        for f in cls_fields:
            fields[f.name] = f
            if f._default is MISSING:
                delattr(cls, f.name)

        for name, value in cls.__dict__.items():
            if isinstance(value, ProtoField) and not name in cls_annotations:
                raise TypeError(f'{name!r} is a proto_field but has no type annotation')

        cls.__fields__ = fields

    def __init_subclass__(cls, **kwargs):
        cls.__proto_debug__ = kwargs.pop("debug") if "debug" in kwargs else False
        cls._process_field()
        super().__init_subclass__(**kwargs)

    def __repr__(self) -> str:
        attrs = ""
        for k, v in vars(self).items():
            if k.startswith("_"):
                continue
            attrs += f"{k}={v!r}, "
        return f"{self.__class__.__name__}({attrs})"


    # @classmethod
    # def _get_field_mapping(cls) -> dict[int, tuple[str, type[_ProtoTypes]]]:  # Tag, (Name, Type)
    #     field_mapping: dict[int, tuple[str, type[_ProtoTypes]]] = {}
    #     for name, (typ, field) in cls._anno_map.items():
    #         field_mapping[field.tag] = (name, typ)
    #     return field_mapping

    # def _get_stored_mapping(self) -> dict[str, NT]:
    #     stored_mapping: dict[str, NT] = {}
    #     for name, (_, _) in self._anno_map.items():
    #         stored_mapping[name] = getattr(self, name)
    #     return stored_mapping

    def _encode(self, v: _ProtoTypes) -> NT:
        if isinstance(v, ProtoStruct):
            v = v.encode()
        return v  # type: ignore

    def encode(self) -> bytes:
        pb_dict: NT = {}
        for name, field in self.__fields__.items():
            tag = field.tag
            if tag in pb_dict:
                raise ValueError(f"duplicate tag: {tag}")
            value: _ProtoTypes = getattr(self, name)
            if isinstance(value, list):
                pb_dict[tag] = [self._encode(v) for v in value]
            else:
                pb_dict[tag] = self._encode(value)
        return proto_encode(cast(Proto, pb_dict))

    @classmethod
    def _decode(cls, typ: type[_ProtoTypes], value):
        if issubclass(typ, ProtoStruct):
            return typ.decode(value)
        elif typ is str:
            return value.decode(errors="ignore")
        elif typ is dict:
            return proto_decode(value).proto
        elif typ is bool:
            return value == 1
        elif typ is list:
            if not isinstance(value, list):
                return [value]
            return value
        elif isinstance(typ, GenericAlias):
            if typ.__name__.lower() == "list":
                real_typ = typ.__args__[0]
                ret = []
                if isinstance(value, list):
                    for v in value:
                        ret.append(cls._decode(real_typ, v))
                else:
                    ret.append(cls._decode(real_typ, value))
                return ret
        elif isinstance(value, typ):
            return value
        else:
            raise NotImplementedError(f"unknown type '{typ}' and data {value}")

    @classmethod
    def decode(cls, data: bytes) -> Self:
        if not data:
            return None  # type: ignore
        pb_dict: Proto = proto_decode(data, 0).proto

        kwargs = {}
        for _, field in cls.__fields__.items():
            if field.tag not in pb_dict:
                if (de := field.get_default()) is not MISSING:
                    kwargs[field.name] = de
                    continue

                raise KeyError(f"tag {field.tag} not found in '{cls.__name__}'")
            kwargs[field.name] = cls._decode(field.type_without_optional, pb_dict.pop(field.tag))
        if pb_dict and cls.__proto_debug__:  # unhandled tags
            pass

        return cls(**kwargs)
