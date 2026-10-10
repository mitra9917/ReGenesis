import { useState, useEffect } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { createDevice, fileToBase64 } from "../api";

const MODELS = [
  {
    key: "poweredge_r740",
    label: "Dell PowerEdge R740 (Enterprise 2U Rack Server)",
    category: "rack_server",
    hints: ["PowerEdge", "R740", "Dell EMC", "Service Tag"],
    expected: "19 components (Dual Xeon, 8x RAM, 4x SSD, 2x GPU, 2x PSU, 1x NIC)",
  },
  {
    key: "thinkpad_t14",
    label: "Lenovo ThinkPad T14 Gen 2 (Business Laptop)",
    category: "laptop",
    hints: ["ThinkPad", "T14", "Lenovo", "Type 20W0"],
    expected: "5 components (50Wh Battery, M.2 SSD, 2x RAM, Wi-Fi 6 card)",
  },
  {
    key: "cisco_catalyst_9300",
    label: "Cisco Catalyst 9300 Series (Enterprise Switch)",
    category: "network_switch",
    hints: ["Catalyst", "9300", "Cisco Systems", "C9300-48P"],
    expected: "9 components (2x PSU, 3x Fan trays, 2x RAM, 1x SSD, 1x NIC)",
  },
];

export function UploadPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialModel = searchParams.get("model") || MODELS[0].key;

  const [model, setModel] = useState(initialModel);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [serialHint, setSerialHint] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const qModel = searchParams.get("model");
    if (qModel && MODELS.some((m) => m.key === qModel)) {
      setModel(qModel);
    }
  }, [searchParams]);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] || null;
    setFile(f);
    if (f) {
      setPreviewUrl(URL.createObjectURL(f));
    } else {
      setPreviewUrl(null);
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload: {
        device_model_key: string;
        image_base64?: string;
        content_type?: string;
        serial_hint?: string;
      } = {
        device_model_key: model,
        serial_hint: serialHint || undefined,
      };
      if (file) {
        payload.image_base64 = await fileToBase64(file);
        payload.content_type = file.type || "image/jpeg";
      }
      const res = await createDevice(payload);
      if (res.execution_arn) {
        sessionStorage.setItem(`execution_${res.device_id}`, res.execution_arn);
      }
      navigate(`/devices/${res.device_id}`);
    } catch (err: any) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  const selectedModelInfo = MODELS.find((m) => m.key === model) || MODELS[0];
  const sampleDeviceId =
    model === "thinkpad_t14"
      ? "sample-t14"
      : model === "cisco_catalyst_9300"
      ? "sample-c9300"
      : "sample-r740";

  return (
    <div className="upload-page">
      <div className="card">
        <div className="intake-card-header">
          <div>
            <h1 className="page-title">Initiate Hardware Recovery Intake</h1>
            <p className="page-subtitle">
              Upload an interior or model plate photo. RE:GENESIS will execute OCR plate extraction,
              YOLOv8 vision detection with catalog fallback, BOM completeness auditing, and RVS disassembly planning.
            </p>
          </div>
          <span className="badge-aws">API Gateway · POST /devices</span>
        </div>

        <form onSubmit={onSubmit}>
          <div className="form-group">
            <label htmlFor="model">Device Target Architecture</label>
            <select
              id="model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="select-input"
            >
              {MODELS.map((m) => (
                <option key={m.key} value={m.key}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>

          <div className="model-spec-box">
            <div className="spec-row">
              <span className="spec-label">Target BOM:</span>
              <span className="spec-val">{selectedModelInfo.expected}</span>
            </div>
            <div className="spec-row">
              <span className="spec-label">OCR Keywords:</span>
              <div className="hint-badges-wrap">
                {selectedModelInfo.hints.map((h) => (
                  <span key={h} className="hint-badge font-mono">
                    "{h}"
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="grid-2 form-row">
            <div className="form-group">
              <label htmlFor="serial">Serial Number / Asset Tag (Optional)</label>
              <input
                id="serial"
                type="text"
                placeholder="e.g. SN-R740-LAB-4289"
                value={serialHint}
                onChange={(e) => setSerialHint(e.target.value)}
                className="input-text"
              />
              <span className="input-hint">Will be bound into KMS signed passport certificates</span>
            </div>

            <div className="form-group">
              <label htmlFor="photo">Interior or Plate Photo (Optional)</label>
              <input
                id="photo"
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="input-file"
              />
              <span className="input-hint">Processed by Amazon S3 &amp; SageMaker YOLOv8</span>
            </div>
          </div>

          {previewUrl && (
            <div className="image-preview-box">
              <div className="preview-label">Selected Intake Photo Preview:</div>
              <img src={previewUrl} alt="Device Preview" className="preview-thumb" />
            </div>
          )}

          {error && (
            <div className="verify-error-box">
              <strong>Error:</strong> {error}
              <div style={{ marginTop: "0.5rem" }}>
                <span>Testing offline? You can view the live demo run directly: </span>
                <Link to={`/devices/${sampleDeviceId}`} className="link-accent">
                  Open {selectedModelInfo.label} Golden Run →
                </Link>
              </div>
            </div>
          )}

          <div className="form-actions-row">
            <button
              className="btn btn-primary"
              type="submit"
              disabled={loading}
            >
              {loading ? "Starting AWS Pipeline…" : "Execute RE:GENESIS Intake"}
            </button>
            <Link to={`/devices/${sampleDeviceId}`} className="btn btn-outline">
              Inspect Pre-Loaded {selectedModelInfo.label.split(" ")[0]} Golden Run
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}

