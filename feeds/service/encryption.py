import os

from gnupg import GPG


class PGPService:
    """ PGP Service: encrypt strings and files using GnuPG """
    encoding = "utf-8"
    key_file_extensions = ".asc"
    new_key_trust_level = "TRUST_ULTIMATE"

    def __init__(self, gpg_home_path: str):
        self.gpg = GPG(gnupghome=gpg_home_path)
        self.gpg.encoding = self.encoding
        if not self.gpg.list_keys():
            self._import_keys_from_homedir()
            if not self.gpg.list_keys():
                raise RuntimeError("No keys found in GnuPG home directory")

        self._ensure_correct_directory_permissions()

    def encrypt_string(self, input_str: str, recipient: str) -> str:
        encrypted = self.gpg.encrypt(input_str, recipients=[recipient])
        if not encrypted.ok:
            raise ValueError(f"Failed to encrypt string for {recipient}: {encrypted.status}")

        return encrypted.data.decode(self.encoding)

    def _import_keys_from_homedir(self) -> None:
        for file in os.listdir(self.gpg.gnupghome):
            if file.endswith(self.key_file_extensions):
                with open(os.path.join(self.gpg.gnupghome, file), "r", encoding=self.encoding) as key_file:
                    import_result = self.gpg.import_keys(key_file.read())
                    self.gpg.trust_keys(import_result.fingerprints, self.new_key_trust_level)

    def _ensure_correct_directory_permissions(self) -> None:
        os.chmod(self.gpg.gnupghome, 0o700)
        for entry in os.listdir(self.gpg.gnupghome):
            if os.path.isdir(os.path.join(self.gpg.gnupghome, entry)):
                os.chmod(os.path.join(self.gpg.gnupghome, entry), 0o700)
            else:
                os.chmod(os.path.join(self.gpg.gnupghome, entry), 0o600)
