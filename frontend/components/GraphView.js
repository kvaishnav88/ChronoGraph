"use client";

import { useMemo, useState, useEffect } from "react";
import ReactFlow, {
  Background,
  Controls,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";

export default function GraphView({ nodes = [], edges = [] }) {
  const sortedTimestamps = useMemo(() => {
    const unique = [...new Set(edges.map((e) => e.timestamp).filter(Boolean))];
    return unique.sort();
  }, [edges]);

  const [cutoffIndex, setCutoffIndex] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    setCutoffIndex(Math.max(sortedTimestamps.length - 1, 0));
    setPlaying(false);
  }, [sortedTimestamps]);

  useEffect(() => {
    if (!playing) return;

    if (cutoffIndex >= sortedTimestamps.length - 1) {
      setPlaying(false);
      return;
    }

    const timer = setTimeout(() => {
      setCutoffIndex((i) => i + 1);
    }, 900);

    return () => clearTimeout(timer);
  }, [playing, cutoffIndex, sortedTimestamps.length]);

  const cutoffDate = sortedTimestamps[cutoffIndex];

  const { flowNodes, flowEdges } = useMemo(() => {
    if (!cutoffDate) {
      return { flowNodes: [], flowEdges: [] };
    }

    const visibleEdges = edges.filter(
      (e) => e.timestamp && e.timestamp <= cutoffDate
    );

    const visibleNodeIds = new Set();

    visibleEdges.forEach((e) => {
      visibleNodeIds.add(e.source);
      visibleNodeIds.add(e.target);
    });

    const personNodes = nodes.filter(
      (n) =>
        n.type === "Person" &&
        visibleNodeIds.has(n.id)
    );

    const techNodes = nodes.filter(
      (n) =>
        n.type === "Technology" &&
        visibleNodeIds.has(n.id)
    );

    /*
     * Keep people on the left and technologies on the right.
     * The larger vertical spacing reduces overlapping connections.
     */
    const flowNodes = [
      ...personNodes.map((n, i) => ({
        id: n.id,
        data: { label: n.label },
        position: {
          x: 80,
          y: i * 150 + 35,
        },
        sourcePosition: Position.Right,
        targetPosition: Position.Right,
        style: {
          background: "#DBEAFE",
          border: "1.5px solid #3B82F6",
          borderRadius: 10,
          padding: "12px 18px",
          minWidth: 180,
          textAlign: "center",
          fontSize: 16,
          fontWeight: 500,
        },
      })),

      ...techNodes.map((n, i) => ({
        id: n.id,
        data: { label: n.label },
        position: {
          x: 620,
          y: i * 150 + 35,
        },
        sourcePosition: Position.Left,
        targetPosition: Position.Left,
        style: {
          background: "#FEF3C7",
          border: "1.5px solid #F59E0B",
          borderRadius: 10,
          padding: "12px 18px",
          minWidth: 180,
          textAlign: "center",
          fontSize: 16,
          fontWeight: 500,
        },
      })),
    ];

    /*
     * Give repeated relationships slightly different routing offsets.
     * This prevents multiple historical events between the same nodes
     * from appearing as one thick/overlapping line.
     */
    const pairCounts = new Map();

    const flowEdges = visibleEdges.map((e, i) => {
      const pairKey = `${e.source}-${e.target}`;
      const pairIndex = pairCounts.get(pairKey) || 0;

      pairCounts.set(pairKey, pairIndex + 1);

      const offsets = [20, 45, 70, 95];
      const offset = offsets[pairIndex % offsets.length];

      return {
        id: `e${i}-${e.source}-${e.target}-${e.timestamp}`,
        source: e.source,
        target: e.target,
        type: "smoothstep",
        label: e.label.replace(/_/g, " ").toLowerCase(),
        pathOptions: {
          offset,
          borderRadius: 12,
        },
        style: {
          stroke: "#94A3B8",
          strokeWidth: 1.5,
        },
        labelStyle: {
          fontSize: 11,
          fill: "#475569",
        },
        labelBgStyle: {
          fill: "#ffffff",
          fillOpacity: 0.9,
        },
        labelBgPadding: [4, 2],
        labelBgBorderRadius: 4,
      };
    });

    return { flowNodes, flowEdges };
  }, [nodes, edges, cutoffDate]);

  if (!nodes || nodes.length === 0) {
    return (
      <div className="flex h-[560px] items-center justify-center rounded-xl border border-gray-200 bg-white text-sm text-gray-400 shadow-sm">
        Ask a question to see the graph
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      {/* Timeline header */}
      <div className="border-b border-gray-100 px-5 pb-4 pt-4">
        <div className="mb-3 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-gray-400">
              Timeline
            </p>

            <p className="mt-1 text-sm font-medium text-gray-700">
              As of {cutoffDate}
              <span className="ml-2 text-xs font-normal text-gray-400">
                Event {cutoffIndex + 1} of {sortedTimestamps.length}
              </span>
            </p>
          </div>

          <button
            onClick={() => {
              if (cutoffIndex >= sortedTimestamps.length - 1) {
                setCutoffIndex(0);
              }

              setPlaying((p) => !p);
            }}
            className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white shadow-sm transition hover:bg-blue-700"
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
          className="w-full cursor-pointer"
        />
      </div>

      {/* Graph */}
      <div className="h-[560px]">
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          fitView
          fitViewOptions={{
            padding: 0.2,
          }}
          minZoom={0.5}
          maxZoom={1.5}
        >
          <Background gap={20} size={1} />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
}