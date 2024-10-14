import sys
from dataclasses import MISSING
from types import GenericAlias
from typing import cast, TypeVar, Union, Any, Callable, overload, get_origin, get_args, ForwardRef
from collections.abc import Mapping
from typing_extensions import Self, TypeAlias, dataclass_transform
from typing import Optional, ClassVar
import typing

from .coder import Proto, proto_decode, proto_encode
from .util import eval_type

_ProtoTypes = Union[str, list, dict, bytes, int, float, bool, "ProtoStruct"]

T = TypeVar("T", bound=_ProtoTypes)
V = TypeVar("V")
NT: TypeAlias = dict[int, Union[_ProtoTypes, "NT"]]
NoneType = type(None)


def _get_all_args(tp):
    if args := get_args(tp):
        for arg in args:
            yield from _get_all_args(arg)
        yield from args


class ProtoField:
    name: str
    type: Any

    def __init__(self, tag: int, default: Any, default_factory: Any):
        if tag <= 0:
            raise ValueError("Tag must be a positive integer")
        self.tag = tag
        self.default = default
        self.default_factory = default_factory
        self._unevaluated = False

    def ensure_annotation(self, name: str, type_: Any) -> None:
        self.name = name
        self.type = type_
        if isinstance(type_, str):
            self._unevaluated = True
        elif (args := [*_get_all_args(type_)]) and any(isinstance(a, str) for a in args):
            self._unevaluated = True

    def get_default(self) -> Any:
        if self.default is not MISSING:
            return self.default
        elif self.default_factory is not MISSING:
            return self.default_factory()
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


def _decode(typ: type[_ProtoTypes], raw):
    if isinstance(typ, str):
        raise ValueError(
            f"ForwardRef '{typ}' not resolved. "
            f"Please call ProtoStruct.update_forwardref({{'{typ}': {typ}}}) before decoding"
        )
    if issubclass(typ, ProtoStruct):
        return typ.decode(raw)
    elif typ is str:
        return raw.decode(errors="ignore")
    elif typ is dict:
        return proto_decode(raw).proto
    elif typ is bool:
        return raw == 1
    elif typ is list:
        if not isinstance(raw, list):
            return [raw]
        return raw
    elif isinstance(typ, GenericAlias) and get_origin(typ) is list:
        real_typ = get_args(typ)[0]
        ret = []
        if isinstance(raw, list):
            for v in raw:
                ret.append(_decode(real_typ, v))
        else:
            ret.append(_decode(real_typ, raw))
        return ret
    elif isinstance(raw, typ):
        return raw
    else:
        raise NotImplementedError(f"unknown type '{typ}' and data {raw}")


def check_type(value: Any, typ: Any) -> bool:
    if isinstance(typ, str):
        raise ValueError(
            f"ForwardRef '{typ}' not resolved. "
            f"Please call ProtoStruct.update_forwardref({{'{typ}': {typ}}}) before decoding"
        )
    if typ is Any:
        return True
    if typ is list:
        return isinstance(value, list)
    if typ is dict:
        return isinstance(value, dict)
    if isinstance(typ, GenericAlias):
        if get_origin(typ) is list:
            return all(check_type(v, get_args(typ)[0]) for v in value)
        if get_origin(typ) is dict:
            return all(check_type(k, get_args(typ)[0]) and check_type(v, get_args(typ)[1]) for k, v in value.items())
        return False
    if get_origin(typ) is Union:  # Should Only be Optional
        return check_type(value, get_args(typ)[0]) if value is not None else True
    if isinstance(value, typ):
        return True
    return True if value is None else False  # proto3 std


_unevaluated_classes: set[type["ProtoStruct"]] = set()


@dataclass_transform(kw_only_default=True, field_specifiers=(proto_field,))
class ProtoStruct:
    __proto_fields__: ClassVar[dict[str, ProtoField]]
    __proto_debug__: ClassVar[bool]

    def __init__(self, __from_raw: bool = False, /, **kwargs):
        undefined_params: list[ProtoField] = []
        for name, field in self.__proto_fields__.items():
            if name in kwargs:
                value = kwargs.pop(name)
                if __from_raw:
                    value = _decode(field.type_without_optional, value)
                if not check_type(value, field.type):
                    raise TypeError(
                        f"'{value}' is not a instance of type '{field.type}'"
                    )
                setattr(self, name, value)
            else:
                if (de := field.get_default()) is not MISSING:
                    setattr(self, name, de)
                else:
                    undefined_params.append(field)
        if undefined_params:
            raise AttributeError(
                f"Missing required parameters: {', '.join(f'{f.name}({f.tag})' for f in undefined_params)}"
            )

    @classmethod
    def _process_field(cls):
        fields = {}

        for b in cls.__mro__[-1:0:-1]:
            base_fields = getattr(b, "__proto_fields__", None)
            if base_fields is not None:
                for f in base_fields.values():
                    fields[f.name] = f

        cls_annotations = cls.__dict__.get('__annotations__', {})
        cls_fields: list[ProtoField] = []
        for name, typ in cls_annotations.items():
            field = getattr(cls, name, MISSING)
            if field is MISSING:
                raise TypeError(f'{name!r} should define its proto_field!')
            field.ensure_annotation(name, typ)
            if field._unevaluated:
                _unevaluated_classes.add(cls)
            cls_fields.append(field)

        for f in cls_fields:
            fields[f.name] = f
            if f.default is MISSING:
                delattr(cls, f.name)

        for name, value in cls.__dict__.items():
            if isinstance(value, ProtoField) and not name in cls_annotations:
                raise TypeError(f'{name!r} is a proto_field but has no type annotation')

        cls.__proto_fields__ = fields

    @classmethod
    def update_forwardref(cls, mapping: dict[str, "type[ProtoStruct]"]):
        """更新 ForwardRef"""
        for field in cls.__proto_fields__.values():
            if not field._unevaluated:
                continue
            try:
                typ = field.type
                if isinstance(typ, str):
                    typ = ForwardRef(typ, is_argument=False, is_class=True)
                field.type = eval_type(typ, mapping, mapping)  # type: ignore
                field._unevaluated = False
            except NameError:
                pass

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
        return f"{self.__class__.__name__}({attrs[:-2]})"

    def encode(self) -> bytes:
        pb_dict: NT = {}

        def _encode(v: _ProtoTypes) -> NT:
            if isinstance(v, ProtoStruct):
                v = v.encode()
            return v  # type: ignore

        for name, field in self.__proto_fields__.items():
            tag = field.tag
            if tag in pb_dict:
                raise ValueError(f"duplicate tag: {tag}")
            value: _ProtoTypes = getattr(self, name)
            if isinstance(value, list):
                pb_dict[tag] = [_encode(v) for v in value]
            else:
                pb_dict[tag] = _encode(value)
        return proto_encode(cast(Proto, pb_dict))

    @classmethod
    def decode(cls, data: bytes) -> Self:
        if not data:
            return None  # type: ignore
        pb_dict: Proto = proto_decode(data, 0).proto

        kwargs = {
            field.name: pb_dict.pop(field.tag)
            for field in cls.__proto_fields__.values()
            if field.tag in pb_dict
        }

        if pb_dict and cls.__proto_debug__:  # unhandled tags
            print(f"DEBUG: unhandled tags '{pb_dict}' on {cls}")
        return cls(True, **kwargs)


def evaluate_all():
    modules = set()
    for cls in _unevaluated_classes:
        modules.add(cls.__module__)
        for base in cls.__mro__[-1:0:-1][2:]:
            modules.add(base.__module__)
    globalns = {}
    for module in modules:
        globalns.update(getattr(sys.modules.get(module, None), "__dict__", {}))
    for cls in _unevaluated_classes:
        cls.update_forwardref(globalns)
    _unevaluated_classes.clear()
    modules.clear()
    globalns.clear()
    del modules
    del globalns
