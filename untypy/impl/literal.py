from untypy.error import UntypyTypeError
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from typing import Any, Optional, Literal

LiteralType = type(Literal[42])


class LiteralFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) is LiteralType:
            return LiteralChecker(annotation.__args__)
        else:
            return None


class LiteralChecker(TypeChecker):
    inner: list[Any]

    def __init__(self, inner: list[Any]):
        self.inner = inner

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if arg in self.inner:
            return arg
        else:
            raise ctx.wrap(UntypyTypeError(
                arg,
                self.describe()
            ))

    def describe(self) -> str:
        return f"Literal[{str(self.inner)}]"
