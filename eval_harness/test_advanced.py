import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.parser import parse_python
from analyzer.static import analyze_complexity

tests = [
    {
        "id": "binary_search",
        "code": """def binary_search(arr, target):
    def helper(lo, hi):
        if lo > hi: return -1
        mid = (lo + hi) // 2
        if arr[mid] == target: return mid
        elif arr[mid] < target: return helper(mid + 1, hi)
        else: return helper(lo, mid - 1)
    return helper(0, len(arr) - 1)""",
        "expected": "O(log n)"
    },
    {
        "id": "merge_sort",
        "code": """def merge_sort(arr):
    if len(arr) <= 1: return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    # O(n) merge step
    res = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            res.append(left[i])
            i += 1
        else:
            res.append(right[j])
            j += 1
    res.extend(left[i:])
    res.extend(right[j:])
    return res""",
        "expected": "O(n log n)"
    },
    {
        "id": "manual_memo_fib",
        "code": """def fib(n, memo=None):
    if memo is None: memo = {}
    if n in memo: return memo[n]
    if n <= 1: return n
    memo[n] = fib(n-1, memo) + fib(n-2, memo)
    return memo[n]""",
        "expected": "O(n)"
    },
    {
        "id": "halving_while_loop",
        "code": """def halving_loop(n):
    count = 0
    while n > 1:
        n //= 2
        count += 1
    return count""",
        "expected": "O(log n)"
    },
    {
        "id": "constant_for_loop",
        "code": """def const_loop(n):
    count = 0
    for i in range(26):
        count += 1
    return count""",
        "expected": "O(1)"
    },
    {
        "id": "set_lookup",
        "code": """def set_lookup(arr, targets):
    s = set(arr)
    count = 0
    for target in targets:
        if target in s:
            count += 1
    return count""",
        "expected": "O(n)"
    },
    {
        "id": "valid_parentheses",
        "code": """def isValid(s):
    stack = []
    for c in s:
        if c == '(':
            stack.append(c)
        elif c == ')':
            if not stack:
                return False
            stack.pop()
    return not stack""",
        "expected": "O(n)"
    },
    {
        "id": "list_pop_zero",
        "code": """def slow_queue(arr):
    while arr:
        arr.pop(0)""",
        "expected": "O(n^2)"
    }
]

def run_advanced_tests():
    passed = 0
    for t in tests:
        print(f"Testing [{t['id']}] (Expected: {t['expected']})")
        try:
            ir_graph = parse_python(t['code'])
            static_result = analyze_complexity(ir_graph)
            actual = static_result["complexity"]
            if actual == t['expected']:
                print(f"  [PASS] Got: {actual}")
                passed += 1
            else:
                print(f"  [FAIL] Got: {actual}")
        except Exception as e:
            print(f"  [ERROR] {e}")
    print(f"\\nResults: {passed}/{len(tests)} passed.")

if __name__ == '__main__':
    run_advanced_tests()
