import { useState } from "react";

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

  return (
    <div className="app-shell">
      <main className="content-grid single">
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
        </section>
      </main>
    </div>
  );
}
