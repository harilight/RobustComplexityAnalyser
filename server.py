import os
from flask import Flask, request, jsonify
from analyzer.parser import parse_python
from analyzer.parser_js import parse_javascript
from analyzer.static import analyze_complexity
from analyzer.profiler import profile_function
from analyzer.reconciliation import reconcile

app = Flask(__name__, static_folder='.', static_url_path='')

@app.route('/')
def index():
    return app.send_static_file('index.html')

def ensure_function_wrapper(code: str, language: str) -> str:
    """If the code doesn't define a function, wrap it in one named 'example'."""
    if language == 'python':
        if 'def ' not in code:
            lines = code.split('\n')
            indented = '\n'.join('    ' + line for line in lines)
            return f"def example(arr):\n{indented}\n"
    elif language == 'javascript':
        if 'function ' not in code and '=>' not in code:
            return f"function example(arr) {{\n{code}\n}}"
    return code

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    if not data or 'code' not in data:
        return jsonify({'success': False, 'error': 'No code provided'}), 400
        
    code = data.get('code', '')
    language = data.get('language', 'python')
    generator_name = data.get('generator', 'random')
    
    code = ensure_function_wrapper(code, language)
    
    try:
        # Static Analysis
        if language == 'javascript':
            ir_graph = parse_javascript(code)
        else:
            ir_graph = parse_python(code)
            
        # Auto Inference
        inferred_str = None
        if generator_name == 'auto':
            from analyzer.inference import format_inferred_structure
            sig = ir_graph.inferred_signature
            attrs = ir_graph.accessed_attributes
            
            generator_to_use = sig
            inferred_str = format_inferred_structure(sig, attrs)
        else:
            generator_to_use = generator_name
            
        static_result = analyze_complexity(ir_graph)
        predicted_static = static_result["complexity"]
        tags = static_result["tags"]
        
        # Dynamic Profiling
        func_name = ir_graph.name
        dynamic_result = profile_function(code, generator_to_use, language, func_name)
        
        # Reconciliation
        gen_for_recon = generator_name
        if isinstance(gen_for_recon, dict):
            gen_for_recon = str(gen_for_recon)
        recon = reconcile(predicted_static, {gen_for_recon: dynamic_result}, tags)
        
        response_data = {
            'success': True,
            'static': predicted_static,
            'dynamic': dynamic_result['fit'],
            'verdict': recon['verdict'],
            'confidence': recon['confidence'],
            'reasoning': recon['reasoning']
        }
        
        if inferred_str:
            response_data['inferred_structure'] = inferred_str
            
        return jsonify(response_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
