from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class TextGenerationProvider(Protocol):
    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
        temperature: float = 0.2,
    ) -> T:
        raise NotImplementedError
