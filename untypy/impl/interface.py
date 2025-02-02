from collections.abc import Iterator, Iterable
from typing import TypeVar, Optional, Any, Generic, Dict, List, Set

from untypy.error import UntypyAttributeError, UntypyTypeError
from untypy.impl.wrappedclass import WrappedType
from untypy.interfaces import TypeCheckerFactory, TypeChecker, CreationContext, ExecutionContext
from untypy.util import ReplaceTypeExecutionContext

K = TypeVar("K")
V = TypeVar("V")


class WDict(Generic[K, V], dict):
    def __getitem__(self, item: K) -> V:
        pass

    def __setitem__(self, key: K, value: V) -> None:
        pass


I = TypeVar("I")


class WList(Generic[I], list):
    def __getitem__(self, item: int) -> I:
        pass

    def __setitem__(self, key: int, value: I) -> None:
        pass


I = TypeVar("I")


class WSet(Generic[I], set):
    def __contains__(self, item: I) -> bool:
        pass

    def add(self, elem: I) -> None:
        pass


I = TypeVar("I")


class WIterable(Generic[I]):
    def __iter__(self) -> Iterator[I]:
        pass


InterfaceMapping = {
    dict: (WDict,),
    Dict: (WDict,),
    list: (WList,),
    List: (WList,),
    set: (WSet,),
    Set: (WSet,),
    Iterable: (WIterable),
}


class InterfaceFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if hasattr(annotation, '__origin__') and hasattr(annotation,
                                                         '__args__') and annotation.__origin__ in InterfaceMapping:
            (protocol,) = InterfaceMapping[annotation.__origin__]
            bindings = protocol.__parameters__  # args of Generic super class
            origin = annotation.__origin__

            inner_checkers = []
            for param in annotation.__args__:
                ch = ctx.find_checker(param)
                if ch is None:
                    raise UntypyAttributeError(f"Could not resolve annotation {param} inside of {annotation}")
                inner_checkers.append(ch)
            if len(inner_checkers) != len(bindings):
                raise UntypyAttributeError(f"Expected {len(bindings)} type arguments inside of {annotation}")

            name = f"{origin.__name__}[" + (', '.join(map(lambda t: t.describe(), inner_checkers))) + "]"

            bindings = dict(zip(bindings, annotation.__args__))
            ctx.with_typevars(bindings)
            template = WrappedType(protocol, ctx.with_typevars(bindings), name=name, implementation_template=origin,
                                   declared=ctx.declared_location())
            return InterfaceChecker(origin, template, name)
        else:
            return None


class InterfaceChecker(TypeChecker):

    def __init__(self, origin, template, name):
        self.origin = origin
        self.template = template
        self.name = name
        pass

    def may_change_identity(self) -> bool:
        return True

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if not issubclass(type(arg), self.origin):
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

        instance = self.template.__new__(self.template)
        instance._WrappedClassFunction__inner = arg
        instance._WrappedClassFunction__return_ctx = ReplaceTypeExecutionContext(ctx, self.name)
        return instance

    def describe(self) -> str:
        return self.name
