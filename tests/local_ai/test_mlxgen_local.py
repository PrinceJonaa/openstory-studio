import os
from pathlib import Path

import pytest
from openstory.providers.image.mlxgen import MLXGenImageProvider
from PIL import Image

pytestmark = pytest.mark.local_ai


@pytest.mark.asyncio
async def test_mlxgen_renders_one_local_panel(tmp_path: Path) -> None:
    if os.getenv("OPENSTORY_RUN_LOCAL_AI") != "1":
        pytest.skip("Set OPENSTORY_RUN_LOCAL_AI=1 to run local model proofs.")

    provider = MLXGenImageProvider(
        executable=os.getenv("OPENSTORY_MLXGEN_EXECUTABLE", "mlxgen"),
        model=os.getenv(
            "OPENSTORY_MLXGEN_MODEL",
            "AbstractFramework/flux.2-klein-9b-8bit",
        ),
    )
    if not provider.is_available():
        pytest.skip("MLX-Gen executable is unavailable.")

    output_path = tmp_path / "mlxgen-panel.png"
    result = await provider.generate(
        prompt="Monochrome storyboard panel of two travelers at a fortified gate",
        negative_prompt="color, text, watermark",
        width=512,
        height=512,
        seed=42,
        output_path=output_path,
    )

    assert result.provider == "mlxgen"
    with Image.open(output_path) as image:
        assert image.size == (512, 512)
        assert image.format == "PNG"
