# mydifflib.py
from difflib import SequenceMatcher
#from heapq import nlargest as _nlargest
import numpy as np

def get_close_matches_indexes(word, possibilities, n=3, cutoff=0.75):
    """Use SequenceMatcher to return a list of the indexes of the best
    "good enough" matches. word is a sequence for which close matches
    are desired (typically a string).
    possibilities is a list of sequences against which to match word
    (typically a list of strings).
    Optional arg n (default 3) is the maximum number of close matches to
    return.  n must be > 0.
    Optional arg cutoff (default 0.6) is a float in [0, 1].  Possibilities
    that don't score at least that similar to word are ignored.
    """

    if not n >  0:
        raise ValueError("n must be > 0: %r" % (n,))
    if not 0.0 <= cutoff <= 1.0:
        raise ValueError("cutoff must be in [0.0, 1.0]: %r" % (cutoff,))
    result_ratio = []
    result_idx = []
    # se vogliamo escludere le "junk sequence" (in questo caso lo spazio) SequenceMatcher(lambda x: x==" "),  
    s = SequenceMatcher()
    s.set_seq2(word)
    for idx, x in enumerate(possibilities):
        s.set_seq1(x)
        our_ratio = (s.find_longest_match(0, len(x), 0, len(word)).size) / len(word)
        if our_ratio >= cutoff:
            result_ratio.append(our_ratio)
            result_idx.append(idx)
    #    if s.real_quick_ratio() >= cutoff and \
    #       s.quick_ratio() >= cutoff and \
    #       s.ratio() >= cutoff:
    #        result_ratio.append(s.ratio())
    #        result_idx.append(idx)

    # Move the best scorers to head of list
    if not result_ratio:
        result = -1
    else:
        ratios = np.asarray(result_ratio)
        result = result_idx[np.argmax(result_ratio)]

    # Strip scores for the best n matches
    return result
