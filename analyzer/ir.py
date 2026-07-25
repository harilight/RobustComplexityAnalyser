from dataclasses import dataclass, field
from typing import List, Optional, Any, Union

@dataclass
class IRNode:
    """Base class for all Intermediate Representation nodes."""
    pass

@dataclass
class FunctionNode(IRNode):
    name: str
    args: list[str]
    body: list[IRNode] = field(default_factory=list)
    inferred_signature: dict = field(default_factory=dict)
    accessed_attributes: set = field(default_factory=set)

@dataclass
class LoopNode(IRNode):
    bound_type: str  # 'linear', 'log', 'sqrt', 'const'
    body: List[IRNode] = field(default_factory=list)

@dataclass
class RecursiveCallNode(IRNode):
    branch_factor: int
    is_memoized: bool

@dataclass
class BuiltinCallNode(IRNode):
    name: str
    receiver_type: Optional[str] = None # e.g. 'list', 'set', 'dict'
    arg_sizes: List[str] = field(default_factory=list)

@dataclass
class DataStructureOpNode(IRNode):
    structure_type: str
    op: str
    position: Optional[str] = None # 'front', 'back', 'middle'

@dataclass
class AllocationNode(IRNode):
    size_expr: str
    location: str
