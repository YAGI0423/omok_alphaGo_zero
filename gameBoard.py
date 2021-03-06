class GameBoard():
    def __init__(self):
        self.__board = []

    def get_board(self):
        return tuple(self.__board.copy())

    def put_stone(self, x, y):
        self.__board.append((x, y))
