from tqdm import tqdm
from itertools import chain

import torch
import copy

max_time = 5
max_len = 1024
utter_len = (max_len - max_time - 2) // max_time
speaker1 = 10001
speaker2 = 10002
bos_id = 10003
eos_id = 10004
pad_id = 10005
# self.config['utter_len'] = (self.config['max_len']-self.config['max_time']-2) // self.config['max_time']

class CustomDataset():
    def __init__(self):

        data_name = "valid"

        print(f"Loading {data_name}_id.txt...")
        with open(f"{data_name}.id", 'r') as f:
            lines = f.readlines()

        self.input_ids = []  # (N, L)
        self.token_type_ids = []  # (N, L)
        self.labels = []  # (N, L)

        print(f"Processing {data_name}.id...")
        dialogues = []
        dialogue = []
        cur_speaker = 1
        for i, line in enumerate(tqdm(lines)):
            if line.strip() == "[END OF DIALOGUE]":
                dialogue = []
                cur_speaker = 1
            else:
                if cur_speaker == 1:
                    speaker_id = speaker1
                else:
                    speaker_id = speaker2

                token_ids = line.strip().split(' ')
                token_ids = [speaker_id] + [int(idx) for idx in token_ids]

                if len(dialogue) < max_time:
                    dialogue.append(token_ids)
                else:
                    dialogue = dialogue[1:] + [token_ids]

                cur_speaker = (cur_speaker % 2) + 1
                dialogues.append(copy.deepcopy(dialogue))

        for d, dialogue in enumerate(tqdm(dialogues)):
            if len(dialogue) > 1 and dialogue[-1][0] == speaker2:
                dialogue[0] = [bos_id] + dialogue[0]
                dialogue[-1] = dialogue[-1] + [eos_id]

                total_len = 0
                for utter in dialogue:
                    total_len += len(utter)

                if total_len > max_len:
                    dialogue = [utter[:utter_len] for utter in dialogue]
                    dialogue[-1][-1] = eos_id

                token_type_id = [[utter[0]] * len(utter) if u != 0 else [utter[1]] * len(utter) for u, utter in
                                 enumerate(dialogue)]
                lm_label = [[-100] * len(utter) if u != len(dialogue) - 1 else utter for u, utter in
                            enumerate(dialogue)]
                input_id = list(chain.from_iterable(dialogue))
                token_type_id = list(chain.from_iterable(token_type_id))
                lm_label = list(chain.from_iterable(lm_label))

                assert len(input_id) == len(lm_label) and len(input_id) == len(
                    token_type_id), "There is something wrong in dialogue process."

                input_id, token_type_id, lm_label = self.make_padding(input_id, token_type_id, lm_label,
                                                                      pad_id, max_len)

                self.input_ids.append(input_id)
                self.token_type_ids.append(token_type_id)
                self.labels.append(lm_label)

        self.input_ids = torch.LongTensor(self.input_ids)  # (N, L)
        self.token_type_ids = torch.LongTensor(self.token_type_ids)  # (N, L)
        self.labels = torch.LongTensor(self.labels)  # (N, L)

    def __len__(self):
        return self.input_ids.shape[0]

    def __getitem__(self, idx):
        return self.input_ids[idx], self.token_type_ids[idx], self.labels[idx]

    def make_padding(self, input_id, token_type_id, lm_label, pad_id, max_len):
        left = max_len - len(input_id)

        input_id += [pad_id] * left
        token_type_id += [pad_id] * left
        lm_label += [-100] * left

        return input_id, token_type_id, lm_label


ds = CustomDataset()
print(ds)