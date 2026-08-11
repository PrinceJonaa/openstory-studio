import asyncio
import re
import shutil
from pathlib import Path
from time import perf_counter

from PIL import Image, UnidentifiedImageError

from openstory.domain.assets import ImageGenerationResult
from openstory.providers.image.base import (
    ImageGenerationError,
    ImageProviderUnavailableError,
)


class MLXGenUnavailableError(ImageProviderUnavailableError):
    pass


class MLXGenGenerationError(ImageGenerationError):
    pass


_ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_OUTPUT_LIMIT = 1_000


class MLXGenImageProvider:
    def __init__(self, executable: str, model: str) -> None:
        if not executable.strip():
            raise ValueError("MLX-Gen executable cannot be empty.")
        if not model.strip():
            raise ValueError("MLX-Gen model cannot be empty.")
        self.executable = executable
        self.model = model

    def is_available(self) -> bool:
        return shutil.which(self.executable) is not None

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
        if width <= 0 or height <= 0:
            raise ValueError("Image dimensions must be positive.")
        if output_path.exists():
            raise FileExistsError(f"Render output already exists: {output_path}")
        if references:
            raise MLXGenGenerationError(
                "MLX-Gen reference images are not supported by the initial CLI adapter."
            )
        if not self.is_available():
            raise MLXGenUnavailableError(
                f"MLX-Gen executable '{self.executable}' is unavailable."
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        effective_prompt = prompt
        if negative_prompt:
            effective_prompt = f"{prompt}\nAvoid: {negative_prompt}"
        command = [
            self.executable,
            "generate",
            "--model",
            self.model,
            "--prompt",
            effective_prompt,
            "--width",
            str(width),
            "--height",
            str(height),
        ]
        if seed is not None:
            command.extend(["--seed", str(seed)])
        command.extend(["--output", str(output_path)])

        started_at = perf_counter()
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        duration_ms = round((perf_counter() - started_at) * 1_000)

        if process.returncode != 0:
            output_path.unlink(missing_ok=True)
            detail = _sanitize_output(stderr) or "no error output"
            raise MLXGenGenerationError(
                f"MLX-Gen failed with exit code {process.returncode}: {detail}"
            )
        if not output_path.is_file():
            raise MLXGenGenerationError(
                "MLX-Gen completed successfully but did not create the requested output file."
            )

        try:
            with Image.open(output_path) as image:
                image_format = image.format
                image_size = image.size
                image.verify()
            if image_format != "PNG" or image_size != (width, height):
                raise MLXGenGenerationError(
                    "MLX-Gen output failed PNG dimension verification."
                )
        except (OSError, UnidentifiedImageError, ValueError) as error:
            output_path.unlink(missing_ok=True)
            if isinstance(error, MLXGenGenerationError):
                raise
            raise MLXGenGenerationError("MLX-Gen output is not a readable PNG.") from error

        return ImageGenerationResult(
            output_path=output_path,
            width=width,
            height=height,
            seed=seed,
            provider="mlxgen",
            metadata={
                "model": self.model,
                "executable": self.executable,
                "duration_ms": duration_ms,
                "stdout": _sanitize_output(stdout),
                "negative_prompt_included": negative_prompt is not None,
                "reference_count": 0,
            },
        )


def _sanitize_output(data: bytes) -> str:
    decoded = data.decode("utf-8", errors="replace")
    without_ansi = _ANSI_ESCAPE.sub("", decoded)
    return " ".join(without_ansi.split())[:_OUTPUT_LIMIT]
