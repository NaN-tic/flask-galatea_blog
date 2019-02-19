from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import (Blueprint, render_template, current_app, abort, g,
    request, url_for, session, flash, redirect)
from galatea.tryton import tryton
# from galatea.utils import get_tryton_language
from flask_paginate import Pagination
from flask_babel import gettext as _, lazy_gettext
from flask_mail import Mail, Message
# from trytond.config import config as tryton_config
from trytond.transaction import Transaction
# from whoosh import index
# from whoosh.qparser import MultifieldParser
# import os

import galatea


blog = Blueprint('blog', __name__, template_folder='templates')

DISPLAY_MSG = lazy_gettext('Displaying <b>{start} - {end}</b> of <b>{total}</b>')

Website = tryton.pool.get('galatea.website')
Post = tryton.pool.get('galatea.blog.post')
Comment = tryton.pool.get('galatea.blog.comment')
Uri = tryton.pool.get('galatea.uri')
User = tryton.pool.get('galatea.user')

GALATEA_WEBSITE = current_app.config.get('TRYTON_GALATEA_SITE')
LIMIT = current_app.config.get('TRYTON_PAGINATION_BLOG_LIMIT', 20)
COMMENTS = current_app.config.get('TRYTON_BLOG_COMMENTS', True)
WHOOSH_MAX_LIMIT = current_app.config.get('WHOOSH_MAX_LIMIT', 500)

POST_FIELD_NAMES = ['name', 'slug', 'description', 'comment', 'total_comments',
    'metakeywords', 'user', 'user.rec_name', 'post_published_date']
BLOG_SCHEMA_PARSE_FIELDS = ['title', 'content']

def _visibility():
    visibility = ['public']
    if session.get('logged_in'):
        visibility.append('register')
    if session.get('manager'):
        visibility.append('manager')
    return visibility


@blog.route("/", endpoint="home")
@tryton.transaction()
def home():
    '''Blog home'''
    websites = Website.search([
        ('id', '=', GALATEA_WEBSITE),
        ], limit=1)
    if not websites:
        abort(404)
    website, = websites
    uri = website.archives_base_uri

    posts, pagination = paginated_posts(uri=uri.uri)
    return render_template('blog.html',
        uri=uri,
        posts=posts,
        pagination=pagination)


@blog.route("/<path:uri_str>", endpoint="archives")
@tryton.transaction()
def archives(uri_str):
    '''Blog Archives'''
    websites = Website.search([
        ('id', '=', GALATEA_WEBSITE),
        ], limit=1)
    if not websites:
        abort(404)
    website, = websites

    blog_base_uri_str = website.archives_base_uri.uri + '/'
    tags_base_uri = website.tags_base_uri
    archives_base_uri = website.archives_base_uri

    current_uri_str = blog_base_uri_str + uri_str
    with Transaction().set_context(website=GALATEA_WEBSITE):
        uris = Uri.search([
            ('uri', '=', current_uri_str[1:]),
            ('active', '=', True),
            ('website', '=', GALATEA_WEBSITE),
            ])

    if uris:
        if current_uri_str.startswith(tags_base_uri.uri):
            posts, pagination = paginated_posts(current_uri_str, tag=uris[0].content)
            return render_template(uris[0].template.filename,
                uri=uris[0],
                posts=posts,
                pagination=pagination)

        # Blog posts
        return galatea.uri_aux(uris[0])

    if current_uri_str.startswith(archives_base_uri.uri):
        archive_params = current_uri_str.replace(archives_base_uri.uri,
            '').split('/')[1:]
        if not archive_params[-1]:  # current_uri_str ends with '/'
            archive_params = archive_params[:-1]

        if len(archive_params) == 2:
            try:
                year, month = map(int, archive_params)
            except ValueError:
                abort(404)

            title = '{:0>2}/{}'.format(month, year)
            start_date = datetime(year, month, 1, 0, 0, 0)
            end_date = start_date + relativedelta(months=+1)
        elif len(archive_params) == 1:
            try:
                year = int(archive_params[0])
            except ValueError:
                abort(404)

            title = year
            start_date = datetime(year, 1, 1, 0, 0, 0)
            end_date = datetime(year + 1, 1, 1, 0, 0, 0)
        else:
            abort(404)

        posts, pagination = paginated_posts(current_uri_str,
            start_date=start_date, end_date=end_date)
        return render_template('blog-archive.html',
            title=title,
            posts=posts,
            pagination=pagination)
    else:
        abort(404)


def paginated_posts(uri, tag=None, start_date=None, end_date=None, offset=None,
        limit=None):
    try:
        page = int(request.args.get('p', 1))
    except ValueError:
        page = 1

    if limit is None:
        limit = LIMIT
    if offset is None:
        offset = (page - 1) * limit

    domain = [
        ('active', '=', True),
        ('visibility', 'in', _visibility()),
        ('websites', 'in', [GALATEA_WEBSITE]),
        ]
    if tag:
        domain.append(('tags', 'in', [tag.id]))
    if start_date:
        domain.append(('post_published_date', '>=', start_date))
    if end_date:
        domain.append(('post_published_date', '<', end_date))

    total = Post.search_count(domain)
    posts = Post.search(domain, offset=offset, limit=LIMIT, order=[
            ('post_published_date', 'DESC'),
            ('id', 'DESC'),
            ])
    pagination = Pagination(page=page, total=total, per_page=limit,
        display_msg=DISPLAY_MSG, bs_version='3', href=uri + '?p={0}')
    return posts, pagination
