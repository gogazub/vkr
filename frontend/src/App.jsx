import { useCallback, useEffect, useRef, useState } from "react";

const modelBoxes = [
  { id: "m1", top: 16, left: 12, width: 22, height: 16 },
  { id: "m2", top: 38, left: 48, width: 18, height: 14 },
  { id: "m3", top: 62, left: 30, width: 14, height: 10 }
];

const expertBoxes = [
  { id: "e1", top: 18, left: 14, width: 20, height: 14 },
  { id: "e2", top: 40, left: 50, width: 16, height: 12 },
  { id: "e3", top: 64, left: 32, width: 12, height: 9 }
];

export default function App() {
  const [showModel, setShowModel] = useState(true);
  const [showExpert, setShowExpert] = useState(true);
  const [apiInfo, setApiInfo] = useState({ state: "loading" });
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
              <div className="stage-label">Bone marrow smear · 1024×1024</div>
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
