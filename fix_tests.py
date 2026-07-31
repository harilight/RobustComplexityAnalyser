import json

with open('eval_harness/dataset.json', 'r') as f:
    data = json.load(f)
    
for d in data:
    if d['id'] == 'cat_c_monotonic_stack_py':
        d['code'] = d['code'].replace('def monotonic_stack(arr):', 'def example(arr):')
        d.pop('generator', None)
        d.pop('generator_args', None)
    if d['id'] == 'cat_c_sliding_window_js':
        d['code'] = d['code'].replace('function sliding_window(arr, k)', 'function example(arr, k)')
        d.pop('generator', None)
        d.pop('generator_args', None)
        # We need generator that returns two args: array and target k
        d['generators'] = {'random_with_target': {'fit': 'O(n)'}}
        
with open('eval_harness/dataset.json', 'w') as f:
    json.dump(data, f, indent=2)
