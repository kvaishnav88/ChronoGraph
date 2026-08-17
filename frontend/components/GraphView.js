"use client";

import { useMemo, useState, useEffect } from "react";
import ReactFlow, { Background, Controls } from "reactflow";
import "reactflow/dist/style.css";

export default function GraphView({ nodes, edges }) {
  const sortedTimestamps = useMemo(() => {
    const unique = [...new Set(edges.map((e) => e.timestamp))];
    return unique.sort();
  }, [edges]);

  const [cutoffIndex, setCutoffIndex] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    setCutoffIndex(sortedTimestamps.length - 1);
    setPlaying(false);
  }, [sortedTimestamps]);

  useEffect(() => {
    if (!playing) return;
    if (cutoffIndex >= sortedTimestamps.length - 1) {
      setPlaying(false);
      return;
    }
    const timer = setTimeout(() => setCutoffIndex((i) => i + 1), 900);
    return () => clearTimeout(timer);
  }, [playing, cutoffIndex, sortedTimestamps.length]);

  const cutoffDate = sortedTimestamps[cutoffIndex];

  const { flowNodes, flowEdges } = useMemo(() => {
    if (!cutoffDate) return { flowNodes: [], flowEdges: [] };

    const visibleEdges = edges.filter((e) => e.timestamp <= cutoffDate);
    const visibleNodeIds = new Set();
    visibleEdges.forEach((e) => {
      visibleNodeIds.add(e.source);
      visibleNodeIds.add(e.target);
    });

    const personNodes = nodes.filter((n) => n.type === "Person" && visibleNodeIds.has(n.id));
    const techNodes = nodes.filter((n) => n.type === "Technology" && visibleNodeIds.has(n.id));

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

    const flowEdges = visibleEdges.map((e, i) => ({
      id: `e${i}-${e.source}-${e.target}`,
      source: e.source,
      target: e.target,
      label: e.label.replace(/_/g, " ").toLowerCase(),
      style: { stroke: "#94A3B8" },
      labelStyle: { fontSize: 10, fill: "#64748B" },
    }));

    return { flowNodes, flowEdges };
  }, [nodes, edges, cutoffDate]);

  if (!nodes || nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        Ask a question to see the graph
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200">
      <div className="px-4 pt-3 pb-2 border-b border-gray-100">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-gray-600">
            As of: {cutoffDate} &middot; event {cutoffIndex + 1} of {sortedTimestamps.length}
          </span>
          <button
            onClick={() => {
              if (cutoffIndex >= sortedTimestamps.length - 1) setCutoffIndex(0);
              setPlaying((p) => !p);
            }}
            className="text-xs bg-blue-600 text-white rounded px-3 py-1"
          >
            {playing ? "Pause" : "▶ Play"}
          </button>
        </div>
        <input
          type="range"
          min={0}
          max={Math.max(sortedTimestamps.length - 1, 0)}
          value={cutoffIndex}
          onChange={(e) => {
            setPlaying(false);
            setCutoffIndex(Number(e.target.value));
          }}
          className="w-full"
        />
      </div>
      <div style={{ height: "440px" }}>
        <ReactFlow nodes={flowNodes} edges={flowEdges} fitView>
          <Background />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
}