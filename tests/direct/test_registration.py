"""Direct tests for QuestionZero registration and deterministic views."""

from __future__ import annotations

import pytest

from fixtures.specs import (
    build_spec_fingerprint,
    DECISION_DEADLINE_UNIX,
    EVIDENCE_MODE,
    OUTCOME_SCHEMA,
    RESOLVABLE_RULES,
    SPEC_KEY,
)


def _register(contract):
    return contract.register_spec(
        SPEC_KEY,
        RESOLVABLE_RULES,
        OUTCOME_SCHEMA,
        EVIDENCE_MODE,
        DECISION_DEADLINE_UNIX,
    )


def test_registers_canonical_public_spec(questionzero, direct_alice):
    spec_id = _register(questionzero)
    spec = questionzero.get_spec(spec_id)

    assert spec_id == questionzero.build_spec_id(spec["creator"], SPEC_KEY)
    assert spec["schema"] == "questionzero/spec/v1"
    assert spec["spec_fingerprint"] == build_spec_fingerprint(spec["creator"])
    assert spec["spec_key"] == SPEC_KEY
    assert spec["outcome_schema"] == OUTCOME_SCHEMA
    assert spec["evidence_mode"] == EVIDENCE_MODE
    assert spec["decision_deadline_unix"] == DECISION_DEADLINE_UNIX
    assert questionzero.get_spec_count() == 1
    assert questionzero.get_spec_id(0) == spec_id
    assert questionzero.is_audited(spec_id) is False
    assert questionzero.has_resolvable_audit(spec_id) is False
    assert questionzero.matches_resolvable_spec(
        spec_id,
        spec["spec_fingerprint"],
    ) is False


def test_spec_fingerprint_has_a_fixed_cross_language_vector():
    assert build_spec_fingerprint(
        "0x0000000000000000000000000000000000000001",
    ) == "sha256:4b66fc869478b52866332640a527fceb4aed8837b0154c65fcc78198525efe5a"


def test_equivalent_inputs_produce_the_canonical_fingerprint(questionzero):
    spec_id = questionzero.register_spec(
        f"  {SPEC_KEY.lower()}  ",
        f"\r\n{RESOLVABLE_RULES}\r\n",
        " approve | reject ",
        f" {EVIDENCE_MODE.lower()} ",
        DECISION_DEADLINE_UNIX,
    )
    spec = questionzero.get_spec(spec_id)

    assert spec["spec_fingerprint"] == build_spec_fingerprint(spec["creator"])


def test_exact_duplicate_registration_is_idempotent(questionzero):
    first = _register(questionzero)
    second = _register(questionzero)

    assert second == first
    assert questionzero.get_spec_count() == 1


def test_same_key_from_another_wallet_has_a_distinct_spec_id(
    questionzero,
    direct_vm,
    direct_bob,
):
    first = _register(questionzero)
    direct_vm.sender = direct_bob
    second = _register(questionzero)

    assert first != second
    assert questionzero.get_spec_count() == 2
    assert questionzero.get_spec(second)["creator"] == str(direct_bob)


def test_spec_id_index_checks_bounds(questionzero, direct_vm):
    with direct_vm.expect_revert("spec_index_out_of_bounds"):
        questionzero.get_spec_id(0)


@pytest.mark.parametrize(
    ("spec_key", "rules_text", "outcomes", "evidence_mode", "deadline", "message"),
    [
        ("", RESOLVABLE_RULES, OUTCOME_SCHEMA, EVIDENCE_MODE, DECISION_DEADLINE_UNIX, "invalid_spec_key"),
        (SPEC_KEY, "too short", OUTCOME_SCHEMA, EVIDENCE_MODE, DECISION_DEADLINE_UNIX, "invalid_rules_text"),
        (SPEC_KEY, RESOLVABLE_RULES + " caf\u00e9", OUTCOME_SCHEMA, EVIDENCE_MODE, DECISION_DEADLINE_UNIX, "invalid_rules_text"),
        (SPEC_KEY, RESOLVABLE_RULES, "ONLY_ONE", EVIDENCE_MODE, DECISION_DEADLINE_UNIX, "invalid_outcome_schema"),
        (SPEC_KEY, RESOLVABLE_RULES, "YES|YES", EVIDENCE_MODE, DECISION_DEADLINE_UNIX, "duplicate_outcome_label"),
        (SPEC_KEY, RESOLVABLE_RULES, OUTCOME_SCHEMA, "PRIVATE_ONLY", DECISION_DEADLINE_UNIX, "invalid_evidence_mode"),
        (SPEC_KEY, RESOLVABLE_RULES, OUTCOME_SCHEMA, EVIDENCE_MODE, 0, "invalid_decision_deadline"),
        (SPEC_KEY, RESOLVABLE_RULES, OUTCOME_SCHEMA, EVIDENCE_MODE, 4_102_444_801, "invalid_decision_deadline"),
    ],
)
def test_rejects_invalid_registration_fields(
    questionzero,
    direct_vm,
    spec_key,
    rules_text,
    outcomes,
    evidence_mode,
    deadline,
    message,
):
    with direct_vm.expect_revert(message):
        questionzero.register_spec(
            spec_key,
            rules_text,
            outcomes,
            evidence_mode,
            deadline,
        )


def test_conflicting_same_wallet_registration_is_rejected(questionzero, direct_vm):
    _register(questionzero)

    with direct_vm.expect_revert("spec_registration_conflict"):
        questionzero.register_spec(
            SPEC_KEY,
            RESOLVABLE_RULES + " A later sentence changes the terms.",
            OUTCOME_SCHEMA,
            EVIDENCE_MODE,
            DECISION_DEADLINE_UNIX,
        )
