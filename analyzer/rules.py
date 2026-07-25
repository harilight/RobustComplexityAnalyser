from .ir import BuiltinCallNode, DataStructureOpNode, IRNode, RecursiveCallNode

def get_op_complexity(node: IRNode) -> tuple:
    """Returns (power, tag) where power is the n-exponent and tag is a string or None."""
    
    if isinstance(node, RecursiveCallNode):
        if node.branch_factor >= 2 and not node.is_memoized:
            return 999, 'recursion'
        elif node.branch_factor >= 1:
            return 1, 'recursion'
            
    if isinstance(node, BuiltinCallNode):
        # Category A: Builtins that hide a loop
        if node.name == 'in':
            if node.receiver_type == 'list':
                return 1, 'builtin-hidden-loop'
            elif node.receiver_type in ('set', 'dict'):
                return 0, 'amortized-cost'
        
        elif node.name == 'includes':
            if node.receiver_type == 'array':
                return 1, 'builtin-hidden-loop'
                
        # Sorting
        elif node.name in ('sort', 'sorted'):
            return 1.5, 'sorting' # Using 1.5 to represent n log n internally if max_power logic rounds, wait, max_power is an int.
            # I'll return 1 for now and flag as 'sorting'. We can handle 1.5 later. Actually, wait!
            # If I return 2 for sorting, it overestimates to O(n^2). If 1, it underestimates to O(n).
            # Let's return 1.5 and update static.py to handle float powers!
            return 1.5, 'sorting'
            
        # Linear math & array aggregates
        elif node.name in ('min', 'max', 'sum', 'all', 'any'):
            return 1, 'linear-aggregate'
            
        # String ops
        elif node.name in ('split', 'join', 'replace'):
            return 1, 'string-op'
            
        # Heaps
        elif node.name in ('heappush', 'heappop'):
            return 0.5, 'heap-op' # 0.5 to represent log n
            
        # Queues
        elif node.name == 'popleft':
            return 0, 'queue-op'
                
    elif isinstance(node, DataStructureOpNode):
        # Category C: Amortized cost
        if node.structure_type == 'list' and node.op == 'append':
            return 0, 'amortized-cost'
            
    return 0, None
