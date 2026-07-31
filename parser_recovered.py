from tree_sitter import Language, Parser
import tree_sitter_python as tspython
from .ir import FunctionNode, LoopNode, BuiltinCallNode, DataStructureOpNode, IRNode, RecursiveCallNode

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

def get_recursive_calls(node, func_name: str) -> int:
    if node is None: return 0
    if node.type == 'call':
        func = node.children[0]
        if func.type == 'identifier' and func.text.decode('utf8') == func_name:
            return 1 + sum(get_recursive_calls(c, func_name) for c in node.children)
            
    if node.type in ('for_statement', 'while_statement'):
        return sum(get_recursive_calls(c, func_name) for c in node.children) * 2
    
    if node.type == 'if_statement':
        cons = _get_child_by_type(node, 'block')
        
        alt_calls = 0
        for c in node.children:
             if c.type == 'elif_clause' or c.type == 'else_clause':
                  b = _get_child_by_type(c, 'block')
                  if b:
                      alt_calls = max(alt_calls, get_recursive_calls(b, func_name))
        
        c_calls = get_recursive_calls(cons, func_name) if cons else 0
        
        cond_calls = 0
        for c in node.children:
            if c.type not in ('block', 'elif_clause', 'else_clause'):
                cond_calls += get_recursive_calls(c, func_name)
                
        return cond_calls + max(c_calls, alt_calls)
        
    return sum(get_recursive_calls(c, func_name) for c in node.children)

def parse_python(code: str) -> FunctionNode:
    tree = parser.parse(bytes(code, "utf8"))
    root = tree.root_node
    
    func_def = None
    decorators = []
    
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
                                func_def = m
                                break
                                
    if not func_def:
        raise ValueError("No function definition found")
        
    ident_node = _get_child_by_type(func_def, 'identifier')
    func_name = ident_node.text.decode('utf8') if ident_node else "unknown"
    
    # Extract parameters
    params = []
    param_node = _get_child_by_type(func_def, 'parameters')
    if param_node:
        for p in param_node.children:
            if p.type == 'identifier':
                params.append(p.text.decode('utf8'))
            elif p.type == 'typed_parameter':
                id_node = _get_child_by_type(p, 'identifier')
                if id_node: params.append(id_node.text.decode('utf8'))
                
    dict_vars = set()
    string_literals = set()
    
    def pre_traverse(n):
        if not hasattr(n, 'type'): return
        
        if n.type == 'assignment':
            left = n.children[0]
            right = n.children[-1]
            if left.type == 'identifier' and right.type in ('dictionary', 'set'):
                dict_vars.add(left.text.decode('utf8'))
                
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
    
    # We will track attributes accessed on these parameters
    accessed_attributes = set()
    func_node.accessed_attributes = accessed_attributes
    func_node.string_literals = string_literals
    
    is_memoized = False
    for dec in decorators:
        dec_text = dec.text.decode('utf8')
        if 'cache' in dec_text or 'memoize' in dec_text:
            is_memoized = True
            break
            
    from .inference import infer_signature
    func_node.inferred_signature = infer_signature(params, accessed_attributes, string_literals)
    
    body = _get_child_by_type(func_def, 'block')
    if body:
        func_node.body = _traverse_block(body, params, accessed_attributes, dict_vars)
        
        branch_factor = get_recursive_calls(body, func_name)
        if branch_factor > 0:
            func_node.body.append(RecursiveCallNode(branch_factor=branch_factor, is_memoized=is_memoized))
            
    return func_node

def _get_child_by_type(node, node_type):
    if not hasattr(node, 'children'):
        return None
    for child in node.children:
        if child.type == node_type:
            return child
    return None

def _traverse_block(block_node, params=None, accessed_attributes=None, dict_vars=None) -> list[IRNode]:
    nodes = []
    if not params: params = []
    if not accessed_attributes: accessed_attributes = set()
    if not dict_vars: dict_vars = set()
    
    if not hasattr(block_node, 'children'):
        return nodes
        
    for child in block_node.children:
        if child.type in ('for_statement', 'while_statement'):
            loop = LoopNode(bound_type='linear')
            loop_body = _get_child_by_type(child, 'block')
            if loop_body:
                loop.body = _traverse_block(loop_body, params, accessed_attributes, dict_vars)
            else:
                loop.body = _find_operations(child, params, accessed_attributes, dict_vars)
            nodes.append(loop)
        elif child.type == 'function_definition':
            inner_name = _get_child_by_type(child, 'identifier')
            inner_func_name = inner_name.text.decode('utf8') if inner_name else "unknown"
            
            inner_block = _get_child_by_type(child, 'block')
            if inner_block:
                inner_nodes = _traverse_block(inner_block, params, accessed_attributes, dict_vars)
                branch = get_recursive_calls(inner_block, inner_func_name)
                if branch > 0:
                    inner_nodes.append(RecursiveCallNode(branch_factor=branch, is_memoized=False))
                nodes.extend(inner_nodes)
        elif child.type in ('if_statement', 'try_statement', 'with_statement', 'block', 'elif_clause', 'else_clause', 'except_clause', 'finally_clause'):
            nodes.extend(_traverse_block(child, params, accessed_attributes, dict_vars))
        else:
            # Recursively find calls and data structure ops in other statements
            nodes.extend(_find_operations(child, params, accessed_attributes, dict_vars))
            
    return nodes

def _find_operations(node, params=None, accessed_attributes=None, dict_vars=None) -> list[IRNode]:
    nodes = []
    if params is None: params = []
    if accessed_attributes is None: accessed_attributes = set()
    if dict_vars is None: dict_vars = set()
    
    if not hasattr(node, 'type'):
        return nodes
        
    # Attribute Tracking
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
            attr_name = func.children[2].text.decode('utf8')
            if attr_name == 'append':
                nodes.append(DataStructureOpNode(structure_type='list', op='append', position='back'))
            elif attr_name == 'pop':
                args = _get_child_by_type(node, 'argument_list')
                is_front = False
                if args:
                    for arg in args.children:
                        if arg.type == 'integer' and arg.text.decode('utf8') == '0':
                            is_front = True
                receiver_name = func.children[0].text.decode('utf8') if func.children[0].type == 'identifier' else None
                nodes.append(DataStructureOpNode(structure_type='list', op='pop', position=receiver_name if is_front else 'back'))
            elif attr_name in ('popleft', 'sort', 'split', 'join', 'replace'):
                nodes.append(BuiltinCallNode(name=attr_name))
        elif func.type == 'identifier':
            func_name = func.text.decode('utf8')
            if func_name in ('sorted', 'min', 'max', 'sum', 'all', 'any', 'heappush', 'heappop'):
                nodes.append(BuiltinCallNode(name=func_name))
                
    for child in node.children:
        nodes.extend(_find_operations(child, params, accessed_attributes, dict_vars))
        
    return nodes
