# RE:GENESIS class mapping (I-2.1.2)

## Target classes

- `0`: CPU
- `1`: GPU
- `2`: RAM
- `3`: SSD
- `4`: HDD
- `5`: PSU
- `6`: NIC
- `7`: Fan
- `8`: Other

## Source → target

| Source (Roboflow) | → | RE:GENESIS |
|-------------------|---|------------|
| HDD, internal HDD | → | HDD |
| NetworkSwitch, Router | → | NIC |
| Battery, 9V Battery, Keyboard, PCB, Remote, Phone, USB, cable, mouse | → | Other |

## Coverage note

This export has **no** labeled examples yet for: `CPU`, `GPU`, `RAM`, `SSD`, `PSU`, `Fan`.
Those class ids stay reserved so the train script / Lambda schema match.
Hackathon demo can still run; improve coverage later with more images.

## Adding leftover classes later (after M6 — low complexity)

Keep **the same ids** (`0=CPU` … `8=Other`). Do not rename or reorder.

1. Label new images into `regenesis_yolo` (or remapped export) using those ids.  
2. Retrain → replace `ml/weights/best.pt`.  
3. Rebuild `model.tar.gz` (include `code/inference.py` + `code/class_schema.py`).  
4. Update SageMaker endpoint weights (same endpoint name is fine).  
5. No change needed to API Gateway, Step Functions, UI routes, or detection JSON schema.

Canonical map: `ml/training/class_schema.py`.
