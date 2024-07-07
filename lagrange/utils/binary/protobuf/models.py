import inspect
from types import GenericAlias
from typing import cast, Dict, List, Tuple, Type, TypeVar, Union, Generic, Any, Callable, Mapping, overload
from typing_extensions import Optional, Self, TypeAlias, dataclass_transform, get_origin, get_args

from .coder import Proto, proto_decode, proto_encode

_ProtoTypes = Union[str, list, dict, bytes, int, float, bool, "ProtoStruct"]

T = TypeVar("T", str, list, dict, bytes, int, float, bool, "ProtoStruct")
V = TypeVar("V")
NT: TypeAlias = Dict[int, Union[_ProtoTypes, "NT"]]
NoneType = type(None)


class ProtoField(Generic[T]):
    def __init__(self, tag: int, default: T):
        if tag <= 0:
            raise ValueError("Tag must be a positive integer")
        self._tag = tag
        self._default = default

    @property
    def tag(self) -> int:
        return self._tag

    def get_default(self) -> T:
        return self._default


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
    default: Optional[Any] = ...,
    default_factory: Optional[Any] = ...,
    init: bool = True,
    repr: bool = True,
    metadata: Optional[Mapping[Any, Any]] = None,
    kw_only: bool = False,
) -> "Any":
    return ProtoField(tag, default)


@dataclass_transform(kw_only_default=True, field_specifiers=(proto_field,))
class ProtoStruct:
    _anno_map: Dict[str, Tuple[Type[_ProtoTypes], ProtoField[Any]]]
    _proto_debug: bool

    def __init__(self, *args, **kwargs):
        undefined_params: List[str] = []
        args = list(args)
        for name, (typ, field) in self._anno_map.items():
            if args:
                self._set_attr(name, typ, args.pop(0))
            elif name in kwargs:
                self._set_attr(name, typ, kwargs.pop(name))
            else:
                if field.get_default() is not ...:
                    self._set_attr(name, typ, field.get_default())
                else:
                    undefined_params.append(name)
        if undefined_params:
            raise AttributeError(
                "Undefined parameters in '{}': {}".format(self, undefined_params)
            )

    def __init_subclass__(cls, **kwargs):
        cls._anno_map = cls._get_annotations()
        cls._proto_debug = kwargs.pop("debug") if "debug" in kwargs else False
        super().__init_subclass__(**kwargs)

    def __repr__(self) -> str:
        attrs = ""
        for k, v in self._get_stored_mapping().items():
            attrs += f"{k}={v}, "
        return f"{self.__class__.__name__}({attrs[:-2]})"

    def _set_attr(self, name: str, data_typ: Type[V], value: V) -> None:
        # if get_origin(data_typ) is Union:
        #     data_typ = (typ for typ in get_args(data_typ) if typ is not NoneType)  # type: ignore
        if isinstance(data_typ, GenericAlias):  # force ignore
            pass
        elif not isinstance(value, data_typ) and value is not None:
            raise TypeError(
                "'{}' is not a instance of type '{}'".format(value, data_typ)
            )
        setattr(self, name, value)

    @classmethod
    def _get_annotations(
        cls,
    ) -> Dict[str, Tuple[Type[_ProtoTypes], "ProtoField"]]:  # Name: (ReturnType, ProtoField)
        annotations: Dict[str, Tuple[Type[_ProtoTypes], "ProtoField"]] = {}
        for obj in reversed(inspect.getmro(cls)):
            if obj in (ProtoStruct, object):  # base object, ignore
                continue
            for name, typ in obj.__annotations__.items():
                if name[0] == "_":  # ignore internal var
                    continue
                if not hasattr(obj, name):
                    raise AttributeError(f"attribute ‘{name}' not defined")
                field = getattr(obj, name)  # type: ProtoField

                if not isinstance(field, ProtoField):
                    raise TypeError("attribute '{name}' is not a ProtoField object")

                if hasattr(typ, "__origin__"):
                    typ = typ.__origin__[typ.__args__[0]]
                annotations[name] = (typ, field)

        return annotations

    @classmethod
    def _get_field_mapping(cls) -> Dict[int, Tuple[str, Type[_ProtoTypes]]]:  # Tag, (Name, Type)
        field_mapping: Dict[int, Tuple[str, Type[_ProtoTypes]]] = {}
        for name, (typ, field) in cls._anno_map.items():
            field_mapping[field.tag] = (name, typ)
        return field_mapping

    def _get_stored_mapping(self) -> Dict[str, NT]:
        stored_mapping: Dict[str, NT] = {}
        for name, (_, _) in self._anno_map.items():
            stored_mapping[name] = getattr(self, name)
        return stored_mapping

    def _encode(self, v: _ProtoTypes) -> NT:
        if isinstance(v, ProtoStruct):
            v = v.encode()
        return v

    def encode(self) -> bytes:
        pb_dict: NT = {}
        for name, (_, field) in self._anno_map.items():
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
    def _decode(cls, typ: Type[_ProtoTypes], value):
        if issubclass(typ, ProtoStruct):
            return typ.decode(value)
        elif typ == str:
            return value.decode(errors="ignore")
        elif typ == dict:
            return proto_decode(value)
        elif typ == bool:
            return value == 1
        elif typ == list:
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
        pb_dict: Proto = proto_decode(data, 0)
        mapping = cls._get_field_mapping()

        kwargs = {}
        for tag, (name, typ) in mapping.items():
            if tag not in pb_dict:
                _, field = cls._anno_map[name]
                if field.get_default() is not ...:
                    kwargs[name] = field.get_default()
                    continue

                raise KeyError(f"tag {tag} not found in '{cls.__name__}'")
            kwargs[name] = cls._decode(typ, pb_dict.pop(tag))
        if pb_dict and cls._proto_debug:  # unhandled tags
            print(f"unhandled tags on '{cls.__name__}': {pb_dict}")

        return cls(**kwargs)


