import requests

def test_code(name, code, generator='random'):
    res = requests.post('http://127.0.0.1:5000/api/analyze', json={'code': code, 'language': 'python', 'generator': generator})
    print(f"{name}: {res.json()}")

test_branching = '''
def example(arr, flag):
    if flag == 1:
        for i in arr:
            pass
    elif flag == 2:
        for i in arr:
            for j in arr:
                pass
'''

test_set_lookup = '''
def example(arr):
    seen = set()
    for x in arr:
        if x in seen:
            pass
        seen.add(x)
'''

test_list_lookup = '''
def example(arr):
    seen = []
    for x in arr:
        if x in seen:
            pass
        seen.append(x)
'''

test_pop_front = '''
def example(arr):
    while arr:
        arr.pop(0)
'''

test_string_concat = '''
def example(arr):
    s = ""
    for char in arr:
        s += char
'''

test_sliding_window = '''
def example(arr):
    left = 0
    res = 0
    for right in range(len(arr)):
        while left < right and arr[left] < 0:
            left += 1
        res = max(res, right - left)
    return res
'''

test_code("Branch Disjointness (flag=2 worst path)", test_branching, {'arr': 'random', 'flag': 'flag_2'})
test_code("Set Lookup (O(N))", test_set_lookup)
test_code("List Lookup (O(N^2))", test_list_lookup)
test_code("Pop Front (O(N^2))", test_pop_front)
test_code("String Concat (O(N^2))", test_string_concat, {'arr': '1d_string_array'})
test_code("Sliding Window (O(N))", test_sliding_window)
