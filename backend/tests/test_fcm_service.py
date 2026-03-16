from app.core.config import settings


def test_fcm_config_required():
    assert settings.fcm_service_account_path
