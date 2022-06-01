import pickle
import random
import numpy as np

class DataBook:
    def __init__(self, buffer_size=1024, load_dir=None):
        self.buffer_size = buffer_size

        self.state = []
        self.policy_y = []
        self.value_y = []

        if load_dir:
            self.load_databook(load_dir)

    def add_data(self, data_dict):
        check_datas = ('state', 'policy_y', 'value_y')

        for name in check_datas:    
            if name in data_dict.keys():
                if name == 'policy_y':
                    self.__dict__[name].append(data_dict[name])
                else:
                    self.__dict__[name].extend(data_dict[name])

    def get_data(self, shuffle=False, augment_rate=None):
        def update_databook():
            state_policy_TF = len(self.state) == len(self.policy_y)
            policy_value_TF = len(self.policy_y) == len(self.value_y)

            if state_policy_TF and policy_value_TF:   #must dataset size is same
                over_num = len(self.state) - self.buffer_size

                if over_num > 0:
                    del_idx = np.random.choice(
                        range(len(self.state)), replace=False, size=over_num
                    )
                    
                    del_idx.sort()
                    
                    for idx in del_idx[::-1]:
                        del self.state[idx]
                        del self.policy_y[idx]
                        del self.value_y[idx]
            else:
                raise

        def data_augment(x, policy_y, value_y, rate=0.3):

            data_len = len(value_y)
            augment_num = int(data_len * rate)

            aug_idx_list = random.choices(range(data_len), k=augment_num)

            aug_x = x[aug_idx_list].copy()
            aug_policy_y = policy_y[aug_idx_list].copy()
            aug_value_y = value_y[aug_idx_list].copy()

            aug_x = np.rot90(aug_x, k=random.randint(1, 4), axes=(1, 2))
            if random.randint(0, 2):
                aug_x = np.flip(aug_x, axis=2)
            
            x = np.concatenate((x, aug_x), axis=0)
            policy_y = np.concatenate((policy_y, aug_policy_y))
            value_y = np.concatenate((value_y, aug_value_y))

            return x, policy_y, value_y

        update_databook()
        dataset_len = len(self.state)

        state = np.asarray(self.state, dtype=np.float64)
        policy_y = np.asarray(self.policy_y, dtype=np.float64).reshape(dataset_len, -1)
        value_y = np.asarray(self.value_y, dtype=np.float64).reshape(-1, 1)

        if shuffle:
            idx = np.array(range(dataset_len))
            np.random.shuffle(idx)

            state = state[idx]
            policy_y = policy_y[idx]
            value_y = value_y[idx]

        if augment_rate:
            state, policy_y, value_y = data_augment(state, policy_y, value_y, augment_rate)

        return {
            'x': state,
            'policy_y': policy_y,
            'value_y': value_y
        }

    def save_databook(self, save_dir):
        with open(save_dir, 'wb') as pick:
            save_databook = {
                'state': self.state,
                'policy_y': self.policy_y,
                'value_y': self.value_y
            }
            pickle.dump(save_databook, pick)

    def load_databook(self, load_dir):
        with open(load_dir, 'rb') as pick:
            data = pickle.load(pick)
    
        self.state = data['state']
        self.policy_y = data['policy_y']
        self.value_y = data['value_y']