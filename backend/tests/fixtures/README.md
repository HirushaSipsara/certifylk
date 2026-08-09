# Synthetic evidence fixtures

These images are fictional, non-sensitive test evidence generated for CertifyLK's
Gemini transport and UI regression coverage. They are not records from a real
manufacturer and do not claim certification or compliance.

- `handwashing-facility.png` visibly contains a sink, liquid-soap dispenser, and
  single-use paper-towel dispenser.
- `irrelevant-office.png` contains an office desk and deliberately provides no
  handwashing evidence.

Production AI behavior must never key off these filenames. Tests use them to prove
that the exact binary bytes and MIME types reach the provider request.
