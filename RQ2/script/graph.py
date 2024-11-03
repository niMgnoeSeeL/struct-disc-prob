# library for generating the graph
from typing import Dict, Set, List, Tuple
import networkx as nx
import pandas as pd


def construct_graph_from_transitions(
    trace_ids: List[str], transition_dfs: List[pd.DataFrame]
) -> nx.DiGraph:
    G = nx.DiGraph()
    num_traces = len(trace_ids)
    iter_idx = 0
    for trace_id, transition_df in zip(trace_ids, transition_dfs):
        iter_idx += 1
        print(
            f"Processing trace_id: {trace_id} ({iter_idx}/{num_traces})",
            end="\r",
            flush=True,
        )
        for _, row in transition_df.iterrows():
            if row["taken"] == 0:
                continue
            src = row["source"]
            dest = row["destination"]
            branch_type = row["branch_type"]
            if src not in G:
                G.add_node(src, visited=set())
            if dest not in G:
                G.add_node(dest, visited=set())
            # add trace_id to the visited set
            G.nodes[src]["visited"].add(trace_id)
            G.nodes[dest]["visited"].add(trace_id)
            # add the edge
            G.add_edge(src, dest, branch_type=branch_type)
    return G


def split_graph(G: nx.DiGraph) -> List[nx.DiGraph]:
    # split the graph into connected components
    G_copy = G.copy()
    G_copy.remove_node("entry")
    G_copy.remove_node("exit")
    clusters = nx.weakly_connected_components(G_copy)
    Gs = []
    for cluster in clusters:
        G_cluster = G.subgraph(cluster).copy()
        # add the entry and exit node back
        G_cluster.add_node("entry", visited=G.nodes["entry"]["visited"])
        G_cluster.add_node("exit", visited=G.nodes["exit"]["visited"])
        nodes_from_entry = set(G.successors("entry")).intersection(cluster)
        nodes_to_exit = set(G.predecessors("exit")).intersection(cluster)
        for node in nodes_from_entry:
            G_cluster.add_edge("entry", node)
        for node in nodes_to_exit:
            G_cluster.add_edge(node, "exit")
        Gs.append(G_cluster)
    return Gs


def get_idom_seq(idoms, node, entry="entry"):
    while node != entry:
        yield node
        node = idoms[node]
    yield node


def merge_single_edge(G: nx.DiGraph) -> nx.DiGraph:
    G_new = G.copy()
    # remove the self loop
    for node in G_new:
        if G_new.has_edge(node, node):
            G_new.remove_edge(node, node)
    node2cluster = {}
    cluster2startend = {}
    G_rev = G_new.reverse()

    for source in G_new:
        if source == "entry":
            continue
        if G_new.out_degree(source) == 1:
            dest = list(G_new.successors(source))[0]
            if dest == "exit":
                continue
            if G_rev.out_degree(dest) == 1:
                # merge the edge
                if source not in node2cluster and dest not in node2cluster:
                    cluster = {source, dest}
                    node2cluster[source] = cluster
                    node2cluster[dest] = cluster
                    cluster2startend[tuple(sorted(cluster))] = (source, dest)
                elif source in node2cluster and dest in node2cluster:
                    cluster_src = node2cluster[source]
                    cluster_dest = node2cluster[dest]
                    if cluster_src != cluster_dest:
                        cluster_start = cluster2startend[
                            tuple(sorted(cluster_src))
                        ][0]
                        del cluster2startend[tuple(sorted(cluster_src))]
                        cluster_end = cluster2startend[
                            tuple(sorted(cluster_dest))
                        ][1]
                        del cluster2startend[tuple(sorted(cluster_dest))]
                        cluster_src.update(cluster_dest)
                        for node in cluster_dest:
                            node2cluster[node] = cluster_src
                        cluster2startend[tuple(sorted(cluster_src))] = (
                            cluster_start,
                            cluster_end,
                        )
                elif source in node2cluster:
                    cluster = node2cluster[source]
                    cluster_start = cluster2startend[tuple(sorted(cluster))][0]
                    del cluster2startend[tuple(sorted(cluster))]
                    cluster.add(dest)
                    node2cluster[dest] = cluster
                    cluster2startend[tuple(sorted(cluster))] = (
                        cluster_start,
                        dest,
                    )
                else:
                    cluster = node2cluster[dest]
                    cluster_end = cluster2startend[tuple(sorted(cluster))][1]
                    del cluster2startend[tuple(sorted(cluster))]
                    cluster.add(source)
                    node2cluster[source] = cluster
                    cluster2startend[tuple(sorted(cluster))] = (
                        source,
                        cluster_end,
                    )
    nodes_not_merged = {node for node in G_new if node not in node2cluster}
    nodemap = {}
    for node in nodes_not_merged:
        nodemap[node] = node
    for cluster in cluster2startend:
        node_cluster = "\n".join(cluster)
        for node in cluster:
            nodemap[node] = node_cluster
    G_simple = nx.DiGraph()
    for node in G_new:
        if node in nodes_not_merged:
            G_simple.add_node(
                nodemap[node], visited=G_new.nodes[node]["visited"]
            )
            for dest in G_new.successors(node):
                G_simple.add_edge(nodemap[node], nodemap[dest])
    for cluster in cluster2startend:
        node_cluster = "\n".join(cluster)
        G_simple.add_node(
            node_cluster, visited=G_new.nodes[cluster[0]]["visited"]
        )
        start, end = cluster2startend[cluster]
        for dest in G_new.successors(end):
            G_simple.add_edge(node_cluster, nodemap[dest])
    # drop the self loop
    for node in G_simple:
        if G_simple.has_edge(node, node):
            G_simple.remove_edge(node, node)
    return G_simple


def get_mm_nodes_with_cycle(
    G: nx.DiGraph, entry="entry", exit="exit"
) -> Set[str]:
    _G = G.copy()
    idoms = nx.immediate_dominators(_G, entry)
    dom_dict = {}
    for node in _G:
        doms = set(get_idom_seq(idoms, node, entry))
        dom_dict[node] = doms
    for node in _G.nodes:
        doms = [d for d in dom_dict[node] if d != node]
        # check if there is an edge from the node to its dominator
        for dom in doms:
            if _G.has_edge(node, dom):
                _G.remove_edge(node, dom)
    # recompute the dom_dict
    rev_G = nx.reverse(_G)
    mm_nodes = set()
    visited = set()
    queue = [entry]
    # what_was_like_visited = {}
    already_skipped = set()
    while len(queue):
        node = queue.pop(0)
        if node in visited:
            continue
        # check if every predecessor is visited
        predecessors = set(rev_G[node])
        if not predecessors.issubset(visited):
            if node not in already_skipped:
                already_skipped.add(node)
                queue.append(node)
                continue
            else:
                for pred in predecessors - visited:
                    _G.remove_edge(pred, node)
        visited.add(node)
        already_skipped = set()
        if len(_G[node]) > 1:
            adding = set(_G[node]) - {exit}
            mm_nodes.update(adding)
        if node in mm_nodes:
            keep = len(_G[node]) == 0
            for dest in _G[node]:
                if dest == exit or node not in dom_dict[dest]:
                    keep = True
                    break
            if not keep:
                mm_nodes.remove(node)
        adding = set(_G[node]) - visited
        queue = list(adding) + queue  # add to the front
    return mm_nodes
