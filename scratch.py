from tree_sitter import Language, Parser
import tree_sitter_javascript as tsjavascript

JS_LANGUAGE = Language(tsjavascript.language())
parser = Parser(JS_LANGUAGE)

code = """
function example() {
    for (let i = 0; i < n; i++) {}
    while (i * i <= n) {}
    for (let i = 1; i < n; i *= 2) {}
    arr.shift();
    Object.keys(obj);
}
"""

tree = parser.parse(bytes(code, "utf8"))

def print_tree(node, depth=0):
    print("  " * depth + node.type + " " + (node.text.decode('utf8') if len(node.children) == 0 else ""))
    for child in node.children:
        print_tree(child, depth + 1)

print_tree(tree.root_node)
