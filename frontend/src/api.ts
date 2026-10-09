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
