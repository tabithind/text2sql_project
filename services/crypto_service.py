import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from config.settings import settings

class CryptoService:
    @staticmethod
    def get_master_key() -> bytes:
        key = settings.MASTER_ENCRYPTION_KEY_BYTES
        if not key or len(key) != 32:
            raise ValueError("MASTER_ENCRYPTION_KEY must be a 32-byte (64 hex characters) key.")
        return key

    @staticmethod
    def chiffrer(texte_brut: str) -> dict:
        """
        Chiffre un texte en utilisant AES-256-GCM.
        Retourne un dictionnaire contenant cle_chiffree, iv, et auth_tag en hex/base64.
        """
        key = CryptoService.get_master_key()
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        
        # Le résultat contient le ciphertext concaténé avec l'auth_tag (16 bytes à la fin)
        chiffre = aesgcm.encrypt(nonce, texte_brut.encode('utf-8'), None)
        
        ciphertext = chiffre[:-16]
        auth_tag = chiffre[-16:]
        
        return {
            'cle_chiffree': base64.b64encode(ciphertext).decode('utf-8'),
            'iv': nonce.hex(),
            'auth_tag': auth_tag.hex()
        }

    @staticmethod
    def dechiffrer(cle_chiffree: str, iv: str, auth_tag: str) -> str:
        """
        Déchiffre un texte chiffré (AES-256-GCM).
        """
        key = CryptoService.get_master_key()
        nonce = bytes.fromhex(iv)
        
        # On reconstitue le payload attendu par AESGCM.decrypt : ciphertext + auth_tag
        payload = base64.b64decode(cle_chiffree) + bytes.fromhex(auth_tag)
        aesgcm = AESGCM(key)
        
        return aesgcm.decrypt(nonce, payload, None).decode('utf-8')
