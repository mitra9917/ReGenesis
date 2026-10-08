const API_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

export async function createDevice(payload: {
  device_model_key: string;
  image_base64?: string;
  content_type?: string;
  serial_hint?: string;
}) {
  const res = await fetch(`${API_URL}/devices`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getDevice(deviceId: string) {
  const res = await fetch(`${API_URL}/devices/${deviceId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getJob(executionArn: string) {
  const q = encodeURIComponent(executionArn);
  const res = await fetch(`${API_URL}/jobs?execution_arn=${q}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function verifyPassport(passportId: string) {
  const res = await fetch(`${API_URL}/passports/${passportId}/verify`);
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
