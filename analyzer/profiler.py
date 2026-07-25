import sys
import math
import random
from typing import Callable, Any, Dict, List, Tuple, Union

def gen_random_with_target(size):
    arr = [random.randint(1, 1000) for _ in range(size)]
    target = arr[random.randint(0, size-1)]
    return (arr, target)
    
def gen_random(size):
    return ([random.randint(1, 1000) for _ in range(size)],)
    
def gen_random_two_args(size):
    return ([random.randint(1, 1000) for _ in range(size)], [random.randint(1, 100) for _ in range(size)])

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def gen_binary_tree(size):
    if size == 0: return (None,)
    nodes = [TreeNode(i) for i in range(size)]
    for i in range(size):
        if 2*i + 1 < size: nodes[i].left = nodes[2*i + 1]
        if 2*i + 2 < size: nodes[i].right = nodes[2*i + 2]
    return (nodes[0],)

def gen_linked_list(size):
    if size == 0: return (None,)
    head = ListNode(0)
    curr = head
    for i in range(1, size):
        curr.next = ListNode(i)
        curr = curr.next
    return (head,)

def gen_graph_adj_list(size):
    graph = {i: [] for i in range(size)}
    if size > 1:
        for i in range(size - 1):
            graph[i].append(i + 1)
            graph[i + 1].append(i)
        for _ in range(size // 2):
            u = random.randint(0, size - 1)
            v = random.randint(0, size - 1)
            if u != v and v not in graph[u]:
                graph[u].append(v)
                graph[v].append(u)
    return (graph,)

def gen_matrix(size):
    side = size
    if side == 0: side = 1
    mat = [[random.randint(1, 100) for _ in range(side)] for _ in range(side)]
    return (mat,)

generators = {
    'random': gen_random,
    'target_at_start': lambda size: ([42] + [random.randint(1, 1000) for _ in range(size-1)], 42),
    'random_with_target': gen_random_with_target,
    'target_absent': lambda size: ([random.randint(1, 1000) for _ in range(size)], -1),
    'fib_arg': lambda size: (size,),
    'binary_tree': gen_binary_tree,
    'linked_list': gen_linked_list,
    'graph_adj_list': gen_graph_adj_list,
    'matrix': gen_matrix
}

def get_generator_for_type(type_name: str | dict, size: int) -> Any:
    alphabet = None
    if isinstance(type_name, dict):
        alphabet = type_name.get('alphabet')
        type_name = type_name.get('type')
        
    type_name = type_name.lower()
    if type_name == 'scalar_int':
        return random.randint(1, 1000)
    elif type_name == 'size_int':
        return size
    elif type_name == 'scalar_float':
        return random.uniform(1.0, 1000.0)
    elif type_name == 'scalar_string':
        if alphabet:
            return "".join(random.choice(alphabet) for _ in range(size))
        # Mirror String Profile for Palindrome tests (worst-case O(N))
        half = size // 2
        chars = [chr(random.randint(97, 122)) for _ in range(half)]
        s = "".join(chars)
        return s + s[::-1][:size - half]
    elif type_name == 'scalar_bool':
        return True
    elif type_name in ('1d_array_random', 'random'):
        return random.sample(range(1, max(1000, size * 10)), size)
    elif type_name == '1d_array_sorted':
        return sorted(random.sample(range(1, max(1000, size * 10)), size))
    elif type_name == '1d_array_reverse':
        return sorted(random.sample(range(1, max(1000, size * 10)), size), reverse=True)
    elif type_name == '1d_string_array':
        return [f"word{i}" for i in range(size)]
    elif type_name in ('2d_matrix', 'matrix'):
        return gen_matrix(size)[0]
    elif type_name in ('linked_list_singly', 'linked_list'):
        return gen_linked_list(size)[0]
    elif type_name == 'linked_list_doubly':
        return gen_linked_list(size)[0] # approx for MVP
    elif type_name == 'linked_list_cyclic':
        head = gen_linked_list(size)[0]
        if head:
            tail = head
            while tail.next: tail = tail.next
            tail.next = head
        return head
    elif type_name in ('binary_tree_balanced', 'binary_tree'):
        return gen_binary_tree(size)[0]
    elif type_name == 'binary_tree_skewed':
        head = TreeNode(0)
        curr = head
        for i in range(1, size):
            curr.left = TreeNode(i)
            curr = curr.left
        return head
    elif type_name == 'binary_search_tree':
        def build_bst(arr):
            if not arr: return None
            mid = len(arr) // 2
            root = TreeNode(arr[mid])
            root.left = build_bst(arr[:mid])
            root.right = build_bst(arr[mid+1:])
            return root
        return build_bst(list(range(size)))
    elif type_name == 'graph_adj_list':
        return gen_graph_adj_list(size)[0]
    elif type_name == 'graph_edges':
        if size == 0: return []
        return [[random.randint(0, size - 1), random.randint(0, size - 1)] for _ in range(size)]
    elif type_name == 'graph_adj_matrix':
        return gen_matrix(size)[0]
    else:
        return random.sample(range(1, max(1000, size * 10)), size)

def gen_multi_args(signature: dict, size: int) -> tuple:
    args = []
    for param_name, type_name in signature.items():
        args.append(get_generator_for_type(type_name, size))
    return tuple(args)

def count_operations(func: Callable, args: tuple) -> int:
    op_count = [0]
    
    target_code = getattr(func, '__wrapped__', func).__code__
    target_file = target_code.co_filename
    
    def trace_calls(frame, event, arg):
        if event == 'line':
            # Count lines inside any function defined in the same file (handles nested functions)
            if frame.f_code.co_filename == target_file:
                op_count[0] += 1
                if op_count[0] > 1000000:
                    raise RuntimeError("Watchdog timeout")
        return trace_calls

    sys.settrace(trace_calls)
    try:
        func(*args)
    finally:
        sys.settrace(None)
        
    return op_count[0]

def linear_regression(x: List[float], y: List[float]) -> Tuple[float, float, float]:
    """Returns (m, c, R^2) for y = mx + c"""
    n = len(x)
    if n == 0: return 0, 0, 0
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
    
    if denominator == 0:
        return 0, mean_y, 0
        
    m = numerator / denominator
    c = mean_y - m * mean_x
    
    ss_tot = sum((y[i] - mean_y) ** 2 for i in range(n))
    ss_res = sum((y[i] - (m * x[i] + c)) ** 2 for i in range(n))
    
    if ss_tot == 0:
        return m, c, 1.0 # perfectly flat
        
    r_squared = 1 - (ss_res / ss_tot)
    return m, c, r_squared

def fit_curves(N_values: List[int], op_counts: List[int]) -> Dict[str, Any]:
    mean_y = sum(op_counts) / len(op_counts)
    variance_y = sum((y - mean_y)**2 for y in op_counts)
    
    if variance_y < 1e-5:
        return {"fit": "O(1)", "r2": 1.0, "margin": 1.0}

    # Candidate curves
    candidates = [
        ("O(1)", lambda n: 1),
        ("O(log n)", lambda n: math.log(n) if n > 0 else 0),
        ("O(n)", lambda n: n),
        ("O(n log n)", lambda n: n * math.log(n) if n > 0 else 0),
        ("O(n^2)", lambda n: n * n),
        ("O(2^n)", lambda n: 2**n)
    ]
    
    best_fit = None
    best_r2 = -float('inf')
    runner_up_r2 = -float('inf')
    
    for name, func in candidates:
        try:
            x_vals = [func(n) for n in N_values]
            m, c, r2 = linear_regression(x_vals, op_counts)
        except OverflowError:
            continue
        
        # Reject inverted fits where operations decrease as size increases (unless it's O(1))
        if m < -1e-5 and name != "O(1)":
             continue
             
        # Add a penalty threshold so we prefer simpler models unless a more complex one is significantly better
        if r2 > best_r2 + 0.02:
            runner_up_r2 = best_r2
            best_r2 = r2
            best_fit = name
        elif r2 <= best_r2 and r2 > runner_up_r2:
            runner_up_r2 = r2
            
    margin = best_r2 - runner_up_r2 if runner_up_r2 != -float('inf') else 1.0
    return {"fit": best_fit, "r2": best_r2, "margin": margin}

def profile_function(func_or_code: Union[Callable, str], generator_name: str | dict = 'random', language: str = 'python', func_name: str = 'example') -> Dict[str, Any]:
    N_values = [10, 50, 100, 200, 400]
    if 'fib' in generator_name or 'small' in generator_name:
        N_values = [5, 10, 15, 20, 25]
        
    op_counts = []
    
    if language == 'javascript':
        from .sandbox_js import execute_js_benchmark
        if not ('fib' in generator_name or 'small' in generator_name):
            N_values = [1000, 2000, 4000, 8000, 16000]
            
        for n in N_values:
            try:
                count = execute_js_benchmark(func_or_code, generator_name, n, trials=100, func_name=func_name)
                op_counts.append(count)
            except RuntimeError as e:
                if "Watchdog" in str(e):
                    return {"fit": "O(2^n)", "r2": 1.0, "margin": 1.0}
                raise
    else:
        from .sandbox_py import execute_py_benchmark
        for n in N_values:
            try:
                count = execute_py_benchmark(func_or_code, generator_name, n, trials=10, func_name=func_name)
                op_counts.append(count)
            except RuntimeError as e:
                if "Watchdog" in str(e):
                    return {"fit": "O(2^n)", "r2": 1.0, "margin": 1.0}
                raise
                
    return fit_curves(N_values, op_counts)
