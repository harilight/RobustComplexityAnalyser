from .ir import FunctionNode, LoopNode, BuiltinCallNode, DataStructureOpNode, IRNode, RecursiveCallNode
from .rules import get_op_complexity

def analyze_complexity(func_node: FunctionNode) -> dict:
    """Returns a dict with 'complexity' string and 'tags' list"""
    tags = set()
    max_power = _analyze_block(func_node.body, tags)
    
    if max_power >= 999:
        c = "O(2^n)"
    elif max_power == 0:
        c = "O(1)"
    elif max_power == 0.5:
        c = "O(log n)"
    elif max_power == 1:
        c = "O(n)"
    elif max_power == 1.5:
        c = "O(n log n)"
    else:
        c = f"O(n^{max_power})"
    return {"complexity": c, "tags": list(tags)}

def _analyze_block(nodes: list[IRNode], tags: set) -> int:
    max_power = 0
    for node in nodes:
        power = 0
        if isinstance(node, LoopNode):
            # linear loop adds 1 to the power
            body_power = _analyze_block(node.body, tags)
            power = 1 + body_power
        elif isinstance(node, BuiltinCallNode) or isinstance(node, DataStructureOpNode) or isinstance(node, RecursiveCallNode):
            power, tag = get_op_complexity(node)
            if tag:
                tags.add(tag)
            
        if power > max_power:
            max_power = power
            
    return max_power
