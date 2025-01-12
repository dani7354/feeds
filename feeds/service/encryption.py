import os

from gnupg import GPG


class PGPService:
    """ PGP Service: encrypt strings and files using GnuPG """
    encoding = "utf-8"

    def __init__(self, gpg_home_path: str):
        self.gpg = GPG(gnupghome=gpg_home_path)
        self.gpg.encoding = self.encoding
        if not (self.gpg.list_keys()):
            self._import_keys_from_homedir()
            if not self.gpg.list_keys():
                raise RuntimeError("No keys found in GnuPG home directory")

    def encrypt_string(self, input_str: str, recipient: str) -> str:
        encrypted = self.gpg.encrypt(input_str, recipients=[recipient])
        if not encrypted.ok:
            raise ValueError(f"Failed to encrypt string for {recipient}: {encrypted.status}")

        return encrypted.data.decode(self.encoding)

    def _import_keys_from_homedir(self) -> None:
        for file in os.listdir(self.gpg.gnupghome):
            if file.endswith(".asc"):
                with open(file, "rb", encoding=self.encoding) as key_file:
                    self.gpg.import_keys(key_file.read())
