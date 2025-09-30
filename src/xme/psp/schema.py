from __future__ import annotations
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
import orjson
import networkx as nx
from pathlib import Path


def _dumps(v, *, default):
    return orjson.dumps(v, option=orjson.OPT_SORT_KEYS).decode()


class DAGMeta(BaseModel):
    nodes: int = 0
    edges: int = 0
    acyclic: bool = True


class ProofMeta(BaseModel):
    theorem: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = []


class Block(BaseModel):
    id: str
    kind: str
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
    model_config = ConfigDict(populate_by_name=True)
    blocks: List[Block] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)
    cuts: List[Cut] = Field(default_factory=list)
    dag: DAGMeta = Field(default_factory=DAGMeta)
    meta: ProofMeta = Field(default_factory=ProofMeta)

    @field_validator("edges")
    @classmethod
    def _acyclic(cls, edges: List[Edge], info):
        blocks = info.data.get("blocks", [])
        g = nx.DiGraph()
        for b in blocks:
            g.add_node(b.id)
        for e in edges:
            g.add_edge(e.src, e.dst)
        if not nx.is_directed_acyclic_graph(g):
            raise ValueError("PSP graph must be acyclic")
        return edges
    
    def model_post_init(self, __context):
        """Update DAG metadata after initialization."""
        g = nx.DiGraph()
        for b in self.blocks:
            g.add_node(b.id)
        for e in self.edges:
            g.add_edge(e.src, e.dst)
        self.dag = DAGMeta(
            nodes=g.number_of_nodes(), 
            edges=g.number_of_edges(), 
            acyclic=nx.is_directed_acyclic_graph(g)
        )

    def canonical_json(self) -> str:
        return orjson.dumps(self.model_dump(), option=orjson.OPT_SORT_KEYS).decode()


def load_psp(path: str | Path) -> PSP:
    data = orjson.loads(Path(path).read_bytes())
    return PSP(**data)
