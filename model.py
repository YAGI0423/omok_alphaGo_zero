from tree import Node
from util import Util

import numpy as np
import tensorflow as tf
from tensorflow import keras as K

class User:
    def __init__(self, board_size, rule):
        self.board_size = board_size
        self.rule = rule

    def act(self, seq_xy_board):
        def check_input(message):
            #check user input value
            while True:
                input_data = input(f"{message}: ")
                if (input_data) == "": continue  #빈 값
                if input_data == "None": return None;   #None값
                try:
                    input_data = int(input_data)   #정수값
                    return input_data
                except:
                    continue

        while True:
            input_x, input_y = check_input("x"), check_input("y")
            able_loc = self.rule.get_able_loc(seq_xy_board)
            if (input_x, input_y) in able_loc: break;   #aleady put stone
        return {'xy_loc':(input_x, input_y)}


class RandomChoice:
    def __init__(self, board_size, rule):
        self.board_size = board_size
        self.rule = rule

    def act(self, seq_xy_board):
        able_loc = list(self.rule.get_able_loc(seq_xy_board))
        able_loc.remove((None, None))   #surrender
        rand_idx = np.random.choice(len(able_loc))
        return {'xy_loc': able_loc[rand_idx]}


class AlphaO:
    def __init__(self, board_size, rule, round_num=1600):
        self.board_size = board_size
        self.model = self.__get_model()
        self.rule = rule

        self.c = np.sqrt(2)
        self.round_num = round_num

    def __get_model(self):
        input = K.layers.Input(shape=(self.board_size, self.board_size, 3))
        conv1 = K.layers.Conv2D(kernel_size=3, filters=64, activation="relu", padding="same")(input)

        flat = K.layers.Flatten()(conv1)
        dense1 = K.layers.Dense(256, activation="relu")(flat)

        policy_dense = K.layers.Dense(128, activation="relu")(dense1)
        policy_output = K.layers.Dense(self.board_size ** 2 + 1, activation="softmax", name="PNN")(policy_dense)

        value_dense = tf.keras.layers.Dense(128, activation="relu")(dense1)
        value_output = tf.keras.layers.Dense(1, activation="tanh", name="VNN")(value_dense)

        model = K.models.Model(inputs=input, outputs=[policy_output, value_output])
        return model

    def predict_stone(self, seq_xy_board):
        #MCTS tree search

        #function====================================
        def seq_xy_to_idx(seq_xy_board):
            #convert x, y location to idx
            loc2idx = tuple(   #able loc -> idx
                x + y * self.board_size for x, y in seq_xy_board
            )
            return loc2idx

        def element_idx_to_xy(idx_loc):
            #convert branch idx, to x, y location
            x = idx_loc % self.board_size
            y = idx_loc // self.board_size
            return x, y

        def model_predict(seq_xy_board):
            #get policy, value

            input_board = Util.get_model_input(seq_xy_board, self.board_size)
            policy_pred, value_pred = self.model(input_board)
            policy_pred = np.array(policy_pred[0])
            value_pred = np.array(value_pred[0][0])
            return policy_pred, value_pred

        def create_node(seq_xy_board, idx, parent):
            policy_pred, value_pred = model_predict(seq_xy_board)

            #get node's branches
            able_loc = self.rule.get_able_loc(seq_xy_board)

            #surrender is another algorithm
            able_loc = list(able_loc)
            able_loc.remove((None, None))
            able_loc = tuple(able_loc)

            seq_idx_board = seq_xy_to_idx(able_loc)
            branches = {idx: policy_pred[idx] for idx in seq_idx_board}

            node = Node(
                state=seq_xy_board,
                value=value_pred,
                idx=idx,
                parent=parent,
                branches=branches
            )

            #add child to parent
            if parent is not None:
                parent.childrens[idx] = node
            return node

        def select_branch(node):
            #Evaluate Branch and Select
            #return branch idx
            total_n = node.total_visit

            def score_branch(branch_idx):
                #Calculate Branch Value
                q = node.get_expected_value(branch_idx)   #total value / visit
                p = node.get_prior(branch_idx)
                n = node.get_visit(branch_idx)
                return q + self.c * p * np.sqrt(total_n) / (n + 1)
            return max(node.get_branches_keys(), key=score_branch)
        #End=========================================


        root = create_node(seq_xy_board, idx=None, parent=None)

        for round in range(self.round_num):
            node = root
            branch_idx = select_branch(node)

            #explore tree
            while node.has_child(branch_idx):
                #has child: follow root, no child: stop
                node = node.childrens[branch_idx]
                branch_idx = select_branch(node)

            #create new state
            xy_loc = element_idx_to_xy(branch_idx)

            branch_board = list(node.state)
            branch_board.append(xy_loc)
            branch_board = tuple(branch_board)

            #create child node
            game_status = self.rule.game_status(branch_board)
            if game_status['during']:   #during
                child_node = create_node(branch_board, idx=branch_idx, parent=node)
                value = -1. * child_node.value
            else:   #done | is terminal node
                #draw: 0, win: -1
                value = 0. if game_status['win'] == 2 else 1.

            child_idx = branch_idx

            #record visit
            while node is not None:
                node.record_visit(child_idx, value)

                value = -1. * value
                child_idx = node.idx
                node = node.parent

        result_idx = max(root.branches.keys(), key=root.get_visit)
        return root, element_idx_to_xy(result_idx)

    def act(self, seq_xy_board):
        root, xy_loc = self.predict_stone(seq_xy_board)
        return {'root': root, 'xy_loc': xy_loc}
