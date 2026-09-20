import time
from collections import defaultdict, deque


spam = defaultdict(
    lambda: deque(maxlen=10)
)


BAD_WORDS = {

    "плохое_слово_1",
    "плохое_слово_2"
}


def is_spam(
    chat_id,
    user_id
):

    now = time.time()

    key = (
        chat_id,
        user_id
    )

    q = spam[key]

    q.append(
        now
    )

    recent = [
        x for x in q
        if now - x < 5
    ]

    spam[key] = deque(
        recent,
        maxlen=10
    )

    return len(
        recent
    ) >= 7


def contains_bad_word(
    text
):

    lower = text.lower()

    return any(
        word in lower
        for word in BAD_WORDS
    )
