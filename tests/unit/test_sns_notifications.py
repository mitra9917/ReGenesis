import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_step_functions_sns_notify_complete_state():
    """Verify that recovery_flow.asl.json configures NotifyComplete as the SNS terminal step."""
    asl_path = ROOT / "infrastructure" / "sam" / "statemachines" / "recovery_flow.asl.json"
    assert asl_path.exists(), "State machine ASL definition must exist"

    with open(asl_path, encoding="utf-8") as f:
        definition = json.load(f)

    states = definition.get("States", {})
    assert "NotifyComplete" in states, "NotifyComplete state must be defined"

    notify_state = states["NotifyComplete"]
    assert notify_state.get("Type") == "Task"
    assert notify_state.get("Resource") == "arn:aws:states:::sns:publish"
    assert notify_state.get("End") is True

    parameters = notify_state.get("Parameters", {})
    assert parameters.get("TopicArn") == "${RecoveryCompleteTopicArn}"
    assert parameters.get("Message.$") == "States.JsonToString($)"


def test_template_defines_recovery_complete_topic():
    """Verify that template.yaml defines RecoveryCompleteTopic with correct environment naming."""
    template_path = ROOT / "infrastructure" / "sam" / "template.yaml"
    content = template_path.read_text(encoding="utf-8")

    assert "RecoveryCompleteTopic:" in content
    assert "Type: AWS::SNS::Topic" in content
    assert "regenesis-recovery-complete-${Environment}" in content
    assert "RecoveryCompleteTopicArn:" in content
