#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
from collections import namedtuple

import numpy as np


def argp():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--logging', choices=['NOTSET', 0, 'DEBUG', 10, 'INFO', 20,
                                                    'WARNING', 30, 'ERROR', 40, 'CRITICAL', 50],
                        default='INFO', help='Set logging level.')
    return parser.parse_args()


def get_ordered_sets(args, cursor) -> list:
    import logging
    logging.basicConfig(level=args.logging)

    nb_set = cursor.fetchone()[0]
    logging.info(f'{nb_set} sets in database')

    np.random.seed(85)
    # noinspection All
    sets: list = np.random.permutation(52).tolist()
    sets.extend(list(range(52, nb_set)))
    return sets


Pack = namedtuple('Pack', ['id', 'cnt', 'set_nb', 'pos', 'set_size'])


class Tweet:
    def __init__(self, id_, pack, text, user, replies_to, quoting, quoting_id, images=None):
        self.id, self.pack, self.user, self.replies_to, self.quoting, self.quoting_id = (
            id_, pack, user, replies_to, quoting, quoting_id)

        self.replyto_re = re.compile(r'(^.+?(?=\s[^@]))')
        self.hashtag_re = re.compile(r'(#(?:(?!\s+).)*)')
        self.mention_re = re.compile(r'(@(?:(?!\s+).)*)')

        if images is not None:
            self.images = eval(images)
            print(images)
        self.replies = []

        self.text = self.format_tags_and_mentions(text)

    def format_tags_and_mentions(self, text):
        """
        >>> tweet1 = "@User text."
        >>> tweet2 = "@User text #HashTag text."
        >>> tweet3 = "@User text @User_target text."
        >>> print(tweet_obj.format_tags_and_mentions(tweet1))
        <...>En réponse à : <span class="mention">@User</span><br/><br/></span> text.
        >>> print(tweet_obj.format_tags_and_mentions(tweet2))
        <...>En réponse à : <...>@User</span><br/><br/></span> text <...>#HashTag</span> text.
        >>> print(tweet_obj.format_tags_and_mentions(tweet3))
        <...>En réponse à : <...>@User</span><br/><br/></span> text <...>@User_target</span> text.
        """
        if text[0] == '@':
            text = self.replyto_re.sub(
                r'<span class="inReplyTo">En réponse à : \g<1></span><br/><br/>', text)
        text = self.hashtag_re.sub(r'<span class="hashtag">\g<1></span>', text)
        text = self.mention_re.sub(r'<span class="mention">\g<1></span>', text)
        return text


if __name__ == '__main__':
    import doctest

    tweet_obj = Tweet(*(['x'] * 7))

    doctest.testmod(verbose=True,
                    optionflags=doctest.ELLIPSIS,
                    extraglobs={'tweet_obj': tweet_obj})
