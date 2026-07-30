import requests

def test_code(name, code, generator='random'):
    try:
        res = requests.post('http://127.0.0.1:5000/api/analyze', json={'code': code, 'language': 'python', 'generator': generator})
        print(f"{name}: {res.json()}")
    except Exception as e:
        print(f"{name}: Failed - {e}")

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

target_sum = '''
def findTargetSumWays(nums, target):
    def backtrack(i, total):
        if i == len(nums):
            return 1 if total == target else 0
        return backtrack(i + 1, total + nums[i]) + backtrack(i + 1, total - nums[i])
    return backtrack(0, 0)
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

print("--- LeetCode Verifications ---")
test_code("Climbing Stairs (Memoized Tree)", climbing_stairs, "small_integer")
test_code("Target Sum (Exponential Branching)", target_sum, "random_with_target")
test_code("3Sum (Nested Amortized O(N^2))", three_sum, "random")
test_code("Longest Substring (Amortized Sliding Window O(N))", longest_substring, {'s': 'scalar_string'})
