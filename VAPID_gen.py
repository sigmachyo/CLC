import os
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

prv_bytes = private_key.private_numbers().private_value.to_bytes(32, 'big')
pub_bytes = public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)

vapid_private = base64.urlsafe_b64encode(prv_bytes).decode('utf-8').rstrip('=')
vapid_public = base64.urlsafe_b64encode(pub_bytes).decode('utf-8').rstrip('=')

print(f"VAPID_PUBLIC_KEY = '{vapid_public}'")
print(f"VAPID_PRIVATE_KEY = '{vapid_private}'")
