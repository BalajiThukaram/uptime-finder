from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from bbg.auth import login_required
from bbg.db import get_db
import requests
bp = Blueprint('func', __name__)
def runAllTime():
    db=get_db()
    works=db.execute(
        'select urlString,timeLimit from post'
    ).fetchall()
    for work in works:
        stat=""
        try:
            r=requests.get(work['urlString'])
            if r.status_code==requests.codes.ok:
                stat="ACTIVE"
            else:
                stat="NOT ACTIVE"
        except requests.exceptions.ConnectionError:
            stat="NOT ACTIVE"
        db = get_db()
        db.execute(
                'INSERT INTO fullData (urlString, timeLimit, author_id,stat)'
                'VALUES (?, ?, ?,?)',
            (work['urlString'], work['timeLimit'], g.user['id'],stat)
        )
        db.commit()

@bp.route('/')
def index():
    return render_template('index.html',)
@bp.route('/all')
def all():
    runAllTime()
    db = get_db()
    posts = db.execute(
        'SELECT p.id, urlString, timeLimit, created, author_id, username,stat'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('all.html', posts=posts)

@bp.route('/status.html')
def status():
    runAllTime()
    db=get_db()
    lasts=db.execute(
        'select *'
        'from post p join user u on p.author_id=u.id'
    ).fetchall()
    return render_template('status.html',lasts=lasts)

@bp.route('/singleUrl.html')
def final():
    runAllTime()
    db=get_db()
    lists=db.execute(
        'select id,urlString,stat,created from fullData'
    ).fetchall()
    return render_template('singleUrl.html',lists=lists)
    
@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    runAllTime()
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            stat=""
            try:
                r=requests.get(title)
                if r.status_code==requests.codes.ok:
                    stat="ACTIVE"
                else:
                    stat="NOT ACTIVE"
            except requests.exceptions.ConnectionError:
                stat="NOT ACTIVE"
            db = get_db()
            db.execute(
                'INSERT INTO post (urlString, timeLimit, author_id,stat)'
                ' VALUES (?, ?, ?,?)',
                (title, body, g.user['id'],stat)
            )
            db.commit()
            return redirect(url_for('index'))

    return render_template('create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, urlString, timeLimit, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    runAllTime()
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET urlString = ?, timeLimit = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('index'))

    return render_template('update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute(
        'INSERT INTO stats Select * from post where id=?',(id,))
    db.commit()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('func.index'))

@bp.route('/deleted.html')
def deleted():
    runAllTime()
    db=get_db()
    books=db.execute(
        'select *'
        'from stats s join user u on s.author_id=u.id'
    ).fetchall()
    return render_template('deleted.html',books=books)