from pathlib import Path

from app.core.config import Settings


def test_env_file_is_resolved_from_project_root():
    env_file = Path(Settings.model_config["env_file"])

    assert env_file.is_absolute()
    assert env_file == Path(__file__).resolve().parents[3] / ".env"
