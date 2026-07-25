# ⚡ Robust Complexity Analyzer

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![JavaScript](https://img.shields.io/badge/JavaScript-V8_Engine-yellow.svg)
![AST](https://img.shields.io/badge/Analysis-AST_Static-brightgreen.svg)
![Dynamic](https://img.shields.io/badge/Analysis-Dynamic_Profiling-orange.svg)

Robust Complexity Analyzer is an advanced, production-grade engine that determines the **Time Complexity** (Big-O) of arbitrary Python and JavaScript algorithms. 

Unlike traditional profilers that rely solely on execution time, or static analyzers that get confused by hidden C-level builtins, this engine uses a **Two-Pronged Reconciliation Engine** to combine the theoretical accuracy of Abstract Syntax Tree (AST) parsing with the empirical ground-truth of isolated Sandbox Execution.

## ✨ Features

- **🧠 AST-Driven Static Analysis**: Parses source code to detect recursive branches, loop bounds, and hidden $O(n)$ builtins (e.g., `in list`, `.sort()`).
- **🏃‍♂️ Isolated Dynamic Profiling**: Executes code in an OS-level timeout-protected Python sandbox or a V8 JavaScript Sandbox. Dynamically measures execution time across aggressively scaling input sizes ($10 \times 10 \rightarrow 400 \times 400$).
- **⚖️ Reconciliation Engine**: Merges Static and Dynamic signals. Automatically flags data-dependent early exits (e.g. $O(1)$ best-case vs $O(n)$ worst-case) and catches hidden amortized operations.
- **🔮 Zero-Click Auto-Inference**: Automatically infers the required mock data structures (Trees, Graphs, Matrices, Sorted Arrays) by analyzing parameter names and attribute accesses in your code.
- **🛡️ Edge-Case Immunity**: 
  - Prevents $O(1)$ false positives in Palindrome algorithms via Mirror String generation.
  - Links integer constraints to graph structures to prevent Out-Of-Bounds exceptions.
  - Understands the difference between $O(1)$ Dictionary lookups and $O(n)$ Array searches.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- `pip install tree-sitter tree-sitter-python tree-sitter-javascript flask mini-racer numpy scipy`

### Running the App
1. Clone the repository:
```bash
git clone https://github.com/harilight/RobustComplexityAnalyser.git
cd RobustComplexityAnalyser
```
2. Start the Backend Server:
```bash
python server.py
```
3. Open your browser and navigate to `http://localhost:5000`.

## 🏗️ Architecture

1. **Parser Layer (`parser.py`)**: Uses `tree-sitter` to parse code into an Intermediate Representation (IR).
2. **Inference Engine (`inference.py`)**: Maps function parameters to mock data generators (e.g., `matrix`, `graph_adj_list`, `linked_list`).
3. **Execution Sandbox (`sandbox_py.py`, `sandbox_js.py`)**: Safely executes the algorithm against scaling datasets and records $R^2$ fit for various Big-O curves.
4. **Reconciler (`reconciliation.py`)**: Acts as the ultimate judge, comparing Static AST logic against empirical runtime to yield a highly-confident, explainable Big-O verdict.

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.
