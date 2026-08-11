import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from openstory.providers.image.mlxgen import (
    MLXGenGenerationError,
    MLXGenImageProvider,
    MLXGenUnavailableError,
)
from openstory_api.dependencies import Settings, build_image_provider
from PIL import Image

MODEL = "AbstractFramework/flux.2-klein-9b-8bit"


def successful_process(output_path: Path, width: int, height: int) -> SimpleNamespace:
    async def communicate() -> tuple[bytes, bytes]:
        Image.new("RGB", (width, height), "white").save(output_path, format="PNG")
        return b"render complete\n", b""

    return SimpleNamespace(returncode=0, communicate=AsyncMock(side_effect=communicate))


@pytest.mark.asyncio
async def test_provider_builds_safe_positional_subprocess_command(tmp_path: Path) -> None:
    output_path = tmp_path / "panel.png"
    subprocess = AsyncMock(return_value=successful_process(output_path, 768, 1024))
    provider = MLXGenImageProvider(executable="mlxgen", model=MODEL)

    with (
        patch("openstory.providers.image.mlxgen.shutil.which", return_value="/usr/bin/mlxgen"),
        patch("openstory.providers.image.mlxgen.asyncio.create_subprocess_exec", subprocess),
    ):
        result = await provider.generate(
            prompt="Lira at the North Gate",
            negative_prompt=None,
            width=768,
            height=1024,
            seed=42,
            output_path=output_path,
        )

    subprocess.assert_awaited_once_with(
        "mlxgen",
        "generate",
        "--model",
        MODEL,
        "--prompt",
        "Lira at the North Gate",
        "--width",
        "768",
        "--height",
        "1024",
        "--seed",
        "42",
        "--output",
        str(output_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    assert result.output_path == output_path
    assert result.provider == "mlxgen"
    assert result.metadata["model"] == MODEL
    assert result.metadata["stdout"] == "render complete"
    assert isinstance(result.metadata["duration_ms"], int)


@pytest.mark.asyncio
async def test_provider_omits_seed_flag_when_seed_is_none(tmp_path: Path) -> None:
    output_path = tmp_path / "panel.png"
    subprocess = AsyncMock(return_value=successful_process(output_path, 512, 512))
    provider = MLXGenImageProvider(executable="mlxgen", model=MODEL)

    with (
        patch("openstory.providers.image.mlxgen.shutil.which", return_value="/usr/bin/mlxgen"),
        patch("openstory.providers.image.mlxgen.asyncio.create_subprocess_exec", subprocess),
    ):
        await provider.generate(
            prompt="North Gate",
            negative_prompt=None,
            width=512,
            height=512,
            seed=None,
            output_path=output_path,
        )

    command = subprocess.await_args.args
    assert "--seed" not in command
    assert command[-2:] == ("--output", str(output_path))


@pytest.mark.asyncio
async def test_missing_executable_reports_unavailable_without_spawning(tmp_path: Path) -> None:
    subprocess = AsyncMock()
    provider = MLXGenImageProvider(executable="missing-mlxgen", model=MODEL)

    with (
        patch("openstory.providers.image.mlxgen.shutil.which", return_value=None),
        patch("openstory.providers.image.mlxgen.asyncio.create_subprocess_exec", subprocess),
    ):
        assert provider.is_available() is False
        with pytest.raises(MLXGenUnavailableError, match="missing-mlxgen.*unavailable"):
            await provider.generate(
                prompt="panel",
                negative_prompt=None,
                width=512,
                height=512,
                seed=7,
                output_path=tmp_path / "panel.png",
            )

    subprocess.assert_not_awaited()


@pytest.mark.asyncio
async def test_nonzero_exit_reports_sanitized_stderr(tmp_path: Path) -> None:
    process = SimpleNamespace(
        returncode=2,
        communicate=AsyncMock(
            return_value=(b"", b"\x1b[31mpermission\n  denied\x1b[0m\n")
        ),
    )
    provider = MLXGenImageProvider(executable="mlxgen", model=MODEL)

    with (
        patch("openstory.providers.image.mlxgen.shutil.which", return_value="/usr/bin/mlxgen"),
        patch(
            "openstory.providers.image.mlxgen.asyncio.create_subprocess_exec",
            AsyncMock(return_value=process),
        ),
        pytest.raises(MLXGenGenerationError) as captured,
    ):
        await provider.generate(
            prompt="panel",
            negative_prompt=None,
            width=512,
            height=512,
            seed=7,
            output_path=tmp_path / "panel.png",
        )

    assert "exit code 2" in str(captured.value)
    assert "permission denied" in str(captured.value)
    assert "\x1b" not in str(captured.value)


@pytest.mark.asyncio
async def test_zero_exit_without_output_file_is_rejected(tmp_path: Path) -> None:
    process = SimpleNamespace(
        returncode=0,
        communicate=AsyncMock(return_value=(b"done", b"")),
    )
    provider = MLXGenImageProvider(executable="mlxgen", model=MODEL)

    with (
        patch("openstory.providers.image.mlxgen.shutil.which", return_value="/usr/bin/mlxgen"),
        patch(
            "openstory.providers.image.mlxgen.asyncio.create_subprocess_exec",
            AsyncMock(return_value=process),
        ),
        pytest.raises(MLXGenGenerationError, match="did not create"),
    ):
        await provider.generate(
            prompt="panel",
            negative_prompt=None,
            width=512,
            height=512,
            seed=7,
            output_path=tmp_path / "panel.png",
        )


@pytest.mark.asyncio
async def test_invalid_image_output_is_removed(tmp_path: Path) -> None:
    output_path = tmp_path / "panel.png"

    async def communicate() -> tuple[bytes, bytes]:
        output_path.write_bytes(b"not a png")
        return b"done", b""

    process = SimpleNamespace(
        returncode=0,
        communicate=AsyncMock(side_effect=communicate),
    )
    provider = MLXGenImageProvider(executable="mlxgen", model=MODEL)

    with (
        patch("openstory.providers.image.mlxgen.shutil.which", return_value="/usr/bin/mlxgen"),
        patch(
            "openstory.providers.image.mlxgen.asyncio.create_subprocess_exec",
            AsyncMock(return_value=process),
        ),
        pytest.raises(MLXGenGenerationError, match="readable PNG"),
    ):
        await provider.generate(
            prompt="panel",
            negative_prompt=None,
            width=512,
            height=512,
            seed=7,
            output_path=output_path,
        )

    assert not output_path.exists()


def test_image_provider_configuration_selects_mlxgen() -> None:
    provider = build_image_provider(
        Settings(
            image_provider="mlxgen",
            mlxgen_executable="custom-mlxgen",
            mlxgen_model=MODEL,
        )
    )

    assert isinstance(provider, MLXGenImageProvider)
    assert provider.executable == "custom-mlxgen"
    assert provider.model == MODEL
