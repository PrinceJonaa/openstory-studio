from enum import StrEnum


class ProductionStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    LOCKED = "locked"
    REVISE = "revise"


class InvalidStatusTransitionError(ValueError):
    def __init__(self, current: ProductionStatus, target: ProductionStatus) -> None:
        super().__init__(f"Cannot transition production status from {current} to {target}.")
        self.current = current
        self.target = target


class LockedArtifactError(InvalidStatusTransitionError):
    pass


ALLOWED_TRANSITIONS: dict[ProductionStatus, frozenset[ProductionStatus]] = {
    ProductionStatus.DRAFT: frozenset({ProductionStatus.REVIEW}),
    ProductionStatus.REVIEW: frozenset(
        {ProductionStatus.APPROVED, ProductionStatus.REVISE}
    ),
    ProductionStatus.APPROVED: frozenset(
        {ProductionStatus.LOCKED, ProductionStatus.REVISE}
    ),
    ProductionStatus.REVISE: frozenset(
        {ProductionStatus.DRAFT, ProductionStatus.REVIEW}
    ),
    ProductionStatus.LOCKED: frozenset(),
}


def require_transition(current: ProductionStatus, target: ProductionStatus) -> None:
    if current is ProductionStatus.LOCKED:
        raise LockedArtifactError(current, target)
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidStatusTransitionError(current, target)

