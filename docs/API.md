# HTTP API

Base URL: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}`

## `POST /devices`

Create a device and start recovery pipeline.

**JSON body (multipart alternative: base64 image in JSON for simplicity)**

```json
{
  "device_model_key": "poweredge_r740",
  "image_base64": "<optional>",
  "content_type": "image/jpeg",
  "serial_hint": "ABC123",
  "plate_text": "<optional OCR override, e.g. Dell PowerEdge R740>"
}
```

With an image and `DETECTION_MODE=auto`, Lambda runs **Tesseract** on the photo to confirm/influence the model key. `plate_text` skips image OCR when provided.

**Response `202`**

```json
{
  "device_id": "uuid",
  "execution_arn": "arn:aws:states:...",
  "status": "RECOVERY_STARTED"
}
```

## `GET /devices/{device_id}`

Full device snapshot: status, detections, completeness audit, plan, components, impact summary.

## `POST /devices/{device_id}/recover`

Restart recovery for an existing device (optional image update).

## `GET /jobs?execution_arn=...`

Poll Step Functions execution status (URL-encoded ARN).

## `GET /passports/{passport_id}`

Passport JSON from S3 (via Lambda).

## `GET /passports/{passport_id}/verify`

```json
{
  "passport_id": "...",
  "valid": true,
  "algorithm": "RSASSA_PSS_SHA_256",
  "verified_at": "2026-10-08T12:00:00Z"
}
```

## Passport signing (canonical form)

1. Copy passport object without `signature`.
2. `json.dumps(obj, sort_keys=True, separators=(",", ":"))`.
3. SHA-256 digest → KMS `Sign` with passport key.
4. Store base64 signature in `signature` field.

Verification uses KMS `Verify` on the same canonical bytes.
