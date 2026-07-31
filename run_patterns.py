import re
from analyzer.parser import parse_python, _detect_loop_bound_type, _get_child_by_type
import analyzer.parser as parser

original_detect = parser._detect_loop_bound_type

def patched_detect(loop_ts_node, enclosing_block_ts_node=None, is_inner_loop=False):
    res = original_detect(loop_ts_node, enclosing_block_ts_node, is_inner_loop)
    if res[0] != 'linear':
        return res
        
    condition_node = None
    if loop_ts_node.type == 'while_statement':
        condition_node = loop_ts_node.children[1]
    elif loop_ts_node.type == 'for_statement':
        condition_node = loop_ts_node.children[3]
    
    if condition_node is None: return res
    cond_vars = parser._get_identifiers(condition_node)
    
    block = _get_child_by_type(loop_ts_node, 'block')
    if enclosing_block_ts_node and is_inner_loop:
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
                
    return res

parser._detect_loop_bound_type = patched_detect

codes = {
    "monotonic_stack": """
def monotonic_stack(arr):
    stack = []
    res = []
    for x in arr:
        while stack and stack[-1] < x:
            stack.pop()
        res.append(x)
        stack.append(x)
    return res
"""
}

from analyzer.static import analyze_complexity
for name, code in codes.items():
    node = parse_python(code)
    print(f"{name}:", analyze_complexity(node))

