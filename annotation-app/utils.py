#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web-based application for tweet stance annotation (library)
===========================================================
Web-based application developed under flask allowing for the annotation of tweet stance. Two levels
of annotation are offered, the stance of the target tweet toward the tweet it responds to, and
toward the root tweet of the thread. The database (not provided - for Twitter privacy policy reason)
is in the .sqlite format.

Synopsis
--------
    examples, for testing:
    ``````````````````````
    python utils.py

Authors
-------
Marc Evrard  <mevrard@ina.fr>
Rémi Uro     <ruro@ina.fr>

License
-------
The MIT License

Copyright 2019 INA (Rémi Uro and Marc Evrard - http://www.ina.fr/)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES
OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

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
        self.id, self.pack, self.text, self.user, self.replies_to, self.quoting, self.quoting_id = (
            id_, pack, text, user, replies_to, quoting, quoting_id)

        if images is not None:
            self.images = eval(images)
        self.replies = []

        self.format_tags_and_mentions()

    def format_tags_and_mentions(self):
        """
        >>> text = "@User text."
        >>> tweet_1 = Tweet('x', 'x', text, 'x', 'x', 'x', 'x')
        >>> print(tweet_1.text)
        <...>En réponse à : <span class="mention">@User</span><br/><br/></span> text.

        >>> text = "@User text #HashTag text."
        >>> tweet_2 = Tweet('x', 'x', text, 'x', 'x', 'x', 'x')
        >>> print(tweet_2.text)
        <...>En réponse à : <...>@User</span><br/><br/></span> text <...>#HashTag</span> text.

        >>> text = "@User text @User_target text."
        >>> tweet_3 = Tweet('x', 'x', text, 'x', 'x', 'x', 'x')
        >>> print(tweet_3.text)
        <...>En réponse à : <...>@User</span><br/><br/></span> text <...>@User_target</span> text.
        """
        if self.text[0] == '@':
            self.text = re.sub(r'(^.+?(?=\s[^@]))',
                               r'<span class="inReplyTo">En réponse à : \g<1></span><br/><br/>',
                               self.text)
        self.text = re.sub(r'(#(?:(?!\s+).)*)', r'<span class="hashtag">\g<1></span>', self.text)
        self.text = re.sub(r'(@(?:(?!\s+).)*)', r'<span class="mention">\g<1></span>', self.text)


if __name__ == '__main__':
    import doctest

    doctest.testmod(verbose=True, optionflags=doctest.ELLIPSIS)
