import sys
sys.path.append('.')
from analyzer.parser import parse_python
from analyzer.static import analyze_complexity

climbing_stairs = '''
def climbStairs(n):
    memo = {}
    def recurse(i):
        if i <= 2: return i
        if i in memo: return memo[i]
        memo[i] = recurse(i - 1) + recurse(i - 2)
        return memo[i]
    return recurse(n)
'''

three_sum = '''
def threeSum(nums):
    res = []
    nums.sort()
    for i in range(len(nums)):
        if i > 0 and nums[i] == nums[i-1]:
            continue
        l, r = i + 1, len(nums) - 1
        while l < r:
            s = nums[i] + nums[l] + nums[r]
            if s < 0:
                l += 1
            elif s > 0:
                r -= 1
            else:
                res.append([nums[i], nums[l], nums[r]])
                l += 1
                while nums[l] == nums[l-1] and l < r:
                    l += 1
    return res
'''

longest_substring = '''
def lengthOfLongestSubstring(s):
    char_set = set()
    left = 0
    res = 0
    for right in range(len(s)):
        while s[right] in char_set:
            char_set.remove(s[left])
            left += 1
        char_set.add(s[right])
        res = max(res, right - left + 1)
    return res
'''

def dump(node, depth=0):
    indent = "  " * depth
    if hasattr(node, 'body') and isinstance(node.body, list):
        print(f"{indent}{type(node).__name__}: {getattr(node, 'bound_type', '')} {getattr(node, 'bound_value', '')}")
        for c in node.body: dump(c, depth+1)
    elif hasattr(node, 'branches'):
        print(f"{indent}BranchNode:")
        for b in node.branches:
            for c in b: dump(c, depth+1)
    else:
        print(f"{indent}{type(node).__name__}: {vars(node)}")

print("== Climbing Stairs ==")
ir = parse_python(climbing_stairs)
dump(ir)

print("\n== 3Sum ==")
ir = parse_python(three_sum)
dump(ir)

print("\n== Longest Substring ==")
ir = parse_python(longest_substring)
dump(ir)
