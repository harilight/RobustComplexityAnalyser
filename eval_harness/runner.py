import json
import sys
import os

# Add parent directory to path so we can import analyzer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.parser import parse_python
from analyzer.parser_js import parse_javascript
from analyzer.static import analyze_complexity
from analyzer.profiler import profile_function
from analyzer.reconciliation import reconcile

def run_eval():
    dataset_path = os.path.join(os.path.dirname(__file__), 'dataset.json')
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)

    passed = 0
    total = 0
    
    print(f"Running Eval Harness on {len(dataset)} snippets...\n")

    for item in dataset:
        print(f"Testing [{item['id']}] (Tags: {', '.join(item['tags'])})")
        
        try:
            is_js = item.get('language', 'python') == 'javascript'
            if is_js:
                ir_graph = parse_javascript(item['code'])
            else:
                ir_graph = parse_python(item['code'])
                
            # Static Analysis
            static_result = analyze_complexity(ir_graph)
            if isinstance(static_result, dict):
                predicted_static = static_result["complexity"]
                static_tags = static_result["tags"]
            else:
                predicted_static = static_result
                static_tags = []
                
            print(f"  [Static] -> {predicted_static} (Tags: {static_tags})")
            
            # Dynamic Profiling
            generators = item.get('generators', {'random': item['expected_time']})
            
            dynamic_results = {}
            for gen_name in generators.keys():
                lang = 'javascript' if is_js else 'python'
                dynamic_results[gen_name] = profile_function(item['code'], gen_name, language=lang)
            
            # Combine dataset tags and auto tags
            all_tags = set(item.get('tags', [])) | set(static_tags)
            
            # Reconciliation
            recon = reconcile(predicted_static, dynamic_results, list(all_tags))
            verdict = recon['verdict']
            conf = recon['confidence']
            reason = recon['reasoning']
            
            print(f"  Verdict: {verdict} (Confidence: {conf})")
            print(f"  Reasoning: {reason}")
            
            total += 1
            expected = item['expected_time']
            
            if isinstance(verdict, dict):
                actual_str = verdict['average']
            else:
                actual_str = verdict
                
            if actual_str == expected:
                print(f"  [PASS] Expected: {expected}, Got: {actual_str}")
                passed += 1
            else:
                print(f"  [FAIL] Expected: {expected}, Got: {actual_str}")
                    
        except Exception as e:
            total += 1
            print(f"  [ERROR] {e}")
            
    if total > 0:
        print(f"\nResults: {passed}/{total} passed ({(passed/total)*100:.1f}%)")
    
    if passed != total:
        sys.exit(1)

if __name__ == "__main__":
    run_eval()
