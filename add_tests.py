import json

with open('eval_harness/dataset.json', 'r') as f:
    data = json.load(f)
    
data.append({
    "id": "cat_c_monotonic_stack_py",
    "language": "python",
    "tags": ["category-c", "amortized-cost", "monotonic-stack"],
    "code": "def monotonic_stack(arr):\n    stack = []\n    res = []\n    for x in arr:\n        while stack and stack[-1] < x:\n            stack.pop()\n        res.append(x)\n        stack.append(x)\n    return res",
    "expected_complexity": "O(n)",
    "generator": "random_list",
    "generator_args": {"min_len": 10, "max_len": 200, "element_range": [0, 1000]}
})

data.append({
    "id": "cat_c_sliding_window_js",
    "language": "javascript",
    "tags": ["category-c", "amortized-cost", "sliding-window"],
    "code": "function sliding_window(arr, k) {\n    let left = 0;\n    let curr = 0;\n    let res = 0;\n    for (let right = 0; right < arr.length; right++) {\n        curr += arr[right];\n        while (curr > k && left <= right) {\n            curr -= arr[left];\n            left++;\n        }\n        res = Math.max(res, right - left + 1);\n    }\n    return res;\n}",
    "expected_complexity": "O(n)",
    "generator": "random_list",
    "generator_args": {"min_len": 10, "max_len": 200, "element_range": [0, 100]}
})

with open('eval_harness/dataset.json', 'w') as f:
    json.dump(data, f, indent=2)
