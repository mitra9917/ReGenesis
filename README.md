# RE:GENESIS

**Adaptive electronics recovery** — computer vision, preservation-aware disassembly planning, and KMS-signed **Second-Life Passports** for components worth reusing before recycling.

Built for [Environmental Hacks | Bharat Builds Tour](https://www.wemakedevs.org/aws/env) (track: **Waste and Energy → E-waste**).

## Problem

Roughly 62 Mt of e-waste was generated globally in 2022, with a large share of valuable metals and still-functional parts lost to destructive recycling. RE:GENESIS identifies recoverable components, plans safe extraction order, simulates requalification, and issues tamper-evident passports so reuse is trustworthy.

## What this repo delivers

| Capability | AWS services |
|------------|----------------|
| Image ingest & orchestration | API Gateway, Lambda, Step Functions, S3 |
| Component detection | SageMaker (YOLO) + Textract/catalog fallback |
| Disassembly planning (RVS) | Lambda, DynamoDB |
| Diagnostic simulation | Lambda (Map state in Step Functions) |
| Second-Life Passport | KMS Sign/Verify, S3, DynamoDB |
| Impact metrics | Lambda, CloudWatch custom metrics |
| Demo UI | S3 + CloudFront (static React) |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/AWS_SERVICES.md](docs/AWS_SERVICES.md).

## Novel mechanisms

1. **Reuse Value Score (RVS)** — ranks disassembly steps by embodied CO₂e, recoverability, and risk.
2. **Completeness audit** — compares catalog BOM vs CV detections before parts are lost.
3. **Passport verify API** — `GET /passports/{id}/verify` checks KMS signatures.

## Quick start (local)

```bash
# Shared library tests
python -m pytest tests/unit -q

# SAM build (requires AWS SAM CLI)
cd infrastructure/sam
sam build
```

Deploy:

```bash
./scripts/deploy.sh
```

Copy `infrastructure/sam/samconfig.toml.example` to `samconfig.toml` after first guided deploy.

Frontend:

```bash
cd frontend
cp env.example .env
npm install
npm run dev
```

Set `VITE_API_URL` to your API Gateway stage URL after deploy.

## ML (SageMaker)

See [ml/README.md](ml/README.md) for YOLO training and endpoint deployment. Set `DETECTION_MODE=mock` on Lambdas for pipeline testing without an endpoint.

## Impact numbers

Embodied CO₂e and mass factors live in [shared/catalog/components_specs.json](shared/catalog/components_specs.json). Values are indicative ranges from public lifecycle literature — the UI shows estimates, not certified LCA.

## Team roadmap (milestones / phases / issues)

Full start→finish board with owners, labels, and what you can run in parallel or skip:

→ **[docs/HACKATHON_PIPELINE.md](docs/HACKATHON_PIPELINE.md)** (includes Cursor AWS MCP setup)

## Team demo checklist

- [ ] One server scenario end-to-end on deployed stack
- [ ] 3-minute video per [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)
- [ ] Builder Center post per [docs/SUBMISSION.md](docs/SUBMISSION.md)

## License

MIT — see [LICENSE](LICENSE).
