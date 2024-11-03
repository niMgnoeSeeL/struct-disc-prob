import os
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Set, Optional, FrozenSet


class Manager:
    def __init__(self, subject, trace_dict, trace_size_dict):
        self.subject: str = subject
        print("Loading trace_dict...")
        self.thash2traces: Dict[str, Set[str]] = {
            thash: set(traces) for thash, traces in trace_dict.items()
        }
        self.trace2thash: Dict[str, str] = {
            trace: thash
            for thash, traces in self.thash2traces.items()
            for trace in traces
        }
        self.thashs = sorted(list(self.thash2traces.keys()))
        print("Loading trace_size_dict...")
        self.trace_size_dict: Dict[str, int] = trace_size_dict
        print("Calculating trace_probability_dict...")
        self.trace_probability_dict: Dict[str, float] = (
            self.get_trace_probability_dict()
        )
        print("Calculating addr_dict...")
        self.node2ncluster: Dict[str, int] = None
        self.ncluster2node: Dict[int, Set[str]] = None
        self.ncluster2thashs: Dict[int, Set[str]] = None
        self.thash2nclusters: Dict[str, Set[int]] = None
        self.unreached_addrs: Set[str] = None
        self.process_traces()
        self.nodes: List[str] = self.get_nodes()

    def get_trace_probability_dict(self) -> Dict[str, float]:
        total_size = sum(self.trace_size_dict.values())
        return {
            trace_hash: size / total_size
            for trace_hash, size in self.trace_size_dict.items()
        }

    def process_traces(self):
        # compute ncluster2node, node2ncluster, ncluster2thashs,
        # thash2nclusters,and unreached_addrs
        print("Processing traces...")
        unreached_addrs = set()
        node2thashs: Dict[str, Set[str]] = {}
        for th_idx, thash in enumerate(self.thashs, 1):
            print(f"Processing traces {th_idx}/{len(self.thashs)}", end="\r")
            trace_file = next(iter(self.thash2traces[thash]))
            df = pd.read_csv(os.path.join("../data/", trace_file))
            addr_set = set(df["branch_addr"])
            addr_set |= set(df[df["taken"] == 1]["target"])
            unreached_addrs |= set(df[df["taken"] == 0]["target"])
            for addr in addr_set:
                if addr not in node2thashs:
                    node2thashs[addr] = set()
                node2thashs[addr].add(thash)
        self.unreached_addrs = unreached_addrs
        thashs2nodes: Dict[FrozenSet[str], Set[str]] = {}
        for node, thashs in node2thashs.items():
            if frozenset(thashs) not in thashs2nodes:
                thashs2nodes[frozenset(thashs)] = set()
            thashs2nodes[frozenset(thashs)].add(node)
        unique_nodesets = sorted(
            list({frozenset(nodes) for nodes in thashs2nodes.values()})
        )
        nclusters = range(len(unique_nodesets))
        self.ncluster2node = {
            n: set(nodes) for n, nodes in zip(nclusters, unique_nodesets)
        }
        self.node2ncluster = {
            node: n for n, nodes in self.ncluster2node.items() for node in nodes
        }
        self.thash2nclusters = {}
        for thashs, nodes in thashs2nodes.items():
            for thash in thashs:
                if thash not in self.thash2nclusters:
                    self.thash2nclusters[thash] = set()
                self.thash2nclusters[thash] |= {
                    self.node2ncluster[node] for node in nodes
                }
        self.ncluster2thashs = {n: set() for n in nclusters}
        for thash, nclusters in self.thash2nclusters.items():
            for ncluster in nclusters:
                self.ncluster2thashs[ncluster].add(thash)

    def get_nodes(self) -> List[str]:
        return sorted(list(self.node2ncluster.keys()))

    def sample_tracehash(self, num_samples: int) -> List[str]:
        return np.random.choice(
            self.thashs,
            num_samples,
            p=[
                self.trace_probability_dict[trace_hash]
                for trace_hash in self.thashs
            ],
        )

    def compute_missing_mass(self, trace_hashes: List[str]) -> float:
        # compute the missing mass of the trace_hashes
        nclusters_covered = set()
        for thash in trace_hashes:
            nclusters_covered |= self.thash2nclusters[thash]
        nclusters_uncovered = (
            set(self.ncluster2thashs.keys()) - nclusters_covered
        )
        trace_hashes_revealing = {
            _thash
            for _thash, _nclusters in self.thash2nclusters.items()
            if _nclusters & nclusters_uncovered
        }
        assert not trace_hashes_revealing.intersection(trace_hashes)
        return sum(
            self.trace_probability_dict[thash]
            for thash in trace_hashes_revealing
        )

    def get_singleton_nclusters(
        self, trace_hashes: List[str], node_set: Set[str] = None
    ) -> Set[int]:
        if trace_hashes is None or len(trace_hashes) == 0:
            return set()
        if node_set is not None and len(node_set) == 0:
            return set()
        seens = set()
        singletons = set()
        for thash in trace_hashes:
            if thash not in self.thash2nclusters:
                continue
            nclusters = self.thash2nclusters[thash]
            singletons -= nclusters  # remove already seen nclusters
            singletons |= nclusters - seens  # add fresh nclusters
            seens |= nclusters  # update seen nclusters
        if node_set is not None:
            nclusters4nodes = {self.node2ncluster[node] for node in node_set}
            singletons &= nclusters4nodes
        return singletons

    def good_turing(
        self, trace_hashes: List[str], node_set: Optional[Set[str]] = None
    ) -> float:
        if len(trace_hashes) == 0:
            return 1
        singleton_nclusters = self.get_singleton_nclusters(
            trace_hashes, node_set
        )
        n_singleton_nodes = sum(
            len(self.ncluster2node[n]) for n in singleton_nclusters
        )
        ret = n_singleton_nodes / len(trace_hashes)
        return min(ret, 1)

    def struct_original(
        self, trace_hashes: List[str], node_set: Optional[Set[str]] = None
    ) -> float:
        if len(trace_hashes) == 0:
            return 1
        singleton_nclusters = self.get_singleton_nclusters(
            trace_hashes, node_set
        )
        n_thash_with_singleton = len(
            [
                th
                for th in trace_hashes
                if self.thash2nclusters[th] & singleton_nclusters
            ]
        )
        return n_thash_with_singleton / len(trace_hashes)
