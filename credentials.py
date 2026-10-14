"""Only native OS credential stores; never a plaintext/file fallback."""
import hashlib
import sys


class CredentialStore:
    def __init__(self, namespace):
        self.service = 'PythonTech/' + hashlib.sha256(namespace.encode()).hexdigest()[:24]

    def _backend(self):
        # Select explicitly: third-party keyring plugins may store plaintext.
        if sys.platform == 'win32':
            from keyring.backends.Windows import WinVaultKeyring
            return WinVaultKeyring()
        if sys.platform == 'darwin':
            from keyring.backends.macOS import Keyring
            return Keyring()
        from keyring.backends.SecretService import Keyring
        return Keyring()

    @staticmethod
    def account(url, model):
        return hashlib.sha256((url + '\n' + model).encode()).hexdigest()

    def save(self, url, model, key):
        self._backend().set_password(self.service, self.account(url, model), key)

    def load(self, url, model):
        return self._backend().get_password(self.service, self.account(url, model)) or ''

    def delete(self, url, model):
        backend = self._backend()
        account = self.account(url, model)
        if backend.get_password(self.service, account) is not None:
            backend.delete_password(self.service, account)
