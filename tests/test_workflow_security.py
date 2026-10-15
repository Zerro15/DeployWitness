from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(__file__).parents[1] / ".github/workflows/deploywitness-pr.yml"


def test_repository_workflows_pin_third_party_actions_to_full_shas() -> None:
    for workflow_path in WORKFLOW.parent.glob("*.yml"):
        workflow = workflow_path.read_text(encoding="utf-8")
        action_refs = re.findall(r"^\s+uses:\s+([^\s]+)$", workflow, flags=re.MULTILINE)
        assert all(
            re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", ref) for ref in action_refs
        ), workflow_path


def test_reusable_workflow_pins_actions_and_analyzer_source() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    action_refs = re.findall(r"^\s+uses:\s+([^\s]+)$", workflow, flags=re.MULTILINE)

    assert len(action_refs) == 3
    assert all(re.fullmatch(r"actions/[\w-]+@[0-9a-f]{40}", ref) for ref in action_refs)
    assert "required: true" in workflow
    assert "default: main" not in workflow
    assert "must be a full 40-character commit SHA" in workflow


def test_reusable_workflow_uses_read_only_permissions_and_not_privileged_pr_event() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert re.search(r"^permissions:\s*\n\s+contents: read\s*$", workflow, re.MULTILINE)
    assert "pull_request_target" not in workflow
    assert "persist-credentials: false" in workflow


def test_reusable_workflow_bounds_runner_time() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert re.search(r"^\s+timeout-minutes:\s*10\s*$", workflow, re.MULTILINE)
