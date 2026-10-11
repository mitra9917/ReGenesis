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

## Coverage note (updated 2026-10-11)

Merged **Computer Parts** Universe export (`GPU/HDD/RAM/SSD/cpu`) + prior e-waste remap.

| Class | Status |
|-------|--------|
| CPU, GPU, RAM, SSD, HDD, NIC, Other | Labeled — training run `regenesis-yolo-5` |
| PSU, Fan | Still **0** samples (reserved) |

## Adding PSU / Fan later

Keep **the same ids** (`0=CPU` … `8=Other`). Do not rename or reorder.

1. Label new images into `regenesis_yolo` using those ids.  
2. Retrain → replace `ml/weights/best.pt`.  
3. Rebuild `model.tar.gz` (include `code/inference.py` + `code/class_schema.py`).  
4. Update SageMaker endpoint weights (same endpoint name is fine).  
5. No change needed to API Gateway, Step Functions, UI routes, or detection JSON schema.

Canonical map: `ml/training/class_schema.py`.  
Remap helper: `ml/training/remap_computer_parts.py`.
