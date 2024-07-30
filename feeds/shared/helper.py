from hashlib import sha256


def hash_equals(feed_one_bytes: bytes, feed_two_bytes: bytes) -> bool:
    return sha256(feed_one_bytes).hexdigest() == sha256(feed_two_bytes).hexdigest()
