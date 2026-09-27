"""Self-contained salted scrypt credentials; no plaintext is retained in state."""
import hashlib
import hmac
import secrets


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=16384, r=8, p=1, dklen=32)
    return {'algorithm': 'scrypt', 'n': 16384, 'r': 8, 'p': 1,
            'salt': salt.hex(), 'digest': digest.hex()}


def verify_password(password, stored):
    digest = hashlib.scrypt(password.encode('utf-8'), salt=bytes.fromhex(stored['salt']),
                            n=stored['n'], r=stored['r'], p=stored['p'], dklen=32)
    return hmac.compare_digest(digest.hex(), stored['digest'])


def valid_hash(stored):
    return (type(stored) is dict and set(stored) == {'algorithm', 'n', 'r', 'p', 'salt', 'digest'}
            and stored['algorithm'] == 'scrypt' and type(stored['n']) is int and stored['n'] == 16384
            and type(stored['r']) is int and stored['r'] == 8
            and type(stored['p']) is int and stored['p'] == 1
            and type(stored['salt']) is str and len(stored['salt']) == 32
            and type(stored['digest']) is str and len(stored['digest']) == 64
            and all(c in '0123456789abcdef' for c in stored['salt'] + stored['digest']))
