import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from openstory.domain.assets import ImageGenerationResult


class PlaceholderImageProvider:
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
        if width < 64 or height < 64:
            raise ValueError("Placeholder dimensions must be at least 64 pixels.")
        if output_path.exists():
            raise FileExistsError(f"Render output already exists: {output_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = output_path.with_suffix(".tmp.png")
        temporary_path.unlink(missing_ok=True)
        try:
            image = Image.new("RGB", (width, height), color=(244, 241, 233))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            border = max(12, min(width, height) // 40)
            draw.rectangle(
                (border, border, width - border - 1, height - border - 1),
                outline=(40, 43, 42),
                width=max(2, border // 5),
            )
            header_height = max(42, min(72, height // 10))
            draw.rectangle(
                (border, border, width - border - 1, border + header_height),
                fill=(40, 43, 42),
            )
            draw.text(
                (border + 16, border + 15),
                "OPENSTORY / PLACEHOLDER",
                fill=(244, 241, 233),
                font=font,
            )

            content = prompt
            if negative_prompt:
                content = f"{content}\nNEGATIVE: {negative_prompt}"
            characters_per_line = max(20, (width - (border + 16) * 2) // 7)
            wrapped_lines: list[str] = []
            for source_line in content.splitlines() or [content]:
                wrapped_lines.extend(
                    textwrap.wrap(
                        source_line,
                        width=characters_per_line,
                        replace_whitespace=False,
                        drop_whitespace=True,
                    )
                    or [""]
                )

            line_height = 18
            text_x = border + 16
            text_y = border + header_height + 22
            max_y = height - border - 20
            for line in wrapped_lines:
                if text_y + line_height > max_y:
                    draw.text((text_x, text_y), "…", fill=(40, 43, 42), font=font)
                    break
                draw.text((text_x, text_y), line, fill=(40, 43, 42), font=font)
                text_y += line_height

            image.save(temporary_path, format="PNG")
            with Image.open(temporary_path) as verification:
                if verification.format != "PNG" or verification.size != (width, height):
                    raise ValueError("Placeholder output failed PNG verification.")
                verification.verify()
            os.replace(temporary_path, output_path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

        return ImageGenerationResult(
            output_path=output_path,
            width=width,
            height=height,
            seed=seed,
            provider="placeholder",
            metadata={
                "placeholder": True,
                "reference_count": len(references or []),
            },
        )
