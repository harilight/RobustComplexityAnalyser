from .ir import BuiltinCallNode, DataStructureOpNode, IRNode, RecursiveCallNode

def get_op_complexity(node: IRNode) -> tuple:
    """Returns (power, tag) where power is the n-exponent and tag is a string or None."""
    
    if isinstance(node, RecursiveCallNode):
        if getattr(node, 'is_memoized', False):
            return getattr(node, 'dp_dimension', 1), 'memoization'
        if getattr(node, 'is_factorial', False):
            return 9999, 'factorial'
        if node.branch_factor > 1:
            if getattr(node, 'arg_reduction', None) == 'halving':
                return 1.5, 'divide-and-conquer'
            if getattr(node, 'arg_reduction', None) == 'partition':
                return 1.5, 'partition-recursion'
            return 1000 + node.branch_factor, f'exponential-{node.branch_factor}'
        elif node.branch_factor == 1:
            if getattr(node, 'arg_reduction', None) == 'halving':
                return 0.5, 'log-n-recursion'
            return 1, 'recursion'
            
    from .ir import StringConcatNode
    if isinstance(node, StringConcatNode):
        return 1, 'string-concat'
        
    elif isinstance(node, DataStructureOpNode):
        # Category C: Amortized cost
        if node.structure_type == 'list' and node.op == 'append':
            return 0, 'amortized-cost'
        elif node.structure_type == 'list' and node.op == 'pop':
            if getattr(node, 'position', None) == 'front':
                return 1, 'list-shift'
            else:
                return 0, 'constant-pop'
                
    if isinstance(node, BuiltinCallNode):
        if node.name == 'in':
            if node.receiver_type in ('list', 'tuple', 'string'):
                return 1, 'builtin-hidden-loop'
            else:
                return 0, 'hash-lookup'
        elif node.name in ('index', 'count'):
            return 1, 'linear-scan'
        elif node.name in ('includes', 'indexOf', 'lastIndexOf'):
            if node.receiver_type == 'array':
                return 1, 'builtin-hidden-loop'
        elif node.name in ('sort', 'sorted'):
            return 1.5, 'sorting'
        elif node.name in ('min', 'max', 'sum', 'all', 'any', 'Counter', 'zip', 'map', 'filter', 'list', 'set', 'reversed', 'keys', 'values', 'entries'):
            return 1, 'linear-aggregate'
        elif node.name in ('split', 'join', 'replace', 'splice', 'slice', 'concat'):
            return 1, 'string-op'
        elif node.name in ('heappush', 'heappop'):
            return 0.5, 'heap-op'
        elif node.name == 'popleft':
            return 0, 'queue-op'
            
    return 0, None
