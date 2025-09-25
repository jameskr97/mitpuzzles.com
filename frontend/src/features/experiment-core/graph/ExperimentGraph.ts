import type { experiment_definition, graph_node, graph_edge } from "@/features/experiment-core/graph/types";

/** in-memory graph that we can use to query the craph */
export class ExperimentGraph {
  readonly graph_data: experiment_definition;
  private node_map: Map<string, graph_node>;
  private edge_map: Map<string, graph_edge>;

  constructor(graph_data: experiment_definition) {
    this.graph_data = { ...graph_data };
    this.node_map = new Map();
    this.edge_map = new Map();

    this.build_internal_maps();
  }

  /** build internal graph */
  private build_internal_maps(): void {
    // build node map
    this.node_map.clear();
    for (const node of this.graph_data.nodes) {
      this.node_map.set(node.id, node);
    }

    // build edge map
    this.edge_map.clear();
    for (const edge of this.graph_data.edges) {
      this.edge_map.set(edge.id, edge);
    }
  }

  add_node(node: graph_node): boolean {
    if (this.node_map.has(node.id)) {
      return false;
    }

    this.graph_data.nodes.push(node);
    this.node_map.set(node.id, node);
    return true;
  }

  get_connected_nodes(node_id: string): string[] {
    return this.graph_data.edges.filter((edge) => edge.from_node === node_id).map((edge) => edge.to_node);
  }

  get_nodes(): graph_node[] { return [...this.graph_data.nodes]; }
  get entry_node(): string { return this.graph_data.entry_node; }
}
