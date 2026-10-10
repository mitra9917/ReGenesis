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
            <p style={{ marginTop: "0.75rem", fontSize: "0.9rem" }}>
              Completeness score: <strong>{audit.score}</strong>
              {audit.gaps?.length ? ` · ${audit.gaps.length} gap(s) flagged` : " · within tolerance"}
            </p>
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
