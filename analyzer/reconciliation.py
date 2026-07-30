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
        
    import re
    def get_order(c_str):
        if c_str == "O(1)": return 1
        if c_str == "O(log n)": return 2
        if c_str == "O(n)": return 3
        if c_str == "O(n log n)": return 4
        m_poly = re.search(r'O\(n\^([\d.]+)\)', c_str)
        if m_poly: return 4 + float(m_poly.group(1))
        m_exp = re.search(r'O\(([\d.]+)\^n\)', c_str)
        if m_exp: return 1000 + float(m_exp.group(1))
        if c_str == "O(n!)": return 10000
        return 0
        
    static_val = get_order(static_result)
    dyn_val = get_order(dyn_fit)
    
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
