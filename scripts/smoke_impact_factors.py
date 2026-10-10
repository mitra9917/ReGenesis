import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared", "python"))

from regenesis_common.impact import compute_impact_summary



def main():
    print("--- [I-4.4 Smoke Test] Impact Calculation with Catalog Factors & Ranges ---")

    # Sample batch of components representing a decommissioned enterprise server
    sample_components = [
        {"comp_id": "c-01", "comp_type": "CPU", "status": "qualified", "serial_number": "CPU-XEON-991"},
        {"comp_id": "c-02", "comp_type": "CPU", "status": "qualified", "serial_number": "CPU-XEON-992"},
        {"comp_id": "c-03", "comp_type": "GPU", "status": "qualified", "serial_number": "GPU-A100-001"},
        {"comp_id": "c-04", "comp_type": "RAM", "status": "qualified", "serial_number": "RAM-DDR4-32G"},
        {"comp_id": "c-05", "comp_type": "RAM", "status": "qualified", "serial_number": "RAM-DDR4-32G-2"},
        {"comp_id": "c-06", "comp_type": "SSD", "status": "qualified", "serial_number": "SSD-NVME-1TB"},
        {"comp_id": "c-07", "comp_type": "HDD", "status": "failed", "serial_number": "HDD-SAS-2TB"},
    ]

    summary = compute_impact_summary(sample_components)

    print(f"Qualified components: {summary['components_qualified']} / {summary['components_total']}")
    print(f"Failed components:    {summary['components_failed']}")
    print(f"Diverted Mass:        {summary['mass_diverted_kg']} kg (Range: {summary['mass_diverted_kg_range']['low']} - {summary['mass_diverted_kg_range']['high']} kg)")
    print(f"CO2e Avoided:         {summary['co2e_avoided_kg']} kg CO2e")
    print(f"Honest CO2e Range:    [{summary['co2e_avoided_kg_range']['low']} .. {summary['co2e_avoided_kg_range']['high']}] kg CO2e")
    print(f"Baseline Shred Reuse: {summary['baseline_shred_reuse_count']} units")
    print(f"Improvement vs Shred: +{summary['improvement_vs_shred']} parts saved\n")

    print("Factor Citations Breakdown:")
    for comp_type, citation in summary["factor_citations"].items():
        print(f"  [{comp_type}] x{citation['count']}")
        print(f"     Factor: {citation['embodied_co2e_factor_kg']} kg CO2e (Range: {citation['embodied_co2e_range_kg']['low']}-{citation['embodied_co2e_range_kg']['high']} kg)")
        print(f"     Subtotal CO2e: {citation['subtotal_co2e_kg']} kg [{citation['subtotal_co2e_range_kg']['low']} - {citation['subtotal_co2e_range_kg']['high']} kg]")
        print(f"     LCA Source: {citation['lca_source']}")

    print("\nMethodology Statement:")
    print(f"  \"{summary['methodology']}\"")
    print("\n--- Smoke test completed successfully! ---")


if __name__ == "__main__":
    main()
