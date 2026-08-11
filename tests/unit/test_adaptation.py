import pytest
from openstory.domain.adaptation import (
    AdaptEpisodeCommand,
    EpisodeAdaptationResponse,
    EpisodeDraft,
    SceneDraft,
)
from pydantic import ValidationError


def test_adaptation_requires_at_least_one_source_chunk() -> None:
    with pytest.raises(ValidationError):
        AdaptEpisodeCommand(
            project_id="project",
            source_chunk_ids=[],
            number=1,
            target_format="storyboard",
        )


@pytest.mark.parametrize(
    "ordinals",
    [[2], [1, 3], [1, 1]],
)
def test_adaptation_requires_contiguous_scene_ordinals(ordinals: list[int]) -> None:
    with pytest.raises(ValidationError):
        EpisodeAdaptationResponse(
            episode=EpisodeDraft(
                title="Episode",
                logline="A visual story beat.",
                adaptation_notes="Omissions: none. Reordering: none.",
            ),
            scenes=[
                SceneDraft(
                    ordinal=ordinal,
                    title=f"Scene {ordinal}",
                    purpose="Move the story forward.",
                    summary="A grounded visual beat.",
                )
                for ordinal in ordinals
            ],
        )


def test_adaptation_response_accepts_contiguous_scenes() -> None:
    response = EpisodeAdaptationResponse(
        episode=EpisodeDraft(
            title="Episode",
            logline="A visual story beat.",
            adaptation_notes="Omissions: none. Reordering: none.",
        ),
        scenes=[
            SceneDraft(
                ordinal=1,
                title="Scene 1",
                purpose="Introduce the problem.",
                summary="The problem appears.",
            ),
            SceneDraft(
                ordinal=2,
                title="Scene 2",
                purpose="Resolve the immediate beat.",
                summary="The characters respond.",
            ),
        ],
    )

    assert [scene.ordinal for scene in response.scenes] == [1, 2]
