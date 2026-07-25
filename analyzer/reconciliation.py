from typing import Dict, Any, List

def _fit_confidence(metrics: Dict[str, Any]) -> str:
    """
    Returns HIGH if R^2 is near perfect OR the margin over the runner-up is decisive.
    Otherwise returns LOW.
    """
    if metrics.get('r2', 0.0) >= 0.999 or metrics.get('margin', 0.0) >= 0.05:
        return "HIGH"
    return "LOW"

def reconcile(static_result: str, dynamic_results: Dict[str, Dict[str, Any]], tags: List[str] = None) -> Dict[str, Any]:
    if tags is None:
        tags = []
        
    # Rule 2: Category D (Data-Dependent Early Termination) Range Handling
    if 'target_at_start' in dynamic_results and 'target_absent' in dynamic_results:
        best_case = dynamic_results['target_at_start']
        worst_case = dynamic_results['target_absent']
        average_case = dynamic_results.get('random_with_target', worst_case)
        
        # Static is ONLY compared against worst
        if worst_case['fit'] == static_result:
            conf = _fit_confidence(worst_case)
        else:
            conf = "LOW"
            
        return {
            "verdict": {
                "best": best_case['fit'],
                "average": average_case['fit'],
                "worst": worst_case['fit']
            },
            "confidence": conf,
            "reasoning": f"Mismatch: Data-Dependent Early Exit Detected. Static ({static_result}) reconciled against dynamic worst-case."
        }
        
    # Standard single-generator scenario
    if 'random' in dynamic_results:
        dyn = dynamic_results['random']
    elif len(dynamic_results) == 1:
        dyn = list(dynamic_results.values())[0]
    else:
        return {"verdict": static_result, "confidence": "LOW", "reasoning": "Missing 'random' generator"}
        
    dyn_fit = dyn['fit']
    
    # Rule 1: Match
    if dyn_fit == static_result:
        return {
            "verdict": static_result,
            "confidence": _fit_confidence(dyn),
            "reasoning": "Static and dynamic analysis perfectly match."
        }
        
    # Complexity ordering to compare "lower" vs "higher"
    order = {"O(1)": 1, "O(log n)": 2, "O(n)": 3, "O(n log n)": 4, "O(n^2)": 5, "O(2^n)": 6}
    static_val = order.get(static_result, 0)
    dyn_val = order.get(dyn_fit, 0)
    
    # Rule 3: Static > Dynamic
    if static_val > dyn_val:
        if "category-a" in tags or "builtin-hidden-loop" in tags:
            return {
                "verdict": static_result,
                "confidence": "MEDIUM",
                "reasoning": f"Mismatch: Hidden C-Level Operations Detected. Trusting static ({static_result}) over dynamic ({dyn_fit})."
            }
        elif "sorting" in tags:
            return {
                "verdict": static_result,
                "confidence": "HIGH",
                "reasoning": f"Mismatch: C-level sorting algorithm detected. Trusting static ({static_result})."
            }
        elif "queue-op" in tags and dyn_fit == "O(n)":
            return {
                "verdict": dyn_fit,
                "confidence": "HIGH",
                "reasoning": f"Mismatch: Potential Amortized Loop (Graph Traversal). Trusting dynamic ({dyn_fit}) over static ({static_result})."
            }
        else:
            return {
                "verdict": static_result,
                "confidence": "LOW",
                "reasoning": f"Mismatch: Static ({static_result}) > Dynamic ({dyn_fit}). Data-Dependent Early Exit or Hardcoded Bounds Detected. Trusting STATIC_ONLY."
            }
            
    # Rule 4: Dynamic > Static
    if dyn_val > static_val:
        conf = _fit_confidence(dyn)
        if conf == "HIGH":
            return {
                "verdict": dyn_fit,
                "confidence": "MEDIUM", # Capped at medium because static missed it
                "reasoning": f"Mismatch: Dynamic ({dyn_fit}) > Static ({static_result}). Decisive fit indicates hidden overhead missed by static analysis."
            }
        else:
             return {
                 "verdict": static_result,
                 "confidence": "LOW",
                 "reasoning": f"Mismatch: Dynamic ({dyn_fit}) > Static ({static_result}), but dynamic fit is noisy. Trusting static."
             }
             
    return {"verdict": "UNKNOWN", "confidence": "LOW", "reasoning": "Unhandled case."}
