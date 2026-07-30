import sys
import json
import traceback
import time
import requests

sys.path.append('.')

def check_analyze(code, expected_static=None, expected_dynamic=None, generator='random'):
    url = "http://127.0.0.1:5000/api/analyze"
    data = {
        "code": code,
        "language": "python",
        "generator": generator
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        res = response.json()
        if not res.get("success"):
            return {"error": res.get("error")}
        return {
            "static": res.get("static"),
            "dynamic": res.get("dynamic"),
            "verdict": res.get("verdict"),
            "confidence": res.get("confidence"),
            "reasoning": res.get("reasoning")
        }
    except Exception as e:
        return {"error": str(e)}

PROBLEMS = {
    # 1. Conditional-Dependent Loops
    "Word Break (Memoized DFS)": (
        """class Solution:
    def wordBreak(self, s: str, wordDict: list[str]) -> bool:
        memo = {}
        def dfs(i):
            if i == len(s): return True
            if i in memo: return memo[i]
            for w in wordDict:
                if s[i:i+len(w)] == w:
                    if dfs(i + len(w)):
                        memo[i] = True
                        return True
            memo[i] = False
            return False
        return dfs(0)""",
        "scalar_string"
    ),
    "Valid Number": (
        """class Solution:
    def isNumber(self, s: str) -> bool:
        seen_digit = seen_exponent = seen_dot = False
        for i, c in enumerate(s):
            if c.isdigit():
                seen_digit = True
            elif c in '+-':
                if i > 0 and s[i-1] not in 'eE':
                    return False
            elif c in 'eE':
                if seen_exponent or not seen_digit:
                    return False
                seen_exponent = True
                seen_digit = False
            elif c == '.':
                if seen_dot or seen_exponent:
                    return False
                seen_dot = True
            else:
                return False
        return seen_digit""",
        "scalar_string"
    ),
    "Integer to Roman": (
        """class Solution:
    def intToRoman(self, num: int) -> str:
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syb = ["M","CM","D","CD","C","XC","L","XL","X","IX","V","IV","I"]
        roman_num = ''
        i = 0
        while num > 0:
            for _ in range(num // val[i]):
                roman_num += syb[i]
                num -= val[i]
            i += 1
        return roman_num""",
        "scalar_int"
    ),
    
    # 2. Data-Dependent Inner Bounds
    "Longest Substring (Sliding Window)": (
        """class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        char_set = set()
        left = 0
        res = 0
        for right in range(len(s)):
            while s[right] in char_set:
                char_set.remove(s[left])
                left += 1
            char_set.add(s[right])
            res = max(res, right - left + 1)
        return res""",
        "scalar_string"
    ),
    "Minimum Size Subarray Sum": (
        """class Solution:
    def minSubArrayLen(self, target: int, nums: list[int]) -> int:
        left = 0
        curr_sum = 0
        min_len = float('inf')
        for right in range(len(nums)):
            curr_sum += nums[right]
            while curr_sum >= target:
                min_len = min(min_len, right - left + 1)
                curr_sum -= nums[left]
                left += 1
        return min_len if min_len != float('inf') else 0""",
        {"target": "small_integer", "nums": "random"}
    ),
    "Trapping Rain Water (Two Pointers)": (
        """class Solution:
    def trap(self, height: list[int]) -> int:
        if not height: return 0
        l, r = 0, len(height) - 1
        leftMax, rightMax = height[l], height[r]
        res = 0
        while l < r:
            if leftMax < rightMax:
                l += 1
                leftMax = max(leftMax, height[l])
                res += leftMax - height[l]
            else:
                r -= 1
                rightMax = max(rightMax, height[r])
                res += rightMax - height[r]
        return res""",
        "random"
    ),
    
    # 3. Multi-Branch Recursion Blowups
    "Fibonacci Number (Naive)": (
        """class Solution:
    def fib(self, n: int) -> int:
        if n <= 1: return n
        return self.fib(n-1) + self.fib(n-2)""",
        "small_integer"
    ),
    "Climbing Stairs (Double Branch Memoized)": (
        """class Solution:
    def climbStairs(self, n: int) -> int:
        memo = {}
        def recurse(i):
            if i > n: return 0
            if i == n: return 1
            if i in memo: return memo[i]
            memo[i] = recurse(i + 1) + recurse(i + 2)
            return memo[i]
        return recurse(0)""",
        "small_integer"
    ),
    "Target Sum": (
        """class Solution:
    def findTargetSumWays(self, nums: list[int], target: int) -> int:
        def backtrack(i, total):
            if i == len(nums):
                return 1 if total == target else 0
            return backtrack(i+1, total + nums[i]) + backtrack(i+1, total - nums[i])
        return backtrack(0, 0)""",
        {"nums": "1d_array_random", "target": "small_integer"}
    ),
    "Sudoku Solver": (
        """class Solution:
    def solveSudoku(self, board: list[list[str]]) -> None:
        def is_valid(board, row, col, ch):
            for i in range(9):
                if board[i][col] == ch: return False
                if board[row][i] == ch: return False
                if board[3 * (row // 3) + i // 3][3 * (col // 3) + i % 3] == ch: return False
            return True
        def backtrack(board):
            for r in range(9):
                for c in range(9):
                    if board[r][c] == '.':
                        for k in '123456789':
                            if is_valid(board, r, c, k):
                                board[r][c] = k
                                if backtrack(board): return True
                                board[r][c] = '.'
                        return False
            return True
        backtrack(board)""",
        "matrix"
    ),

    # 4. Hidden Library Complexities
    "Contains Duplicate (List in loop)": (
        """class Solution:
    def containsDuplicate(self, nums: list[int]) -> bool:
        seen = []
        for n in nums:
            if n in seen:
                return True
            seen.append(n)
        return False""",
        "random"
    ),
    "Intersection of Two Arrays (Naive)": (
        """class Solution:
    def intersection(self, nums1: list[int], nums2: list[int]) -> list[int]:
        res = []
        for n in nums1:
            if n in nums2 and n not in res:
                res.append(n)
        return res""",
        {"nums1": "random", "nums2": "random"}
    ),
    "Two Sum (Optimal)": (
        """class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen = {}
        for i, num in enumerate(nums):
            if target - num in seen:
                return [seen[target-num], i]
            seen[num] = i
        return []""",
        {"nums": "random", "target": "small_integer"}
    ),

    # 5. String Immutability
    "Longest Palindromic Substring (Expand Around Center)": (
        """class Solution:
    def longestPalindrome(self, s: str) -> str:
        res = ""
        for i in range(len(s)):
            # odd
            l, r = i, i
            while l >= 0 and r < len(s) and s[l] == s[r]:
                if (r - l + 1) > len(res):
                    res = s[l:r+1]
                l -= 1
                r += 1
            # even
            l, r = i, i+1
            while l >= 0 and r < len(s) and s[l] == s[r]:
                if (r - l + 1) > len(res):
                    res = s[l:r+1]
                l -= 1
                r += 1
        return res""",
        "scalar_string"
    ),
    "Add Binary (String Accumulation)": (
        """class Solution:
    def addBinary(self, a: str, b: str) -> str:
        res = ""
        carry = 0
        i, j = len(a) - 1, len(b) - 1
        while i >= 0 or j >= 0 or carry:
            if i >= 0:
                carry += int(a[i])
                i -= 1
            if j >= 0:
                carry += int(b[j])
                j -= 1
            res = str(carry % 2) + res
            carry //= 2
        return res""",
        {"a": "scalar_string", "b": "scalar_string"}
    )
}

if __name__ == "__main__":
    results = {}
    for name, (code, generator) in PROBLEMS.items():
        print(f"Testing {name}...")
        res = check_analyze(code, generator=generator)
        results[name] = res
        time.sleep(1) # don't overwhelm sandbox

    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Done! Results written to test_results.json")
