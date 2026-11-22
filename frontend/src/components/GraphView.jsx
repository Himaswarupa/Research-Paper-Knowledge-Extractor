import { useEffect, useRef } from "react";
import { DataSet, Network } from "vis-network/standalone";

export const TYPE_COLORS = {
  Paper: "#ef4444",
  Model: "#3b82f6",
  Method: "#22c55e",
  Algorithm: "#14b8a6",
  Dataset: "#f59e0b",
  Metric: "#a855f7",
  Objective: "#f97316",
  Finding: "#94a3b8",
};

export default function GraphView({ graph, onSelect }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!graph || !containerRef.current) return;

    const nodes = new DataSet(
      graph.nodes.map((n) => ({
        id: n.id,
        label: n.label,
        title: `${n.label} (${n.type})`,
        size: 12 + Math.min(n.degree, 25) * 1.5,
        color: {
          background: TYPE_COLORS[n.type] || "#64748b",
          border: "#0f172a",
        },
      }))
    );

    const edges = new DataSet(
      graph.edges.map((e, i) => ({
        id: i,
        from: e.source,
        to: e.target,
        title: e.relation,
        arrows: "to",
        color: { color: "#475569", highlight: "#e2e8f0" },
      }))
    );

    const network = new Network(
      containerRef.current,
      { nodes, edges },
      {
        nodes: { shape: "dot", font: { color: "#e2e8f0", size: 14 } },
        edges: { smooth: { type: "continuous" }, width: 1.2 },
        physics: {
          barnesHut: { gravitationalConstant: -8000, springLength: 180 },
          stabilization: { iterations: 150 },
        },
        interaction: { hover: true, tooltipDelay: 150 },
      }
    );

    network.on("click", (params) => {
      if (onSelect) onSelect(params.nodes.length ? params.nodes[0] : null);
    });

    return () => network.destroy();
  }, [graph, onSelect]);

  return (
    <div>
      <div
        ref={containerRef}
        style={{
          height: 650,
          background: "#0b1220",
          border: "1px solid #1e293b",
          borderRadius: 12,
        }}
      />
      <div style={{ display: "flex", flexWrap: "wrap", gap: 14, marginTop: 10 }}>
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <span key={type} style={{ fontSize: 13, color: "#cbd5e1" }}>
            <span
              style={{
                display: "inline-block",
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: color,
                marginRight: 6,
              }}
            />
            {type}
          </span>
        ))}
      </div>
    </div>
  );
}