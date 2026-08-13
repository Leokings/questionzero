"""Direct leader-path tests for QuestionZero audits."""

from __future__ import annotations

import json

import pytest

from fixtures.specs import (
    ADVERSARIAL_OUTCOME_SCHEMA,
    ADVERSARIAL_RULES,
    ADVERSARIAL_SPEC_KEY,
    AMBIGUOUS_OUTCOME_SCHEMA,
    AMBIGUOUS_RULES,
    AMBIGUOUS_SPEC_KEY,
    DECISION_DEADLINE_UNIX,
    EVIDENCE_MODE,
    MANIPULABLE_OUTCOME_SCHEMA,
    MANIPULABLE_RULES,
    MANIPULABLE_SPEC_KEY,
    OUTCOME_SCHEMA,
    RESOLVABLE_RULES,
    SPEC_KEY,
    build_spec_fingerprint,
)


LLM_PATTERN = r"independent adjudicability auditor"


def _register(contract, key=SPEC_KEY, rules=RESOLVABLE_RULES, outcomes=OUTCOME_SCHEMA):
    return contract.register_spec(
        key,
        rules,
        outcomes,
        EVIDENCE_MODE,
        DECISION_DEADLINE_UNIX,
    )


def _mock_audit(direct_vm, issue_codes):
    direct_vm.mock_llm(LLM_PATTERN, json.dumps({"issue_codes": issue_codes}))


def test_resolvable_spec_persists_a_safe_audit(questionzero, direct_vm):
    spec_id = _register(questionzero)
    _mock_audit(direct_vm, [])

    questionzero.audit_spec(spec_id)

    audit = questionzero.get_audit(spec_id)
    assert audit["schema"] == "questionzero/audit/v1"
    assert audit["verdict"] == "RESOLVABLE"
    assert audit["issue_mask"] == 0
    assert audit["issue_codes"] == []
    assert questionzero.is_audited(spec_id) is True
    assert questionzero.has_resolvable_audit(spec_id) is True
    assert questionzero.get_audit_count() == 1
    assert questionzero.get_audit_id(0) == spec_id


@pytest.mark.parametrize(
    ("key", "rules", "outcomes", "issue_codes", "verdict"),
    [
        (
            AMBIGUOUS_SPEC_KEY,
            AMBIGUOUS_RULES,
            AMBIGUOUS_OUTCOME_SCHEMA,
            ["OUTCOME_OVERLAP", "MISSING_TIE_RULE"],
            "AMBIGUOUS",
        ),
        (
            MANIPULABLE_SPEC_KEY,
            MANIPULABLE_RULES,
            MANIPULABLE_OUTCOME_SCHEMA,
            ["PARTICIPANT_CONTROLLED_EVIDENCE"],
            "MANIPULABLE",
        ),
        (
            "PRIVATE-EVIDENCE",
            "Approve only when a private email confirms completion before the deadline, and reject in every other case.",
            OUTCOME_SCHEMA,
            ["UNVERIFIABLE_EVIDENCE"],
            "UNVERIFIABLE",
        ),
        (
            "VAGUE-TERM",
            "Approve only when the task is sufficiently excellent before the deadline according to the stated public policy.",
            OUTCOME_SCHEMA,
            ["UNDEFINED_MATERIAL_TERM"],
            "INCOMPLETE",
        ),
        (
            ADVERSARIAL_SPEC_KEY,
            ADVERSARIAL_RULES,
            ADVERSARIAL_OUTCOME_SCHEMA,
            ["ADVERSARIAL_INSTRUCTION"],
            "MANIPULABLE",
        ),
    ],
)
def test_issue_taxonomy_derives_conservative_verdicts(
    questionzero,
    direct_vm,
    key,
    rules,
    outcomes,
    issue_codes,
    verdict,
):
    spec_id = _register(questionzero, key, rules, outcomes)
    _mock_audit(direct_vm, issue_codes)

    questionzero.audit_spec(spec_id)

    audit = questionzero.get_audit(spec_id)
    assert audit["verdict"] == verdict
    assert audit["issue_codes"] == issue_codes
    assert questionzero.has_resolvable_audit(spec_id) is False


@pytest.mark.parametrize(
    "response",
    [
        {},
        {"issue_codes": "UNDEFINED_MATERIAL_TERM"},
        {"issue_codes": ["NOT_A_VALID_CODE"]},
        {"issue_codes": ["OUTCOME_GAP", "OUTCOME_GAP"]},
        {"issue_codes": [], "verdict": "RESOLVABLE"},
    ],
)
def test_malformed_model_output_does_not_persist_an_audit(
    questionzero,
    direct_vm,
    response,
):
    spec_id = _register(questionzero)
    direct_vm.mock_llm(LLM_PATTERN, json.dumps(response))

    with direct_vm.expect_revert("[LLM_ERROR]"):
        questionzero.audit_spec(spec_id)

    assert questionzero.is_audited(spec_id) is False
    assert questionzero.get_audit_count() == 0


def test_audit_is_immutable(questionzero, direct_vm):
    spec_id = _register(questionzero)
    _mock_audit(direct_vm, [])
    questionzero.audit_spec(spec_id)

    with direct_vm.expect_revert("spec_already_audited"):
        questionzero.audit_spec(spec_id)


def test_bound_resolvable_gate_requires_exact_expected_specification(
    questionzero,
    direct_vm,
):
    spec_id = _register(questionzero)
    _mock_audit(direct_vm, [])
    questionzero.audit_spec(spec_id)
    spec = questionzero.get_spec(spec_id)
    expected_fingerprint = build_spec_fingerprint(spec["creator"])

    assert spec["spec_fingerprint"] == expected_fingerprint
    assert questionzero.get_audit(spec_id)["spec_fingerprint"] == expected_fingerprint
    assert questionzero.matches_resolvable_spec(spec_id, expected_fingerprint) is True

    wrong_policy = build_spec_fingerprint(spec["creator"], policy_version=2)
    assert questionzero.matches_resolvable_spec(spec_id, wrong_policy) is False

    wrong_creator = build_spec_fingerprint(
        "0x0000000000000000000000000000000000000001",
    )
    assert questionzero.matches_resolvable_spec(spec_id, wrong_creator) is False

    wrong_rules = build_spec_fingerprint(
        spec["creator"],
        rules_text=RESOLVABLE_RULES + " This is a materially different rule.",
    )
    wrong_key = build_spec_fingerprint(spec["creator"], spec_key="OTHER-SPEC")
    wrong_outcomes = build_spec_fingerprint(
        spec["creator"],
        outcome_schema="APPROVE|REJECT|REVIEW",
    )
    wrong_evidence = build_spec_fingerprint(
        spec["creator"],
        evidence_mode="ONCHAIN_ONLY",
    )
    wrong_deadline = build_spec_fingerprint(
        spec["creator"],
        decision_deadline_unix=DECISION_DEADLINE_UNIX + 1,
    )
    for wrong_fingerprint in (
        wrong_rules,
        wrong_key,
        wrong_outcomes,
        wrong_evidence,
        wrong_deadline,
    ):
        assert questionzero.matches_resolvable_spec(
            spec_id,
            wrong_fingerprint,
        ) is False
    for malformed_fingerprint in (
        "not-a-fingerprint",
        "sha256:" + "0" * 63,
        "SHA256:" + "0" * 64,
        "sha256:" + "A" + "0" * 63,
        "sha256:" + "g" * 64,
    ):
        assert questionzero.matches_resolvable_spec(
            spec_id,
            malformed_fingerprint,
        ) is False


def test_bound_gate_rejects_a_non_resolvable_audit(questionzero, direct_vm):
    spec_id = _register(
        questionzero,
        AMBIGUOUS_SPEC_KEY,
        AMBIGUOUS_RULES,
        AMBIGUOUS_OUTCOME_SCHEMA,
    )
    _mock_audit(direct_vm, ["UNBOUNDED_DISCRETION"])
    questionzero.audit_spec(spec_id)
    spec = questionzero.get_spec(spec_id)

    assert questionzero.get_audit(spec_id)["verdict"] == "MANIPULABLE"
    assert questionzero.matches_resolvable_spec(
        spec_id,
        spec["spec_fingerprint"],
    ) is False


def test_missing_records_and_out_of_bounds_audit_ids_revert(questionzero, direct_vm):
    with direct_vm.expect_revert("spec_not_registered"):
        questionzero.audit_spec("missing")
    with direct_vm.expect_revert("spec_not_registered"):
        questionzero.get_spec("missing")
    with direct_vm.expect_revert("spec_not_audited"):
        questionzero.get_audit("missing")
    with direct_vm.expect_revert("audit_index_out_of_bounds"):
        questionzero.get_audit_id(0)
