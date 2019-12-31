#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sqlite3

from flask import Flask, render_template, session, request, redirect

from utils import argp, get_ordered_sets, Pack, Tweet


args = argp()
logging.basicConfig(level=args.logging)

app = Flask(__name__)
app.secret_key = 'blabla'

database = sqlite3.connect("./database/tweet_annotation.sqlite", check_same_thread=False)
# TODO: Dirty not to check thread?
cursor = database.cursor()
logging.info("*** Database connection OK ***")

cursor.execute("SELECT COUNT(*) FROM sets")

set_list = get_ordered_sets(args, cursor)


# TODO: fix the redirection when restarting unfinished set
@app.route('/')
def home_session():
    if 'username' in session:
        cursor.execute('select set_nb from set_annotation where annotator == ?',
                       [session['username']])
        sets = cursor.fetchall()
        if sets:
            ids = [set_list.index(x[0]) for x in sets]
            set_number = set_list[max(ids) + 1]
        else:
            set_number = set_list[0]

        cursor.execute("select count(*) from set_annotation where set_nb == ?", [set_number])
        n = cursor.fetchone()
        logging.info(f'*** set_number: {set_number} ***')
        while n[0] >= 3:
            set_number = set_list[set_list.index(set_number) + 1]
            logging.debug(f'*** set_number (while n[0] >= 3): {set_number} ***')
            cursor.execute("select count(*) from set_annotation where set_nb == ?", [set_number])
            n = cursor.fetchone()

        cursor.execute("insert into set_annotation values (?, ?)",
                       [set_number, session['username']])
        database.commit()

        return redirect(f'/set/{set_number}/pack/1')
    else:
        return ("You are not logged in <br><a href = '/login'></b>"
                "click here to log in</b></a>")


@app.route('/set/<int:set_number>/pack/<int:pack_number>', methods=['GET'])
def get_pack(set_number, pack_number):
    try:
        username = session['username']
    except KeyError:
        return ("You are not logged in <br><a href = '/login'></b>"
                "click here to log in</b></a>")

    # Get pack information
    cursor.execute("select id_pack, cnt, s.set_nb, pos, s.size from pack p join sets s "
                   "on s.set_nb = p.set_nb where p.set_nb == ? AND p.pos == ?",
                   [set_number, pack_number])
    p = cursor.fetchone()
    pack = Pack(*p)

    # Get tweets from this pack
    cursor.execute("SELECT * FROM tweet t WHERE t.pack == ?"
                   " ORDER BY CAST(id_tweet AS INTEGER)", [pack.id])
    tweets = []
    tweets_hash = {}

    # Manage replies and quotes
    for t in cursor.fetchall():
        tweet = Tweet(*t)
        tweets_hash[tweet.id] = tweet
        if tweet.replies_to in tweets_hash:
            tweets_hash[tweet.replies_to].replies.append(tweet)
        elif tweet.quoting_id in tweets_hash:
            tweets_hash[tweet.quoting_id].replies.append(tweet)
        else:
            tweets.append(tweet)

    logging.debug([t.text for t in tweets])

    return render_template('annotate_pack.html', tweets=tweets, username=username, pack=pack)


@app.route('/annotate/set/<int:set_number>/pack/<int:pack_number>', methods=['POST'])
def annotate_pack(set_number, pack_number):
    cursor.execute("select id_pack, cnt, s.set_nb, pos, s.size from pack p join sets s "
                   "on s.set_nb = p.set_nb where p.set_nb == ? AND p.pos == ?",
                   [set_number, pack_number])
    p = cursor.fetchone()
    pack = Pack(*p)

    logging.info(f"pack annotation: {request.form['annotation']}")
    cursor.execute("INSERT OR REPLACE INTO pack_annotation VALUES (?,?,?)",
                   (pack.id, session['username'], request.form['annotation']))
    ids = request.form.getlist('tweet_id')[1:]
    annotations_prev = request.form.getlist('tweet_annotation_prev')
    annotations_src = request.form.getlist('tweet_annotation_src')

    logging.debug(ids)
    logging.debug(annotations_prev)
    logging.debug(annotations_src)

    for t_id, annotation_prev, annotation_src in zip(ids, annotations_prev, annotations_src):
        logging.debug(f"INSERT OR REPLACE INTO tweet_annotation VALUES "
                      f"({t_id}, {session['username']}, {annotation_prev}, {annotation_src})")

        cursor.execute("INSERT OR REPLACE INTO tweet_annotation VALUES (?,?,?,?)",
                       (t_id, session['username'], annotation_prev, annotation_src))
    database.commit()

    # Next pack
    if pack.pos == pack.set_size:
        return redirect(f'/next_set/{pack.set_nb}')
    else:
        return redirect(f'/set/{pack.set_nb}/pack/{pack.pos + 1}')


@app.route('/next_set/<int:set_number>')
def next_set(set_number):
    return render_template('next_set.html', set=set_number)


@app.route('/set/<int:set_number>/start')
def start_set(set_number):
    set_number = set_list[set_list.index(set_number) + 1]
    cursor.execute("select count(*) from set_annotation where set_nb == ?", [set_number])
    n = cursor.fetchone()
    while n[0] >= 3:
        set_number = set_list[set_list.index(set_number) + 1]
        cursor.execute("select count(*) from set_annotation where set_nb == ?", [set_number])
        n = cursor.fetchone()

    cursor.execute("insert into set_annotation values (?, ?)", [set_number, session['username']])
    database.commit()
    return redirect(f'/set/{set_number}/pack/1')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect('/')
    return '''
       <form action = "" method = "post">
          <p><input type = "text" name ="username" required/></p>
          <p><input type = "submit" value ="Login"/></p>
       </form>
       '''


if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000)
