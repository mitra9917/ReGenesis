# Data model

## DynamoDB tables

### `Devices`

| Attribute | Key | Description |
|-----------|-----|-------------|
| `device_id` | PK | UUID |
| `device_model_key` | | Catalog key |
| `status` | | `INGESTED`, `RECOVERING`, `COMPLETED`, `FAILED` |
| `image_s3_key` | | Original image |
| `execution_arn` | | Latest Step Functions run |
| `detection_source` | | `vision`, `catalog-assisted`, `mock` |
| `completeness_audit` | | Map: expected vs detected per class |
| `impact_summary` | | Aggregated kg, CO₂e |
| `created_at` | | ISO8601 |
| `updated_at` | | ISO8601 |

**GSI `StatusIndex`**: PK `status`, SK `created_at`

### `Components`

| Attribute | Key | Description |
|-----------|-----|-------------|
| `device_id` | PK | |
| `component_id` | SK | UUID |
| `comp_type` | | GPU, RAM, SSD, ... |
| `detection_confidence` | | 0–1 |
| `bbox` | | `[x,y,w,h]` normalized 0–1 |
| `status` | | `pending`, `tested`, `qualified`, `failed` |
| `extraction_step` | | Order in plan |
| `test_results` | | JSON |
| `passport_id` | | If qualified |

**GSI `DeviceStatusIndex`**: PK `device_id`, SK `status`

### `Passports`

| Attribute | Key | Description |
|-----------|-----|-------------|
| `passport_id` | PK | UUID |
| `device_id` | | |
| `component_id` | | |
| `s3_key` | | |
| `status` | | `qualified_for_reuse`, `failed` |
| `created_at` | | |

**GSI `DevicePassportsIndex`**: PK `device_id`, SK `created_at`

### `PipelineEvents`

| Attribute | Key | Description |
|-----------|-----|-------------|
| `device_id` | PK | |
| `event_id` | SK | `{iso}#{uuid}` |
| `event_type` | | ingest, detect, plan, test, passport |
| `detail` | | JSON |
| `status` | | started, succeeded, failed |

## JSON schemas

See [shared/schemas/](../shared/schemas/).
