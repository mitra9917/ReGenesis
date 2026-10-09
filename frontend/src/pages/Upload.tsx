import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createDevice, fileToBase64 } from "../api";

const MODELS = [
  { key: "poweredge_r740", label: "Dell PowerEdge R740 (rack server)" },
  { key: "thinkpad_t14", label: "Lenovo ThinkPad T14 (laptop)" },
  { key: "cisco_catalyst_9300", label: "Cisco Catalyst 9300 (switch)" },
];

export function UploadPage() {
  const navigate = useNavigate();
  const [model, setModel] = useState(MODELS[0].key);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload: {
        device_model_key: string;
        image_base64?: string;
        content_type?: string;
      } = { device_model_key: model };
      if (file) {
        payload.image_base64 = await fileToBase64(file);
        payload.content_type = file.type || "image/jpeg";
      }
      const res = await createDevice(payload);
      sessionStorage.setItem(`execution_${res.device_id}`, res.execution_arn);
      navigate(`/devices/${res.device_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  const apiConfigured = Boolean(import.meta.env.VITE_API_URL || import.meta.env.DEV);

  return (
    <div className="card">
      <h1>Start recovery</h1>
      <p style={{ color: "var(--muted)" }}>
        Upload an interior photo or select a known device model. The pipeline detects components,
        plans extraction, runs diagnostics, and issues KMS-signed passports.
      </p>
      {!apiConfigured && (
        <p style={{ color: "var(--warn)" }}>
          Set <code className="mono">VITE_API_URL</code> in <code className="mono">.env</code> after SAM deploy.
        </p>
      )}
      <form onSubmit={onSubmit}>
        <label htmlFor="model">Device model</label>
        <select id="model" value={model} onChange={(e) => setModel(e.target.value)}>
          {MODELS.map((m) => (
            <option key={m.key} value={m.key}>{m.label}</option>
          ))}
        </select>
        <div style={{ marginTop: "1rem" }}>
          <label htmlFor="photo">Interior photo (optional)</label>
          <input
            id="photo"
            type="file"
            accept="image/*"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </div>
        {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
        <div style={{ marginTop: "1.25rem" }}>
          <button className="btn" type="submit" disabled={loading || !apiConfigured}>
            {loading ? "Starting pipeline…" : "Run RE:GENESIS"}
          </button>
        </div>
      </form>
    </div>
  );
}
