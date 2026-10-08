type Comp = {
  comp_type?: string;
  bbox?: number[] | string;
  detection_confidence?: string | number;
};

export function DetectionOverlay({ components }: { components: Comp[] }) {
  if (!components?.length) {
    return (
      <div className="overlay-wrap">
        <div className="overlay-placeholder">No components yet</div>
      </div>
    );
  }

  return (
    <div className="overlay-wrap">
      <div className="overlay-placeholder">Component layout (normalized bbox)</div>
      {components.map((c, i) => {
        let bbox = c.bbox;
        if (typeof bbox === "string") {
          try {
            bbox = JSON.parse(bbox);
          } catch {
            bbox = [];
          }
        }
        if (!Array.isArray(bbox) || bbox.length < 4) return null;
        const [x, y, w, h] = bbox;
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
          >
            {c.comp_type}
          </div>
        );
      })}
    </div>
  );
}
