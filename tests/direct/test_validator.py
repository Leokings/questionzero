"""Direct manual tests for QuestionZero's independent LLM validator."""

from __future__ import annotations

import json

from fixtures.specs import (
    DECISION_DEADLINE_UNIX,
    EVIDENCE_MODE,
    OUTCOME_SCHEMA,
    RESOLVABLE_RULES,
    SPEC_KEY,
)


LLM_PATTERN = r"independent adjudicability auditor"


def _register_and_audit(questionzero, direct_vm):
    spec_id = questionzero.register_spec(
        SPEC_KEY,
        RESOLVABLE_RULES,
        OUTCOME_SCHEMA,
        EVIDENCE_MODE,
        DECISION_DEADLINE_UNIX,
    )
    direct_vm.mock_llm(LLM_PATTERN, json.dumps({"issue_codes": []}))
    questionzero.audit_spec(spec_id)
    return direct_vm._captured_validators[-1][0]


def test_validator_independently_repeats_and_accepts_same_issue_mask(
    questionzero,
    direct_vm,
):
    leader = _register_and_audit(questionzero, direct_vm)

    assert leader == {"issue_mask": 0}
    assert direct_vm.run_validator(leader_result=leader) is True


def test_validator_rejects_different_independent_classification(
    questionzero,
    direct_vm,
):
    leader = _register_and_audit(questionzero, direct_vm)
    direct_vm.clear_mocks()
    direct_vm.mock_llm(
        LLM_PATTERN,
        json.dumps({"issue_codes": ["UNDEFINED_MATERIAL_TERM"]}),
    )

    assert direct_vm.run_validator(leader_result=leader) is False


def test_validator_rejects_tampered_or_noncanonical_leader_result(
    questionzero,
    direct_vm,
):
    leader = _register_and_audit(questionzero, direct_vm)

    assert direct_vm.run_validator(leader_result={"issue_mask": 1}) is False
    assert direct_vm.run_validator(leader_result={"issue_mask": "0"}) is False
    assert direct_vm.run_validator(leader_result={"issue_mask": True}) is False
    assert direct_vm.run_validator(leader_result={"issue_mask": 2048}) is False
    assert direct_vm.run_validator(leader_result={"issue_mask": 0, "extra": 1}) is False
    assert direct_vm.run_validator(leader_result={}) is False
    assert direct_vm.run_validator(leader_result=leader) is True


def test_validator_rejects_leader_error(questionzero, direct_vm):
    _register_and_audit(questionzero, direct_vm)

    assert direct_vm.run_validator(
        leader_error=RuntimeError("[LLM_ERROR] invalid_issue_code")
    ) is False


def test_validator_rejects_invalid_independent_model_output(questionzero, direct_vm):
    leader = _register_and_audit(questionzero, direct_vm)
    direct_vm.clear_mocks()
    direct_vm.mock_llm(
        LLM_PATTERN,
        json.dumps({"issue_codes": ["NOT_A_VALID_CODE"]}),
    )

    assert direct_vm.run_validator(leader_result=leader) is False
