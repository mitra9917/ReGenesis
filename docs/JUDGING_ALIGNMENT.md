# Judging alignment

| Criterion | Where we show it |
|-----------|------------------|
| **Idea & impact** | README problem stats; Impact panel (CO₂e, mass); Waste/E-waste track |
| **Built on AWS** | [AWS_SERVICES.md](AWS_SERVICES.md); call out Step Functions trace + KMS in video |
| **Design & usability** | Upload → single results page; clear labels for vision vs catalog-assisted |
| **Execution** | End-to-end deploy via SAM; verify button proves crypto path works |
| **Demo video** | [DEMO_SCRIPT.md](DEMO_SCRIPT.md); record against deployed URL |

## KPIs to capture (screenshot slide)

- Components recovered vs baseline (0 reuse if shredded)
- End-to-end wall time (from Step Functions)
- Detection path used and completeness audit score
- Passport verify: valid=true
- Estimated CO₂e avoided (range from catalog factors)
