from .ir import FunctionNode, LoopNode, BuiltinCallNode, DataStructureOpNode, IRNode, RecursiveCallNode, BranchNode, StringConcatNode
from .rules import get_op_complexity

def analyze_complexity(func_node: FunctionNode) -> dict:
    """Returns a dict with 'complexity' string and 'tags' list"""
    tags = set()
    max_power = _analyze_block(func_node.body, tags)
    
    if max_power >= 9999:
        c = "O(n!)"
    elif max_power > 1000:
        base = max_power - 1000
        c = f"O({base}^n)"
    elif max_power >= 999:
        c = "O(2^n)"
    elif max_power == 0:
        c = "O(1)"
    elif max_power == 0.5:
        c = "O(log n)"
    elif max_power == 0.6:
        c = "O(sqrt n)"
    elif max_power == 1:
        c = "O(n)"
    elif max_power == 1.5:
        c = "O(n log n)"
    else:
        c = f"O(n^{max_power})"
        
    if 'partition-recursion' in tags:
        return {"complexity": {"best": "O(n log n)", "average": "O(n log n)", "worst": "O(n^2)"}, "tags": list(tags)}
        
    return {"complexity": c, "tags": list(tags)}

def _analyze_block(nodes: list[IRNode], tags: set) -> int:
    max_power = 0
    for node in nodes:
        power = 0
        if isinstance(node, LoopNode):
            body_power = _analyze_block(node.body, tags)
            loop_power = 1
            if node.bound_type == 'log':
                loop_power = 0.5
            elif node.bound_type == 'sqrt':
                loop_power = 0.6
            elif node.bound_type in ('amortized', 'const'):
                loop_power = 0
            power = loop_power + body_power
        elif isinstance(node, BranchNode):
            branch_max = 0
            for b in node.branches:
                b_pow = _analyze_block(b, tags)
                if b_pow > branch_max:
                    branch_max = b_pow
            power = branch_max
        elif isinstance(node, BuiltinCallNode) or isinstance(node, DataStructureOpNode) or isinstance(node, RecursiveCallNode) or isinstance(node, StringConcatNode):
            power, tag = get_op_complexity(node)
            if tag:
                tags.add(tag)
            
        if power > max_power:
            max_power = power
            
    return max_power
