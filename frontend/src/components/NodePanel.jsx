import { useEffect, useState } from "react";
import { queryNode } from "../api";
import { TYPE_COLORS } from "./GraphView";

function Relations({ title, items, arrow, onPick }) {
  if (!items.length) return null;
  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ color: "#94a3b8", fontSize: 13, marginBottom: 6 }}>
        {title} ({items.length})
      </div>
      {items.map((r, i) => (
        <div
          key={i}
          onClick={() => onPick(r.id)}
          style={{
            padding: "6px 8px",
            borderRadius: 6,
            cursor: "pointer",
            fontSize: 14,
            background: "#0f172a",
            marginBottom: 4,
          }}
        >
          <span style={{ color: "#818cf8", fontSize: 12 }}>
            {arrow} {r.relation}
          </span>
          <div>{r.label}</div>
        </div>
      ))}
    </div>
  );
}

export default function NodePanel({ nodeId, onPick }) {
  const [info, setInfo] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!nodeId) {
      setInfo(null);
      return;
    }
    let cancelled = false;
    setError("");
    queryNode(nodeId)
      .then((res) => {
        if (cancelled) return;
        const exact = res.matches.find((m) => m.id === nodeId);
        setInfo(exact || res.matches[0]);
      })
      .catch((e) => {
        if (!cancelled) {
          setInfo(null);
          setError(e.message);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [nodeId]);

  const box = {
    background: "#1e293b",
    borderRadius: 12,
    padding: 16,
    height: 650,
    overflowY: "auto",
  };

  if (!nodeId) {
    return (
      <div style={box}>
        <p style={{ color: "#94a3b8" }}>Click a node in the graph to see its details here.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={box}>
        <p style={{ color: "#f87171" }}>{error}</p>
      </div>
    );
  }

  if (!info) {
    return (
      <div style={box}>
        <p style={{ color: "#94a3b8" }}>Loading...</p>
      </div>
    );
  }

  return (
    <div style={box}>
      <h2 style={{ margin: 0, fontSize: 20 }}>{info.label}</h2>
      <span
        style={{
          display: "inline-block",
          marginTop: 8,
          padding: "2px 10px",
          borderRadius: 999,
          fontSize: 12,
          background: TYPE_COLORS[info.type] || "#64748b",
          color: "white",
        }}
      >
        {info.type}
      </span>

      <Relations title="Outgoing" items={info.outgoing} arrow="→" onPick={onPick} />
      <Relations title="Incoming" items={info.incoming} arrow="←" onPick={onPick} />

      {!info.outgoing.length && !info.incoming.length && (
        <p style={{ color: "#94a3b8", marginTop: 16 }}>No relations found for this node.</p>
      )}
    </div>
  );
}