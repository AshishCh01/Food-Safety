"""Guards the composite indexes recommended by docs/DATABASE_SCHEMA.md
section 22 (docs/PROJECT_AUDIT_REPORT.md finding 1.8) against accidental
removal - these back the per-inspector "my active cases" queries
(assignment_repository.list_by_inspector / inspection_repository.list_by_inspector)."""

from app.models.assignment import Assignment
from app.models.inspection import Inspection


def _index_names(table) -> set[str]:
    return {index.name for index in table.indexes}


def _index_column_names(table, index_name: str) -> list[str]:
    index = next(index for index in table.indexes if index.name == index_name)
    return [column.name for column in index.columns]


def test_assignments_has_composite_staff_status_index() -> None:
    assert "ix_assignments_staff_status" in _index_names(Assignment.__table__)
    assert _index_column_names(Assignment.__table__, "ix_assignments_staff_status") == [
        "assigned_to_staff_id",
        "status",
    ]


def test_inspections_has_composite_inspector_status_index() -> None:
    assert "ix_inspections_inspector_status" in _index_names(Inspection.__table__)
    assert _index_column_names(Inspection.__table__, "ix_inspections_inspector_status") == [
        "inspector_id",
        "inspection_status",
    ]
