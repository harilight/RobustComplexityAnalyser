import re
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
from .ir import FunctionNode, LoopNode, BuiltinCallNode, DataStructureOpNode, IRNode, RecursiveCallNode, BranchNode, StringConcatNode

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

_LOG_BOUND_RE = re.compile(r'(//\s*2\b|/\s*2\b|>>\s*1\b|>>=\s*1\b|\*=\s*2\b|//=\s*2\b|<<\s*1\b|<<=\s*1\b|\*\s*0\.5|\[\s*:\s*\w*mid\w*\s*\]|\[\s*\w*mid\w*\s*:\s*\])', re.IGNORECASE)
_SQRT_RE = re.compile(r'\*\s*([a-zA-Z_]\w*)\s*<=\s*([a-zA-Z_]\w*)', re.IGNORECASE)
_INCREMENT_RE = re.compile(r'(\+=\s*1\b|-=\s*1\b)', re.IGNORECASE)

def _get_identifiers(node) -> set:
    ids = set()
    def walk(n):
        if not hasattr(n, 'type'):
            return
        if n.type == 'identifier':
            ids.add(n.text.decode('utf8'))
        for c in getattr(n, 'children', []):
            walk(c)
    walk(node)
    return ids

def _detect_loop_bound_type(loop_ts_node, enclosing_block_ts_node=None, is_inner_loop=False) -> tuple[str, str]:
    if loop_ts_node.type == 'for_statement':
        for c in loop_ts_node.children:
            if c.type == 'call':
                func = _get_child_by_type(c, 'identifier')
                if func and func.text.decode('utf8') == 'range':
                    args = _get_child_by_type(c, 'argument_list')
                    if args:
                        args_text = args.text.decode('utf8').replace('(', '').replace(')', '').strip()
                        parts = [p.strip() for p in args_text.split(',')]
                        if all(p.isdigit() for p in parts) and parts:
                            return 'const', parts[-1]
            elif c.type == 'string':
                val = c.text.decode('utf8').strip("'\"")
                return 'const', str(len(val))
        return 'linear', None

    if loop_ts_node.type != 'while_statement':
        return 'linear', None

    condition_node = None
    for c in loop_ts_node.children:
        if c.type not in ('while', ':', 'block', 'comment'):
            condition_node = c
            break
    if condition_node is None:
        return 'linear', None

    cond_vars = _get_identifiers(condition_node)
    if not cond_vars:
        return 'linear', None

    cond_text = condition_node.text.decode('utf8')
    if re.search(r'\b([a-zA-Z_]\w*)\s*\*\s*\1\s*<=', cond_text) or re.search(r'\b([a-zA-Z_]\w*)\s*\*\*\s*2\s*<=', cond_text):
        return 'sqrt', None

    block = _get_child_by_type(loop_ts_node, 'block')
    if not block:
        return 'linear', None

    assignments = []
    def collect(n):
        if not hasattr(n, 'type'):
            return
        if n.type in ('for_statement', 'while_statement'):
            return
        if n.type in ('assignment', 'augmented_assignment'):
            lhs = n.children[0] if n.children else None
            if lhs is not None and lhs.type == 'identifier':
                assignments.append((lhs.text.decode('utf8'), n.text.decode('utf8')))
        for c in getattr(n, 'children', []):
            collect(c)
    collect(block)

    for lhs, text in assignments:
        if lhs in cond_vars and _LOG_BOUND_RE.search(text):
            return 'log', None

    midpoint_vars = {lhs for lhs, text in assignments if _LOG_BOUND_RE.search(text)}
    if midpoint_vars:
        for lhs, text in assignments:
            if lhs not in cond_vars:
                continue
            rhs = text.split('=', 1)[1] if '=' in text else text
            if any(re.search(r'\b' + re.escape(mv) + r'\b', rhs) for mv in midpoint_vars):
                return 'log', None
                
    if enclosing_block_ts_node and is_inner_loop:
        increments = {lhs for lhs, text in assignments if _INCREMENT_RE.search(text)}
        
        indices = set()
        def find_indices(n):
            if not hasattr(n, 'type'): return
            if n.type == 'subscript':
                indices.update(_get_identifiers(n))
            for c in getattr(n, 'children', []):
                find_indices(c)
        find_indices(block)
        
        candidates = {inc for inc in increments if inc in cond_vars or inc in indices}
        
        if candidates:
            resets = set()
            def find_resets(n):
                if not hasattr(n, 'type') or n == loop_ts_node:
                    return
                if n.type == 'assignment':
                    lhs = n.children[0] if n.children else None
                    if lhs is not None:
                        resets.update(_get_identifiers(lhs))
                for c in getattr(n, 'children', []):
                    find_resets(c)
            find_resets(enclosing_block_ts_node)
            if any(c not in resets for c in candidates):
                return 'amortized', None
                
        inner_pops = set()
        def find_inner_pops(n):
            if not hasattr(n, 'type'): return
            if n.type == 'call':
                func = _get_child_by_type(n, 'attribute')
                if func and len(func.children) >= 3:
                    obj = func.children[0]
                    attr = func.children[2]
                    if attr.type == 'identifier' and attr.text.decode('utf8') in ('pop', 'popleft', 'popitem', 'remove'):
                        if obj.type == 'identifier':
                            inner_pops.add(obj.text.decode('utf8'))
            for c in getattr(n, 'children', []):
                find_inner_pops(c)
        if block:
            find_inner_pops(block)
            
        if inner_pops:
            outer_appends = set()
            def find_outer_appends(n):
                if not hasattr(n, 'type') or n == loop_ts_node: return
                if n.type == 'call':
                    func = _get_child_by_type(n, 'attribute')
                    if func and len(func.children) >= 3:
                        obj = func.children[0]
                        attr = func.children[2]
                        if attr.type == 'identifier' and attr.text.decode('utf8') in ('append', 'push', 'add', 'insert'):
                            if obj.type == 'identifier':
                                outer_appends.add(obj.text.decode('utf8'))
                for c in getattr(n, 'children', []):
                    find_outer_appends(c)
            find_outer_appends(enclosing_block_ts_node)
            
            if any(p in outer_appends and p in cond_vars for p in inner_pops):
                return 'amortized', None

    if loop_ts_node.type == 'while_statement':
        has_queue_pop = False
        queue_vars = set()
        def find_queue_pop(n):
            nonlocal has_queue_pop
            if not hasattr(n, 'type'): return
            if n.type == 'call':
                func = _get_child_by_type(n, 'attribute')
                if func and len(func.children) >= 3:
                    obj = func.children[0]
                    attr = func.children[2]
                    if attr.type == 'identifier' and attr.text.decode('utf8') in ('popleft', 'pop'):
                        if obj.type == 'identifier':
                            has_queue_pop = True
                            queue_vars.add(obj.text.decode('utf8'))
            for c in getattr(n, 'children', []):
                find_queue_pop(c)
        find_queue_pop(block)
        
        if has_queue_pop and any(qv in cond_vars for qv in queue_vars):
            for c in getattr(block, 'children', []):
                if c.type in ('for_statement', 'while_statement'):
                    inner_has_append = False
                    inner_has_add = False
                    inner_has_remove = False
                    def check_bfs_inner(n):
                        nonlocal inner_has_append, inner_has_add, inner_has_remove
                        if not hasattr(n, 'type'): return
                        if n.type == 'call' and getattr(n, 'children', []):
                            func = n.children[0]
                            if func.type == 'attribute' and len(func.children) >= 3:
                                obj = func.children[0]
                                attr = func.children[2]
                                if obj.type == 'identifier' and attr.type == 'identifier':
                                    obj_name = obj.text.decode('utf8')
                                    attr_name = attr.text.decode('utf8')
                                    if attr_name == 'append' and obj_name in queue_vars:
                                        inner_has_append = True
                                    elif attr_name == 'add':
                                        inner_has_add = True
                                    elif attr_name in ('remove', 'discard'):
                                        inner_has_remove = True
                        for ch in getattr(n, 'children', []):
                            check_bfs_inner(ch)
                    check_bfs_inner(c)
                    if inner_has_append and inner_has_add and not inner_has_remove:
                        return 'amortized', None

    return 'linear', None

def _find_midpoint_vars(node) -> set:
    midpoint_vars = set()
    def walk(n):
        if not hasattr(n, 'type'):
            return
        if n.type == 'assignment':
            lhs = n.children[0] if n.children else None
            if lhs is not None and lhs.type == 'identifier' and _LOG_BOUND_RE.search(n.text.decode('utf8')):
                midpoint_vars.add(lhs.text.decode('utf8'))
        for c in getattr(n, 'children', []):
            walk(c)
    walk(node)
    return midpoint_vars

def _find_partition_vars(node) -> set:
    partition_vars = set()
    def walk(n):
        if not hasattr(n, 'type'):
            return
        if n.type == 'assignment':
            lhs = n.children[0] if n.children else None
            if lhs is not None and lhs.type == 'identifier':
                rhs = n.children[2] if len(n.children) > 2 else None
                if rhs and rhs.type == 'list_comprehension':
                    if _get_child_by_type(rhs, 'if_clause'):
                        partition_vars.add(lhs.text.decode('utf8'))
        for c in getattr(n, 'children', []):
            walk(c)
    walk(node)
    return partition_vars

def _analyze_reduction_arg(node, func_name: str, midpoint_vars: set = None, partition_vars: set = None) -> str:
    if midpoint_vars is None:
        midpoint_vars = _find_midpoint_vars(node)
    if partition_vars is None:
        partition_vars = _find_partition_vars(node)
        
    def walk(n):
        if n is None or not hasattr(n, 'type'):
            return 'unknown'
        if n.type == 'call':
            func = n.children[0]
            if func.type == 'identifier' and func.text.decode('utf8') == func_name:
                args_node = _get_child_by_type(n, 'argument_list')
                if args_node:
                    args_text = args_node.text.decode('utf8')
                    if _LOG_BOUND_RE.search(args_text):
                        return 'halving'
                    if any(re.search(r'\b' + re.escape(mv) + r'\b', args_text) for mv in midpoint_vars):
                        return 'halving'
                    if any(re.search(r'\b' + re.escape(pv) + r'\b', args_text) for pv in partition_vars):
                        return 'partition'
                        
                    for arg_c in args_node.children:
                        if arg_c.type == 'list_comprehension':
                            if _get_child_by_type(arg_c, 'if_clause'):
                                return 'partition'
                                
        for c in getattr(n, 'children', []):
            res = walk(c)
            if res != 'unknown':
                return res
        return 'unknown'
        
    return walk(node)

def check_memo(node, dict_vars):
    memo_vars = set()
    def find_memo_vars(n):
        if not hasattr(n, 'type'): return
        if n.type == 'comparison_operator':
            for i, comp_c in enumerate(n.children):
                if comp_c.type == 'in':
                    right_operand = n.children[i+1] if i+1 < len(n.children) else None
                    if right_operand and right_operand.type == 'identifier':
                        var_name = right_operand.text.decode('utf8')
                        if var_name in dict_vars or 'memo' in var_name.lower() or 'cache' in var_name.lower() or 'dp' in var_name.lower() or 'visit' in var_name.lower() or 'path' in var_name.lower():
                            memo_vars.add(var_name)
        elif n.type == 'assignment':
            left = n.children[0]
            if left.type == 'subscript':
                obj = left.children[0] if left.children else None
                if obj and obj.type == 'identifier':
                    var_name = obj.text.decode('utf8')
                    if var_name in dict_vars or 'memo' in var_name.lower() or 'cache' in var_name.lower() or 'dp' in var_name.lower():
                        memo_vars.add(var_name)
        for child in getattr(n, 'children', []):
            find_memo_vars(child)
            
    find_memo_vars(node)
    
    removed_vars = set()
    def find_removes(n):
        if not hasattr(n, 'type'): return
        if n.type == 'call':
            func = n.children[0]
            if func.type == 'attribute':
                obj = func.children[0]
                attr = func.children[2]
                if obj.type == 'identifier' and attr.type == 'identifier':
                    obj_name = obj.text.decode('utf8')
                    attr_name = attr.text.decode('utf8')
                    if obj_name in memo_vars and attr_name in ('remove', 'discard', 'pop'):
                        removed_vars.add(obj_name)
        for child in getattr(n, 'children', []):
            find_removes(child)
            
    find_removes(node)
    
    return any(mv not in removed_vars for mv in memo_vars)

def _combine_sequential(paths_seq: list[list[dict]]) -> list[dict]:
    current_paths = [{'bf': 0, 'isf': False, 'rft': False, 'ft': True}]
    completed_paths = []
    
    for statement_paths in paths_seq:
        next_paths = []
        for cp in current_paths:
            if not cp['ft']:
                completed_paths.append(cp)
                continue
            
            for sp in statement_paths:
                next_paths.append({
                    'bf': cp['bf'] + sp['bf'],
                    'isf': cp['isf'] or sp['isf'],
                    'rft': (cp['rft'] and sp['ft']) or sp['rft'],
                    'ft': cp['ft'] and sp['ft']
                })
        current_paths = next_paths
        
    return completed_paths + current_paths

def _get_recursive_paths(node, func_name: str, in_variable_loop: bool = False) -> list[dict]:
    if node is None:
        return [{'bf': 0, 'isf': False, 'rft': False, 'ft': True}]
        
    if node.type == 'call':
        func = node.children[0]
        call_name = None
        if func.type == 'identifier': call_name = func.text.decode('utf8')
        elif func.type == 'attribute': call_name = func.children[-1].text.decode('utf8')
        
        if call_name == func_name:
            paths_seq = [_get_recursive_paths(c, func_name, in_variable_loop) for c in node.children]
            res = _combine_sequential(paths_seq)
            for p in res:
                p['bf'] += 1
                p['isf'] = p['isf'] or in_variable_loop
                p['rft'] = True
            return res
            
    if node.type in ('return_statement', 'break_statement'):
        paths_seq = [_get_recursive_paths(c, func_name, in_variable_loop) for c in node.children]
        res = _combine_sequential(paths_seq)
        for p in res:
            p['ft'] = False
            p['rft'] = False
        return res
        
    if node.type in ('for_statement', 'while_statement'):
        btype, bval = _detect_loop_bound_type(node)
        is_var = (btype != 'const')
        
        paths_seq = [_get_recursive_paths(c, func_name, is_var or in_variable_loop) for c in node.children]
        res = _combine_sequential(paths_seq)
        
        for p in res:
            if p['bf'] > 0:
                multiplier = int(bval) if btype == 'const' and bval else 2
                if is_var:
                    p['isf'] = True
                    multiplier = 1
                if not p['rft']:
                    multiplier = 1
                p['bf'] *= multiplier
                
        # A loop can always skip or terminate without hitting a nested return
        res.append({'bf': 0, 'isf': False, 'rft': False, 'ft': True})
        return res
        
    if node.type == 'if_statement':
        cons = _get_child_by_type(node, 'block')
        
        cond_children = [c for c in node.children if c.type not in ('block', 'elif_clause', 'else_clause')]
        cond_paths_seq = [_get_recursive_paths(c, func_name, in_variable_loop) for c in cond_children]
        cond_paths = _combine_sequential(cond_paths_seq)
        
        branches = []
        if cons:
            branches.append(_get_recursive_paths(cons, func_name, in_variable_loop))
        else:
            branches.append([{'bf': 0, 'isf': False, 'rft': False, 'ft': True}])
            
        has_else = False
        for c in node.children:
            if c.type in ('elif_clause', 'else_clause'):
                if c.type == 'else_clause': has_else = True
                b = _get_child_by_type(c, 'block')
                if b:
                    branches.append(_get_recursive_paths(b, func_name, in_variable_loop))
                else:
                    branches.append([{'bf': 0, 'isf': False, 'rft': False, 'ft': True}])
                    
        if not has_else:
            branches.append([{'bf': 0, 'isf': False, 'rft': False, 'ft': True}])
            
        merged_branches = []
        for branch_paths in branches:
            merged_branches.extend(_combine_sequential([cond_paths, branch_paths]))
            
        return merged_branches
        
    paths_seq = [_get_recursive_paths(c, func_name, in_variable_loop) for c in node.children]
    return _combine_sequential(paths_seq)

def get_recursive_calls(node, func_name: str, in_variable_loop: bool = False) -> tuple[int, bool, bool, bool]:
    paths = _get_recursive_paths(node, func_name, in_variable_loop)
    if not paths:
        return 0, False, False, True
    
    max_bf = max(p['bf'] for p in paths)
    isf = any(p['isf'] for p in paths if p['bf'] == max_bf)
    rft = any(p['rft'] for p in paths)
    ft = any(p['ft'] for p in paths)
    
    return max_bf, isf, rft, ft

def parse_python(code: str) -> FunctionNode:
    tree = parser.parse(bytes(code, "utf8"))
    root = tree.root_node
    
    func_def = None
    decorators = []
    
    class_methods = {}
    def extract_func(node):
        nonlocal func_def
        name = _get_child_by_type(node, 'identifier')
        if name:
            name_text = name.text.decode('utf8')
            if name_text == 'example' or not func_def:
                func_def = node
                
    for child in root.children:
        if child.type == 'function_definition':
            extract_func(child)
        elif child.type == 'decorated_definition':
            for d in child.children:
                if d.type == 'decorator':
                    decorators.append(d)
                elif d.type == 'function_definition':
                    extract_func(d)
        elif child.type == 'class_definition':
            name = _get_child_by_type(child, 'identifier')
            if name and name.text.decode('utf8') == 'Solution':
                body = _get_child_by_type(child, 'block')
                if body:
                    for m in body.children:
                        if m.type == 'function_definition':
                            m_name = _get_child_by_type(m, 'identifier')
                            if m_name and not m_name.text.decode('utf8').startswith('__'):
                                name_text = m_name.text.decode('utf8')
                                class_methods[name_text] = m
                                if not func_def:
                                    func_def = m
                                
    if not func_def:
        raise ValueError("No function definition found")
        
    ident_node = _get_child_by_type(func_def, 'identifier')
    func_name = ident_node.text.decode('utf8') if ident_node else "unknown"
    
    params = []
    string_vars = set()
    param_node = _get_child_by_type(func_def, 'parameters')
    
    if param_node:
        for p in param_node.children:
            if p.type == 'identifier':
                name = p.text.decode('utf8')
                if name != 'self':
                    params.append(name)
            elif p.type == 'typed_parameter':
                id_node = _get_child_by_type(p, 'identifier')
                type_node = _get_child_by_type(p, 'type')
                if id_node:
                    name = id_node.text.decode('utf8')
                    if name != 'self':
                        params.append(name)
                        if type_node and 'str' in type_node.text.decode('utf8'):
                            string_vars.add(name)
                
    dict_vars = set()
    string_literals = set()
    
    def pre_traverse(n):
        if not hasattr(n, 'type'): return
        
        if n.type == 'assignment':
            left = n.children[0]
            right = n.children[-1]
            if left.type == 'identifier':
                var_name = left.text.decode('utf8')
                if right.type in ('dictionary', 'set'):
                    dict_vars.add(var_name)
                elif right.type == 'call':
                    func = right.children[0]
                    if func.type == 'identifier' and func.text.decode('utf8') in ('set', 'dict'):
                        dict_vars.add(var_name)
                elif right.type == 'string':
                    string_vars.add(var_name)
                    
        if n.type == 'call':
            func = n.children[0]
            if func.type == 'attribute':
                obj = func.children[0]
                attr = func.children[2]
                if obj.type == 'identifier' and attr.type == 'identifier':
                    attr_name = attr.text.decode('utf8')
                    if attr_name in ('add', 'remove', 'discard'):
                        dict_vars.add(obj.text.decode('utf8'))
                        
        if n.type == 'string':
            for c in n.children:
                if c.type == 'string_content':
                    text = c.text.decode('utf8')
                    if 0 < len(text) < 10:
                        for char in text:
                            string_literals.add(char)
                            
        if hasattr(n, 'children'):
            for child in n.children:
                pre_traverse(child)
                
    pre_traverse(root)
    
    func_node = FunctionNode(name=func_name, args=params)
    accessed_attributes = set()
    func_node.accessed_attributes = accessed_attributes
    func_node.string_literals = string_literals
    
    is_memoized = False
    for dec in decorators:
        dec_text = dec.text.decode('utf8')
        if 'cache' in dec_text or 'memoize' in dec_text or 'lru_cache' in dec_text:
            is_memoized = True
            break
            
    if not is_memoized:
        is_memoized = check_memo(func_def, dict_vars) if func_def else False
        
    body = _get_child_by_type(func_def, 'block') if func_def else None
            
    from .inference import infer_signature
    func_node.inferred_signature = infer_signature(params, accessed_attributes, string_literals)
    
    if body:
        func_node.body = _traverse_block(body, body, params, accessed_attributes, dict_vars, False, string_vars, func_name, class_methods, [func_name])
        branch_factor, is_factorial, _, _ = get_recursive_calls(body, func_name)

        dp_dimension = len(params) if params else 1
        if branch_factor > 0:
            arg_red = _analyze_reduction_arg(body, func_name)
            func_node.body.append(RecursiveCallNode(branch_factor=branch_factor, is_memoized=is_memoized, arg_reduction=arg_red, is_factorial=is_factorial, dp_dimension=dp_dimension))
            
    return func_node

def _get_child_by_type(node, node_type):
    if not hasattr(node, 'children'):
        return None
    for child in node.children:
        if child.type == node_type:
            return child
    return None

def _traverse_block(block_node, enclosing_block_ts_node=None, params=None, accessed_attributes=None, dict_vars=None, in_loop=False, string_vars=None, current_func_name="unknown", class_methods=None, parse_stack=None) -> list[IRNode]:
    nodes = []
    if not params: params = []
    if not accessed_attributes: accessed_attributes = set()
    if not dict_vars: dict_vars = set()
    if not string_vars: string_vars = set()
    if class_methods is None: class_methods = {}
    if parse_stack is None: parse_stack = []
    
    if not hasattr(block_node, 'children'):
        return nodes
        
    for child in block_node.children:
        if child.type in ('for_statement', 'while_statement'):
            btype, bval = _detect_loop_bound_type(child, enclosing_block_ts_node, in_loop)
            loop = LoopNode(bound_type=btype, bound_value=bval)
            loop_body = _get_child_by_type(child, 'block')
            if loop_body:
                loop.body = _traverse_block(loop_body, loop_body, params, accessed_attributes, dict_vars, True, string_vars, current_func_name, class_methods, parse_stack)
            else:
                loop.body = _find_operations(child, params, accessed_attributes, dict_vars, string_vars, current_func_name, class_methods, parse_stack)
            nodes.append(loop)
        elif child.type == 'function_definition':
            inner_name = _get_child_by_type(child, 'identifier')
            inner_func_name = inner_name.text.decode('utf8') if inner_name else "unknown"
            
            inner_block = _get_child_by_type(child, 'block')
            if inner_block:
                inner_nodes = _traverse_block(inner_block, inner_block, params, accessed_attributes, dict_vars, False, string_vars, inner_func_name, class_methods, parse_stack + [inner_func_name])
                branch, is_fac, _, _ = get_recursive_calls(inner_block, inner_func_name)
                inner_memoized = check_memo(child, dict_vars)
                inner_params = []
                inner_params_node = _get_child_by_type(child, 'parameters')
                if inner_params_node:
                    for p in inner_params_node.children:
                        if p.type not in ('(', ')', ','):
                            inner_params.append(p.text.decode('utf8'))
                inner_dp_dimension = len(inner_params) if inner_params else 1
                
                if branch > 0:
                    inner_arg_red = _analyze_reduction_arg(inner_block, inner_func_name)
                    inner_nodes.append(RecursiveCallNode(branch_factor=branch, is_memoized=inner_memoized, arg_reduction=inner_arg_red, is_factorial=is_fac, dp_dimension=inner_dp_dimension))
                nodes.extend(inner_nodes)
        elif child.type in ('list_comprehension', 'set_comprehension', 'dictionary_comprehension', 'generator_expression'):
            loop = LoopNode(bound_type='linear', bound_value=None)
            loop.body = _traverse_block(child, child, params, accessed_attributes, dict_vars, True, string_vars, current_func_name, class_methods, parse_stack)
            nodes.append(loop)
        elif child.type == 'if_statement':
            branch_node = BranchNode(branches=[])
            cons = _get_child_by_type(child, 'block')
            if cons:
                branch_node.branches.append(_traverse_block(cons, enclosing_block_ts_node, params, accessed_attributes, dict_vars, in_loop, string_vars, current_func_name, class_methods, parse_stack))
            for sub_child in child.children:
                if sub_child.type in ('elif_clause', 'else_clause'):
                    alt = _get_child_by_type(sub_child, 'block')
                    if alt:
                        branch_node.branches.append(_traverse_block(alt, enclosing_block_ts_node, params, accessed_attributes, dict_vars, in_loop, string_vars, current_func_name, class_methods, parse_stack))
            nodes.append(branch_node)
            for sub_child in child.children:
                if sub_child.type not in ('block', 'elif_clause', 'else_clause'):
                    nodes.extend(_find_operations(sub_child, params, accessed_attributes, dict_vars, string_vars, current_func_name, class_methods, parse_stack))
        elif child.type in ('try_statement', 'with_statement', 'block', 'elif_clause', 'else_clause', 'except_clause', 'finally_clause'):
            nodes.extend(_traverse_block(child, enclosing_block_ts_node, params, accessed_attributes, dict_vars, in_loop, string_vars, current_func_name, class_methods, parse_stack))
        else:
            nodes.extend(_find_operations(child, params, accessed_attributes, dict_vars, string_vars, current_func_name, class_methods, parse_stack))
            
    return nodes

def _find_operations(node, params=None, accessed_attributes=None, dict_vars=None, string_vars=None, current_func_name="unknown", class_methods=None, parse_stack=None) -> list[IRNode]:
    nodes = []
    if params is None: params = []
    if accessed_attributes is None: accessed_attributes = set()
    if dict_vars is None: dict_vars = set()
    if string_vars is None: string_vars = set()
    if class_methods is None: class_methods = {}
    if parse_stack is None: parse_stack = []
    
    if not hasattr(node, 'type'):
        return nodes
        
    if node.type == 'augmented_assignment':
        if '+=' in node.text.decode('utf8'):
            left = node.children[0]
            if left.type == 'identifier':
                name = left.text.decode('utf8')
                if name in string_vars:
                    nodes.append(StringConcatNode())
                    
    if node.type == 'attribute':
        obj_node = node.children[0]
        attr_node = _get_child_by_type(node, 'identifier')
        if obj_node.type == 'identifier' and attr_node:
            obj_name = obj_node.text.decode('utf8')
            if obj_name in params:
                accessed_attributes.add(attr_node.text.decode('utf8'))
                
    if node.type == 'comparison_operator':
        for i, child in enumerate(node.children):
            if child.type == 'in':
                right_operand = node.children[i+1] if i+1 < len(node.children) else None
                is_dict = False
                if right_operand and right_operand.type == 'identifier':
                    if right_operand.text.decode('utf8') in dict_vars:
                        is_dict = True
                if not is_dict:
                    nodes.append(BuiltinCallNode(name='in', receiver_type='list'))
                
    elif node.type == 'call':
        func = node.children[0]
        if func.type == 'attribute':
            obj = func.children[0]
            attr = func.children[2]
            
            if obj.type == 'identifier' and attr.type == 'identifier':
                obj_name = obj.text.decode('utf8')
                attr_name = attr.text.decode('utf8')
                if obj_name == 'self' and attr_name in class_methods:
                    if attr_name == current_func_name:
                        pass # standard self-recursion, handled by branch_factor logic
                    elif attr_name in parse_stack:
                        # Mutual recursion fallback
                        nodes.append(RecursiveCallNode(branch_factor=1, dp_dimension=1))
                    else:
                        # Inline interprocedural helper!
                        target_ast = class_methods[attr_name]
                        target_block = _get_child_by_type(target_ast, 'block')
                        
                        t_params = []
                        t_param_node = _get_child_by_type(target_ast, 'parameters')
                        if t_param_node:
                            for p in t_param_node.children:
                                if p.type not in ('(', ')', ','):
                                    t_p_name = p.text.decode('utf8') if p.type == 'identifier' else _get_child_by_type(p, 'identifier').text.decode('utf8') if _get_child_by_type(p, 'identifier') else None
                                    if t_p_name and t_p_name != 'self':
                                        t_params.append(t_p_name)
                                        
                        if target_block:
                            parse_stack.append(attr_name)
                            inlined = _traverse_block(target_block, target_block, t_params, accessed_attributes, dict_vars, False, string_vars, attr_name, class_methods, parse_stack)
                            parse_stack.pop()
                            
                            branch, is_fac, _, _ = get_recursive_calls(target_block, attr_name)
                            if branch > 0:
                                t_dp_dim = len(t_params) if t_params else 1
                                arg_red = _analyze_reduction_arg(target_block, attr_name)
                                inlined.append(RecursiveCallNode(branch_factor=branch, is_memoized=False, arg_reduction=arg_red, is_factorial=is_fac, dp_dimension=t_dp_dim))
                            nodes.extend(inlined)
                            return nodes
                            
            attr_name = attr.text.decode('utf8')
            if attr_name == 'append':
                nodes.append(DataStructureOpNode(structure_type='list', op='append', position='back'))
            elif attr_name == 'pop':
                args_node = _get_child_by_type(node, 'argument_list')
                if args_node and '0' in args_node.text.decode('utf8'):
                    nodes.append(DataStructureOpNode(structure_type='list', op='pop', position='front'))
                else:
                    nodes.append(DataStructureOpNode(structure_type='list', op='pop', position='back'))
            elif attr_name in ('popleft', 'sort', 'split', 'join', 'replace', 'index', 'count'):
                nodes.append(BuiltinCallNode(name=attr_name))
            elif attr_name in ('heappush', 'heappop'):
                nodes.append(BuiltinCallNode(name=attr_name))
        elif func.type == 'identifier':
            func_name = func.text.decode('utf8')
            if func_name in ('min', 'max'):
                args_node = _get_child_by_type(node, 'argument_list')
                arg_count = 0
                if args_node:
                    arg_count = sum(1 for c in args_node.children if c.type not in ('(', ')', ',', 'comment'))
                if arg_count < 2:
                    nodes.append(BuiltinCallNode(name=func_name))
            elif func_name in ('sorted', 'sum', 'all', 'any', 'heappush', 'heappop', 'Counter', 'zip', 'map', 'filter', 'list', 'set', 'reversed'):
                args_node = _get_child_by_type(node, 'argument_list')
                arg_count = 0
                if args_node:
                    arg_count = sum(1 for c in args_node.children if c.type not in ('(', ')', ',', 'comment'))
                if arg_count >= 1:
                    nodes.append(BuiltinCallNode(name=func_name))

    if node.type in ('list_comprehension', 'set_comprehension', 'dictionary_comprehension', 'generator_expression'):
        loop = LoopNode(bound_type='linear', bound_value=None)
        loop.body = _traverse_block(node, node, params, accessed_attributes, dict_vars, True, string_vars, current_func_name, class_methods, parse_stack)
        nodes.append(loop)
        return nodes
                
    for child in node.children:
        nodes.extend(_find_operations(child, params, accessed_attributes, dict_vars, string_vars, current_func_name, class_methods, parse_stack))
        
    return nodes
