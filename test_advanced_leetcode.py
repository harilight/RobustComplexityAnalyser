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
        response = requests.post(url, json=data, timeout=30)
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
    # 1. Graph & DFS/BFS
    "Course Schedule": (
        """class Solution:
    def canFinish(self, numCourses: int, prerequisites: list[list[int]]) -> bool:
        preMap = {i: [] for i in range(numCourses)}
        for crs, pre in prerequisites:
            preMap[crs].append(pre)
        visitSet = set()
        def dfs(crs):
            if crs in visitSet:
                return False
            if preMap[crs] == []:
                return True
            visitSet.add(crs)
            for pre in preMap[crs]:
                if not dfs(pre): return False
            visitSet.remove(crs)
            preMap[crs] = []
            return True
        for crs in range(numCourses):
            if not dfs(crs): return False
        return True""",
        {"numCourses": "size_int", "prerequisites": "graph_edges"}
    ),
    "Word Search": (
        """class Solution:
    def exist(self, board: list[list[str]], word: str) -> bool:
        ROWS, COLS = len(board), len(board[0])
        path = set()
        def dfs(r, c, i):
            if i == len(word): return True
            if r < 0 or c < 0 or r >= ROWS or c >= COLS or word[i] != board[r][c] or (r, c) in path:
                return False
            path.add((r, c))
            res = dfs(r+1, c, i+1) or dfs(r-1, c, i+1) or dfs(r, c+1, i+1) or dfs(r, c-1, i+1)
            path.remove((r, c))
            return res
        for r in range(ROWS):
            for c in range(COLS):
                if dfs(r, c, 0): return True
        return False""",
        {"board": "matrix", "word": "scalar_string"}
    ),

    # 2. Combinatorics & Backtracking
    "Word Break II": (
        """class Solution:
    def wordBreak(self, s: str, wordDict: list[str]) -> list[str]:
        wordSet = set(wordDict)
        memo = {}
        def backtrack(start):
            if start == len(s): return [""]
            if start in memo: return memo[start]
            res = []
            for end in range(start + 1, len(s) + 1):
                word = s[start:end]
                if word in wordSet:
                    for sub in backtrack(end):
                        res.append(word + (" " if sub else "") + sub)
            memo[start] = res
            return res
        return backtrack(0)""",
        "auto"
    ),
    "Permutations": (
        """class Solution:
    def permute(self, nums: list[int]) -> list[list[int]]:
        res = []
        if len(nums) == 1: return [nums[:]]
        for i in range(len(nums)):
            n = nums.pop(0)
            perms = self.permute(nums)
            for perm in perms:
                perm.append(n)
            res.extend(perms)
            nums.append(n)
        return res""",
        "random"
    ),
    "Combinations": (
        """class Solution:
    def combine(self, n: int, k: int) -> list[list[int]]:
        res = []
        def backtrack(start, comb):
            if len(comb) == k:
                res.append(comb[:])
                return
            for i in range(start, n + 1):
                comb.append(i)
                backtrack(i + 1, comb)
                comb.pop()
        backtrack(1, [])
        return res""",
        {"n": "small_integer", "k": "small_integer"}
    ),
    "Subsets": (
        """class Solution:
    def subsets(self, nums: list[int]) -> list[list[int]]:
        res = []
        subset = []
        def dfs(i):
            if i >= len(nums):
                res.append(subset[:])
                return
            subset.append(nums[i])
            dfs(i + 1)
            subset.pop()
            dfs(i + 1)
        dfs(0)
        return res""",
        "random"
    ),
    "N-Queens": (
        """class Solution:
    def solveNQueens(self, n: int) -> list[list[str]]:
        col, posDiag, negDiag = set(), set(), set()
        res = []
        board = [["."] * n for i in range(n)]
        def backtrack(r):
            if r == n:
                res.append(["".join(row) for row in board])
                return
            for c in range(n):
                if c in col or (r + c) in posDiag or (r - c) in negDiag: continue
                col.add(c)
                posDiag.add(r + c)
                negDiag.add(r - c)
                board[r][c] = "Q"
                backtrack(r + 1)
                col.remove(c)
                posDiag.remove(r + c)
                negDiag.remove(r - c)
                board[r][c] = "."
        backtrack(0)
        return res""",
        {"n": "small_integer"}
    ),
    "Letter Combinations": (
        """class Solution:
    def letterCombinations(self, digits: str) -> list[str]:
        res = []
        digitToChar = {"2":"abc","3":"def","4":"ghi","5":"jkl","6":"mno","7":"pqrs","8":"tuv","9":"wxyz"}
        def backtrack(i, curStr):
            if len(curStr) == len(digits):
                res.append(curStr)
                return
            for c in digitToChar[digits[i]]:
                backtrack(i + 1, curStr + c)
        if digits:
            backtrack(0, "")
        return res""",
        "scalar_string"
    ),

    # 3. 2D Dynamic Programming
    "Wildcard Matching": (
        """class Solution:
    def isMatch(self, s: str, p: str) -> bool:
        memo = {}
        def dfs(i, j):
            if (i, j) in memo: return memo[(i, j)]
            if i == len(s) and j == len(p): return True
            if j == len(p): return False
            if i == len(s):
                for k in range(j, len(p)):
                    if p[k] != '*': return False
                return True
            if p[j] == '*':
                memo[(i, j)] = dfs(i+1, j) or dfs(i, j+1)
            elif p[j] == '?' or s[i] == p[j]:
                memo[(i, j)] = dfs(i+1, j+1)
            else:
                memo[(i, j)] = False
            return memo[(i, j)]
        return dfs(0, 0)""",
        {"s": "scalar_string", "p": "scalar_string"}
    ),
    "Partition Equal Subset Sum": (
        """class Solution:
    def canPartition(self, nums: list[int]) -> bool:
        if sum(nums) % 2: return False
        dp = set()
        dp.add(0)
        target = sum(nums) // 2
        for i in range(len(nums)):
            nextDP = set()
            for t in dp:
                if t + nums[i] == target: return True
                nextDP.add(t + nums[i])
                nextDP.add(t)
            dp = nextDP
        return True""",
        "random"
    ),
    "Edit Distance": (
        """class Solution:
    def minDistance(self, word1: str, word2: str) -> int:
        cache = [[float("inf")] * (len(word2) + 1) for i in range(len(word1) + 1)]
        for j in range(len(word2) + 1): cache[len(word1)][j] = len(word2) - j
        for i in range(len(word1) + 1): cache[i][len(word2)] = len(word1) - i
        for i in range(len(word1) - 1, -1, -1):
            for j in range(len(word2) - 1, -1, -1):
                if word1[i] == word2[j]:
                    cache[i][j] = cache[i + 1][j + 1]
                else:
                    cache[i][j] = 1 + min(cache[i + 1][j], cache[i][j + 1], cache[i + 1][j + 1])
        return cache[0][0]""",
        {"word1": "scalar_string", "word2": "scalar_string"}
    ),

    # 4. Advanced Sliding Windows & Hashes
    "Longest Repeating Character Replacement": (
        """class Solution:
    def characterReplacement(self, s: str, k: int) -> int:
        count = {}
        res = 0
        l = 0
        maxf = 0
        for r in range(len(s)):
            count[s[r]] = 1 + count.get(s[r], 0)
            maxf = max(maxf, count[s[r]])
            while (r - l + 1) - maxf > k:
                count[s[l]] -= 1
                l += 1
            res = max(res, r - l + 1)
        return res""",
        {"s": "scalar_string", "k": "small_integer"}
    ),
    "Permutation in String": (
        """class Solution:
    def checkInclusion(self, s1: str, s2: str) -> bool:
        if len(s1) > len(s2): return False
        s1Count, s2Count = [0] * 26, [0] * 26
        for i in range(len(s1)):
            s1Count[ord(s1[i]) - ord('a')] += 1
            s2Count[ord(s2[i]) - ord('a')] += 1
        matches = 0
        for i in range(26):
            matches += 1 if s1Count[i] == s2Count[i] else 0
        l = 0
        for r in range(len(s1), len(s2)):
            if matches == 26: return True
            index = ord(s2[r]) - ord('a')
            s2Count[index] += 1
            if s1Count[index] == s2Count[index]: matches += 1
            elif s1Count[index] + 1 == s2Count[index]: matches -= 1
            index = ord(s2[l]) - ord('a')
            s2Count[index] -= 1
            if s1Count[index] == s2Count[index]: matches += 1
            elif s1Count[index] - 1 == s2Count[index]: matches -= 1
            l += 1
        return matches == 26""",
        {"s1": "scalar_string", "s2": "scalar_string"}
    ),
    "Find All Anagrams": (
        """class Solution:
    def findAnagrams(self, s: str, p: str) -> list[int]:
        if len(p) > len(s): return []
        pCount, sCount = {}, {}
        for i in range(len(p)):
            pCount[p[i]] = 1 + pCount.get(p[i], 0)
            sCount[s[i]] = 1 + sCount.get(s[i], 0)
        res = [0] if sCount == pCount else []
        l = 0
        for r in range(len(p), len(s)):
            sCount[s[r]] = 1 + sCount.get(s[r], 0)
            sCount[s[l]] -= 1
            if sCount[s[l]] == 0: sCount.pop(s[l])
            l += 1
            if sCount == pCount: res.append(l)
        return res""",
        {"s": "scalar_string", "p": "scalar_string"}
    ),
    "Subarray Sum Equals K": (
        """class Solution:
    def subarraySum(self, nums: list[int], k: int) -> int:
        res = 0
        curSum = 0
        prefixSums = {0: 1}
        for n in nums:
            curSum += n
            diff = curSum - k
            res += prefixSums.get(diff, 0)
            prefixSums[curSum] = 1 + prefixSums.get(curSum, 0)
        return res""",
        {"nums": "random", "k": "small_integer"}
    ),
    "Repeated DNA Sequences": (
        """class Solution:
    def findRepeatedDnaSequences(self, s: str) -> list[str]:
        seen, res = set(), set()
        for l in range(len(s) - 9):
            cur = s[l:l+10]
            if cur in seen:
                res.add(cur)
            seen.add(cur)
        return list(res)""",
        "scalar_string"
    ),

    # 5. String & Array Manipulation
    "Longest Valid Parentheses": (
        """class Solution:
    def longestValidParentheses(self, s: str) -> int:
        left, right, maxlength = 0, 0, 0
        for i in range(len(s)):
            if s[i] == '(': left += 1
            else: right += 1
            if left == right: maxlength = max(maxlength, 2 * right)
            elif right > left: left = right = 0
        left, right = 0, 0
        for i in range(len(s) - 1, -1, -1):
            if s[i] == '(': left += 1
            else: right += 1
            if left == right: maxlength = max(maxlength, 2 * left)
            elif left > right: left = right = 0
        return maxlength""",
        "scalar_string"
    ),
    "Valid Anagram": (
        """class Solution:
    def isAnagram(self, s: str, t: str) -> bool:
        if len(s) != len(t): return False
        countS, countT = {}, {}
        for i in range(len(s)):
            countS[s[i]] = 1 + countS.get(s[i], 0)
            countT[t[i]] = 1 + countT.get(t[i], 0)
        return countS == countT""",
        {"s": "scalar_string", "t": "scalar_string"}
    ),
    "Group Anagrams": (
        """class Solution:
    def groupAnagrams(self, strs: list[str]) -> list[list[str]]:
        res = {}
        for s in strs:
            count = [0] * 26
            for c in s:
                count[ord(c) - ord("a")] += 1
            k = tuple(count)
            if k not in res: res[k] = []
            res[k].append(s)
        return res.values()""",
        "1d_string_array"
    ),
    "Longest Common Prefix": (
        """class Solution:
    def longestCommonPrefix(self, strs: list[str]) -> str:
        res = ""
        for i in range(len(strs[0])):
            for s in strs:
                if i == len(s) or s[i] != strs[0][i]:
                    return res
            res += strs[0][i]
        return res""",
        "1d_string_array"
    ),
    "Implement strStr()": (
        """class Solution:
    def strStr(self, haystack: str, needle: str) -> int:
        if needle == "": return 0
        for i in range(len(haystack) + 1 - len(needle)):
            if haystack[i:i + len(needle)] == needle:
                return i
        return -1""",
        {"haystack": "scalar_string", "needle": "scalar_string"}
    ),
    "Valid Sudoku": (
        """class Solution:
    def isValidSudoku(self, board: list[list[str]]) -> bool:
        cols = {i: set() for i in range(9)}
        rows = {i: set() for i in range(9)}
        squares = {(r//3, c//3): set() for r in range(9) for c in range(9)}
        for r in range(9):
            for c in range(9):
                if board[r][c] == ".": continue
                if board[r][c] in rows[r] or board[r][c] in cols[c] or board[r][c] in squares[(r // 3, c // 3)]:
                    return False
                cols[c].add(board[r][c])
                rows[r].add(board[r][c])
                squares[(r // 3, c // 3)].add(board[r][c])
        return True""",
        "matrix"
    ),
    "Spiral Matrix": (
        """class Solution:
    def spiralOrder(self, matrix: list[list[int]]) -> list[int]:
        res = []
        left, right = 0, len(matrix[0])
        top, bottom = 0, len(matrix)
        while left < right and top < bottom:
            for i in range(left, right):
                res.append(matrix[top][i])
            top += 1
            for i in range(top, bottom):
                res.append(matrix[i][right - 1])
            right -= 1
            if not (left < right and top < bottom): break
            for i in range(right - 1, left - 1, -1):
                res.append(matrix[bottom - 1][i])
            bottom -= 1
            for i in range(bottom - 1, top - 1, -1):
                res.append(matrix[i][left])
            left += 1
        return res""",
        "matrix"
    ),
    "Rotate Array": (
        """class Solution:
    def rotate(self, nums: list[int], k: int) -> None:
        k = k % len(nums)
        l, r = 0, len(nums) - 1
        while l < r:
            nums[l], nums[r] = nums[r], nums[l]
            l, r = l + 1, r - 1
        l, r = 0, k - 1
        while l < r:
            nums[l], nums[r] = nums[r], nums[l]
            l, r = l + 1, r - 1
        l, r = k, len(nums) - 1
        while l < r:
            nums[l], nums[r] = nums[r], nums[l]
            l, r = l + 1, r - 1""",
        {"nums": "random", "k": "small_integer"}
    ),
    "Container With Most Water": (
        """class Solution:
    def maxArea(self, height: list[int]) -> int:
        res = 0
        l, r = 0, len(height) - 1
        while l < r:
            area = (r - l) * min(height[l], height[r])
            res = max(res, area)
            if height[l] < height[r]:
                l += 1
            else:
                r -= 1
        return res""",
        "random"
    )
}

if __name__ == "__main__":
    results = {}
    for name, (code, generator) in PROBLEMS.items():
        print(f"Testing {name}...")
        res = check_analyze(code, generator=generator)
        results[name] = res
        time.sleep(1) # don't overwhelm sandbox

    with open("test_advanced_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Done! Results written to test_advanced_results.json")
