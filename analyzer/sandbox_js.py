import math
from py_mini_racer import MiniRacer
from py_mini_racer.py_mini_racer import JSTimeoutException

JS_SETUP = """
const generators = {
    random: (size) => [Array.from({length: size}, () => Math.floor(Math.random() * 1000)), Array.from({length: size}, () => Math.floor(Math.random() * 100))],
    target_at_start: (size) => [[42].concat(Array.from({length: size-1}, () => Math.floor(Math.random() * 1000))), 42],
    target_absent: (size) => [Array.from({length: size}, () => Math.floor(Math.random() * 1000)), -1],
    fib_arg: (size) => [size],
    
    binary_tree: (size) => {
        if (size === 0) return [null];
        class TreeNode { constructor(val) { Object.assign(this, {val, left: null, right: null}); } }
        let nodes = Array.from({length: size}, (_, i) => new TreeNode(i));
        for (let i = 0; i < size; i++) {
            if (2*i + 1 < size) nodes[i].left = nodes[2*i + 1];
            if (2*i + 2 < size) nodes[i].right = nodes[2*i + 2];
        }
        return [nodes[0]];
    },
    
    linked_list: (size) => {
        if (size === 0) return [null];
        class ListNode { constructor(val) { Object.assign(this, {val, next: null}); } }
        let head = new ListNode(0);
        let curr = head;
        for (let i = 1; i < size; i++) { curr.next = new ListNode(i); curr = curr.next; }
        return [head];
    },
    
    graph_adj_list: (size) => {
        let graph = {};
        for(let i=0; i<size; i++) graph[i] = [];
        if (size > 1) {
            for(let i=0; i<size-1; i++) { graph[i].push(i+1); graph[i+1].push(i); }
            for(let i=0; i<Math.floor(size/2); i++) {
                let u = Math.floor(Math.random() * size);
                let v = Math.floor(Math.random() * size);
                if (u !== v && !graph[u].includes(v)) { graph[u].push(v); graph[v].push(u); }
            }
        }
        return [graph];
    },
    
    graph_edges: (size) => {
        if (size === 0) return [[]];
        let edges = [];
        for(let i=0; i<size; i++) {
            edges.push([Math.floor(Math.random() * size), Math.floor(Math.random() * size)]);
        }
        return [edges];
    },
    
    matrix: (size) => {
        let side = Math.max(1, size);
        return [Array.from({length: side}, () => Array.from({length: side}, () => Math.floor(Math.random() * 100)))];
    }
};
"""

def execute_js_benchmark(code: str, generator_name: str | dict, n: int, trials: int = 100, func_name: str = 'example') -> float:
    """
    Evaluates the JS code securely in V8, runs it `trials` times for input size `n`,
    and returns the average execution time in milliseconds.
    """
    ctx = MiniRacer()
    
    ctx.eval(JS_SETUP)
    ctx.eval(code)
    
    # Generate the string to build test_args
    def map_js_gen(g):
        if isinstance(g, dict):
            g_type = g.get('type')
            if g_type == 'scalar_string':
                alphabet = g.get('alphabet')
                if alphabet:
                    alph_str = "".join(alphabet).replace("'", "\\'").replace("\n", "").replace("\\", "\\\\")
                    return f"(function(sz) {{ let a='{alph_str}'; let res=''; for(let i=0; i<sz; i++) res+=a.charAt(Math.floor(Math.random()*a.length)); return res; }})(size)"
            g = g_type
            
        if g in ['matrix', 'linked_list', 'binary_tree', 'graph_adj_list', 'graph_edges']:
            return f"generators['{g}'](size)[0]"
        elif g == 'scalar_string':
            # Mirror String Profile for Palindrome tests (worst-case O(N))
            return "(function(sz) { let half = Math.floor(sz/2); let s = Array.from({length: half}, () => String.fromCharCode(97 + Math.floor(Math.random() * 26))).join(''); return s + s.split('').reverse().join('').substring(0, sz - half); })(size)"
        elif g == 'size_int':
            return "size"
        elif g == '1d_array_sorted':
            return "Array.from({length: size}, () => Math.floor(Math.random() * 1000)).sort((a,b) => a-b)"
        elif g == '1d_string_array':
            return "Array.from({length: size}, (_, i) => String.fromCharCode(97 + (i % 26)))"
        else:
            return f"generators['random'](size)[0]"

    if isinstance(generator_name, dict):
        args_builder = "[" + ", ".join(map_js_gen(g) for g in generator_name.values()) + "]"
        args_builder = args_builder.replace("generators['random'](size)[0]", "Array.from({length: size}, () => Math.floor(Math.random() * 1000))")
    else:
        if generator_name in ['random', 'target_at_start', 'target_absent', 'fib_arg', 'binary_tree', 'linked_list', 'graph_adj_list', 'graph_edges', 'matrix']:
            args_builder = f"generators['{generator_name}'](size)"
        else:
            args_builder = "[" + map_js_gen(generator_name) + "]"
        
    # Warmup to trigger V8 JIT Compilation
    ctx.eval(f"var size = 10; var test_args = {args_builder};")
    ctx.eval(f"for(var i=0; i<10; i++) {{ var _res = {func_name}.apply(null, test_args); }}")
    
    # Benchmark with dynamic calibration loop (run until 200ms elapsed)
    ctx.eval(f"size = {n}; test_args = {args_builder};")
    
    benchmark_code = """
    var start = new Date().getTime();
    var _res_acc = 0;
    var trials = 0;
    while (true) {
        var _res = FUNC_NAME.apply(null, test_args);
        if (typeof _res === 'number') _res_acc += _res;
        trials++;
        var now = new Date().getTime();
        if (now - start >= 200) break;
    }
    var end = new Date().getTime();
    (end - start) / trials;
    """.replace('FUNC_NAME', func_name)
    
    try:
        # Time out after 5000ms just in case a single run takes too long
        avg_time = ctx.eval(benchmark_code, timeout=5000)
        return float(avg_time)
    except JSTimeoutException:
        raise RuntimeError("Watchdog timeout")
    except Exception as e:
        raise RuntimeError(f"Sandbox Error: {e}")
