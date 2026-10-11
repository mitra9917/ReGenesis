type Comp = {
  comp_type?: string;
  class?: string;
  bbox?: number[] | string;
  detection_confidence?: string | number;
  confidence?: string | number;
  source?: string;
};

type Props = {
  components?: Comp[];
  detections?: Comp[];
  imageS3Key?: string;
  deviceModelKey?: string;
};

function parseBbox(bbox: Comp["bbox"]): number[] | null {
  if (typeof bbox === "string") {
    try {
      bbox = JSON.parse(bbox);
    } catch {
      return null;
    }
  }
  if (!Array.isArray(bbox) || bbox.length < 4) return null;
  return bbox.map(Number);
}

export function DetectionOverlay({ components, detections }: Props) {
  const items = (components?.length ? components : detections) || [];

  if (!items.length) {
    return (
      <div className="overlay-wrap">
        <div className="overlay-placeholder">No components yet</div>
      </div>
    );
  }

  return (
    <div className="overlay-wrap">
      <div className="overlay-placeholder">
        Normalized bbox layout ({items.length} detections)
      </div>
      {items.map((c, i) => {
        const bbox = parseBbox(c.bbox);
        if (!bbox) return null;
        const [x, y, w, h] = bbox;
        const label = c.comp_type || c.class || `part-${i + 1}`;
        const conf = c.detection_confidence ?? c.confidence;
        const title = conf != null ? `${label} ${Number(conf).toFixed(2)}` : label;
        return (
          <div
            key={i}
            className="bbox"
            style={{
              left: `${x * 100}%`,
              top: `${y * 100}%`,
              width: `${w * 100}%`,
              height: `${h * 100}%`,
            }}
            title={title}
          >
            {label}
          </div>
        );
      })}
    </div>
  );
}
