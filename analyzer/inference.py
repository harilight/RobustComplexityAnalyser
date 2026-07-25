def infer_signature(params: list[str], accessed_attributes: set[str], string_literals: set[str] = None) -> dict:
    sig = {}
    main_structure = None
    
    if not params:
        return {}
        
    if string_literals is None:
        string_literals = set()
        
    # Precedence: Tree / Graph -> Linked List -> 2D Matrix / Grid -> Flat Array
    for p in params:
        p_lower = p.lower()
        if p_lower in ('root', 'tree', 'node') and not main_structure:
            sig[p] = 'binary_tree'
            main_structure = 'binary_tree'
        elif p_lower in ('graph', 'adj', 'edges') and not main_structure:
            sig[p] = 'graph_adj_list'
            main_structure = 'graph_adj_list'
        elif p_lower in ('head', 'list', 'curr') and not main_structure:
            sig[p] = 'linked_list'
            main_structure = 'linked_list'
        elif p_lower in ('matrix', 'grid', 'board', 'maze') and not main_structure:
            sig[p] = 'matrix'
            main_structure = 'matrix'
        elif p_lower in ('target', 'val', 'k', 'n', 'x', 'y', 'amount', 'size', 'num'):
            sig[p] = 'size_int'
        elif p_lower in ('s', 'text', 'word', 'string'):
            if string_literals:
                sig[p] = {'type': 'scalar_string', 'alphabet': list(string_literals)}
            else:
                sig[p] = 'scalar_string'
        elif 'sorted' in p_lower:
            sig[p] = '1d_array_sorted'
        else:
            sig[p] = 'random' # default array
            
    # If no structural parameter found, check attributes on the first parameter
    if not main_structure and len(params) > 0:
        first_param = params[0]
        if 'left' in accessed_attributes or 'right' in accessed_attributes:
            sig[first_param] = 'binary_tree'
        elif 'next' in accessed_attributes:
            sig[first_param] = 'linked_list'
            
    # Coupled Graph Dependencies: If matrix + size_int, convert matrix to graph_edges
    has_size_int = any(g == 'size_int' for g in sig.values())
    if has_size_int:
        for p, g in sig.items():
            if g == 'matrix':
                sig[p] = 'graph_edges'
                
    return sig

def format_inferred_structure(sig: dict, attributes: set[str]) -> str:
    if not sig:
        return "Auto-Detected: Flat Array (Default)"
        
    main_type = "Flat Array"
    reasons = []
    
    for param, gen in sig.items():
        if isinstance(gen, dict):
            gen = gen.get('type')
            
        if gen == 'binary_tree':
            main_type = "Binary Tree"
            reasons.append(f"'{param}'")
            if 'left' in attributes: reasons.append('.left')
        elif gen == 'graph_adj_list' or gen == 'graph_edges':
            main_type = "Graph"
            reasons.append(f"'{param}'")
        elif gen == 'linked_list':
            main_type = "Linked List"
            reasons.append(f"'{param}'")
            if 'next' in attributes: reasons.append('.next')
        elif gen == 'matrix':
            main_type = "2D Matrix"
            reasons.append(f"'{param}'")
        elif gen == 'scalar_string' and main_type == "Flat Array":
            main_type = "String"
            reasons.append(f"'{param}'")
        elif gen == '1d_array_sorted' and main_type == "Flat Array":
            main_type = "Sorted Array"
            reasons.append(f"'{param}'")
            
    if main_type == "Flat Array":
        return "Auto-Detected: Flat Array (Default)"
        
    # unique reasons
    reasons = list(dict.fromkeys(reasons))
    return f"{main_type} (Detected from {', '.join(reasons)})"
