import json

import yaml

from cognition.revision_secrets import REDACTED, load_local_config, redact_mapping, redact_text


def test_load_local_config_reads_yaml_and_json(tmp_path) -> None:
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text("providers:\n  openai:\n    api_key: sk-test-SENTINEL\n", encoding="utf-8")
    json_path = tmp_path / "config.json"
    json_path.write_text(json.dumps({"pricing": {"openai": {"gpt": {"in_per_1k": 0.0}}}}))

    assert load_local_config(None) == {}
    assert load_local_config("") == {}
    assert load_local_config(yaml_path)["providers"]["openai"]["api_key"] == "sk-test-SENTINEL"
    assert load_local_config(json_path)["pricing"]["openai"]["gpt"]["in_per_1k"] == 0.0


def test_redact_mapping_redacts_secret_key_fragments() -> None:
    value = {
        "providers": {
            "openai": {
                "api_key": "sk-test-SENTINEL",
                "nested": [{"access_token": "secret-SENTINEL"}],
            }
        },
        "password": "not-for-output",
        "safe": "visible",
    }

    redacted = redact_mapping(value)

    assert redacted["providers"]["openai"]["api_key"] == REDACTED
    assert redacted["providers"]["openai"]["nested"][0]["access_token"] == REDACTED
    assert redacted["password"] == REDACTED
    assert redacted["safe"] == "visible"
    assert "sk-test-SENTINEL" not in yaml.safe_dump(redacted)
    assert "secret-SENTINEL" not in yaml.safe_dump(redacted)


def test_redact_text_removes_credential_like_values() -> None:
    text = (
        "api_key=sk-test-SENTINEL "
        "secret-SENTINEL "
        "xoxb-test-SENTINEL "
        "plain text remains"
    )

    redacted = redact_text(text)

    assert "sk-test-SENTINEL" not in redacted
    assert "secret-SENTINEL" not in redacted
    assert "xoxb-test-SENTINEL" not in redacted
    assert "plain text remains" in redacted
