import pytest
from gnupg import GPG

from feeds.service.encryption import PGPService

VALID_RECIPENT_EMAIL = "robert@robert.dk"


@pytest.fixture
def pgp(tmp_path):
    gpg_home_path = str(tmp_path)
    gpg = GPG(gnupghome=gpg_home_path)
    key_input = gpg.gen_key_input(
        name_email=f"Robert <{VALID_RECIPENT_EMAIL}>",
        passphrase="Robert123",
        key_type="RSA",
        key_length=4096)
    key = gpg.gen_key(key_input)
    public_key = gpg.export_keys(key.fingerprint)
    with open(tmp_path / "public_key.asc", "w") as key_file:
        key_file.write(public_key)

    return PGPService(gpg_home_path=str(tmp_path))


def test_encrypt_string_works_with_email_recipient(pgp):
    encrypted_message = pgp.encrypt_string("Hello, World!", recipient=VALID_RECIPENT_EMAIL)
    assert encrypted_message


def test_encrypt_string_fails_with_invalid_recipient(pgp):
    with pytest.raises(ValueError):
        pgp.encrypt_string("Hello, World!", recipient="soren@soren.dk")
