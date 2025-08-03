from p21api.config import Config


def test_password_strip():
    # Password with leading/trailing whitespace and newline
    config = Config(password="  secret123\n")
    assert config.password == "secret123"

    # Password with only whitespace
    config = Config(password="  secret  ")
    assert config.password == "secret"

    # Password is None
    config = Config(password=None)
    assert config.password is None

    # Password is already clean
    config = Config(password="cleanpass")
    assert config.password == "cleanpass"
