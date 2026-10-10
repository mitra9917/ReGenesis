# Tesseract OCR Lambda layer (I-3.1.3)

Free replacement for Amazon Textract. Binaries come from
[bweigel/aws-lambda-tesseract-layer](https://github.com/bweigel/aws-lambda-tesseract-layer)
(Amazon Linux 2023 / x86_64 / Python 3.12).

## Setup (before first `sam deploy`)

```powershell
python scripts/fetch_tesseract_layer.py
```

This fills `shared/tesseract_layer/content/` (gitignored). SAM packages it as
`TesseractOcrLayer` and attaches it to `InvokeDetectionFunction`.

## Runtime paths (set in `template.yaml`)

| Env | Value |
|-----|--------|
| `TESSERACT_CMD` | `/opt/bin/tesseract` |
| `TESSDATA_PREFIX` | `/opt/tesseract/share/tessdata` |

Python deps (`Pillow`, `pytesseract`) live in
`backend/functions/invoke_detection/requirements.txt`.
