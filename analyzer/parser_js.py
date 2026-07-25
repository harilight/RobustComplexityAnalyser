from tree_sitter import Language, Parser
import tree_sitter_javascript as tsjavascript
from .ir import FunctionNode, LoopNode, BuiltinCallNode, DataStructureOpNode, IRNode

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

def _traverse_block(block_node) -> list[IRNode]:
    nodes = []
    
    if not hasattr(block_node, 'children'):
        return nodes
        
    for child in block_node.children:
        if child.type in ('for_statement', 'while_statement', 'for_in_statement', 'for_of_statement'):
            loop = LoopNode(bound_type='linear')
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
                    
                elif prop in ('includes', 'indexOf'):
                    receiver = func.children[0]
                    nodes.extend(_find_operations(receiver))
                    
                    nodes.append(BuiltinCallNode(name='includes', receiver_type='array'))
                    return nodes
                    
    for child in node.children:
         nodes.extend(_find_operations(child))
         
    return nodes
