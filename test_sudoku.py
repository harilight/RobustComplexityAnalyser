import sys
sys.path.append('.')
from analyzer.parser import parse_python
from analyzer.static import analyze_complexity

sudoku_code = '''
def solve(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == '.':
                for k in '123456789':
                    if True:
                        board[r][c] = k
                        if solve(board):
                            return True
                        board[r][c] = '.'
                return False
    return True
'''

ir = parse_python(sudoku_code)
res = analyze_complexity(ir)
print("Sudoku Complexity:", res["complexity"])
