from pathlib import Path

import pytest
from openstory.providers.image.placeholder import PlaceholderImageProvider
from PIL import Image


@pytest.mark.asyncio
async def test_placeholder_renderer_creates_png(tmp_path: Path) -> None:
    output = tmp_path / "panel.png"

    result = await PlaceholderImageProvider().generate(
        prompt="PANEL 1\nSHOT: wide\nACTION: Lira approaches the gate.",
        negative_prompt=None,
        width=640,
        height=960,
        seed=7,
        output_path=output,
        references=[],
    )

    assert result.output_path == output
    assert result.provider == "placeholder"
    with Image.open(output) as image:
        assert image.format == "PNG"
        assert image.mode == "RGB"
        assert image.size == (640, 960)


@pytest.mark.asyncio
async def test_placeholder_renderer_will_not_overwrite_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "panel.png"
    output.write_bytes(b"existing")

    with pytest.raises(FileExistsError):
        await PlaceholderImageProvider().generate(
            prompt="panel",
            negative_prompt=None,
            width=320,
            height=480,
            seed=None,
            output_path=output,
        )

    assert output.read_bytes() == b"existing"
