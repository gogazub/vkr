import { useCallback, useEffect, useMemo, useRef, useState } from "react";

export default function App() {
  const [showModel, setShowModel] = useState(true);
  const [showExpert, setShowExpert] = useState(true);
  const [apiInfo, setApiInfo] = useState({ state: "loading" });
  const [viewerData, setViewerData] = useState({
    state: "loading",
    imageId: "sample-001",
    imageUrl: "",
    boxes: [],
    message: ""
  });
  const controllerRef = useRef(null);
  const baseUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

  const checkHealth = useCallback(async () => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    setApiInfo((prev) => (prev.state === "ok" ? prev : { state: "loading" }));

    try {
      const response = await fetch(`${baseUrl}/health`, { signal: controller.signal });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setApiInfo({
        state: "ok",
        status: data.status ?? "ok",
        service: data.service,
        version: data.version
      });
    } catch (error) {
      if (error?.name === "AbortError") return;
      setApiInfo({ state: "error", message: error?.message ?? "Network error" });
    }
  }, [baseUrl]);

  useEffect(() => {
    checkHealth();
    const intervalId = setInterval(checkHealth, 10000);

    return () => {
      controllerRef.current?.abort();
      clearInterval(intervalId);
    };
  }, [checkHealth]);

  const loadViewer = useCallback(async () => {
    setViewerData((prev) => ({ ...prev, state: "loading", message: "" }));
    try {
      const response = await fetch(
        `${baseUrl}/api/v1/viewer/${viewerData.imageId}`
      );
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setViewerData({
        state: "ok",
        imageId: data.image_id,
        imageUrl: data.image_url,
        boxes: Array.isArray(data.boxes) ? data.boxes : [],
        message: ""
      });
    } catch (error) {
      setViewerData((prev) => ({
        ...prev,
        state: "error",
        imageUrl: "",
        boxes: [],
        message: error?.message ?? "Network error"
      }));
    }
  }, [baseUrl, viewerData.imageId]);

  useEffect(() => {
    loadViewer();
  }, [loadViewer]);

  const resolvedImageUrl = useMemo(() => {
    if (!viewerData.imageUrl) return "";
    if (viewerData.imageUrl.startsWith("http")) return viewerData.imageUrl;
    return `${baseUrl}${viewerData.imageUrl}`;
  }, [baseUrl, viewerData.imageUrl]);

  const expertBoxes = useMemo(
    () =>
      viewerData.boxes.map((box, index) => {
        const width = Number(box.width) * 100;
        const height = Number(box.height) * 100;
        const top = Number(box.y_center) * 100 - height / 2;
        const left = Number(box.x_center) * 100 - width / 2;
        return {
          id: `${box.class_id}-${index}`,
          top,
          left,
          width,
          height
        };
      }),
    [viewerData.boxes]
  );

  const modelBoxes = [];

  return (
    <div className="app-shell">
      <main className="content-grid">
        <section className="panel viewer">
          <div className="panel-header">
            <h2>Interactive viewer</h2>
            <div className="toggles">
              <span
                className="api-status"
                data-state={apiInfo.state}
                title={
                  apiInfo.state === "ok"
                    ? `${apiInfo.service ?? "API"} ${apiInfo.version ?? ""}`.trim()
                    : apiInfo.state === "error"
                      ? apiInfo.message
                      : "Connecting to API"
                }
              >
                API:{" "}
                {apiInfo.state === "loading"
                  ? "connecting..."
                  : apiInfo.state === "error"
                    ? "offline"
                    : apiInfo.status}
              </span>
              <button className="api-refresh" type="button" onClick={checkHealth}>
                Refresh
              </button>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={showExpert}
                  onChange={() => setShowExpert((prev) => !prev)}
                />
                Expert layer
              </label>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={showModel}
                  onChange={() => setShowModel((prev) => !prev)}
                />
                Model layer
              </label>
            </div>
          </div>
          <div className="viewer-stage">
            <div className="stage-image">
              {viewerData.state === "ok" && resolvedImageUrl ? (
                <img
                  className="stage-img"
                  src={resolvedImageUrl}
                  alt={`Image ${viewerData.imageId}`}
                />
              ) : (
                <div className="stage-placeholder">
                  {viewerData.state === "loading"
                    ? "Loading image..."
                    : `Image unavailable: ${viewerData.message}`}
                </div>
              )}
              <div className="stage-label">{viewerData.imageId}</div>
            </div>
            {showModel && (
              <div className="overlay model">
                {modelBoxes.map((box) => (
                  <span
                    key={box.id}
                    className="bbox"
                    style={{
                      top: `${box.top}%`,
                      left: `${box.left}%`,
                      width: `${box.width}%`,
                      height: `${box.height}%`
                    }}
                  />
                ))}
              </div>
            )}
            {showExpert && (
              <div className="overlay expert">
                {expertBoxes.map((box) => (
                  <span
                    key={box.id}
                    className="bbox"
                    style={{
                      top: `${box.top}%`,
                      left: `${box.left}%`,
                      width: `${box.width}%`,
                      height: `${box.height}%`
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
