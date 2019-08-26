# -*- coding:utf-8 -*-

import curses
from random import randrange, choice        # generate and place new title
from collections import defaultdict
from itertools import chain


# 游戏的6个按键
actions = ['Up', 'Left', 'Down', 'Right', 'Restart', 'Exit']

"""
WASD对应方向上左下右，R键是重置游戏，Q键是退出（含大小写）
ord()函数是以一个字符（长度为1的字符串）作为参数，返回对应的ASCII数值，或者Unicode数值。
如ord('a')的输出是 97， 即“a”的ASCII码是97
所以letter_codes的结果是一个含12个数字的列表：[87, 65, 83, ...]
"""
letter_codes = [ord(ch) for ch in 'WASDRQwasdrq']

"""
zip(letter_codes, actions)中，zip()函数是将letter_codes和action中的元素一一对应，成为被列表包含的元组
由于letter_codes有12个元素，而actions只有6个，所以这里把actions * 2
对应后的结果为[(87, 'Up'), (65, 'Left'), (83, 'Down'), ... ]
dict()函数就是把zip生成的list转为dict
所以actions_dict的结果为一个含12组数据的dict： {87: 'Up', 65: 'Left', 83: 'Down', ... }
"""
actions_dict = dict(zip(letter_codes, actions * 2))


# 阻塞+循环，直到获得用户有效输入才返回对应行为
def get_user_action(keyboard):
    char = "N"
    while char not in actions_dict:
        char = keyboard.getch()
    return actions_dict[char]


# 加入矩阵转置和矩阵逆转，可以大大节省我们的代码量，减少重复劳动，看到后面就知道了
# 矩阵转置：
def transpose(field):
    return [list(row) for row in zip(*field)]


# 矩阵逆转（不是逆矩阵）：
# TODO: row[::-1] 是什么？
def invert(field):
    return [row[::-1] for row in field]


class GameField(object):
    def __init__(self, height=4, width=4, win=2048):
        self.height = height    # 高
        self.width = width      # 宽
        self.win_value = win   # 过关分数
        self.score = 0          # 当前分数
        self.highscore = 0      # 最高分
        self.reset()            # 游戏重置

    def reset(self):
        if self.score > self.highscore:
            self.highscore = self.score
        self.score = 0
        self.field = [[0 for i in range(self.width)] for j in range(self.height)]
        self.spawn()
        self.spawn()

    def move(self, direction):
        def move_row_left(row):
            def tighten(row):   # squeese non-zero elements together 把非0的元素靠在一起，便于下一步判断合并
                new_row = [i for i in row if i != 0]
                new_row += [0 for i in range(len(row) - len(new_row))]
                return new_row

            def merge(row):
                pair = False
                new_row = []
                for i in range(len(row)):
                    if pair:
                        new_row.append(2 * row[i])
                        self.score += 2 * row[i]
                        pair = False
                    else:
                        if i + 1 < len(row) and row[i] == row[i + 1]:
                            pair = True
                            new_row.append(0)
                        else:
                            new_row.append(row[i])
                assert len(new_row) == len(row)
                return new_row

            return tighten(merge(tighten(row)))

        moves = {}
        # 这里的 "\" 表示换行（一般用于一行代码太长时使用）
        moves['Left'] = lambda field:               \
            [move_row_left(row) for row in field]
        moves['Right'] = lambda field:              \
            invert(moves['Left'](invert(field)))
        moves['Up'] = lambda field:                 \
            transpose(moves['Left'](transpose(field)))
        moves['Down'] = lambda field:               \
            transpose(moves['Right'](transpose(field)))

        if direction in moves:
            if self.move_is_possible(direction):
                self.field = moves[direction](self.field)
                self.spawn()
                return True
            else:
                return False

    def is_win(self):
        """
        判断是否胜利
        """
        # return any(any(i >= self.win_value for i in row) for row in self.field)
        return max(chain(*self.field)) >= self.win_value        # 或使用上面那行取代，两种方法都可以

    def is_gameover(self):
        return not any(self.move_is_possible(move) for move in actions)

    def draw(self, screen):
        help_string1 = '(W)Up (S)Down (A)Left (D)Right'
        help_string2 = '    (R)Restart   (Q)Exit      '
        gameover_string = '           GAME OVER       '
        win_string = ' Congratulations! YOU WIN!      '

        def cast(string):
            screen.addstr(string + '\n')

        def draw_hor_separator():
            """
            绘制分隔线
            +--------+--------+--------+--------+
            """
            line = '+' + ('+------' * self.width + '+')[1:]
            separator = defaultdict(lambda: line)
            if not hasattr(draw_hor_separator, "counter"):
                draw_hor_separator.counter = 0
            cast(separator[draw_hor_separator.counter])
            draw_hor_separator.counter += 1

        def draw_row(row):
            """
            draw包含数字的行
            |     |  数字 |     |     |  数字  |
            """
            cast(''.join('|{: ^5} '.format(num) if num > 0 else '|      ' for num in row) + '|')

        screen.clear()
        cast('SCORE: ' + str(self.score))
        if 0 != self.highscore:
            cast('HIGHSCORE: ' + str(self.highscore))
        for row in self.field:
            draw_hor_separator()
            draw_row(row)
        draw_hor_separator()
        if self.is_win():
            cast(win_string)
        else:
            if self.is_gameover():
                cast(gameover_string)
            else:
                cast(help_string1)
        cast(help_string2)

    def spawn(self):
        # 生成新元素，当(0 ~ 99)里随机一个数字大于89的时候生成数字4，否则生成2（也就是2和4出现的概率为9：1）
        new_element = 4 if randrange(100) > 89 else 2
        # 随机选择一个空白的位置生成新数字 （random.choice(seq) seq可以是list, 元组, 或 str）
        (i, j) = choice([(i, j) for i in range(self.width) for j in range(self.height) if self.field[i][j] == 0])
        self.field[i][j] = new_element

    def move_is_possible(self, direction):
        def row_is_left_movable(row):
            """
            检查是否能向左移动
            """
            def change(i):      # true if there'll be change in i-th tile
                if row[i] == 0 and row[i + 1] != 0:     # 如果第一个数为空（这里用0表示），第二个非空，movable
                    return True
                if row[i] != 0 and row[i + 1] == row[i]:    # 如果第一个数和第二个数相等且非空，merge
                    return True
                return False
            return any(change(i) for i in range(len(row) - 1))

        check = {}
        check['Left'] = lambda field:   \
            any(row_is_left_movable(row) for row in field)
        check['Right'] = lambda field:  \
            check['Left'](invert(field))
        check['Up'] = lambda field:     \
            check['Left'](transpose(field))
        check['Down'] = lambda field:   \
            check['Right'](transpose(field))

        if direction in check:
            return check[direction](self.field)
        else:
            return False


# stdscr： 是stand screen的缩写，是Python标准库里的curses模块传进来的
def main(stdscr):

    def init():
        # 重置游戏棋盘
        game_field.reset()
        return 'Game'

    def not_game(state):
        # 画出 GameOver 或者 Win 的界面
        game_field.draw(stdscr)
        # 读取用户输入得到action，判断是重启游戏还是结束游戏
        action = get_user_action(stdscr)
        responses = defaultdict(lambda: state)      # 默认是当前状态，没有行为就会一直在当前界面循环
        responses['Restart'], responses['Exit'] = 'Init', 'Exit'    # 对应不同的行为转换到不同的状态
        return responses[action]

    def game():
        # 画出当前棋盘状态
        game_field.draw(stdscr)
        # 读取用户输入得到acion
        action = get_user_action(stdscr)

        if action == 'Restart':
            return 'Init'
        if action == 'Exit':
            return 'Exit'
        if game_field.move(action):     # if move successful
            if game_field.is_win():
                return 'Win'
            if game_field.is_gameover():
                return 'Gameover'
        return 'Game'

    state_actions = {
        'Init': init,
        'Win': lambda: not_game('Win'),
        'Gameover': lambda: not_game('Gameover'),
        'Game': game
    }

    curses.use_default_colors()

    # 设置终结状态最大数值为 32
    game_field = GameField(win=32)

    state = 'Init'

    # 状态机开始循环
    while state != 'Exit':
        state = state_actions[state]()


curses.wrapper(main)
