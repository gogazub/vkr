import { useMemo, useState } from "react";

const sampleCases = [
  {
    id: "IMG-9f2a",
    status: "Reviewed",
    cells: 214,
    agreement: 0.92,
    updated: "2h ago"
  },
  {
    id: "IMG-81bc",
    status: "Pending",
    cells: 187,
    agreement: 0.0,
    updated: "Yesterday"
  },
  {
    id: "IMG-5c10",
    status: "Reviewed",
    cells: 199,
    agreement: 0.88,
    updated: "Jan 25"
  }
];

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
  const [selectedCase, setSelectedCase] = useState(sampleCases[0]);

  const agreementLabel = useMemo(() => {
    if (!selectedCase.agreement) return "--";
    return `${Math.round(selectedCase.agreement * 100)}%`;
  }, [selectedCase]);

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Validation Studio</p>
          <h1>
            Compare expert annotations with model inference in one visual canvas.
          </h1>
          <p className="subhead">
            Track agreement, highlight mismatches, and prepare reports for clinical
            review.
          </p>
        </div>
        <div className="hero-card">
          <div className="pill">MVP status</div>
          <div className="hero-stat">
            <span className="hero-stat__label">Images in queue</span>
            <span className="hero-stat__value">128</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat__label">Avg. agreement</span>
            <span className="hero-stat__value">91.4%</span>
          </div>
          <button className="primary-btn">Open latest case</button>
        </div>
      </header>

      <main className="content-grid">
        <section className="panel cases">
          <div className="panel-header">
            <h2>Case dashboard</h2>
            <span className="tag">DEV | Local FS</span>
          </div>
          <div className="case-list">
            {sampleCases.map((item) => (
              <button
                key={item.id}
                className={`case-row ${
                  selectedCase.id === item.id ? "is-active" : ""
                }`}
                onClick={() => setSelectedCase(item)}
                type="button"
              >
                <div>
                  <p className="case-id">{item.id}</p>
                  <p className="case-meta">
                    {item.cells} cells · {item.updated}
                  </p>
                </div>
                <div className={`status ${item.status.toLowerCase()}`}>
                  {item.status}
                </div>
              </button>
            ))}
          </div>
          <div className="metrics-grid">
            <div>
              <p className="metric-label">Agreement</p>
              <p className="metric-value">{agreementLabel}</p>
            </div>
            <div>
              <p className="metric-label">IoU threshold</p>
              <p className="metric-value">0.50</p>
            </div>
            <div>
              <p className="metric-label">False positives</p>
              <p className="metric-value">6</p>
            </div>
            <div>
              <p className="metric-label">False negatives</p>
              <p className="metric-value">8</p>
            </div>
          </div>
        </section>

        <section className="panel viewer">
          <div className="panel-header">
            <h2>Interactive viewer</h2>
            <div className="toggles">
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
              <div className="stage-glow" />
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
          <div className="viewer-footer">
            <div>
              <p className="metric-label">Active case</p>
              <p className="metric-value">{selectedCase.id}</p>
            </div>
            <div>
              <p className="metric-label">Status</p>
              <p className="metric-value">{selectedCase.status}</p>
            </div>
            <button className="ghost-btn">Generate report</button>
          </div>
        </section>

        <section className="panel activity">
          <div className="panel-header">
            <h2>Pipeline activity</h2>
            <span className="tag">Inference + Comparison</span>
          </div>
          <div className="activity-list">
            <div className="activity-row">
              <span className="dot ok" />
              <div>
                <p className="activity-title">Model inference finished</p>
                <p className="activity-meta">IMG-9f2a · 18s runtime</p>
              </div>
            </div>
            <div className="activity-row">
              <span className="dot warn" />
              <div>
                <p className="activity-title">IoU below threshold</p>
                <p className="activity-meta">6 mismatched cells detected</p>
              </div>
            </div>
            <div className="activity-row">
              <span className="dot" />
              <div>
                <p className="activity-title">Awaiting expert review</p>
                <p className="activity-meta">IMG-81bc assigned</p>
              </div>
            </div>
          </div>
          <div className="panel-footer">
            <button className="secondary-btn">Sync new images</button>
            <button className="secondary-btn">Open metrics</button>
          </div>
        </section>
      </main>
    </div>
  );
}
