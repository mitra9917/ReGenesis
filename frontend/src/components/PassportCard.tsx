import { useState } from "react";
import { verifyPassport } from "../api";
import { copyTextToClipboard } from "../clipboard";

export type PassportLike = {
  passport_id: string;
  component_id?: string;
  comp_type?: string;
  class?: string;
  status?: string;
  health_score?: number;
  letter_grade?: string;
  serial?: string;
  serial_number?: string;
  signature_algorithm?: string;
};

type Props = {
  passport: PassportLike;
  deviceSerial?: string;
};

export function PassportCard({ passport, deviceSerial }: Props) {
  const [result, setResult] = useState<{
    valid?: boolean;
    error?: string;
    demo?: boolean;
    message?: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(false);

  const passportId = passport.passport_id;
  const compType =
    passport.comp_type ||
    (passport as any).component_type ||
    passport.class ||
    "Component";
  const componentId = passport.component_id || "—";
  const serial =
    passport.serial ||
    passport.serial_number ||
    deviceSerial ||
    (componentId !== "—" ? `SN-${String(componentId).slice(0, 8).toUpperCase()}` : "—");
  const grade =
    passport.letter_grade ||
    (passport as any).diagnostics_grade ||
    (passport as any).grade ||
    "—";

  // Live AWS: health is on the component row; passport JSON may only have `tests`
  let health = "—";
  const rawHealth = passport.health_score ?? (passport as any).health;
  if (typeof rawHealth === "number") {
    health = `${Math.round(rawHealth <= 1 ? rawHealth * 100 : rawHealth)}/100`;
  } else if (typeof rawHealth === "string" && rawHealth.trim()) {
    const n = parseFloat(rawHealth);
    health = Number.isFinite(n)
      ? `${Math.round(n <= 1 ? n * 100 : n)}/100`
      : rawHealth;
  } else if ((passport as any).tests && typeof (passport as any).tests === "object") {
    const tests = (passport as any).tests as Record<string, unknown>;
    const vals = Object.values(tests);
    const passed = vals.filter((v) => String(v).toLowerCase() === "pass" || v === 0 || v === true);
    if (vals.length) {
      health = `${Math.round((passed.length / vals.length) * 100)}/100 (from tests)`;
    }
  } else if (passport.status?.includes("qualified")) {
    health = "Qualified";
  }

  async function onVerify() {
    if (!passportId) {
      setResult({ valid: false, error: "Missing passport_id" });
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await verifyPassport(passportId);
      setResult(res);
    } catch (err: any) {
      setResult({ valid: false, error: err?.message || "Verify failed" });
    } finally {
      setLoading(false);
    }
  }

  async function onCopyId() {
    const ok = await copyTextToClipboard(passportId);
    if (ok) {
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    }
  }

  return (
    <div className="passport-card-item">
      <div className="passport-card-meta">
        <div className="passport-card-title-row">
          <span className="comp-badge">{compType}</span>
          {grade !== "—" && <span className="pill pill-catalog">{grade}</span>}
        </div>
        <div className="passport-card-lines">
          <div>
            <span className="meta-k">Component ID:</span>{" "}
            <span className="font-mono">{componentId}</span>
          </div>
          <div>
            <span className="meta-k">Serial / Tag:</span>{" "}
            <span className="font-mono">{serial}</span>
          </div>
          <div>
            <span className="meta-k">Passport ID:</span>{" "}
            <span className="font-mono text-xs">{passportId}</span>
          </div>
          <div>
            <span className="meta-k">Health:</span> <strong>{health}</strong>
          </div>
        </div>
      </div>

      <div className="passport-card-actions">
        <button type="button" className="btn btn-sm btn-outline" onClick={onCopyId}>
          {copiedId ? "✓ Copied ID" : "Copy Passport ID"}
        </button>
        <button
          type="button"
          className="btn btn-sm btn-secondary"
          onClick={onVerify}
          disabled={loading || !passportId}
        >
          {loading ? "Verifying…" : "Verify (KMS)"}
        </button>
      </div>

      {result && (
        <div
          className="passport-verify-result"
          style={{ color: result.valid ? "var(--accent)" : "var(--danger)" }}
        >
          {result.valid
            ? result.demo
              ? "✓ Demo passport valid (sample data — not in AWS yet)"
              : "✓ Signature valid (AWS KMS)"
            : `✗ Invalid${result.error ? ` — ${result.error}` : ""}`}
        </div>
      )}
    </div>
  );
}
