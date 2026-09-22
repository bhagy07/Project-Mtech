import base64
import struct
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def read_mpint(data, offset):
    length = struct.unpack(">I", data[offset:offset+4])[0]
    offset += 4
    val_bytes = data[offset:offset+length]
    offset += length
    val = int.from_bytes(val_bytes, byteorder="big", signed=False)
    return val, offset

def read_string(data, offset):
    length = struct.unpack(">I", data[offset:offset+4])[0]
    offset += 4
    val_bytes = data[offset:offset+length]
    offset += length
    return val_bytes, offset

def convert_ppk_to_pem(ppk_path, pem_path):
    print(f"Reading PuTTY PPK file: {ppk_path}")
    if not os.path.exists(ppk_path):
        print(f"[ERROR] Source file not found: {ppk_path}")
        return False

    with open(ppk_path, "r") as f:
        lines = [line.strip() for line in f.readlines()]

    pub_lines = []
    priv_lines = []
    in_pub = False
    in_priv = False

    for line in lines:
        if line.startswith("Public-Lines:"):
            in_pub = True
            in_priv = False
            continue
        elif line.startswith("Private-Lines:"):
            in_pub = False
            in_priv = True
            continue
        elif line.startswith("Private-MAC:"):
            in_priv = False
            continue

        if in_pub:
            pub_lines.append(line)
        elif in_priv:
            priv_lines.append(line)

    pub_bytes = base64.b64decode("".join(pub_lines))
    priv_bytes = base64.b64decode("".join(priv_lines))

    # Read Public Key Data: string(alg), mpint(e), mpint(n)
    off = 0
    alg, off = read_string(pub_bytes, off)
    e, off = read_mpint(pub_bytes, off)
    n, off = read_mpint(pub_bytes, off)

    # Read Private Key Data: mpint(d), mpint(p), mpint(q), mpint(iqmp)
    off = 0
    d, off = read_mpint(priv_bytes, off)
    p, off = read_mpint(priv_bytes, off)
    q, off = read_mpint(priv_bytes, off)
    iqmp, off = read_mpint(priv_bytes, off)

    # Compute dP and dQ for RSA private key
    dmp1 = d % (p - 1)
    dmq1 = d % (q - 1)

    # Construct Cryptography RSA Private Key
    public_numbers = rsa.RSAPublicNumbers(e, n)
    private_numbers = rsa.RSAPrivateNumbers(
        p=p,
        q=q,
        d=d,
        dmp1=dmp1,
        dmq1=dmq1,
        iqmp=iqmp,
        public_numbers=public_numbers
    )
    private_key = private_numbers.private_key()

    pem_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    with open(pem_path, "wb") as f:
        f.write(pem_bytes)

    print(f"[SUCCESS] Converted '{ppk_path}' -> '{pem_path}'")
    return True

if __name__ == "__main__":
    src_ppk = r"C:\Users\neml10742\Downloads\AWSLinuxKeyPair_putty (1) (1).ppk"
    dst_pem = r"C:\Users\neml10742\Downloads\AWSLinuxKeyPair.pem"
    convert_ppk_to_pem(src_ppk, dst_pem)
