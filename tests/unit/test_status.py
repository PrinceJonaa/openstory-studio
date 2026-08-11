import pytest


def test_locked_artifact_cannot_transition() -> None:
    from openstory.domain.status import (
        LockedArtifactError,
        ProductionStatus,
        require_transition,
    )

    with pytest.raises(LockedArtifactError):
        require_transition(ProductionStatus.LOCKED, ProductionStatus.REVISE)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("draft", "review"),
        ("review", "approved"),
        ("review", "revise"),
        ("revise", "draft"),
        ("revise", "review"),
        ("approved", "locked"),
        ("approved", "revise"),
    ],
)
def test_documented_status_transition_is_allowed(current: str, target: str) -> None:
    from openstory.domain.status import ProductionStatus, require_transition

    require_transition(ProductionStatus(current), ProductionStatus(target))


def test_undocumented_status_transition_is_rejected() -> None:
    from openstory.domain.status import (
        InvalidStatusTransitionError,
        ProductionStatus,
        require_transition,
    )

    with pytest.raises(InvalidStatusTransitionError):
        require_transition(ProductionStatus.DRAFT, ProductionStatus.APPROVED)

