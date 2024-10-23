import collections.abc
import functools
import operator
import sys
import types
import typing
from typing import ForwardRef, List
import typing_extensions
from typing_extensions import ParamSpec

_GenericAlias = type(List[int])
SpecialType = (_GenericAlias, types.GenericAlias)

if sys.version_info >= (3, 10):
    SpecialType += (types.UnionType,)

if sys.version_info >= (3, 11):
    eval_type = typing._eval_type  # type: ignore
else:
    def _is_param_expr(arg):
        return arg is ... or isinstance(arg, (tuple, list, ParamSpec, typing_extensions._ConcatenateGenericAlias))  # type: ignore


    def _should_unflatten_callable_args(typ, args):
        """Internal helper for munging collections.abc.Callable's __args__.

        The canonical representation for a Callable's __args__ flattens the
        argument types, see https://github.com/python/cpython/issues/86361.

        For example::

            >>> import collections.abc
            >>> P = ParamSpec('P')
            >>> collections.abc.Callable[[int, int], str].__args__ == (int, int, str)
            True
            >>> collections.abc.Callable[P, str].__args__ == (P, str)
            True

        As a result, if we need to reconstruct the Callable from its __args__,
        we need to unflatten it.
        """
        return (
            typ.__origin__ is collections.abc.Callable
            and not (len(args) == 2 and _is_param_expr(args[0]))
        )


    def eval_type(t, globalns, localns, recursive_guard=frozenset()):
        """Evaluate all forward references in the given type t.

        For use of globalns and localns see the docstring for get_type_hints().
        recursive_guard is used to prevent infinite recursion with a recursive
        ForwardRef.
        """
        if isinstance(t, ForwardRef):
            return t._evaluate(globalns, localns, recursive_guard)
        if isinstance(t, SpecialType):
            if isinstance(t, types.GenericAlias):
                args = tuple(
                    ForwardRef(arg) if isinstance(arg, str) else arg
                    for arg in t.__args__
                )
                is_unpacked = getattr(t, "__unpacked__", False)
                if _should_unflatten_callable_args(t, args):
                    t = t.__origin__[(args[:-1], args[-1])]  # type: ignore
                else:
                    t = t.__origin__[args]  # type: ignore
                if is_unpacked:
                    t = typing_extensions.Unpack[t]
            ev_args = tuple(eval_type(a, globalns, localns, recursive_guard) for a in t.__args__)  # type: ignore
            if ev_args == t.__args__:  # type: ignore
                return t
            if isinstance(t, types.GenericAlias):
                return types.GenericAlias(t.__origin__, ev_args)
            if hasattr(types, "UnionType") and isinstance(t, types.UnionType):  # type: ignore
                return functools.reduce(operator.or_, ev_args)
            return t.copy_with(ev_args)  # type: ignore
        return t
