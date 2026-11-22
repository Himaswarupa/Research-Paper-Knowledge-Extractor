import { useCallback, useEffect, useState } from "react";
import { getConfig, getGraphData, getHealth } from "./api";
import GraphView from "./components/GraphView";
import NodePanel from "./components/NodePanel";
import UploadPanel from "./components/UploadPanel";
import "./App.css";

export default function App() {
  const [backend, setBackend] = useState("connecting...");
  const [uploadEnabled, setUploadEnabled] = useState(null);
  const [graphVersion, setGraphVersion] = useState(0);
  const [graph, setGraph] = useState(null);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    getHealth()
      .then(() => setBackend("connected"))
      .catch(() => setBackend("not reachable"));
  }, []);

  useEffect(() => {
    getConfig()
      .then((c) => {
        setUploadEnabled(c.upload_enabled);
        if (!c.upload_enabled) setGraphVersion(1);
      })
      .catch(() => setUploadEnabled(true));
  }, []);

  useEffect(() => {
    if (graphVersion === 0) return;
    getGraphData()
      .then((g) => {
        setGraph(g);
        setSelected(null);
      })
      .catch(() => setGraph(null));
  }, [graphVersion]);

  const handleDone = useCallback(() => setGraphVersion((v) => v + 1), []);
  const handleSelect = useCallback((id) => setSelected(id), []);

  return (
    <div style={{ padding: 24, maxWidth: 1400, margin: "0 auto" }}>
      <h1>Research Paper Knowledge Extractor</h1>
      <p>
        Backend: {backend}
        {backend === "connecting..." && (
          <span style={{ color: "#94a3b8" }}>
            {" "}
            (a free server can take up to a minute to wake up)
          </span>
        )}
      </p>

      {uploadEnabled === true && <UploadPanel onDone={handleDone} />}
      {uploadEnabled === false && (
        <div style={{ background: "#1e293b", padding: 16, borderRadius: 12 }}>
          Demo mode: showing a pre-processed paper. Uploads are disabled on this deployment.
        </div>
      )}

      {graph && (
        <div style={{ marginTop: 20 }}>
          <p style={{ margin: "0 0 10px" }}>
            {graph.nodes.length} nodes, {graph.edges.length} edges
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 320px",
              gap: 16,
              alignItems: "start",
            }}
          >
            <GraphView graph={graph} onSelect={handleSelect} />
            <NodePanel nodeId={selected} onPick={handleSelect} />
          </div>
        </div>
      )}
    </div>
  );
}