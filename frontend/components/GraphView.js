"use client";

import {
  useMemo,
  useState,
  useEffect,
} from "react";

import ReactFlow, {
  Background,
  Controls,
  Position,
  MarkerType,
} from "reactflow";

import "reactflow/dist/style.css";

const NODE_STYLES = {
  Person: {
    background: "#062f46",
    border: "#22d3ee",
    glow: "rgba(34, 211, 238, 0.45)",
  },

  Technology: {
    background: "#172554",
    border: "#60a5fa",
    glow: "rgba(96, 165, 250, 0.4)",
  },

  Reason: {
    background: "#2e1065",
    border: "#c084fc",
    glow: "rgba(192, 132, 252, 0.4)",
  },

  Metric: {
    background: "#052e16",
    border: "#4ade80",
    glow: "rgba(74, 222, 128, 0.4)",
  },
};

function formatRelation(value = "") {
  return value
    .replace(/_/g, " ")
    .toLowerCase();
}

export default function GraphView({
  nodes = [],
  edges = [],
}) {
  const sortedTimestamps = useMemo(() => {
    return [
      ...new Set(
        edges
          .map((edge) => edge.timestamp)
          .filter(Boolean)
      ),
    ].sort();
  }, [edges]);

  const [cutoffIndex, setCutoffIndex] =
    useState(0);

  const [playing, setPlaying] =
    useState(false);

  const safeCutoffIndex = Math.min(
    cutoffIndex,
    Math.max(
      sortedTimestamps.length - 1,
      0
    )
  );

  useEffect(() => {
    if (!playing) return;

    if (
      sortedTimestamps.length === 0 ||
      cutoffIndex >=
        sortedTimestamps.length - 1
    ) {
      setPlaying(false);
      return;
    }

    const timer = setTimeout(() => {
      setCutoffIndex(
        (current) => current + 1
      );
    }, 900);

    return () => clearTimeout(timer);
  }, [
    playing,
    cutoffIndex,
    sortedTimestamps.length,
  ]);

  const cutoffDate =
    sortedTimestamps[safeCutoffIndex];

  const {
    flowNodes,
    flowEdges,
  } = useMemo(() => {
    if (!cutoffDate) {
      return {
        flowNodes: [],
        flowEdges: [],
      };
    }

    const visibleEdges = edges.filter(
      (edge) =>
        edge.timestamp &&
        edge.timestamp <= cutoffDate
    );

    const visibleNodeIds = new Set();

    visibleEdges.forEach((edge) => {
      visibleNodeIds.add(edge.source);
      visibleNodeIds.add(edge.target);
    });

    const visibleNodes = nodes.filter(
      (node) =>
        visibleNodeIds.has(node.id)
    );

    const groups = {
      Person: [],
      Technology: [],
      Reason: [],
      Metric: [],
    };

    visibleNodes.forEach((node) => {
      const type = groups[node.type]
        ? node.type
        : "Reason";

      groups[type].push(node);
    });

    /*
     * Four clear graph columns.
     */
    const columns = {
      Person: 40,
      Technology: 300,
      Reason: 590,
      Metric: 880,
    };

    const flowNodes = [];

    Object.entries(groups).forEach(
      ([type, group]) => {
        group.forEach((node, index) => {
          const style =
            NODE_STYLES[type] ||
            NODE_STYLES.Reason;

          flowNodes.push({
            id: node.id,

            type: "default",

            data: {
              label:
                node.label || node.id,
            },

            position: {
              x: columns[type],
              y: 60 + index * 125,
            },

            sourcePosition:
              Position.Right,

            targetPosition:
              Position.Left,

            draggable: true,

            style: {
              width: 175,
              minHeight: 55,

              display: "flex",
              alignItems: "center",
              justifyContent: "center",

              padding: "12px 16px",

              background:
                style.background,

              border:
                `2px solid ${style.border}`,

              borderRadius: 7,

              color: "#f8fafc",

              fontFamily:
                "monospace",

              fontSize: 13,

              fontWeight: 600,

              textAlign: "center",

              boxShadow:
                `0 0 22px ${style.glow}`,

              letterSpacing:
                "0.01em",
            },
          });
        });
      }
    );

    /*
     * Build highly visible graph edges.
     */
    const pairCounts = new Map();

    const flowEdges =
      visibleEdges.map(
        (edge, index) => {
          const pairKey =
            `${edge.source}-${edge.target}`;

          const pairIndex =
            pairCounts.get(
              pairKey
            ) || 0;

          pairCounts.set(
            pairKey,
            pairIndex + 1
          );

          const curvature =
            35 + pairIndex * 12;

          return {
            id:
              `temporal-edge-${index}-${edge.source}-${edge.target}-${edge.timestamp}`,

            source: edge.source,

            target: edge.target,

            type: "bezier",

            animated: true,

            label:
              `${formatRelation(
                edge.label
              )}  •  ${edge.timestamp}`,

            markerEnd: {
              type:
                MarkerType.ArrowClosed,

              width: 18,

              height: 18,

              color: "#22d3ee",
            },

            pathOptions: {
              curvature,
            },

            style: {
              stroke:
                "#22d3ee",

              strokeWidth: 2.2,

              opacity: 0.95,

              filter:
                "drop-shadow(0 0 4px rgba(34,211,238,.45))",
            },

            labelStyle: {
              fill:
                "#bae6fd",

              fontFamily:
                "monospace",

              fontSize: 10,

              fontWeight: 600,

              letterSpacing:
                "0.02em",
            },

            labelBgStyle: {
              fill:
                "#020617",

              fillOpacity: 0.96,

              stroke:
                "#164e63",

              strokeWidth: 1,
            },

            labelBgPadding: [
              6,
              4,
            ],

            labelBgBorderRadius: 4,

            zIndex: 2,
          };
        }
      );

    return {
      flowNodes,
      flowEdges,
    };
  }, [
    nodes,
    edges,
    cutoffDate,
  ]);

  if (
    !nodes ||
    nodes.length === 0
  ) {
    return (
      <div className="graph-empty">
        <div className="graph-empty-icon">
          ◇
        </div>

        <span>
          GRAPH AWAITING QUERY
        </span>

        <small>
          Execute an investigation to
          populate the knowledge graph.
        </small>
      </div>
    );
  }

  if (
    sortedTimestamps.length === 0
  ) {
    return (
      <div className="graph-empty">
        <div className="graph-empty-icon">
          ∅
        </div>

        <span>
          NO TEMPORAL DATA
        </span>
      </div>
    );
  }

  return (
    <div className="graph-container">

      {/* Timeline */}

      <div className="graph-timeline">
        <div className="timeline-info">
          <span>
            TIMELINE
          </span>

          <strong>
            AS OF {cutoffDate}
          </strong>
        </div>

        <button
          onClick={() => {
            if (
              cutoffIndex >=
              sortedTimestamps.length -
                1
            ) {
              setCutoffIndex(0);
            }

            setPlaying(
              (current) =>
                !current
            );
          }}
          className="timeline-play"
        >
          {playing
            ? "Ⅱ PAUSE"
            : "▶ PLAY"}
        </button>

        <input
          type="range"
          min={0}
          max={Math.max(
            sortedTimestamps.length -
              1,
            0
          )}
          value={
            safeCutoffIndex
          }
          onChange={(event) => {
            setPlaying(false);

            setCutoffIndex(
              Number(
                event.target.value
              )
            );
          }}
        />

        <div className="timeline-event">
          EVENT{" "}
          {safeCutoffIndex + 1} /{" "}
          {sortedTimestamps.length}
        </div>
      </div>

      {/* Graph */}

      <div className="graph-canvas">
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          fitView
          fitViewOptions={{
            padding: 0.16,
            minZoom: 0.45,
            maxZoom: 1.1,
          }}
          minZoom={0.35}
          maxZoom={1.6}
          nodesDraggable
          nodesConnectable={false}
          elementsSelectable
          proOptions={{
            hideAttribution: true,
          }}
        >
          <Background
            gap={25}
            size={1}
            color="#164e63"
          />

          <Controls
            showInteractive={false}
          />
        </ReactFlow>

        <div className="graph-fit-label">
          ↖ FIT VIEW
        </div>
      </div>
    </div>
  );
}