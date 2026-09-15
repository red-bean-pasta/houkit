from typing import Generic, TypeVar, Sequence, Iterator, Any


T = TypeVar("T")


class Moject(Generic[T]):
    """Messaged object"""
    def __init__(self, value: T, messages: Sequence[str] = ()):
        self.value = value
        self.messages = list(messages)

    @property
    def has_messages(self) -> bool:
        return bool(self.messages)

    def add_message(self, message: str) -> None:
        self.messages.append(message)

    def add_messages(self, messages: Sequence[str]) -> None:
        self.messages.extend(messages)

    def __iter__(self) -> Iterator[Any]:
        yield self.value
        yield self.messages

    def __getitem__(self, index: int) -> Any:
        return (self.value, self.messages)[index]

    def __len__(self) -> int:
        return 2

    @staticmethod
    def retain(value: T, *results: "Moject") -> "Moject[T]":
        messages: list[str] = []
        for r in results:
            if isinstance(r, Moject):
                messages.extend(r.messages)
        return Moject(value, messages)