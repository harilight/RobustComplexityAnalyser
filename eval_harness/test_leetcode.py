import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analyzer.parser import parse_python
from analyzer.parser_js import parse_javascript
from analyzer.static import analyze_complexity

def assert_complexity(code, expected, lang='python'):
    if lang == 'python':
        func_node = parse_python(code)
    else:
        func_node = parse_javascript(code)
        
    res = analyze_complexity(func_node)
    got = res['complexity']
    if got == expected:
        print(f"  [PASS] Expected: {expected} | Got: {got}")
        return True
    else:
        print(f"  [FAIL] Expected: {expected} | Got: {got}")
        return False

print("=== Basic Loop & Mathematical Bounds ===")
# Linear Loop
assert_complexity('''
def linear(arr):
    for x in arr:
        pass
''', 'O(n)')

# Nested Quadratic Loop
assert_complexity('''
def quadratic(arr):
    for i in arr:
        for j in arr:
            pass
''', 'O(n^2)')

# Independent Variable Nested Loops - O(n * m)
assert_complexity('''
def two_arrays(arr1, arr2):
    for i in arr1:
        for j in arr2:
            pass
''', 'O(n * m)')

# Matrix Traversal
assert_complexity('''
def matrix(rows, cols):
    for i in range(len(rows)):
        for j in range(len(cols)):
            pass
''', 'O(n * m)')

# Logarithmic Loop
assert_complexity('''
def log_loop(n):
    while n > 1:
        n //= 2
''', 'O(log n)')

# Sequential Loops
assert_complexity('''
def sequential(arr1, arr2):
    for i in arr1:
        pass
    for j in arr2:
        pass
''', 'O(n + m)')

print("\\n=== Branching & Control Flow ===")
# Branch with O(n) vs O(n^2)
assert_complexity('''
def branches(arr):
    if len(arr) > 10:
        for x in arr: pass
    else:
        for x in arr:
            for y in arr: pass
''', 'O(n^2)')

print("\\n=== Recursion & DP ===")
# Binary Search
assert_complexity('''
def binary_search(arr, target):
    def helper(lo, hi):
        if lo > hi: return -1
        mid = (lo + hi) // 2
        if arr[mid] == target: return mid
        elif arr[mid] < target: return helper(mid + 1, hi)
        else: return helper(lo, mid - 1)
    return helper(0, len(arr) - 1)
''', 'O(log n)')

# Merge Sort
assert_complexity('''
def merge_sort(arr):
    if len(arr) <= 1: return arr
    mid = len(arr) // 2
    return merge(merge_sort(arr[:mid]), merge_sort(arr[mid:]))
''', 'O(n log n)')

# Memoized DP
assert_complexity('''
def fib(n, memo=None):
    if memo is None: memo = {}
    if n in memo: return memo[n]
    if n <= 1: return n
    memo[n] = fib(n-1, memo) + fib(n-2, memo)
    return memo[n]
''', 'O(n)')

print("\\n=== Hidden Builtin Complexity ===")
# list.pop(0)
assert_complexity('''
def pop_zero(arr):
    for i in range(len(arr)):
        arr.pop(0)
''', 'O(n^2)')

# set.add
assert_complexity('''
def set_add(arr):
    s = set()
    for x in arr:
        s.add(x)
''', 'O(n)')

print("\\n=== JavaScript Verification ===")
assert_complexity('''
function matrixJS(rows, cols) {
    for (let i = 0; i < rows.length; i++) {
        for (let j = 0; j < cols.length; j++) {
            // do something
        }
    }
}
''', 'O(n * m)', 'js')

assert_complexity('''
function shiftLoop(arr) {
    while (arr.length > 0) {
        arr.shift();
    }
}
''', 'O(n^2)', 'js')

assert_complexity('''
function sequentialJS(arr1, arr2) {
    for (let x of arr1) {}
    for (let y of arr2) {}
}
''', 'O(n + m)', 'js')
