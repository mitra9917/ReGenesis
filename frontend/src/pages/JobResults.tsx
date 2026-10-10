import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getDevice, getJob } from "../api";
import { DetectionOverlay } from "../components/DetectionOverlay";
import { PlanTimeline } from "../components/PlanTimeline";
import { PassportCard } from "../components/PassportCard";
import { ImpactPanel } from "../components/ImpactPanel";

export function JobResultsPage() {
  const { deviceId } = useParams<{ deviceId: string }>();
  const [data, setData] = useState<any>(null);
  const [jobStatus, setJobStatus] = useState<string>("RUNNING");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!deviceId) return null;
    const res = await getDevice(deviceId);
    setData(res);
    const arn = sessionStorage.getItem(`execution_${deviceId}`) || res.device?.execution_arn;
    let currentJobStatus = jobStatus;
    if (arn) {
      try {
        const job = await getJob(arn);
        if (job?.status) {
          currentJobStatus = job.status;
          setJobStatus(job.status);
        }
      } catch (jobErr) {
        console.warn("Job status poll warning:", jobErr);
      }
    }
    return { device: res?.device, jobStatus: currentJobStatus };
  }, [deviceId, jobStatus]);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval>;
    let isCancelled = false;

    const poll = async () => {
      try {
        const result = await load();
        if (isCancelled) return;
        setError("");
        const devStatus = result?.device?.status;
        const jStatus = result?.jobStatus;
        const isJobDone = ["SUCCEEDED", "FAILED", "TIMED_OUT", "ABORTED"].includes(jStatus);
        const isDeviceDone = ["COMPLETED", "FAILED"].includes(devStatus);
        if (isJobDone && isDeviceDone) {
          clearInterval(timer);
        }
      } catch (e) {
        if (!isCancelled && !data) {
          setError(e instanceof Error ? e.message : "Load failed");
        }
      }
    };

    poll();
    timer = setInterval(poll, 3000);
    return () => {
      isCancelled = true;
      clearInterval(timer);
    };
  }, [load, data]);

  if (error) return <div className="card">{error}</div>;
  if (!data) return <div className="card">Loading device {deviceId}…</div>;

  const device = data.device || {};
  const source = device.detection_source || "unknown";
  const visionBadge = source === "vision" || source === "hybrid";
  const plan = typeof device.disassembly_plan === "string"
    ? JSON.parse(device.disassembly_plan)
    : device.disassembly_plan;
  const impact = typeof device.impact_summary === "string"
    ? JSON.parse(device.impact_summary)
    : device.impact_summary;
  const audit = typeof device.completeness_audit === "string"
    ? JSON.parse(device.completeness_audit)
    : device.completeness_audit;

  const jobColor =
    jobStatus === "SUCCEEDED"
      ? "var(--accent)"
      : ["FAILED", "TIMED_OUT", "ABORTED"].includes(jobStatus)
      ? "var(--danger)"
      : "#f59e0b";

  return (
    <>
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>Device {deviceId?.slice(0, 8)}…</h2>
          <span className={visionBadge ? "pill pill-vision" : "pill pill-catalog"}>
            {visionBadge ? "SageMaker vision" : source === "mock" ? "Mock" : "Catalog-assisted"}
          </span>
        </div>
        <p className="mono">
          Status: {device.status} · Step Functions:{" "}
          <strong style={{ color: jobColor }}>{jobStatus}</strong>
        </p>
        {device.ocr_confirmed && (
          <p style={{ marginTop: "0.5rem", fontSize: "0.9rem" }}>
            Plate OCR ({device.ocr_engine || "tesseract"}) confirmed model{" "}
            <code className="mono">{device.device_model_key}</code>
            {Array.isArray(device.ocr_matched_hints) && device.ocr_matched_hints.length > 0
              ? ` · hints: ${device.ocr_matched_hints.join(", ")}`
              : ""}
            {device.ocr_influenced ? " · model key updated from plate" : ""}
          </p>
        )}
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>Detection</h3>
          <DetectionOverlay components={data.components || []} />
          {audit && (
            <div className={`audit-card ${audit.gaps?.length ? "audit-card-warn" : "audit-card-ok"}`}>
              <div className="audit-header">
                <div>
                  <strong>BOM Completeness:</strong>{" "}
                  <span style={{ fontWeight: 700, color: audit.score >= 0.8 ? "var(--accent)" : "var(--warn)" }}>
                    {Math.round(audit.score * 100)}%
                  </span>
                  {audit.total_expected !== undefined && (
                    <span style={{ color: "var(--muted)", marginLeft: "0.4rem", fontSize: "0.78rem" }}>
                      ({audit.total_detected}/{audit.total_expected} parts)
                    </span>
                  )}
                </div>
                <span className={`pill ${audit.gaps?.length ? "pill-catalog" : "pill-vision"}`} style={{ fontSize: "0.7rem" }}>
                  {audit.gaps?.length ? `${audit.gaps.length} Gap(s) Flagged` : "Within BOM Tolerance"}
                </span>
              </div>

              {audit.gaps?.length > 0 && (
                <div className="audit-gaps-list">
                  {audit.gaps.map((g: any, gIdx: number) => {
                    const sevClass =
                      g.severity === "critical"
                        ? "severity-critical"
                        : g.severity === "high"
                        ? "severity-high"
                        : "severity-medium";
                    return (
                      <div key={gIdx} className="gap-item">
                        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                          <span className={`pill ${sevClass}`} style={{ fontSize: "0.65rem", padding: "0.1rem 0.35rem" }}>
                            {g.severity || "gap"}
                          </span>
                          <strong>{g.comp_type}</strong>
                          <span style={{ color: "var(--muted)" }}>
                            {g.detected}/{g.expected} detected ({g.missing} missing)
                          </span>
                        </div>
                        {g.deficit_pct !== undefined && (
                          <span style={{ fontSize: "0.75rem", color: "var(--warn)", fontWeight: 600 }}>
                            -{g.deficit_pct}%
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
        <div className="card">
          <h3>Disassembly plan (RVS)</h3>
          <PlanTimeline plan={plan} />
        </div>
      </div>

      {impact && (
        <div className="card">
          <h3>Environmental impact</h3>
          <ImpactPanel impact={impact} />
        </div>
      )}

      <div className="card">
        <h3>Second-Life Passports</h3>
        {(data.passports || []).length === 0 && <p style={{ color: "var(--muted)" }}>Pending pipeline completion…</p>}
        {(data.passports || []).map((p: { passport_id: string }) => (
          <PassportCard key={p.passport_id} passportId={p.passport_id} />
        ))}
      </div>
    </>
  );
}
