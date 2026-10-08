import { useState } from "react";
import { verifyPassport } from "../api";

export function PassportCard({ passportId }: { passportId: string }) {
  const [result, setResult] = useState<{ valid?: boolean } | null>(null);
  const [loading, setLoading] = useState(false);

  async function onVerify() {
    setLoading(true);
    try {
      const res = await verifyPassport(passportId);
      setResult(res);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ borderTop: "1px solid var(--border)", paddingTop: "0.75rem", marginTop: "0.75rem" }}>
      <span className="mono">{passportId}</span>
      <button
        type="button"
        className="btn btn-secondary"
        style={{ marginLeft: "0.75rem" }}
        onClick={onVerify}
        disabled={loading}
      >
        {loading ? "Verifying…" : "Verify (KMS)"}
      </button>
      {result && (
        <span style={{ marginLeft: "0.75rem", color: result.valid ? "var(--accent)" : "var(--danger)" }}>
          {result.valid ? "Signature valid" : "Invalid"}
        </span>
      )}
    </div>
  );
}
