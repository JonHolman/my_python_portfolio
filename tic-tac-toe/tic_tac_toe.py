#!/usr/bin/env python
from utilities import *
from random import shuffle
from collections import Counter


class Board:
    def __init__(self):
        self.size = 3
        self.players = ['Human', 'Computer']  # there can be any number of players
        self.cell_size = max(len(str(self.size**2)), len(max(self.players, key=len)))  # for spacing
        self.turn = 0
        self.board = list(map(str, range(1, 1+self.size**2)))

    def __str__(self):
        clear()  # clear the screen prior to displaying the board
        ret_val = ''
        for i in range(0, self.size**2, self.size):
            # add the horizontal lines
            if i > 0:
                ret_val += '-' * ((self.size-1) * 3 + (self.size * self.cell_size)) + '\n'
            # add the vertical lines between the cells
            ret_val += ' | '.join([x.rjust(self.cell_size) for x in self.board[i:i+self.size]]) + '\n'
        return ret_val

    @staticmethod
    def all_same(items):
        return items[0] if all(i == items[0] for i in items) else False

    @staticmethod
    def any_same(lists):
        result_of_all = [Board.all_same(l) for l in lists]
        any_true = any(result_of_all)
        return [x for x in result_of_all if x][0] if any_true else False

    def current_turn(self):
        return self.players[self.turn % len(self.players)]

    def has_won(self):
        return self.any_same(self.all_winning_combos())

    def spaces_available(self):
        return [int(i) for i in self.board if is_an_int(i)]

    def can_be_won(self):
        return any([2 > len(set([b for b in a if not is_an_int(b)])) for a in self.all_winning_combos()])

    def all_winning_combos(self):
        return (
            # horizontals
            [[self.board[b] for b in range(a*self.size, (a+1)*self.size)] for a in range(self.size)] +
            # verticals
            [[self.board[b] for b in range(a, self.size**2, self.size)] for a in range(self.size)] +
            # diagonals
            [[self.board[(a*self.size)+a] for a in range(self.size)],
             [self.board[(a*self.size)-a] for a in range(1, self.size+1)]])

    def all_winning_combos_with_ids(self):
        return dict(enumerate(self.all_winning_combos()))

    def prioritize_moves_for_offense(self):
        # a winning combination is only a viable option for offense if it has zero players in it so far or just the current player
        viable_options = [id for id, players in self.all_winning_combos_with_ids().items() if 0 == len(
            set([player for player in players if not is_an_int(player) and player != self.current_turn()]))]

        # then prioritize based on the numbers of spots the current player has already filled
        prioritized_combos = {id: len([i for i in self.all_winning_combos_with_ids()[id] if i == self.current_turn()])
                              for id in viable_options}

        return self.rank_available_spaces(prioritized_combos)

    def prioritize_moves_for_defense(self):
        # a winning combination is only a threat if it has 1 player in it so far, and its not the current player
        viable_options = [id for id, players in self.all_winning_combos_with_ids().items() if 1 == len(
            set([player for player in players if not is_an_int(player)])) and self.current_turn() not in players]  # and player != current_turn

        # then prioritize by how many places that players has filled.
        prioritized_combos = {id: len([i for i in self.all_winning_combos_with_ids()[id] if not is_an_int(i)])
                              for id in viable_options}

        return self.rank_available_spaces(prioritized_combos)

    def rank_available_spaces(self, prioritized_combos):
        # for all available spaces, aggregate the max, sum, and count of points for its combinations
        prioritized_spaces = []
        for space in self.spaces_available():
            points = [prioritized_combos[id] for id, players in self.all_winning_combos_with_ids().items()
                      if str(space) in players and id in prioritized_combos]
            prioritized_spaces.append((space, max(points, default=0), sum(points), len(points)))

        prioritized_spaces.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)

        # adding ranking
        ranked_list = []
        current_rank = 0
        last_item = None
        for i in prioritized_spaces:
            if last_item != i[1:]:
                current_rank += 1
            last_item = i[1:]
            i += (current_rank,)
            ranked_list.append(i)

        return [(space, rank) for space, m, s, c, rank in ranked_list]

    def random_rank_available_spaces(self):
        spaces = self.spaces_available()
        shuffle(spaces)
        return [(space, rank+1) for rank, space in enumerate(spaces)]

    def recommended_move(self, defense_weighting=100, offense_weighting=40, random_weighting=10):
        defense = {space: ((self.size**2)+1-rank)*defense_weighting for space,
                   rank in self.prioritize_moves_for_defense()}
        offense = {space: ((self.size**2)+1-rank)*offense_weighting for space,
                   rank in self.prioritize_moves_for_offense()}
        random = {space: ((self.size**2)+1-rank)*random_weighting for space,
                  rank in self.random_rank_available_spaces()}

        combined = list((Counter(defense) + Counter(offense) + Counter(random)).items())
        combined.sort(key=lambda x: x[1], reverse=True)

        with open("recommendations_log.txt", "a") as log:
            log.write('board looked like \n')
            log.write(str(self))
            log.write('\n')
            log.write('defense:' + str(defense) + '\n')
            log.write('offense:' + str(offense) + '\n')
            log.write('random:' + str(random) + '\n')
            log.write('combined:' + str(combined) + '\n')
            log.write('\n')
        return combined

    def play_game(self):
        winner = False

        while True:
            # display board
            print(self)

            if winner:
                print(f'{winner} has won the game, congratulations!')
                print(f'The game took {self.turn} turns.')
                break
            elif not self.can_be_won():
                print('Tie game.')
                break

            if len(self.spaces_available()) == 1:
                move = self.spaces_available()[0]
            else:
                # get move
                if self.current_turn()[0] == 'C':
                    move = self.recommended_move()[0][0]
                else:
                    move = input(f'{self.current_turn()}\'s turn, enter move: ')

            if move == 'q':
                # quit the game
                break
            elif move == 'r':
                print(self.recommended_move(random_weighting=0))
                input('press enter')

            if not is_an_int(move) or int(move) not in self.spaces_available():
                # the move is invalid, so loop again (refresh display) and do not increment turn
                continue
            else:
                self.board[int(move)-1] = self.current_turn()
                self.turn += 1

            winner = self.has_won()


if __name__ == '__main__':
    pass
