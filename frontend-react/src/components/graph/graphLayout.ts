import type { GraphNode, GraphEdge } from '../../types/graph';
import type { Node, Edge } from '@xyflow/react';

export type LayoutDirection = 'LR' | 'TB' | 'RADIAL';

interface LayoutOptions {
  direction?: LayoutDirection;
  nodeWidth?: number;
  nodeHeight?: number;
  rankSep?: number;
  nodeSep?: number;
}

/**
 * Topological layering algorithm for Bitcoin money-flow graphs.
 * Directs IP/Wallets -> Transactions -> Change/Recipient Wallets from Left-to-Right (LR)
 * or Top-to-Bottom (TB) without external dependencies.
 */
export function layoutGraphNodes(
  nodes: GraphNode[],
  edges: GraphEdge[],
  options: LayoutOptions = {}
): { nodes: Node[]; edges: Edge[] } {
  const {
    direction = 'LR',
    nodeWidth = 240,
    nodeHeight = 120,
    rankSep = 180,
    nodeSep = 70,
  } = options;

  const nodeMap = new Map<string, GraphNode>();
  nodes.forEach((n) => nodeMap.set(n.id, n));

  // Compute incoming and outgoing degrees
  const inDegree = new Map<string, number>();
  const outDegree = new Map<string, number>();
  const adj = new Map<string, string[]>();

  nodes.forEach((n) => {
    inDegree.set(n.id, 0);
    outDegree.set(n.id, 0);
    adj.set(n.id, []);
  });

  edges.forEach((e) => {
    if (inDegree.has(e.target)) {
      inDegree.set(e.target, (inDegree.get(e.target) || 0) + 1);
    }
    if (outDegree.has(e.source)) {
      outDegree.set(e.source, (outDegree.get(e.source) || 0) + 1);
    }
    if (adj.has(e.source)) {
      adj.get(e.source)!.push(e.target);
    }
  });

  // Assign layers / ranks based on node type and topological hierarchy
  // Heuristic:
  // - IP nodes: rank 0 (top/left network telemetry)
  // - Source Wallets (inDegree === 0 or spent_from sources): rank 1
  // - Intermediate / TX nodes: rank 2
  // - Destination Wallets (outDegree === 0): rank 3
  const rankMap = new Map<string, number>();

  nodes.forEach((n) => {
    if (n.type === 'ip' || n.type === 'asn' || n.type === 'country') {
      rankMap.set(n.id, 0);
    } else if (n.type === 'wallet') {
      const inDeg = inDegree.get(n.id) || 0;
      const outDeg = outDegree.get(n.id) || 0;
      if (inDeg === 0 && outDeg > 0) {
        rankMap.set(n.id, 1); // Source wallet
      } else if (outDeg === 0 && inDeg > 0) {
        rankMap.set(n.id, 3); // Destination wallet
      } else {
        rankMap.set(n.id, 2); // Intermediate wallet
      }
    } else if (n.type === 'transaction') {
      rankMap.set(n.id, 2); // Core transaction layer
    } else {
      rankMap.set(n.id, 1);
    }
  });

  // Dynamic topological rank refinement using BFS
  const queue: string[] = [];
  nodes.forEach((n) => {
    if ((inDegree.get(n.id) || 0) === 0) {
      queue.push(n.id);
    }
  });

  const visited = new Set<string>();
  while (queue.length > 0) {
    const curr = queue.shift()!;
    visited.add(curr);
    const currRank = rankMap.get(curr) || 0;
    const neighbors = adj.get(curr) || [];

    for (const next of neighbors) {
      const existingRank = rankMap.get(next) || 0;
      if (existingRank <= currRank) {
        rankMap.set(next, currRank + 1);
      }
      if (!visited.has(next)) {
        queue.push(next);
      }
    }
  }

  // Group nodes by their assigned rank
  const layers = new Map<number, string[]>();
  nodes.forEach((n) => {
    const r = rankMap.get(n.id) || 0;
    if (!layers.has(r)) {
      layers.set(r, []);
    }
    layers.get(r)!.push(n.id);
  });

  const sortedRanks = Array.from(layers.keys()).sort((a, b) => a - b);

  // Position nodes layer by layer
  const flowNodes: Node[] = [];

  sortedRanks.forEach((rank, rankIndex) => {
    const nodeIdsInRank = layers.get(rank) || [];
    const totalHeightInLayer = nodeIdsInRank.length * (nodeHeight + nodeSep) - nodeSep;

    nodeIdsInRank.forEach((nodeId, indexInRank) => {
      const gNode = nodeMap.get(nodeId)!;
      let x = 0;
      let y = 0;

      if (direction === 'LR') {
        x = rankIndex * (nodeWidth + rankSep);
        // Center the layer vertically
        y = indexInRank * (nodeHeight + nodeSep) - totalHeightInLayer / 2 + 300;
      } else if (direction === 'TB') {
        y = rankIndex * (nodeHeight + rankSep);
        const totalWidthInLayer = nodeIdsInRank.length * (nodeWidth + nodeSep) - nodeSep;
        x = indexInRank * (nodeWidth + nodeSep) - totalWidthInLayer / 2 + 500;
      } else {
        // Radial distribution around center
        const angle = (2 * Math.PI * indexInRank) / Math.max(1, nodeIdsInRank.length);
        const radius = (rankIndex + 1) * 220;
        x = 500 + radius * Math.cos(angle);
        y = 350 + radius * Math.sin(angle);
      }

      flowNodes.push({
        id: gNode.id,
        type: gNode.type === 'ip' ? 'ip' : gNode.type === 'transaction' ? 'transaction' : 'wallet',
        position: { x, y },
        data: {
          node: gNode,
          label: gNode.label,
        },
      });
    });
  });

  // Convert GraphEdges to ReactFlow Edges
  const flowEdges: Edge[] = edges.map((edge) => {
    const isRelayed = edge.type === 'RELAYED_BY' || edge.type === 'OBSERVED';
    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: 'forensic',
      sourceHandle: isRelayed ? 'relayed' : 'out',
      targetHandle: isRelayed ? 'top' : 'in',
      data: {
        amount: edge.amount,
        type: edge.type,
        basis: edge.basis,
        sourceRecordIds: edge.source_record_ids,
      },
    };
  });

  return { nodes: flowNodes, edges: flowEdges };
}
