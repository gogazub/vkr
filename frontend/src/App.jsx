import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const toOverlayBoxes = (boxes, prefix) =>
  boxes.map((box, index) => {
    const width = Number(box.width) * 100;
    const height = Number(box.height) * 100;
    const top = Number(box.y_center) * 100 - height / 2;
    const left = Number(box.x_center) * 100 - width / 2;
    return {
      id: `${prefix}-${box.class_id}-${index}`,
      top,
      left,
      width,
      height
    };
  });

export default function App() {
  const [showModel, setShowModel] = useState(true);
  const [showExpert, setShowExpert] = useState(true);
  const [apiInfo, setApiInfo] = useState({ state: "loading" });
  const [imageIdInput, setImageIdInput] = useState("sample-001");
  const [activeImageId, setActiveImageId] = useState("sample-001");
  const [viewerData, setViewerData] = useState({
    state: "loading",
    imageId: "",
    imageUrl: "",
    expertBoxes: [],
    modelBoxes: [],
    stats: null,
    message: ""
  });
  const [imageLoadError, setImageLoadError] = useState(false);
  const [datasetInfo, setDatasetInfo] = useState({
    state: "loading",
    imageCount: 0,
    processedCount: 0,
    stats: null,
    message: ""
  });
  const [imageList, setImageList] = useState({
    state: "loading",
    items: [],
    message: ""
  });
  const [hoveredImageId, setHoveredImageId] = useState("");
  const [imageRect, setImageRect] = useState({
    width: 0,
    height: 0,
    offsetX: 0,
    offsetY: 0
  });
  const controllerRef = useRef(null);
  const stageRef = useRef(null);
  const imageRef = useRef(null);
  const baseUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
  const resolveImageUrl = useCallback(
    (imageUrl) => {
      if (!imageUrl) return "";
      if (imageUrl.startsWith("http")) return imageUrl;
      return `${baseUrl}${imageUrl}`;
    },
    [baseUrl]
  );

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

  const loadDatasetStats = useCallback(async () => {
    setDatasetInfo((prev) => (prev.state === "ok" ? prev : { ...prev, state: "loading" }));
    try {
      const response = await fetch(`${baseUrl}/api/v1/analysis/dataset`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setDatasetInfo({
        state: "ok",
        imageCount: data.image_count ?? 0,
        processedCount: data.processed_count ?? 0,
        stats: data.stats ?? null,
        message: ""
      });
    } catch (error) {
      setDatasetInfo({
        state: "error",
        imageCount: 0,
        processedCount: 0,
        stats: null,
        message: error?.message ?? "Network error"
      });
    }
  }, [baseUrl]);

  const loadImageList = useCallback(async () => {
    setImageList((prev) => (prev.state === "ok" ? prev : { ...prev, state: "loading" }));
    try {
      const response = await fetch(`${baseUrl}/api/v1/images`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setImageList({
        state: "ok",
        items: Array.isArray(data.items) ? data.items : [],
        message: ""
      });
    } catch (error) {
      setImageList({
        state: "error",
        items: [],
        message: error?.message ?? "Network error"
      });
    }
  }, [baseUrl]);

  useEffect(() => {
    loadDatasetStats();
    loadImageList();
  }, [loadDatasetStats, loadImageList]);

  const loadViewer = useCallback(
    async (imageId) => {
      const trimmedId = imageId.trim();
      if (!trimmedId) {
        setViewerData((prev) => ({
          ...prev,
          state: "error",
          imageId: "",
          imageUrl: "",
          expertBoxes: [],
          modelBoxes: [],
          stats: null,
          message: "Image id is required"
        }));
        return;
      }
      setViewerData((prev) => ({ ...prev, state: "loading", message: "" }));
      try {
        const response = await fetch(
          `${baseUrl}/api/v1/analysis/${encodeURIComponent(trimmedId)}`
        );
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        setViewerData({
          state: "ok",
          imageId: data.image_id,
          imageUrl: data.image_url,
          expertBoxes: Array.isArray(data.expert_boxes) ? data.expert_boxes : [],
          modelBoxes: Array.isArray(data.model_boxes) ? data.model_boxes : [],
          stats: data.stats ?? null,
          message: ""
        });
      } catch (error) {
        setViewerData((prev) => ({
          ...prev,
          state: "error",
          imageId: trimmedId,
          imageUrl: "",
          expertBoxes: [],
          modelBoxes: [],
          stats: null,
          message: error?.message ?? "Network error"
        }));
      }
    },
    [baseUrl]
  );

  useEffect(() => {
    loadViewer(activeImageId);
  }, [loadViewer, activeImageId]);

  const displayedImageId = viewerData.imageId || activeImageId;
  const fallbackImageUrl = useMemo(() => {
    if (!displayedImageId) return "";
    return `${baseUrl}/api/v1/images/${encodeURIComponent(displayedImageId)}/file`;
  }, [baseUrl, displayedImageId]);
  const resolvedImageUrl = useMemo(() => {
    if (viewerData.imageUrl) {
      return resolveImageUrl(viewerData.imageUrl);
    }
    return fallbackImageUrl;
  }, [resolveImageUrl, viewerData.imageUrl, fallbackImageUrl]);

  const expertBoxes = useMemo(
    () => toOverlayBoxes(viewerData.expertBoxes, "expert"),
    [viewerData.expertBoxes]
  );

  const modelBoxes = useMemo(
    () => toOverlayBoxes(viewerData.modelBoxes, "model"),
    [viewerData.modelBoxes]
  );

  const updateImageRect = useCallback(() => {
    const container = stageRef.current;
    const img = imageRef.current;
    if (!container || !img || !img.naturalWidth || !img.naturalHeight) {
      return;
    }

    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;
    if (!containerWidth || !containerHeight) {
      return;
    }

    const imageRatio = img.naturalWidth / img.naturalHeight;
    const containerRatio = containerWidth / containerHeight;

    let width;
    let height;
    let offsetX;
    let offsetY;

    if (imageRatio > containerRatio) {
      width = containerWidth;
      height = containerWidth / imageRatio;
      offsetX = 0;
      offsetY = (containerHeight - height) / 2;
    } else {
      height = containerHeight;
      width = containerHeight * imageRatio;
      offsetY = 0;
      offsetX = (containerWidth - width) / 2;
    }

    setImageRect({ width, height, offsetX, offsetY });
  }, []);

  useEffect(() => {
    updateImageRect();
    window.addEventListener("resize", updateImageRect);
    return () => window.removeEventListener("resize", updateImageRect);
  }, [updateImageRect, resolvedImageUrl]);

  useEffect(() => {
    setImageLoadError(false);
  }, [resolvedImageUrl]);

  const overlayStyle = useMemo(() => {
    if (!imageRect.width || !imageRect.height) return null;
    return {
      top: `${imageRect.offsetY}px`,
      left: `${imageRect.offsetX}px`,
      width: `${imageRect.width}px`,
      height: `${imageRect.height}px`
    };
  }, [imageRect]);

  const expertCount = viewerData.stats?.expert_count ?? "—";
  const modelCount = viewerData.stats?.model_count ?? "—";
  const tpCount = viewerData.stats?.tp ?? "—";
  const fpCount = viewerData.stats?.fp ?? "—";
  const fnCount = viewerData.stats?.fn ?? "—";
  const precision = viewerData.stats?.precision;
  const recall = viewerData.stats?.recall;
  const f1 = viewerData.stats?.f1;
  const datasetStats = datasetInfo.stats;
  const datasetPrecision = datasetStats?.precision;
  const datasetRecall = datasetStats?.recall;
  const datasetF1 = datasetStats?.f1;
  const datasetExpertCount = datasetStats?.expert_count ?? "—";
  const datasetModelCount = datasetStats?.model_count ?? "—";
  const datasetTpCount = datasetStats?.tp ?? "—";
  const datasetFpCount = datasetStats?.fp ?? "—";
  const datasetFnCount = datasetStats?.fn ?? "—";

  const handleSelectImage = useCallback((imageId) => {
    setActiveImageId(imageId);
    setImageIdInput(imageId);
  }, []);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">MC</div>
          <div className="brand-text">
            <span className="brand-title">MediCore</span>
            <span className="brand-subtitle">Analytics Console</span>
          </div>
        </div>
        <nav className="nav">
          <button className="nav-item is-active" type="button">
            Dashboard
          </button>
          <button className="nav-item" type="button">
            Image Review
          </button>
          <button className="nav-item" type="button">
            Quality Metrics
          </button>
          <button className="nav-item" type="button">
            Audit Logs
          </button>
          <button className="nav-item" type="button">
            Settings
          </button>
        </nav>
        <div className="sidebar-section">
          <span className="section-label">System status</span>
          <div className="status-card">
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
                ? "connecting"
                : apiInfo.state === "error"
                  ? "offline"
                  : apiInfo.status}
            </span>
            <button className="api-refresh" type="button" onClick={checkHealth}>
              Refresh
            </button>
          </div>
          <div className="sidebar-metrics">
            <div className="metric">
              <span className="metric-label">Dataset images</span>
              <span className="metric-value">
                {datasetInfo.state === "ok" ? datasetInfo.imageCount : "—"}
              </span>
            </div>
            <div className="metric">
              <span className="metric-label">Processed</span>
              <span className="metric-value">
                {datasetInfo.state === "ok" ? datasetInfo.processedCount : "—"}
              </span>
            </div>
          </div>
          {datasetInfo.state === "error" && (
            <div className="sidebar-alert">{datasetInfo.message}</div>
          )}
        </div>
      </aside>

      <div className="app-main">
        <header className="topbar">
          <div className="topbar-title">
            <span className="topbar-kicker">Clinical Imaging Analytics</span>
            <h1>Model Quality Dashboard</h1>
          </div>
          <div className="topbar-actions">
            <div className="topbar-card">
              <span className="topbar-label">Viewer image</span>
              <span className="topbar-value">{displayedImageId || "—"}</span>
            </div>
            <div className="topbar-card">
              <span className="topbar-label">Dataset F1</span>
              <span className="topbar-value">
                {datasetF1 === undefined ? "—" : datasetF1.toFixed(2)}
              </span>
            </div>
          </div>
        </header>

        <main className="workspace">
          <section className="panel viewer">
            <div className="panel-header">
              <div>
                <h2>Image review</h2>
                <p className="panel-subtitle">
                  Overlay expert annotations with model detections for a selected study.
                </p>
              </div>
              <div className="panel-actions">
                <form
                  className="viewer-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    setActiveImageId(imageIdInput.trim());
                  }}
                >
                  <input
                    className="viewer-input"
                    type="text"
                    value={imageIdInput}
                    onChange={(event) => setImageIdInput(event.target.value)}
                    placeholder="Enter image id"
                    aria-label="Image id"
                  />
                  <button className="viewer-submit" type="submit">
                    Load
                  </button>
                </form>
                <div className="toggle-group">
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
            </div>

            <div className="viewer-stage">
              <div className="stage-image" ref={stageRef}>
                {resolvedImageUrl && !imageLoadError ? (
                  <img
                    className="stage-img"
                    src={resolvedImageUrl}
                    alt={`Image ${displayedImageId}`}
                    ref={imageRef}
                    onLoad={updateImageRect}
                    onError={() => setImageLoadError(true)}
                  />
                ) : (
                  <div className="stage-placeholder">
                    {viewerData.state === "loading"
                      ? "Loading image..."
                      : `Image unavailable: ${viewerData.message || "Not found"}`}
                  </div>
                )}
                <div className="stage-label">{displayedImageId}</div>
                {overlayStyle && showModel && !imageLoadError && (
                  <div className="overlay model" style={overlayStyle}>
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
                {overlayStyle && showExpert && !imageLoadError && (
                  <div className="overlay expert" style={overlayStyle}>
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
            </div>

            <div className="stats-bar">
              <div className="stat-item">
                <span className="stat-label">Expert boxes</span>
                <span className="stat-value">{expertCount}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Model boxes</span>
                <span className="stat-value">{modelCount}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">TP</span>
                <span className="stat-value">{tpCount}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">FP</span>
                <span className="stat-value">{fpCount}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">FN</span>
                <span className="stat-value">{fnCount}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Precision</span>
                <span className="stat-value">
                  {precision === undefined ? "—" : precision.toFixed(2)}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Recall</span>
                <span className="stat-value">
                  {recall === undefined ? "—" : recall.toFixed(2)}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">F1</span>
                <span className="stat-value">{f1 === undefined ? "—" : f1.toFixed(2)}</span>
              </div>
            </div>
          </section>

          <section className="panel dataset">
            <div className="panel-header">
              <div>
                <h2>Dataset performance</h2>
                <p className="panel-subtitle">Aggregate results across the dataset.</p>
              </div>
              <div className="dataset-meta">
                <span>Images: {datasetInfo.state === "ok" ? datasetInfo.imageCount : "—"}</span>
                <span>
                  Processed: {datasetInfo.state === "ok" ? datasetInfo.processedCount : "—"}
                </span>
              </div>
            </div>

            <div className="stats-bar dataset-stats">
              <div className="stat-item">
                <span className="stat-label">Expert boxes</span>
                <span className="stat-value">{datasetExpertCount}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Model boxes</span>
                <span className="stat-value">{datasetModelCount}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">TP</span>
                <span className="stat-value">{datasetTpCount}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">FP</span>
                <span className="stat-value">{datasetFpCount}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">FN</span>
                <span className="stat-value">{datasetFnCount}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Precision</span>
                <span className="stat-value">
                  {datasetPrecision === undefined ? "—" : datasetPrecision.toFixed(2)}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Recall</span>
                <span className="stat-value">
                  {datasetRecall === undefined ? "—" : datasetRecall.toFixed(2)}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">F1</span>
                <span className="stat-value">{datasetF1 === undefined ? "—" : datasetF1.toFixed(2)}</span>
              </div>
            </div>

            <div className="image-table-wrap">
              <table className="image-table">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Image id</th>
                    <th>Preview</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {imageList.state === "loading" && (
                    <tr>
                      <td colSpan={4} className="table-empty">
                        Loading images...
                      </td>
                    </tr>
                  )}
                  {imageList.state === "error" && (
                    <tr>
                      <td colSpan={4} className="table-empty">
                        {imageList.message}
                      </td>
                    </tr>
                  )}
                  {imageList.state === "ok" && imageList.items.length === 0 && (
                    <tr>
                      <td colSpan={4} className="table-empty">
                        No images found
                      </td>
                    </tr>
                  )}
                  {imageList.state === "ok" &&
                    imageList.items.map((item) => {
                      const isActive = item.id === displayedImageId;
                      const isHovered = hoveredImageId === item.id;
                      const statusState = isActive ? "active" : isHovered ? "watch" : "idle";
                      const statusLabel = isActive ? "Active" : isHovered ? "Preview" : "Idle";

                      return (
                        <tr
                          key={item.id}
                          className="image-row"
                          data-active={isActive}
                          tabIndex={0}
                          onClick={() => handleSelectImage(item.id)}
                          onKeyDown={(event) => {
                            if (event.key === "Enter" || event.key === " ") {
                              event.preventDefault();
                              handleSelectImage(item.id);
                            }
                          }}
                          onMouseEnter={() => setHoveredImageId(item.id)}
                          onMouseLeave={() =>
                            setHoveredImageId((prev) => (prev === item.id ? "" : prev))
                          }
                          onFocus={() => setHoveredImageId(item.id)}
                          onBlur={() =>
                            setHoveredImageId((prev) => (prev === item.id ? "" : prev))
                          }
                        >
                          <td className="cell-status" data-state={statusState}>
                            <span className="status-pill">{statusLabel}</span>
                          </td>
                          <td className="image-id">{item.id}</td>
                          <td className="image-preview-cell">
                            {hoveredImageId === item.id ? (
                              <img
                                className="image-preview"
                                src={resolveImageUrl(item.image_url)}
                                alt={`Preview ${item.id}`}
                                loading="lazy"
                              />
                            ) : (
                              <span className="preview-hint">Hover to preview</span>
                            )}
                          </td>
                          <td className="actions-cell">
                            <button className="icon-button" type="button" aria-label="Edit">
                              <svg viewBox="0 0 20 20" aria-hidden="true">
                                <path d="M4 13.8V16h2.2l6.6-6.6-2.2-2.2L4 13.8zm10.9-6.2c.3-.3.3-.8 0-1.1l-1.4-1.4c-.3-.3-.8-.3-1.1 0l-1.1 1.1 2.2 2.2 1.4-1.4z" />
                              </svg>
                            </button>
                            <button className="icon-button" type="button" aria-label="Delete">
                              <svg viewBox="0 0 20 20" aria-hidden="true">
                                <path d="M6 6h8l-.7 9.5c0 .8-.7 1.5-1.5 1.5H8.2c-.8 0-1.5-.7-1.5-1.5L6 6zm2.5-2h3L12 3h3v2H5V3h3l.5 1z" />
                              </svg>
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
