import tree_sitter_python as tspython
from tree_sitter import Language, Parser

p = Parser(Language(tspython.language()))
tree = p.parse(b"""while n > 1:
    n //= 2
    count += 1
""")

def print_tree(node, depth=0):
    print("  " * depth + node.type + " " + (node.text.decode('utf8') if not node.children else ""))
    for c in node.children:
        print_tree(c, depth + 1)

print_tree(tree.root_node)
