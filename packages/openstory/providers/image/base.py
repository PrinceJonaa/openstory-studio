from pathlib import Path
from typing import Protocol

from openstory.domain.assets import ImageGenerationResult


class ImageGenerationProvider(Protocol):
    async def generate(
        self,
        *,
        prompt: str,
        negative_prompt: str | None,
        width: int,
        height: int,
        seed: int | None,
        output_path: Path,
        references: list[Path] | None = None,
    ) -> ImageGenerationResult:
        raise NotImplementedError
