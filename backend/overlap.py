"""Trims a raw transcript chunk against the tail of the accumulated transcript
to remove duplicated words caused by audio overlap between chunks.

Ported directly from the validated trim_overlap.py prototype (session scratchpad).
"""


def trim_overlap(prev_tail_text: str, new_text: str) -> str:
    prev_tail = prev_tail_text.split()
    new_words = new_text.split()

    max_check = min(len(prev_tail), 10)
    best = 0
    for n in range(max_check, 0, -1):
        if prev_tail[-n:] == new_words[:n]:
            best = n
            break

    trimmed = new_words[best:]
    return " ".join(trimmed)
