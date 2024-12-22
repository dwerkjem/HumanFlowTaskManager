import hashlib
import base64

def generate_human_readable_hash(input_string, length=8, encoding="hex"):
    """
    Generate a human-readable hash for the given input string.

    NOT RECOMMENDED FOR CRYPTOGRAPHIC PURPOSES. This function is intended for generating
    human-readable identifiers, not for secure hashing. Use a dedicated library like 'bcrypt'

    Args:
        input_string (str): The string to hash.
        length (int): Length of the resulting hash (for truncation).
        encoding (str): Encoding type - 'hex', 'base64', or 'custom'.

    Returns:
        str: Human-readable hash of the input string.
    """
    # Step 1: Create a cryptographic hash
    hash_obj = hashlib.sha256(input_string.encode("utf-8"))
    raw_hash = hash_obj.digest()  # Raw bytes
    
    # Step 2: Encode in human-readable format
    if encoding == "hex":
        readable_hash = hash_obj.hexdigest()  # Hexadecimal string
    elif encoding == "base64":
        readable_hash = base64.urlsafe_b64encode(raw_hash).decode("utf-8").rstrip("=")
    elif encoding == "custom":
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        num = int.from_bytes(raw_hash, "big")  # Convert bytes to an integer
        readable_hash = ""
        while num > 0:
            readable_hash = alphabet[num % len(alphabet)] + readable_hash
            num //= len(alphabet)
    else:
        raise ValueError("Unsupported encoding type. Use 'hex', 'base64', or 'custom'.")
    
    # Step 3: Truncate the hash for readability
    return readable_hash[:length]
