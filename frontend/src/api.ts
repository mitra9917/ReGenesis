/** In dev, default `/api` uses Vite proxy (avoids browser CORS). In prod, set full API Gateway URL. */
const API_URL = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");

async function apiFetch(path: string, init?: RequestInit) {
  try {
    return await fetch(`${API_URL}${path}`, init);
  } catch {
    const hint =
      API_URL === "/api"
        ? "Restart Vite after editing frontend/.env, or try without a large photo."
        : "Check network/CORS and that the API URL in the production build is correct.";
    throw new Error(`Failed to fetch — ${hint}`);
  }
}

export async function createDevice(payload: {
  device_model_key: string;
  image_base64?: string;
  content_type?: string;
  serial_hint?: string;
}) {
  const res = await apiFetch("/devices", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getDevice(deviceId: string) {
  const res = await apiFetch(`/devices/${deviceId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getJob(executionArn: string) {
  const q = encodeURIComponent(executionArn);
  const res = await apiFetch(`/jobs?execution_arn=${q}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function verifyPassport(passportId: string) {
  const res = await apiFetch(`/passports/${passportId}/verify`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPipelineEvents(deviceId: string, eventType?: string) {
  const query = eventType ? `?event_type=${encodeURIComponent(eventType)}` : "";
  const res = await apiFetch(`/devices/${deviceId}/events${query}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      resolve(result.split(",")[1] || "");
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export interface SampleDeviceRecord {
  device_id: string;
  device_model_key: string;
  display_name: string;
  category: string;
  status: string;
  serial_hint: string;
  detection_source: string;
  summary: {
    total_components_detected: number;
    health_breakdown: Record<string, number>;
  };
  completeness_audit: {
    score: number;
    status: string;
    gap_count: number;
    gaps: Array<{
      comp_type: string;
      expected: number;
      detected: number;
      missing: number;
      deficit_pct: number;
      severity: string;
      message: string;
      remediation: string;
    }>;
  };
  plan: {
    device_model_key: string;
    total_steps: number;
    total_plan_rvs: number;
    steps: Array<{
      catalog_step: number;
      action: string;
      step_rvs: number;
      priority_tier: string;
      risk: number;
      components: Array<{ comp_id: string; comp_type: string; rvs: number }>;
    }>;
  };
  impact: {
    co2e_avoided_kg: number;
    co2e_avoided_kg_range?: { low: number; high: number };
    mass_diverted_kg: number;
    mass_diverted_kg_range?: { low: number; high: number };
    components_diverted_count: number;
    factor_citations?: Record<string, string>;
  };
  passports: Array<{
    passport_id: string;
    component_id: string;
    comp_type: string;
    status: string;
    health_score: number;
    letter_grade: string;
    signature?: string;
    signature_algorithm?: string;
    metrics: Record<string, any>;
  }>;
}

export const SAMPLE_GOLDEN_RUNS: Record<string, SampleDeviceRecord> = {
  "sample-r740": {
    device_id: "sample-r740",
    device_model_key: "poweredge_r740",
    display_name: "Dell PowerEdge R740 (Rack Server)",
    category: "rack_server",
    status: "SUCCEEDED",
    serial_hint: "SN-DELL-R740-GOLDEN-01",
    detection_source: "vision+catalog",
    summary: {
      total_components_detected: 19,
      health_breakdown: { pass: 17, degraded: 2, fail: 0 },
    },
    completeness_audit: {
      score: 100,
      status: "complete",
      gap_count: 0,
      gaps: [],
    },
    plan: {
      device_model_key: "poweredge_r740",
      total_steps: 7,
      total_plan_rvs: 412.5,
      steps: [
        {
          catalog_step: 1,
          action: "Remove top chassis cover",
          step_rvs: 0.0,
          priority_tier: "standard",
          risk: 0.1,
          components: [],
        },
        {
          catalog_step: 2,
          action: "Remove high-value GPU modules (risers)",
          step_rvs: 264.6,
          priority_tier: "critical",
          risk: 0.35,
          components: [
            { comp_id: "gpu-01", comp_type: "GPU", rvs: 132.3 },
            { comp_id: "gpu-02", comp_type: "GPU", rvs: 132.3 },
          ],
        },
        {
          catalog_step: 3,
          action: "Extract hot-plug redundant PSUs",
          step_rvs: 53.78,
          priority_tier: "high",
          risk: 0.25,
          components: [
            { comp_id: "psu-01", comp_type: "PSU", rvs: 26.89 },
            { comp_id: "psu-02", comp_type: "PSU", rvs: 26.89 },
          ],
        },
        {
          catalog_step: 4,
          action: "Remove dual Intel Xeon CPUs",
          step_rvs: 56.4,
          priority_tier: "high",
          risk: 0.45,
          components: [
            { comp_id: "cpu-01", comp_type: "CPU", rvs: 28.2 },
            { comp_id: "cpu-02", comp_type: "CPU", rvs: 28.2 },
          ],
        },
        {
          catalog_step: 5,
          action: "Extract enterprise SSD array",
          step_rvs: 18.4,
          priority_tier: "medium",
          risk: 0.1,
          components: [
            { comp_id: "ssd-01", comp_type: "SSD", rvs: 4.6 },
            { comp_id: "ssd-02", comp_type: "SSD", rvs: 4.6 },
            { comp_id: "ssd-03", comp_type: "SSD", rvs: 4.6 },
            { comp_id: "ssd-04", comp_type: "SSD", rvs: 4.6 },
          ],
        },
        {
          catalog_step: 6,
          action: "Extract DDR4 ECC RAM banks",
          step_rvs: 16.0,
          priority_tier: "medium",
          risk: 0.15,
          components: [
            { comp_id: "ram-01", comp_type: "RAM", rvs: 2.0 },
            { comp_id: "ram-02", comp_type: "RAM", rvs: 2.0 },
            { comp_id: "ram-03", comp_type: "RAM", rvs: 2.0 },
            { comp_id: "ram-04", comp_type: "RAM", rvs: 2.0 },
          ],
        },
        {
          catalog_step: 7,
          action: "Extract Quad-Port 10GbE NIC",
          step_rvs: 3.32,
          priority_tier: "standard",
          risk: 0.2,
          components: [{ comp_id: "nic-01", comp_type: "NIC", rvs: 3.32 }],
        },
      ],
    },
    impact: {
      co2e_avoided_kg: 524.2,
      co2e_avoided_kg_range: { low: 412.0, high: 648.5 },
      mass_diverted_kg: 14.8,
      mass_diverted_kg_range: { low: 12.1, high: 17.6 },
      components_diverted_count: 19,
      factor_citations: {
        CPU: "Dell Server LCA & IEEE Micro benchmarks (embodied 68kg CO2e)",
        GPU: "Enterprise Accelerator LCA (HBM + massive silicon die, 180kg CO2e)",
        RAM: "JEDEC / Semiconductor LCA report (8kg CO2e per 32GB DIMM)",
        SSD: "Enterprise NVMe Flash LCA (14kg CO2e per U.2 drive)",
        PSU: "Titanium Efficiency Power Supply teardown (16kg CO2e)",
        NIC: "Dual/Quad port PCIe controller LCA (5kg CO2e)",
      },
    },
    passports: [
      {
        passport_id: "pass-r740-gpu-01",
        component_id: "gpu-01",
        comp_type: "GPU",
        status: "pass",
        health_score: 96,
        letter_grade: "Grade A",
        signature_algorithm: "ECDSA_SHA_256",
        signature: "MEQCID...KMS_SIGNATURE_VALID_AWS_ECC_NIST_P256",
        metrics: { vram_errors: 0, compute_flops_pct: 99.2, temp_celsius: 48 },
      },
      {
        passport_id: "pass-r740-cpu-01",
        component_id: "cpu-01",
        comp_type: "CPU",
        status: "pass",
        health_score: 98,
        letter_grade: "Grade A",
        signature_algorithm: "ECDSA_SHA_256",
        signature: "MEQCID...KMS_SIGNATURE_VALID_AWS_ECC_NIST_P256",
        metrics: { cores_active: 24, thermal_throttles: 0, cache_parity: "ok" },
      },
      {
        passport_id: "pass-r740-ssd-01",
        component_id: "ssd-01",
        comp_type: "SSD",
        status: "pass",
        health_score: 92,
        letter_grade: "Grade A",
        signature_algorithm: "ECDSA_SHA_256",
        signature: "MEQCID...KMS_SIGNATURE_VALID_AWS_ECC_NIST_P256",
        metrics: { tbw_pct_used: 14.2, bad_blocks: 0, read_iops_k: 450 },
      },
      {
        passport_id: "pass-r740-psu-01",
        component_id: "psu-01",
        comp_type: "PSU",
        status: "pass",
        health_score: 94,
        letter_grade: "Grade A",
        signature_algorithm: "ECDSA_SHA_256",
        signature: "MEQCID...KMS_SIGNATURE_VALID_AWS_ECC_NIST_P256",
        metrics: { efficiency_pct: 94.1, ripple_mv: 22, fan_rpm: 2100 },
      },
    ],
  },
  "sample-t14": {
    device_id: "sample-t14",
    device_model_key: "thinkpad_t14",
    display_name: "Lenovo ThinkPad T14 (Business Laptop)",
    category: "laptop",
    status: "SUCCEEDED",
    serial_hint: "SN-LENOVO-T14-DEMO-02",
    detection_source: "vision+catalog",
    summary: {
      total_components_detected: 5,
      health_breakdown: { pass: 4, degraded: 1, fail: 0 },
    },
    completeness_audit: {
      score: 100,
      status: "complete",
      gap_count: 0,
      gaps: [],
    },
    plan: {
      device_model_key: "thinkpad_t14",
      total_steps: 5,
      total_plan_rvs: 88.5,
      steps: [
        {
          catalog_step: 1,
          action: "Remove bottom enclosure panel",
          step_rvs: 0.0,
          priority_tier: "standard",
          risk: 0.1,
          components: [],
        },
        {
          catalog_step: 2,
          action: "Disconnect 50Wh Li-Ion internal battery",
          step_rvs: 18.2,
          priority_tier: "critical",
          risk: 0.4,
          components: [{ comp_id: "bat-01", comp_type: "Battery", rvs: 18.2 }],
        },
        {
          catalog_step: 3,
          action: "Extract M.2 PCIe NVMe SSD",
          step_rvs: 32.1,
          priority_tier: "high",
          risk: 0.1,
          components: [{ comp_id: "ssd-01", comp_type: "SSD", rvs: 32.1 }],
        },
        {
          catalog_step: 4,
          action: "Extract DDR4 SO-DIMM RAM modules",
          step_rvs: 24.0,
          priority_tier: "medium",
          risk: 0.15,
          components: [
            { comp_id: "ram-01", comp_type: "RAM", rvs: 12.0 },
            { comp_id: "ram-02", comp_type: "RAM", rvs: 12.0 },
          ],
        },
        {
          catalog_step: 5,
          action: "Remove Wi-Fi 6 M.2 card",
          step_rvs: 14.2,
          priority_tier: "standard",
          risk: 0.2,
          components: [{ comp_id: "wifi-01", comp_type: "WiFi", rvs: 14.2 }],
        },
      ],
    },
    impact: {
      co2e_avoided_kg: 84.6,
      co2e_avoided_kg_range: { low: 68.0, high: 105.2 },
      mass_diverted_kg: 1.45,
      mass_diverted_kg_range: { low: 1.2, high: 1.8 },
      components_diverted_count: 5,
      factor_citations: {
        Battery: "UN Portable Battery Association LCA & EPA benchmark (18kg CO2e)",
        SSD: "Enterprise NVMe Flash LCA (14kg CO2e)",
        RAM: "JEDEC / Semiconductor LCA report (8kg CO2e)",
        WiFi: "Wi-Fi Alliance RF Module LCA (3.5kg CO2e)",
      },
    },
    passports: [
      {
        passport_id: "pass-t14-bat-01",
        component_id: "bat-01",
        comp_type: "Battery",
        status: "pass",
        health_score: 88,
        letter_grade: "Grade B",
        signature_algorithm: "ECDSA_SHA_256",
        signature: "MEQCID...KMS_SIGNATURE_VALID_AWS_ECC_NIST_P256",
        metrics: { cycle_count: 142, capacity_pct: 88.5, swelling_detected: false },
      },
      {
        passport_id: "pass-t14-ssd-01",
        component_id: "ssd-01",
        comp_type: "SSD",
        status: "pass",
        health_score: 95,
        letter_grade: "Grade A",
        signature_algorithm: "ECDSA_SHA_256",
        signature: "MEQCID...KMS_SIGNATURE_VALID_AWS_ECC_NIST_P256",
        metrics: { tbw_pct_used: 9.1, bad_blocks: 0 },
      },
    ],
  },
  "sample-c9300": {
    device_id: "sample-c9300",
    device_model_key: "cisco_catalyst_9300",
    display_name: "Cisco Catalyst 9300 (Network Switch)",
    category: "network_switch",
    status: "SUCCEEDED",
    serial_hint: "SN-CISCO-C9300-SERIES-03",
    detection_source: "vision+catalog",
    summary: {
      total_components_detected: 9,
      health_breakdown: { pass: 9, degraded: 0, fail: 0 },
    },
    completeness_audit: {
      score: 100,
      status: "complete",
      gap_count: 0,
      gaps: [],
    },
    plan: {
      device_model_key: "cisco_catalyst_9300",
      total_steps: 5,
      total_plan_rvs: 142.0,
      steps: [
        {
          catalog_step: 1,
          action: "Extract redundant hot-plug switch PSUs",
          step_rvs: 48.0,
          priority_tier: "critical",
          risk: 0.25,
          components: [
            { comp_id: "psu-01", comp_type: "PSU", rvs: 24.0 },
            { comp_id: "psu-02", comp_type: "PSU", rvs: 24.0 },
          ],
        },
        {
          catalog_step: 2,
          action: "Remove modular uplink network card (NIC)",
          step_rvs: 38.5,
          priority_tier: "high",
          risk: 0.2,
          components: [{ comp_id: "nic-01", comp_type: "NIC", rvs: 38.5 }],
        },
        {
          catalog_step: 3,
          action: "Extract boot storage SSD module",
          step_rvs: 22.0,
          priority_tier: "medium",
          risk: 0.1,
          components: [{ comp_id: "ssd-01", comp_type: "SSD", rvs: 22.0 }],
        },
        {
          catalog_step: 4,
          action: "Extract control-plane RAM DIMMs",
          step_rvs: 18.0,
          priority_tier: "medium",
          risk: 0.15,
          components: [
            { comp_id: "ram-01", comp_type: "RAM", rvs: 9.0 },
            { comp_id: "ram-02", comp_type: "RAM", rvs: 9.0 },
          ],
        },
        {
          catalog_step: 5,
          action: "Remove hot-swap fan tray modules",
          step_rvs: 15.5,
          priority_tier: "standard",
          risk: 0.2,
          components: [
            { comp_id: "fan-01", comp_type: "Fan", rvs: 5.16 },
            { comp_id: "fan-02", comp_type: "Fan", rvs: 5.16 },
            { comp_id: "fan-03", comp_type: "Fan", rvs: 5.16 },
          ],
        },
      ],
    },
    impact: {
      co2e_avoided_kg: 182.4,
      co2e_avoided_kg_range: { low: 148.0, high: 226.0 },
      mass_diverted_kg: 8.9,
      mass_diverted_kg_range: { low: 7.4, high: 10.8 },
      components_diverted_count: 9,
      factor_citations: {
        PSU: "Cisco Catalyst Hardware Lifecycle Report (22kg CO2e per 715W AC PSU)",
        Fan: "Industrial Brushless DC Fan LCA (4.2kg CO2e)",
        NIC: "Modular 4x10G Uplink Module LCA (12kg CO2e)",
      },
    },
    passports: [
      {
        passport_id: "pass-c9300-psu-01",
        component_id: "psu-01",
        comp_type: "PSU",
        status: "pass",
        health_score: 97,
        letter_grade: "Grade A",
        signature_algorithm: "ECDSA_SHA_256",
        signature: "MEQCID...KMS_SIGNATURE_VALID_AWS_ECC_NIST_P256",
        metrics: { power_factor: 0.99, output_watts: 715, temp_celsius: 41 },
      },
      {
        passport_id: "pass-c9300-nic-01",
        component_id: "nic-01",
        comp_type: "NIC",
        status: "pass",
        health_score: 99,
        letter_grade: "Grade A",
        signature_algorithm: "ECDSA_SHA_256",
        signature: "MEQCID...KMS_SIGNATURE_VALID_AWS_ECC_NIST_P256",
        metrics: { ports_tested: 4, crc_errors: 0, sfp_plus_link: "10GbE ok" },
      },
    ],
  },
};

