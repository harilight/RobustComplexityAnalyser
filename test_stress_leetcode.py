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
    "Sudoku Solver (Interprocedural)": (
        """class Solution:
    def solveSudoku(self, board: list[list[str]]) -> None:
        self.board = board
        self.solve()
        
    def solve(self):
        for r in range(9):
            for c in range(9):
                if self.board[r][c] == '.':
                    for k in range(1, 10):
                        if self.isValid(r, c, str(k)):
                            self.board[r][c] = str(k)
                            if self.solve(): return True
                            self.board[r][c] = '.'
                    return False
        return True
        
    def isValid(self, r, c, k):
        for i in range(9):
            if self.board[r][i] == k or self.board[i][c] == k: return False
        return True""",
        "matrix"
    ),
    "Generator Comprehensions": (
        """class Solution:
    def checkValid(self, matrix: list[list[int]]) -> bool:
        n = len(matrix)
        for r in range(n):
            if not all(matrix[r][c] > 0 for c in range(n)):
                return False
        return True""",
        "matrix"
    ),
    "Heapq Kth Largest": (
        """import heapq
class Solution:
    def findKthLargest(self, nums: list[int], k: int) -> int:
        heap = []
        for n in nums:
            heapq.heappush(heap, n)
            if len(heap) > k:
                heapq.heappop(heap)
        return heap[0]""",
        {"nums": "random", "k": "small_integer"}
    ),
    "Number of Islands (BFS Amortized)": (
        """import collections
class Solution:
    def numIslands(self, grid: list[list[str]]) -> int:
        if not grid: return 0
        ROWS, COLS = len(grid), len(grid[0])
        visit = set()
        islands = 0
        def bfs(r, c):
            q = collections.deque()
            visit.add((r, c))
            q.append((r, c))
            while q:
                row, col = q.popleft()
                directions = [[1,0],[-1,0],[0,1],[0,-1]]
                for dr, dc in directions:
                    r, c = row + dr, col + dc
                    if (r in range(ROWS) and c in range(COLS) and grid[r][c] == '1' and (r, c) not in visit):
                        visit.add((r, c))
                        q.append((r, c))
        for r in range(ROWS):
            for c in range(COLS):
                if grid[r][c] == "1" and (r, c) not in visit:
                    bfs(r, c)
                    islands += 1
        return islands""",
        "matrix"
    )
}

if __name__ == "__main__":
    results = {}
    for name, (code, generator) in PROBLEMS.items():
        print(f"Testing {name}...")
        res = check_analyze(code, generator=generator)
        results[name] = res
        print(res)
        time.sleep(1)

    with open("test_stress_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Done! Results written to test_stress_results.json")
