import random
from words_list import words
import pdb

class WordsCodeGen():

    def __init__(self):
        self.specials = words['specials']
        self.specials_after_num = words['specials_after_num']
        self.names = words['names']
        self.adjectives = words['adjectives']
        self.verbs = words['verbs']

    def create_words_code(self):
        num = random.randint(0,99)
        mode = random.choice(['specials',
                              'specials_after_num',
                              'names_adj',
                              'names_verb'])
        words_code = ''
        if mode == 'specials':
            words = random.choice(self.specials).replace(" ", "_")
            words_code = f"{words}_{num}"
        elif mode == 'specials_after_num':
            words = random.choice(self.specials_after_num).replace(" ", "_")
            words_code = f"{num}_{words}"
        elif mode == 'names_adj':
            first_word = random.choice(self.names).replace(" ", "_")
            second_word = random.choice(self.adjectives).replace(" ", "_")
            words_code = f"{first_word}_{second_word}_{num}"
        elif mode == 'names_verb':
            first_word = random.choice(self.verbs).replace(" ", "_")
            second_word = random.choice(self.names).replace(" ", "_")
            words_code = f"{first_word}_{second_word}_{num}"
        # elif mode == 'adj_verb':
        #     first_word = random.choice(self.adjectives).replace(" ", "_")
        #     second_word = random.choice(self.verbs).replace(" ", "_")
        #     words_code = f"{first_word}_{second_word}_{num}"

        return words_code

    def get_nerd_stats(self):
        spec = len(self.specials)
        spec_an = len(self.specials_after_num)
        nam = len(self.names)
        adj = len(self.adjectives)
        ver = len(self.verbs)

        stat_str = f"We have: {spec} specials, {spec_an} specials after a number, {nam} names, {adj} adjectives, {ver} verbs"
        return stat_str
