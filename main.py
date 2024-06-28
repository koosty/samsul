import os, json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

with open("public.pem", "rb") as pem_file:
    public_key = serialization.load_pem_public_key(
        pem_file.read(),
        backend=default_backend()
    )
    print(json.dumps(public_key))