from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from interface import Interface


class Link:
    def __init__(self, interfaces: List["Interface"]) -> None:
        self.interfaces = sorted(interfaces)

    def __eq__(self, other) -> bool:
        return all(
            int1 == int2
            for int1, int2 in zip(self.interfaces, other.interfaces)
        )

    def __hash__(self) -> int:
        return hash(tuple(self.interfaces))

    def __str__(self) -> str:
        return " <-> ".join(
            str(interface)
            for interface in self.interfaces
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__qualname__}("
            f"interfaces={self.interfaces})"
        )

    @property
    def is_point_to_point(self) -> bool:
        return len(self.interfaces) == 2

