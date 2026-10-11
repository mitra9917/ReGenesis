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

function healthPercent(passport: PassportLike): number | null {
  const rawHealth = passport.health_score ?? (passport as any).health;
  if (typeof rawHealth === "number") {
    return Math.round(rawHealth <= 1 ? rawHealth * 100 : rawHealth);
  }
  if (typeof rawHealth === "string" && rawHealth.trim()) {
    const n = parseFloat(rawHealth);
    if (Number.isFinite(n)) return Math.round(n <= 1 ? n * 100 : n);
  }
  const tests = (passport as any).tests;
  if (tests && typeof tests === "object") {
    const vals = Object.values(tests as Record<string, unknown>);
    if (vals.length) {
      const passed = vals.filter(
        (v) => String(v).toLowerCase() === "pass" || v === 0 || v === true
      );
      return Math.round((passed.length / vals.length) * 100);
    }
  }
  return null;
}

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
  const health = healthPercent(passport);
  const healthLabel =
    health != null
      ? `${health}/100`
      : passport.status?.includes("qualified")
        ? "Qualified"
        : "—";
  const algo = passport.signature_algorithm || "ECDSA_SHA_256";

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
    <article className="dpp-card">
      <header className="dpp-card-top">
        <div className="dpp-card-tags">
          <span className="dpp-type">{compType}</span>
          {grade !== "—" && <span className="dpp-grade">{grade}</span>}
        </div>
        <span className="dpp-seal">KMS signed</span>
      </header>

      <div className="dpp-health">
        <div>
          <span className="dpp-health-label">Health score</span>
          <strong className="dpp-health-value">{healthLabel}</strong>
        </div>
        {health != null && (
          <div className="dpp-health-bar" aria-hidden="true">
            <span style={{ width: `${Math.min(100, Math.max(0, health))}%` }} />
          </div>
        )}
      </div>

      <dl className="dpp-meta">
        <div>
          <dt>Component</dt>
          <dd className="font-mono">{componentId}</dd>
        </div>
        <div>
          <dt>Serial / tag</dt>
          <dd className="font-mono">{serial}</dd>
        </div>
        <div>
          <dt>Passport ID</dt>
          <dd className="font-mono dpp-id">{passportId}</dd>
        </div>
        <div>
          <dt>Algorithm</dt>
          <dd className="font-mono">{algo}</dd>
        </div>
      </dl>

      <div className="dpp-card-actions">
        <button type="button" className="dpp-btn dpp-btn-ghost" onClick={onCopyId}>
          {copiedId ? "Copied" : "Copy ID"}
        </button>
        <button
          type="button"
          className="dpp-btn dpp-btn-solid"
          onClick={onVerify}
          disabled={loading || !passportId}
        >
          {loading ? "Verifying…" : "Verify →"}
        </button>
      </div>

      {result && (
        <div
          className={`dpp-verify ${result.valid ? "is-valid" : "is-invalid"}`}
          role="status"
        >
          {result.valid
            ? result.demo
              ? "Demo passport valid (sample — not live AWS)"
              : "Signature valid · AWS KMS"
            : `Invalid${result.error ? ` — ${result.error}` : ""}`}
        </div>
      )}
    </article>
  );
}
