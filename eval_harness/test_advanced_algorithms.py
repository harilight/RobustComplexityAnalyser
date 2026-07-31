import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analyzer.parser import parse_python
from analyzer.parser_js import parse_javascript
from analyzer.static import analyze_complexity

def test_algo(name, code, expected, lang='python'):
    try:
        if lang == 'python':
            func_node = parse_python(code)
        else:
            func_node = parse_javascript(code)
            
        res = analyze_complexity(func_node)
        got = res['complexity']
        if got == expected:
            print(f"  [PASS] {name} | Expected: {expected} | Got: {got}")
            return True
        else:
            print(f"  [FAIL] {name} | Expected: {expected} | Got: {got}")
            return False
    except Exception as e:
        print(f"  [ERROR] {name} | {e}")
        return False

print("=== Advanced Algorithmic Patterns ===")

# Valid Parentheses (O(n))
test_algo('Valid Parentheses', '''
def isValid(s: str) -> bool:
    stack = []
    mapping = {")": "(", "}": "{", "]": "["}
    for char in s:
        if char in mapping:
            top_element = stack.pop() if stack else '#'
            if mapping[char] != top_element:
                return False
        else:
            stack.append(char)
    return not stack
''', 'O(n)')

# Nested loops with shared pointer -> O(n)
test_algo('Two Pointer / Shared Pointer', '''
def two_pointer(arr):
    j = 0
    for i in range(len(arr)):
        while j < len(arr) and arr[j] < arr[i]:
            j += 1
''', 'O(n)')

# T(n) = 2T(n/2) -> O(n)
test_algo('Tree Traversal 2T(n/2) O(1) work', '''
def build_tree(lo, hi):
    if lo > hi: return None
    mid = (lo + hi) // 2
    left = build_tree(lo, mid - 1)
    right = build_tree(mid + 1, hi)
    return left + right
''', 'O(n)')

# T(n) = 2T(n-1) -> O(2^n)
test_algo('Naive Fib 2T(n-1)', '''
def fib(n):
    if n <= 1: return n
    return fib(n-1) + fib(n-2)
''', 'O(2^n)')

# Harmonic loop -> O(n log n)
test_algo('Harmonic Loop', '''
def harmonic(n):
    for i in range(1, n):
        for j in range(i, n, i):
            pass
''', 'O(n log n)')

# Subsets -> O(n * 2^n) or O(2^n)
test_algo('Subsets (Backtracking)', '''
def subsets(nums):
    res = []
    def backtrack(start, path):
        res.append(path)
        for i in range(start, len(nums)):
            backtrack(i + 1, path + [nums[i]])
    backtrack(0, [])
    return res
''', 'O(2^n)')

# Slicing inside a loop -> O(n^2)
test_algo('Slicing inside loop', '''
def slicing_loop(arr):
    for i in range(len(arr)):
        sub = arr[i:]
''', 'O(n^2)')

# Graph BFS -> O(V^2 + E) because of pop(0)
test_algo('Graph BFS', '''
def bfs(graph, start):
    visited = set([start])
    queue = [start]
    while queue:
        node = queue.pop(0)
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
''', 'O(n^2 + m)') # Mathematically accurate due to list.pop(0)

