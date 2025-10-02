"""
Schéma PSP (Proof Structure Protocol) avec validation et normalisation.
"""
from __future__ import annotations
from typing import List, Dict, Optional, Iterable
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
import orjson
import networkx as nx
from pathlib import Path


def _orjson_dumps(v, *, default):
    return orjson.dumps(v, option=orjson.OPT_SORT_KEYS).decode()


class BlockKind(str, Enum):
    axiom = "axiom"
    lemma = "lemma"
    theorem = "theorem"
    object = "object"
    morphism = "morphism"
    functor = "functor"
    rule = "rule"
    concept = "concept"


class DAGMeta(BaseModel):
    nodes: int = 0
    edges: int = 0
    acyclic: bool = True


class ProofMeta(BaseModel):
    version: int = 1
    theorem: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = []


class Block(BaseModel):
    id: str
    kind: BlockKind
    label: Optional[str] = None
    data: Dict[str, object] = {}


class Edge(BaseModel):
    src: str
    dst: str
    kind: str = "dep"


class Cut(BaseModel):
    id: str
    blocks: List[str] = []


class PSP(BaseModel):
    model_config = ConfigDict(json_dumps=_orjson_dumps, populate_by_name=True)

    blocks: List[Block] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)
    cuts: List[Cut] = Field(default_factory=list)
    dag: DAGMeta = Field(default_factory=DAGMeta)
    meta: ProofMeta = Field(default_factory=ProofMeta)

    @field_validator("edges")
    @classmethod
    def _validate_acyclic(cls, edges: List[Edge], info):
        blocks: List[Block] = info.data.get("blocks", [])
        g = nx.DiGraph()
        for b in blocks:
            g.add_node(b.id)
        for e in edges:
            g.add_edge(e.src, e.dst)
        if not nx.is_directed_acyclic_graph(g):
            raise ValueError("PSP graph must be acyclic")
        info.data["dag"] = DAGMeta(nodes=g.number_of_nodes(), edges=g.number_of_edges(), acyclic=True)
        return edges

    def canonical_json(self) -> str:
        return self.model_dump_json()

    def topo_sort(self) -> List[str]:
        g = nx.DiGraph()
        for b in self.blocks:
            g.add_node(b.id)
        for e in self.edges:
            g.add_edge(e.src, e.dst)
        return list(nx.topological_sort(g))

    def normalize(self) -> "PSP":
        # Sort blocks by (kind, id); edges by (src, dst, kind); cuts by id and blocks lexicographically
        self.blocks = sorted(self.blocks, key=lambda b: (b.kind.value, b.id))
        self.edges = sorted(self.edges, key=lambda e: (e.src, e.dst, e.kind))
        self.cuts = sorted(
            [Cut(id=c.id, blocks=sorted(c.blocks)) for c in self.cuts],
            key=lambda c: c.id,
        )
        # Recompute DAG meta
        _ = self._validate_acyclic(self.edges, info=type("I", (), {"data": {"blocks": self.blocks}}))
        return self

    def model_json_schema(self) -> dict:
        # Expose pydantic-generated JSON Schema
        return type(self).model_json_schema()


def load_psp(path: str | Path) -> PSP:
    p = Path(path)
    data = orjson.loads(p.read_bytes())
    return PSP(**data)


def save_psp(psp: PSP, path: str | Path) -> None:
    Path(path).write_text(psp.canonical_json())