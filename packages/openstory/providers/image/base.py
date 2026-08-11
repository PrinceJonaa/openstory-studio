from pathlib import Path
from typing import Protocol

from openstory.domain.assets import ImageGenerationResult


class ImageProviderError(RuntimeError):
    """Base error for replaceable image providers."""


class ImageProviderUnavailableError(ImageProviderError):
    """Raised when a configured provider cannot run in the current environment."""


class ImageGenerationError(ImageProviderError):
    """Raised when a provider runs but cannot produce a valid image."""


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
