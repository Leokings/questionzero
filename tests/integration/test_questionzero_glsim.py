"""Five-validator GLSim consensus tests for QuestionZero."""

from __future__ import annotations

import json
from pathlib import Path

from gltest import get_contract_factory, get_validator_factory
from gltest.assertions import tx_execution_failed, tx_execution_succeeded
from gltest.types import TransactionStatus
from gltest.utils import extract_contract_address

from fixtures.specs import (
    AMBIGUOUS_OUTCOME_SCHEMA,
    AMBIGUOUS_RULES,
    AMBIGUOUS_SPEC_KEY,
    DECISION_DEADLINE_UNIX,
    EVIDENCE_MODE,
    OUTCOME_SCHEMA,
    POLICY_VERSION,
    RESOLVABLE_RULES,
    SPEC_KEY,
    build_spec_fingerprint,
)


PROMPT_KEY = "independent adjudicability auditor"
TEST_DATETIME = "2026-08-10T12:00:00Z"


def _receipt_dump(receipt):
    return json.dumps(receipt, indent=2, sort_keys=True, default=str)


def _validator_context(llm_response: str):
    validators = get_validator_factory().batch_create_mock_validators(
        5,
        mock_llm_response={
            "nondet_exec_prompt": {PROMPT_KEY: llm_response},
        },
    )
    return {
        "validators": [validator.to_dict() for validator in validators],
        "genvm_datetime": TEST_DATETIME,
    }


def _deploy_contract():
    contract_path = Path(__file__).resolve().parents[2] / "contracts" / "question_zero.py"
    factory = get_contract_factory(contract_file_path=contract_path)
    receipt = factory.deploy_contract_tx(
        args=[POLICY_VERSION],
        wait_transaction_status=TransactionStatus.FINALIZED,
    )
    assert tx_execution_succeeded(receipt), _receipt_dump(receipt)
    return factory.build_contract(extract_contract_address(receipt))


def _register(contract, spec_key=SPEC_KEY, rules=RESOLVABLE_RULES, outcomes=OUTCOME_SCHEMA):
    receipt = contract.register_spec(
        args=[
            spec_key,
            rules,
            outcomes,
            EVIDENCE_MODE,
            DECISION_DEADLINE_UNIX,
        ]
    ).transact(wait_transaction_status=TransactionStatus.FINALIZED)
    assert tx_execution_succeeded(receipt), _receipt_dump(receipt)
    assert contract.get_spec_count().call() == 1
    return contract.get_spec_id(args=[0]).call()


def test_glsim_consensus_persists_resolvable_spec_audit():
    contract = _deploy_contract()
    spec_id = _register(contract)
    context = _validator_context('{"issue_codes": []}')

    receipt = contract.audit_spec(args=[spec_id]).transact(
        transaction_context=context,
        wait_transaction_status=TransactionStatus.FINALIZED,
    )
    assert tx_execution_succeeded(receipt), _receipt_dump(receipt)

    audit = contract.get_audit(args=[spec_id]).call()
    assert audit["verdict"] == "RESOLVABLE"
    assert audit["issue_mask"] == 0
    assert contract.has_resolvable_audit(args=[spec_id]).call() is True
    spec = contract.get_spec(args=[spec_id]).call()
    expected_fingerprint = build_spec_fingerprint(spec["creator"])
    assert spec["spec_fingerprint"] == expected_fingerprint
    assert audit["spec_fingerprint"] == expected_fingerprint
    assert contract.matches_resolvable_spec(
        args=[spec_id, expected_fingerprint]
    ).call() is True


def test_glsim_consensus_persists_ambiguous_spec_audit():
    contract = _deploy_contract()
    spec_id = _register(
        contract,
        AMBIGUOUS_SPEC_KEY,
        AMBIGUOUS_RULES,
        AMBIGUOUS_OUTCOME_SCHEMA,
    )
    context = _validator_context(
        '{"issue_codes": ["OUTCOME_OVERLAP", "MISSING_TIE_RULE"]}'
    )

    receipt = contract.audit_spec(args=[spec_id]).transact(
        transaction_context=context,
        wait_transaction_status=TransactionStatus.FINALIZED,
    )
    assert tx_execution_succeeded(receipt), _receipt_dump(receipt)

    audit = contract.get_audit(args=[spec_id]).call()
    assert audit["verdict"] == "AMBIGUOUS"
    assert audit["issue_codes"] == ["OUTCOME_OVERLAP", "MISSING_TIE_RULE"]
    assert contract.has_resolvable_audit(args=[spec_id]).call() is False


def test_glsim_invalid_llm_response_fails_without_persisting_audit():
    contract = _deploy_contract()
    spec_id = _register(contract)
    context = _validator_context('{"issue_codes": ["NOT_A_VALID_CODE"]}')

    receipt = contract.audit_spec(args=[spec_id]).transact(
        transaction_context=context,
        wait_transaction_status=TransactionStatus.FINALIZED,
    )
    assert tx_execution_failed(receipt), _receipt_dump(receipt)
    assert contract.is_audited(args=[spec_id]).call() is False
    assert contract.get_audit_count().call() == 0
