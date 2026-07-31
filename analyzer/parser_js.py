from tree_sitter import Language, Parser
import tree_sitter_javascript as tsjavascript
from .ir import FunctionNode, LoopNode, BuiltinCallNode, DataStructureOpNode, IRNode
import re

_LOG_BOUND_RE = re.compile(r'//=\s*2|/=\s*2|>>=\s*1|>>\s*1|\/\s*2|\*\s*0\.5|\*=\s*2|<<=\s*1|<<\s*1|\*\s*2')

JS_LANGUAGE = Language(tsjavascript.language())
parser = Parser(JS_LANGUAGE)

HOFS = {'map', 'filter', 'forEach', 'reduce', 'some', 'every', 'find'}

def parse_javascript(code: str) -> FunctionNode:
    tree = parser.parse(bytes(code, "utf8"))
    root = tree.root_node
    
    # Find the first function_declaration
    func_def = None
    for child in root.children:
        if child.type == 'function_declaration':
            func_def = child
            break
            
    if not func_def:
        raise ValueError("No function declaration found")
        
    ident_node = _get_child_by_type(func_def, 'identifier')
    func_name = ident_node.text.decode('utf8') if ident_node else "unknown"
    func_node = FunctionNode(name=func_name, args=[])
    
    body = _get_child_by_type(func_def, 'statement_block')
    if body:
        func_node.body = _traverse_block(body)
        
    return func_node

def _get_child_by_type(node, node_type):
    if not hasattr(node, 'children'):
        return None
    for child in node.children:
        if child.type == node_type:
            return child
    return None

def _detect_loop_bound_type(loop_ts_node) -> str:
    if loop_ts_node.type == 'for_statement':
        condition_node = None
        update_node = None
        for c in loop_ts_node.children:
            if c.type in ('binary_expression', 'expression_statement'):
                if c.type == 'binary_expression' and not condition_node:
                    condition_node = c
            elif c.type in ('update_expression', 'augmented_assignment_expression'):
                update_node = c
                
        if condition_node:
            cond_text = condition_node.text.decode('utf8')
            if re.search(r'\b([a-zA-Z_]\w*)\s*\*\s*\1\s*<=', cond_text) or re.search(r'\b([a-zA-Z_]\w*)\s*\*\*\s*2\s*<=', cond_text):
                return 'sqrt'
                
        if update_node:
            update_text = update_node.text.decode('utf8')
            if _LOG_BOUND_RE.search(update_text):
                return 'log'
                
    elif loop_ts_node.type == 'while_statement':
        paren_expr = _get_child_by_type(loop_ts_node, 'parenthesized_expression')
        if paren_expr:
            cond_text = paren_expr.text.decode('utf8')
            if re.search(r'\b([a-zA-Z_]\w*)\s*\*\s*\1\s*<=', cond_text) or re.search(r'\b([a-zA-Z_]\w*)\s*\*\*\s*2\s*<=', cond_text):
                return 'sqrt'
                
        block = _get_child_by_type(loop_ts_node, 'statement_block')
        if block:
            assignments = []
            def collect(n):
                if not hasattr(n, 'type'): return
                if n.type in ('for_statement', 'while_statement', 'for_in_statement', 'for_of_statement'): return
                if n.type in ('assignment_expression', 'augmented_assignment_expression', 'update_expression'):
                    assignments.append(n.text.decode('utf8'))
                for c in getattr(n, 'children', []):
                    collect(c)
            collect(block)
            
            for text in assignments:
                if _LOG_BOUND_RE.search(text):
                    return 'log'
                    
    return 'linear'

def _traverse_block(block_node) -> list[IRNode]:
    nodes = []
    
    if not hasattr(block_node, 'children'):
        return nodes
        
    for child in block_node.children:
        if child.type in ('for_statement', 'while_statement', 'for_in_statement', 'for_of_statement'):
            btype = _detect_loop_bound_type(child)
            loop = LoopNode(bound_type=btype)
            loop_body = _get_child_by_type(child, 'statement_block')
            if loop_body:
                loop.body = _traverse_block(loop_body)
            else:
                loop.body = _find_operations(child)
            nodes.append(loop)
        else:
            nodes.extend(_find_operations(child))
            
    return nodes

def _find_operations(node) -> list[IRNode]:
    nodes = []
    
    if not hasattr(node, 'type'):
        return nodes
        
    if node.type == 'call_expression':
        func = node.children[0]
        if func.type == 'member_expression':
            prop_node = _get_child_by_type(func, 'property_identifier')
            if prop_node:
                prop = prop_node.text.decode('utf8')
                if prop in HOFS:
                    # Evaluate receiver first for chaining
                    receiver = func.children[0]
                    nodes.extend(_find_operations(receiver))
                    
                    # Synthetic Loop for HOF
                    loop = LoopNode(bound_type='linear')
                    
                    args_node = _get_child_by_type(node, 'arguments')
                    if args_node and len(args_node.children) > 1:
                        for arg_child in args_node.children:
                            if arg_child.type in ('arrow_function', 'function_expression'):
                                body = arg_child.children[-1]
                                if body.type == 'statement_block':
                                    loop.body = _traverse_block(body)
                                else:
                                    loop.body = _find_operations(body)
                                break
                    nodes.append(loop)
                    return nodes
                    
                elif prop == 'shift':
                    nodes.append(DataStructureOpNode(structure_type='list', op='pop', position='front'))
                elif prop == 'unshift':
                    nodes.append(DataStructureOpNode(structure_type='list', op='insert', position='front'))
                elif prop == 'push':
                    nodes.append(DataStructureOpNode(structure_type='list', op='append', position='back'))
                elif prop == 'pop':
                    nodes.append(DataStructureOpNode(structure_type='list', op='pop', position='back'))
                elif prop in ('includes', 'indexOf', 'lastIndexOf'):
                    receiver = func.children[0]
                    nodes.extend(_find_operations(receiver))
                    nodes.append(BuiltinCallNode(name='includes', receiver_type='array'))
                    return nodes
                elif prop in ('splice', 'slice', 'concat', 'join', 'split', 'replace', 'sort', 'reverse'):
                    nodes.append(BuiltinCallNode(name=prop, receiver_type='array'))
                    
            # Check Object.keys/values
            obj_node = func.children[0]
            if obj_node.type == 'identifier' and obj_node.text.decode('utf8') == 'Object':
                if prop_node and prop_node.text.decode('utf8') in ('keys', 'values', 'entries'):
                    nodes.append(BuiltinCallNode(name='keys', receiver_type='object'))
                    
    for child in node.children:
         nodes.extend(_find_operations(child))
         
    return nodes
