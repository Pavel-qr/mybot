from random import choice

board = [['x', 'x', 'x'],
         ['f', 'x', 'r'],
         ['x', 'e', 'w']]


def is_win(b, let):
    """Проверка победы"""
    return (any(all(i == let for i in b[j]) for j in range(3)) or
            any(all(b[i][j] == let for i in range(3)) for j in range(3)) or
            all(b[i][i] == let for i in range(3)) or
            b[0][2] == b[1][1] == b[2][0] == let)


def is_empty(b, row, column):
    """Проверка этого квадрата"""
    return b[row][column] == ' '


# место кончилось?
def is_full(b):
    return all(all(i != ' ' for i in b[j]) for j in range(3))


def computer_turn(b, let, pl_let):
    # проверка на победу
    for i in range(3):
        for j in range(3):
            test_board = [e[:] for e in b]
            if is_empty(test_board, i, j):
                test_board[i][j] = let
                if is_win(test_board, let):
                    return i, j
    # проверка на поражение
    for i in range(3):
        for j in range(3):
            test_board = [e[:] for e in b]
            if is_empty(test_board, i, j):
                test_board[i][j] = pl_let
                if is_win(test_board, pl_let):
                    return i, j
    if is_empty(b, 1, 1):
        return 1, 1
    moves = []
    for i in (0, 2):
        for j in (0, 2):
            if is_empty(b, i, j):
                moves.append((i, j))
    if len(moves) != 0:
        return choice(moves)
    for i in range(3):
        for j in range(3):
            if is_empty(b, i, j):
                moves.append((i, j))
    return choice(moves)
