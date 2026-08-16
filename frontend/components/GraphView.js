"use client";

import { useMemo } from "react";
import ReactFlow, { Background, Controls } from "reactflow";
import "reactflow/dist/style.css";

export default function GraphView({ nodes, edges }) {
  const { flowNodes, flowEdges } = useMemo(() => {
    const personNodes = nodes.filter((n) => n.type === "Person");
    const techNodes = nodes.filter((n) => n.type === "Technology");

    const flowNodes = [
      ...personNodes.map((n, i) => ({
        id: n.id,
        data: { label: n.label },
        position: { x: 50, y: i * 100 + 20 },
        style: { background: "#DBEAFE", border: "1px solid #3B82F6", borderRadius: 8, padding: 8 },
      })),
      ...techNodes.map((n, i) => ({
        id: n.id,
        data: { label: n.label },
        position: { x: 400, y: i * 100 + 20 },
        style: { background: "#FEF3C7", border: "1px solid #F59E0B", borderRadius: 8, padding: 8 },
      })),
    ];

    const flowEdges = edges.map((e, i) => ({
      id: `e${i}-${e.source}-${e.target}`,
      source: e.source,
      target: e.target,
      label: e.label.replace(/_/g, " ").toLowerCase(),
      style: { stroke: "#94A3B8" },
      labelStyle: { fontSize: 10, fill: "#64748B" },
    }));

    return { flowNodes, flowEdges };
  }, [nodes, edges]);

  if (!nodes || nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        Ask a question to see the graph
      </div>
    );
  }

  return (
    <div style={{ height: "500px" }} className="bg-white rounded-lg shadow border border-gray-200">
      <ReactFlow nodes={flowNodes} edges={flowEdges} fitView>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}