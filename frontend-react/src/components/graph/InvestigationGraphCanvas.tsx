import React, { useState, useCallback, useMemo, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Panel,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  BackgroundVariant,
} from '@xyflow/react';
import type { Node } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import type { GraphData, GraphNode } from '../../types/graph';
import { customNodeTypes } from './CustomNodes';
import { customEdgeTypes } from './CustomEdges';
import { layoutGraphNodes } from './graphLayout';
import type { LayoutDirection } from './graphLayout';
import { GraphToolbar } from './GraphToolbar';
import { NodeInspectorDrawer } from './NodeInspectorDrawer';

interface InvestigationGraphCanvasProps {
  initialGraphData?: GraphData;
  onNodeClickExternal?: (node: GraphNode) => void;
  className?: string;
}

// Inner canvas component wrapped in ReactFlowProvider
const GraphCanvasInner: React.FC<InvestigationGraphCanvasProps> = ({
  initialGraphData,
  onNodeClickExternal,
  className = '',
}) => {
  const { fitView } = useReactFlow();

  const [layoutMode, setLayoutMode] = useState<LayoutDirection>('LR');
  const [searchQuery, setSearchQuery] = useState('');
  const [showIps, setShowIps] = useState(true);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // Filter raw data based on visibility options
  const activeGraphData = useMemo(() => {
    if (!initialGraphData) {
      return { nodes: [], edges: [] };
    }

    let filteredNodes = initialGraphData.nodes;
    let filteredEdges = initialGraphData.edges;

    if (!showIps) {
      filteredNodes = filteredNodes.filter((n) => n.type !== 'ip');
      const validNodeIds = new Set(filteredNodes.map((n) => n.id));
      filteredEdges = filteredEdges.filter(
        (e) => validNodeIds.has(e.source) && validNodeIds.has(e.target)
      );
    }

    return { nodes: filteredNodes, edges: filteredEdges };
  }, [initialGraphData, showIps]);

  // Compute Layout & React Flow elements
  const { initialNodes, initialEdges } = useMemo(() => {
    const layout = layoutGraphNodes(activeGraphData.nodes, activeGraphData.edges, {
      direction: layoutMode,
    });
    return { initialNodes: layout.nodes, initialEdges: layout.edges };
  }, [activeGraphData, layoutMode]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Sync state when data or layout changes
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
    // Smooth animated fitView after layout calculation
    const timer = setTimeout(() => {
      fitView({ padding: 0.2, duration: 400 });
    }, 50);
    return () => clearTimeout(timer);
  }, [initialNodes, initialEdges, fitView]);

  // Highlight logic for selected nodes and their incident edges
  useEffect(() => {
    if (!selectedNodeId) {
      // Clear selections and highlights
      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          selected: false,
        }))
      );
      setEdges((eds) =>
        eds.map((e) => ({
          ...e,
          selected: false,
          data: {
            ...e.data,
            isHighlighted: false,
          },
        }))
      );
      return;
    }

    // Identify incident edges
    const connectedEdges = new Set<string>();
    const connectedNodes = new Set<string>([selectedNodeId]);

    edges.forEach((e) => {
      if (e.source === selectedNodeId || e.target === selectedNodeId) {
        connectedEdges.add(e.id);
        connectedNodes.add(e.source);
        connectedNodes.add(e.target);
      }
    });

    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        selected: n.id === selectedNodeId,
      }))
    );

    setEdges((eds) =>
      eds.map((e) => ({
        ...e,
        selected: connectedEdges.has(e.id),
        data: {
          ...e.data,
          isHighlighted: connectedEdges.has(e.id),
        },
      }))
    );
  }, [selectedNodeId, setNodes, setEdges]);

  // Handle Search filtering and navigation
  useEffect(() => {
    if (!searchQuery.trim()) return;

    const query = searchQuery.toLowerCase().trim();
    const matched = nodes.find((n) => {
      const gNode = n.data?.node as GraphNode;
      const addr = String(gNode?.attributes?.address || '').toLowerCase();
      const txid = String(gNode?.attributes?.txid || '').toLowerCase();
      const ip = String(gNode?.attributes?.ip || '').toLowerCase();
      const label = String(gNode?.label || '').toLowerCase();
      const id = String(n.id).toLowerCase();

      return (
        addr.includes(query) ||
        txid.includes(query) ||
        ip.includes(query) ||
        label.includes(query) ||
        id.includes(query)
      );
    });

    if (matched) {
      setSelectedNodeId(matched.id);
      fitView({
        nodes: [matched],
        duration: 500,
        padding: 0.8,
      });
    }
  }, [searchQuery, nodes, fitView]);

  // Node Click Handler
  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNodeId(node.id);
      const rawGraphNode = (node.data?.node as GraphNode) || null;
      if (rawGraphNode && onNodeClickExternal) {
        onNodeClickExternal(rawGraphNode);
      }
    },
    [onNodeClickExternal]
  );

  // Pane Click Handler (deselect)
  const onPaneClick = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  // Fit View Callback
  const handleFitView = useCallback(() => {
    fitView({ padding: 0.2, duration: 400 });
  }, [fitView]);

  // Selected Node lookup for Inspector Drawer
  const selectedGraphNode = useMemo(() => {
    if (!selectedNodeId) return null;
    return activeGraphData.nodes.find((n) => n.id === selectedNodeId) || null;
  }, [selectedNodeId, activeGraphData.nodes]);

  // Custom Minimap node color mapper
  const nodeColorMapper = (node: Node) => {
    switch (node.type) {
      case 'wallet':
        return '#38bdf8'; // sky
      case 'transaction':
        return '#818cf8'; // indigo
      case 'ip':
        return '#34d399'; // emerald
      default:
        return '#64748b';
    }
  };

  return (
    <div className={`relative w-full h-full bg-[#090e17] overflow-hidden select-none ${className}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={customNodeTypes}
        edgeTypes={customEdgeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        fitView
        minZoom={0.15}
        maxZoom={2.5}
        defaultEdgeOptions={{
          type: 'forensic',
        }}
        proOptions={{ hideAttribution: true }}
      >
        {/* Dark forensic cyber grid background */}
        <Background
          variant={BackgroundVariant.Dots}
          gap={24}
          size={1.5}
          color="#1e293b"
        />

        {/* Top Control Toolbar Panel */}
        <Panel position="top-left" className="m-4 z-40 max-w-4xl">
          <GraphToolbar
            layoutMode={layoutMode}
            onLayoutChange={setLayoutMode}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            onFitView={handleFitView}
            showIps={showIps}
            onToggleIps={() => setShowIps((prev) => !prev)}
            totalNodes={activeGraphData.nodes.length}
            totalEdges={activeGraphData.edges.length}
          />
        </Panel>

        {/* Zoom, Pan, FitView Controls */}
        <Controls
          className="!bg-slate-900/90 !border !border-slate-800 !rounded-lg !shadow-xl !fill-slate-300 [&>button]:!bg-slate-900 [&>button]:!border-b [&>button]:!border-slate-800 hover:[&>button]:!bg-slate-800"
          showInteractive={false}
        />

        {/* Tactical Minimap */}
        <MiniMap
          nodeColor={nodeColorMapper}
          nodeStrokeWidth={3}
          maskColor="rgba(9, 14, 23, 0.85)"
          className="!bg-slate-950/90 !border !border-slate-800/90 !rounded-lg !shadow-2xl overflow-hidden"
          zoomable
          pannable
        />
      </ReactFlow>

      {/* Node Inspector Drawer */}
      <NodeInspectorDrawer
        selectedNode={selectedGraphNode}
        allEdges={activeGraphData.edges}
        allNodes={activeGraphData.nodes}
        onClose={() => setSelectedNodeId(null)}
        onSelectNode={(nodeId) => setSelectedNodeId(nodeId)}
      />
    </div>
  );
};

// Top-level exported component wrapped with ReactFlowProvider
export const InvestigationGraphCanvas: React.FC<InvestigationGraphCanvasProps> = (props) => {
  return (
    <ReactFlowProvider>
      <GraphCanvasInner {...props} />
    </ReactFlowProvider>
  );
};
