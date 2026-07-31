import multiprocessing
import sys
import random

def run_in_sandbox(func_code: str, generator_name: str | dict, n: int, trials: int, func_name: str, return_dict: dict):
    """Worker function to execute python code and profile it securely."""
    # Build safe environment
    if isinstance(__builtins__, dict):
        safe_builtins = __builtins__.copy()
    else:
        safe_builtins = __builtins__.__dict__.copy()
        
    dangerous = ['eval', 'exec', 'open', 'input', 'memoryview']
    for d in dangerous:
        if d in safe_builtins:
            del safe_builtins[d]
            
    original_import = safe_builtins['__import__']
    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in ['os', 'sys', 'subprocess', 'shutil', 'socket']:
            raise ImportError(f"Import of {name} is restricted in sandbox")
        return original_import(name, globals, locals, fromlist, level)
    safe_builtins['__import__'] = safe_import
            
    env = {'__builtins__': safe_builtins}
    
    # We must allow importing math or functools for some snippets to work.
    # In a real sandbox, we'd use a whitelist. For this MVP, we explicitly allow these two.
    import functools
    import math
    import typing
    env['functools'] = functools
    env['math'] = math
    env['typing'] = typing
    for k, v in typing.__dict__.items():
        if not k.startswith('_'):
            env[k] = v
    
    try:
        exec(func_code, env)
        
        if func_name in env:
            func = env[func_name]
        else:
            found = False
            for k, v in env.items():
                if isinstance(v, type) and hasattr(v, func_name):
                    instance = v()
                    func = getattr(instance, func_name)
                    found = True
                    break
            if not found:
                raise KeyError(func_name)
        
        from .profiler import count_operations, generators, gen_random, gen_random_two_args, gen_multi_args, get_generator_for_type
        if isinstance(generator_name, dict):
            args_gen = lambda n: gen_multi_args(generator_name, n)
        else:
            if generator_name in generators:
                args_gen = generators[generator_name]
            else:
                args_gen = lambda n: (get_generator_for_type(generator_name, n),)
        
        total_count = 0
        for _ in range(trials):
            if hasattr(func, 'cache_clear'):
                func.cache_clear()
            
            try:
                args = args_gen(n)
                total_count += count_operations(func, args)
            except TypeError as e:
                if generator_name == 'random' and ('positional argument' in str(e) or 'takes' in str(e)):
                    args = gen_random_two_args(n)
                    total_count += count_operations(func, args)
                else:
                    raise
                    
        return_dict['result'] = float(total_count) / trials
    except Exception as e:
        return_dict['error'] = e

def execute_py_benchmark(code: str, generator_name: str | dict, n: int, trials: int = 10, timeout_sec: int = 5, func_name: str = 'example') -> float:
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    
    p = multiprocessing.Process(target=run_in_sandbox, args=(code, generator_name, n, trials, func_name, return_dict))
    p.start()
    p.join(timeout_sec)
    
    if p.is_alive():
        p.terminate()
        p.join()
        raise RuntimeError("Watchdog timeout")
        
    if 'error' in return_dict:
        raise return_dict['error']
        
    return return_dict.get('result', 0)
