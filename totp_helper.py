
import pyotp
import sys

if len(sys.argv) < 2:
    print("Usage: python totp_helper.py <SECRET>")
    sys.exit(1)

secret = sys.argv[1]
totp = pyotp.TOTP(secret)
print(f"Current OTP: {totp.now()}")
