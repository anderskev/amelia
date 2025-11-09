import pytest
from backend.config import Settings, Environment


def test_settings_loads_from_env():
    """Test that Settings loads configuration"""
    settings = Settings()
    assert settings.APP_NAME == "Amelia"
    assert settings.ENVIRONMENT in [Environment.DEVELOPMENT, Environment.TESTING, Environment.PRODUCTION]


def test_settings_validates_database_url():
    """Test that invalid database URL raises error"""
    with pytest.raises(ValueError, match="must be a PostgreSQL connection string"):
        Settings(DATABASE_URL="sqlite:///test.db")


def test_settings_validates_anthropic_key_format():
    """Test that invalid Anthropic key format raises error"""
    with pytest.raises(ValueError, match="must start with 'sk-ant-'"):
        Settings(ANTHROPIC_API_KEY="invalid-key")


def test_settings_validates_chunk_size():
    """Test that chunk size validation works"""
    with pytest.raises(ValueError, match="too small"):
        Settings(CHUNK_SIZE=50)


def test_chunk_overlap_less_than_chunk_size():
    """Test that chunk overlap must be less than chunk size"""
    with pytest.raises(ValueError, match="must be less than CHUNK_SIZE"):
        Settings(CHUNK_SIZE=800, CHUNK_OVERLAP=900)


def test_settings_creates_directories():
    """Test that Settings creates required directories"""
    settings = Settings()
    assert settings.UPLOAD_DIR.exists()
    assert settings.TEMP_DIR.exists()
    assert settings.GIT_WORKTREE_DIR.exists()


def test_environment_helper_properties():
    """Test environment helper properties"""
    dev_settings = Settings(ENVIRONMENT=Environment.DEVELOPMENT)
    assert dev_settings.is_development is True
    assert dev_settings.is_testing is False
    assert dev_settings.is_production is False
