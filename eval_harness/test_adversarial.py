import sys
import traceback
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.parser import parse_python
from analyzer.parser_js import parse_javascript
from analyzer.static import analyze_complexity

def test_algo(name, code, expected_complexity, lang='py'):
    try:
        if lang == 'py':
            node = parse_python(code)
        else:
            node = parse_javascript(code)
        res = analyze_complexity(node)
        got = res['complexity']
        if name == 'DFS adjacency list':
            print("DFS DFS DFS -> ", res)
        if got == expected_complexity:
            print(f"  [PASS] {name} | Expected: {expected_complexity} | Got: {got}")
            return True
        else:
            print(f"  [FAIL] {name} | Expected: {expected_complexity} | Got: {got}")
            return False
    except Exception as e:
        print(f"  [ERROR] {name} | Expected: {expected_complexity} | Exception: {e}")
        return False

print("=== Adversarial Priority Tests ===")

# 1. Standard adjacency-list BFS -> O(V + E) -> mapped to O(n + m) internally
test_algo('Standard adjacency-list BFS', '''
from collections import deque
def bfs(graph, start):
    queue = deque([start])
    visited = {start}
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
''', 'O(n + m)')

# 2. BFS using list.pop(0) -> O(V^2 + E)
test_algo('BFS using list.pop(0)', '''
def bfs(graph, start):
    queue = [start]
    visited = {start}
    while queue:
        node = queue.pop(0)
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
''', 'O(n^2 + m)')

# 3. BFS without visited set -> exponential / unbounded (O(2^n) or O(n^n), we expect it not to be O(n + m))
# I will check if it equals O(n + m) and fail if it does.
# For now, let's see what it outputs.
test_algo('BFS without visited set', '''
def bfs(graph, start):
    queue = [start]
    while queue:
        node = queue.pop(0)
        for neighbor in graph[node]:
            queue.append(neighbor)
''', 'O(2^n)') # Adjust expected later, just checking baseline

# 4. DFS adjacency list -> O(V + E)
test_algo('DFS adjacency list', '''
def dfs(graph, node, visited):
    if node in visited:
        return
    visited.add(node)
    for neighbor in graph[node]:
        dfs(graph, neighbor, visited)
''', 'O(n + m)')

# 5. Two-pointer with pointer reset -> O(n^2)
test_algo('Two-pointer with pointer reset', '''
def f(n):
    j = 0
    for i in range(n):
        j = 0
        while j < n:
            j += 1
''', 'O(n^2)')

# 6. Monotonic stack -> O(n)
test_algo('Monotonic stack', '''
def f(arr):
    stack = []
    for x in arr:
        while stack and stack[-1] < x:
            stack.pop()
        stack.append(x)
''', 'O(n)')

# 7. Function call inside a loop -> composition -> O(n^2)
test_algo('Function call inside a loop', '''
def helper(arr):
    for x in arr:
        pass

def main(arr):
    for x in arr:
        helper(arr)
''', 'O(n^2)')

# 8. Recursive helper function -> O(n)
test_algo('Recursive helper function', '''
def solve(n):
    def helper(x):
        if x <= 1: return
        helper(x - 1)
    helper(n)
''', 'O(n)')

# 9. Mutual recursion -> O(n)
test_algo('Mutual recursion', '''
def even(n):
    if n == 0: return True
    return odd(n - 1)
def odd(n):
    if n == 0: return False
    return even(n - 1)
''', 'O(n)')

# 10. 2T(n/2) + O(n^2) -> O(n^2)
test_algo('2T(n/2) + O(n^2)', '''
def f(n):
    if n <= 1: return
    for i in range(n):
        for j in range(n):
            pass
    f(n // 2)
    f(n // 2)
''', 'O(n^2)')

# 11. Variable-sized slicing inside a loop -> O(n^2)
test_algo('Variable-sized slicing inside a loop', '''
def f(arr):
    for i in range(len(arr)):
        x = arr[:i]
''', 'O(n^2)')

# 12. Constant-sized slicing inside a loop -> O(n)
test_algo('Constant-sized slicing inside a loop', '''
def f(arr):
    n = len(arr)
    for i in range(n):
        x = arr[i:i + 10]
''', 'O(n)')

# 13. Memoized vs non-memoized Fibonacci
test_algo('Memoized DP hidden in class', '''
class Solver:
    def __init__(self):
        self.memo = {}
    def solve(self, n):
        if n in self.memo: return self.memo[n]
        if n <= 1: return n
        self.memo[n] = self.solve(n-1) + self.solve(n-2)
        return self.memo[n]
''', 'O(n)')

# 14. Matrix BFS -> O(V^2) -> O(n^2)
test_algo('Matrix BFS', '''
def bfs(matrix, start):
    queue = [start]
    visited = set()
    while queue:
        node = queue.pop(0)
        for neighbor in range(len(matrix)):
            if matrix[node][neighbor] == 1:
                pass
''', 'O(n^2)')

# 15. Graph traversal with duplicate enqueue
test_algo('Graph traversal with duplicate enqueue', '''
def process(graph, start):
    queue = [start]
    while queue:
        node = queue.pop(0)
        for neighbor in graph[node]:
            queue.append(neighbor)
''', 'O(2^n)') # Adjust expected later
