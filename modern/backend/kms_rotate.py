"""
Envelope encryption data key rotation helper (AWS KMS example).

This script demonstrates how to rotate the data key used by `crypto.py`.
It:
 - Generates a new data key via KMS.GenerateDataKey
 - Re-encrypts (rewraps) nothing in this example, but writes the new wrapped key to file
 - In production, you should re-encrypt existing ciphertext with the new data key or keep using envelope rewrap.

Usage (dev): ensure AWS credentials are configured and run:
  python kms_rotate.py --kms-key-id <KMS_KEY_ID>

Note: This is a simple operator helper for demo purposes; adapt safely for production.
"""
import argparse
import boto3
import os

WRAPPED_PATH = os.path.join(os.path.dirname(__file__), 'modern/backend/.wrapped_data_key')

def rotate(kms_key_id: str):
    kms = boto3.client('kms')
    resp = kms.generate_data_key(KeyId=kms_key_id, KeySpec='AES_256')
    ciphertext = resp['CiphertextBlob']
    with open(WRAPPED_PATH, 'wb') as f:
        f.write(ciphertext)
    try:
        os.chmod(WRAPPED_PATH, 0o600)
    except Exception:
        pass
    print('Wrote new wrapped key to', WRAPPED_PATH)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--kms-key-id', required=True)
    args = p.parse_args()
    rotate(args.kms_key_id)