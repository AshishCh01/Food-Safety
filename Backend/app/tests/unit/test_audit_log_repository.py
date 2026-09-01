import inspect

from app.repositories import audit_log_repository
from app.tests.factories import create_user


def test_audit_log_repository_exposes_no_mutation_or_deletion_functions() -> None:
    """Audit logs must be append-only (docs/SECURITY_AND_RBAC.md section 12) -
    this asserts there is no code path in the repository that could update or
    delete an existing row, not just that no route currently calls one."""
    public_functions = {
        name
        for name, obj in inspect.getmembers(audit_log_repository, inspect.isfunction)
        if not name.startswith("_") and obj.__module__ == audit_log_repository.__name__
    }

    assert public_functions == {"record", "list_logs"}
    for forbidden in ("update", "delete", "remove", "edit"):
        assert not any(forbidden in name for name in public_functions)


def test_record_only_flushes_and_lets_caller_control_the_transaction(db_session) -> None:
    """record() must never commit on its own, so it always lands atomically
    with the action it documents (matching notification_repository.create's
    identical contract)."""
    actor = create_user(db_session, email="actor@example.com")

    entry = audit_log_repository.record(
        db_session,
        actor_user_id=actor.id,
        action="test_action",
        entity_type="test_entity",
        entity_id=actor.id,
        details=None,
    )
    assert entry.id is not None

    db_session.rollback()

    items, total = audit_log_repository.list_logs(db_session, action="test_action")
    assert total == 0
    assert items == []
