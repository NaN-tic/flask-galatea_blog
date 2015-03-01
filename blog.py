from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import (Blueprint, render_template, current_app, abort, g,
    request, url_for, session, flash, redirect)
from galatea.tryton import tryton
# from galatea.utils import get_tryton_language
from flask.ext.paginate import Pagination
from flask.ext.babel import gettext as _, lazy_gettext
from flask.ext.mail import Mail, Message
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
    'metakeywords', 'user', 'user.rec_name', 'post_create_date']
BLOG_SCHEMA_PARSE_FIELDS = ['title', 'content']

def _visibility():
    visibility = ['public']
    if session.get('logged_in'):
        visibility.append('register')
    if session.get('manager'):
        visibility.append('manager')
    return visibility

# @blog.route("/search/", methods=["GET"], endpoint="search")
# @tryton.transaction()
# def search(lang):
#     '''Search'''
#     websites = Website.search([
#         ('id', '=', GALATEA_WEBSITE),
#         ], limit=1)
#     if not websites:
#         abort(404)
#     website, = websites
#
#     WHOOSH_BLOG_DIR = current_app.config.get('WHOOSH_BLOG_DIR')
#     if not WHOOSH_BLOG_DIR:
#         abort(404)
#
#     db_name = current_app.config.get('TRYTON_DATABASE')
#     locale = get_tryton_language(lang)
#
#     schema_dir = os.path.join(tryton_config.get('database', 'path'),
#         db_name, 'whoosh', WHOOSH_BLOG_DIR, locale.lower())
#
#     if not os.path.exists(schema_dir):
#         abort(404)
#
#     #breadcumbs
#     breadcrumbs = [{
#         'slug': url_for('.posts', lang=g.language),
#         'name': _('Blog'),
#         }, {
#         'slug': url_for('.search', lang=g.language),
#         'name': _('Search'),
#         }]
#
#     q = request.args.get('q')
#     if not q:
#         return render_template('blog-search.html',
#                 posts=[],
#                 breadcrumbs=breadcrumbs,
#                 pagination=None,
#                 q=None,
#                 )
#
#     # Get posts from schema results
#     try:
#         page = int(request.args.get('page', 1))
#     except ValueError:
#         page = 1
#
#     # Search
#     ix = index.open_dir(schema_dir)
#     query = q.replace('+', ' AND ').replace('-', ' NOT ')
#     query = MultifieldParser(BLOG_SCHEMA_PARSE_FIELDS, ix.schema).parse(query)
#
#     with ix.searcher() as s:
#         all_results = s.search_page(query, 1, pagelen=WHOOSH_MAX_LIMIT)
#         total = all_results.scored_length()
#         results = s.search_page(query, page, pagelen=LIMIT) # by pagination
#         res = [result.get('id') for result in results]
#
#     domain = [
#         ('id', 'in', res),
#         ('active', '=', True),
#         ('visibility', 'in', _visibility()),
#         ]
#     order = [('post_create_date', 'DESC'), ('id', 'DESC')]
#
#     posts = Post.search_read(domain, order=order, fields_names=POST_FIELD_NAMES)
#
#     pagination = Pagination(page=page, total=total, per_page=LIMIT, display_msg=DISPLAY_MSG, bs_version='3')
#
#     return render_template('blog-search.html',
#             website=website,
#             posts=posts,
#             pagination=pagination,
#             breadcrumbs=breadcrumbs,
#             q=q,
#             )

# @blog.route("/comment", methods=['POST'], endpoint="comment")
# @tryton.transaction()
# def comment(lang):
#     '''Add Comment'''
#     websites = Website.search([
#         ('id', '=', GALATEA_WEBSITE),
#         ], limit=1)
#     if not websites:
#         abort(404)
#     website, = websites
#
#     post = request.form.get('post')
#     comment = request.form.get('comment')
#
#     domain = [
#         ('id', '=', post),
#         ('active', '=', True),
#         ('visibility', 'in', _visibility()),
#         ('galatea_website', '=', GALATEA_WEBSITE),
#         ]
#     posts = Post.search_read(domain, limit=1, fields_names=POST_FIELD_NAMES)
#     if not posts:
#         abort(404)
#     post, = posts
#
#     if not website.blog_comment:
#         flash(_('Not available to publish comments.'), 'danger')
#     elif not website.blog_anonymous and not session.get('user'):
#         flash(_('Not available to publish comments and anonymous users.' \
#             ' Please, login in'), 'danger')
#     elif not comment or not post:
#         flash(_('Add a comment to publish.'), 'danger')
#     else:
#         c = Comment()
#         c.post = post['id']
#         c.user = session['user'] if session.get('user') \
#             else website.blog_anonymous_user.id
#         c.description = comment
#         c.save()
#         flash(_('Comment published successfully.'), 'success')
#
#         mail = Mail(current_app)
#
#         mail_to = current_app.config.get('DEFAULT_MAIL_SENDER')
#         subject =  '%s - %s' % (current_app.config.get('TITLE'), _('New comment published'))
#         msg = Message(subject,
#                 body = render_template('emails/blog-comment-text.jinja', post=post, comment=comment),
#                 html = render_template('emails/blog-comment-html.jinja', post=post, comment=comment),
#                 sender = mail_to,
#                 recipients = [mail_to])
#         mail.send(msg)
#
#     return redirect(url_for('.post', lang=g.language, slug=post['slug']))

# @blog.route("/<slug>", endpoint="post")
# @tryton.transaction()
# def post(lang, slug):
#     '''Post detaill'''
#     websites = Website.search([
#         ('id', '=', GALATEA_WEBSITE),
#         ], limit=1)
#     if not websites:
#         abort(404)
#     website, = websites
#
#     posts = Post.search([
#         ('slug', '=', slug),
#         ('active', '=', True),
#         ('visibility', 'in', _visibility()),
#         ('galatea_website', '=', GALATEA_WEBSITE),
#         ], limit=1)
#
#     if not posts:
#         abort(404)
#     post, = posts
#
#     breadcrumbs = [{
#         'slug': url_for('.posts', lang=g.language),
#         'name': _('Blog'),
#         }, {
#         'slug': url_for('.post', lang=g.language, slug=post.slug),
#         'name': post.name,
#         }]
#
#     return render_template('blog-post.html',
#             website=website,
#             post=post,
#             breadcrumbs=breadcrumbs,
#             )

# @blog.route("/key/<key>", endpoint="key")
# @tryton.transaction()
# def key(lang, key):
#     '''Posts by Key'''
#     websites = Website.search([
#         ('id', '=', GALATEA_WEBSITE),
#         ], limit=1)
#     if not websites:
#         abort(404)
#     website, = websites
#
#     try:
#         page = int(request.args.get('page', 1))
#     except ValueError:
#         page = 1
#
#     domain = [
#         ('metakeywords', 'ilike', '%'+key+'%'),
#         ('active', '=', True),
#         ('visibility', 'in', _visibility()),
#         ('galatea_website', '=', GALATEA_WEBSITE),
#         ]
#     total = Post.search_count(domain)
#     offset = (page-1)*LIMIT
#
#     order = [('post_create_date', 'DESC'), ('id', 'DESC')]
#     posts = Post.search_read(domain, offset, LIMIT, order, POST_FIELD_NAMES)
#
#     pagination = Pagination(page=page, total=total, per_page=LIMIT, display_msg=DISPLAY_MSG, bs_version='3')
#
#     #breadcumbs
#     breadcrumbs = [{
#         'slug': url_for('.posts', lang=g.language),
#         'name': _('Blog'),
#         }, {
#         'slug': url_for('.key', lang=g.language, key=key),
#         'name': key,
#         }]
#
#     return render_template('blog-key.html',
#             website=website,
#             posts=posts,
#             pagination=pagination,
#             breadcrumbs=breadcrumbs,
#             key=key,
#             )

# @blog.route("/user/<user>", endpoint="user")
# @tryton.transaction()
# def users(lang, user):
#     '''Posts by User'''
#     websites = Website.search([
#         ('id', '=', GALATEA_WEBSITE),
#         ], limit=1)
#     if not websites:
#         abort(404)
#     website, = websites
#
#     try:
#         user = int(user)
#     except:
#         abort(404)
#
#     users = User.search([
#         ('id', '=', user)
#         ], limit=1)
#     if not users:
#         abort(404)
#     user, = users
#
#     try:
#         page = int(request.args.get('page', 1))
#     except ValueError:
#         page = 1
#
#     domain = [
#         ('user', '=', user.id),
#         ('active', '=', True),
#         ('visibility', 'in', _visibility()),
#         ('galatea_website', '=', GALATEA_WEBSITE),
#         ]
#     total = Post.search_count(domain)
#     offset = (page-1)*LIMIT
#
#     if not total:
#         abort(404)
#
#     order = [('post_create_date', 'DESC'), ('id', 'DESC')]
#     posts = Post.search_read(domain, offset, LIMIT, order, POST_FIELD_NAMES)
#
#     pagination = Pagination(page=page, total=total, per_page=LIMIT, display_msg=DISPLAY_MSG, bs_version='3')
#
#     #breadcumbs
#     breadcrumbs = [{
#         'slug': url_for('.posts', lang=g.language),
#         'name': _('Blog'),
#         }, {
#         'slug': url_for('.user', lang=g.language, user=user.id),
#         'name': user.rec_name,
#         }]
#
#     return render_template('blog-user.html',
#             website=website,
#             posts=posts,
#             user=user,
#             pagination=pagination,
#             breadcrumbs=breadcrumbs,
#             )

@blog.route("/", endpoint="home")
@tryton.transaction()
def home():
    '''Blog home'''
    # TODO: get it from website conf?
    with Transaction().set_context(website=GALATEA_WEBSITE):
        uris = Uri.search([
                ('slug', 'in', ('noticies', 'noticias', 'news')),
                ('parent.slug', 'in', ('ca', 'es', 'en')),
                ('active', '=', True),
                ('website', '=', GALATEA_WEBSITE),
                ])
    if not uris:
        abort(404)
    uri = uris[0]

    posts, pagination = paginated_posts()
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

    # TODO: get it from some "blog" attribute?
    blog_base_uri_str = url_for('.home')
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
            posts, pagination = paginated_posts(tag=uris[0].content)
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

        posts, pagination = paginated_posts(start_date=start_date,
            end_date=end_date)
        return render_template('blog-archive.html',
            title=title,
            posts=posts,
            pagination=pagination)
    else:
        abort(404)


def paginated_posts(tag=None, start_date=None, end_date=None, offset=None,
        limit=None):
    try:
        page = int(request.args.get('page', 1))
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
        domain.append(('post_create_date', '>=', start_date))
    if end_date:
        domain.append(('post_create_date', '<', end_date))

    total = Post.search_count(domain)
    posts = Post.search(domain, offset=offset, limit=LIMIT, order=[
            ('post_create_date', 'DESC'),
            ('id', 'DESC'),
            ])
    pagination = Pagination(page=page, total=total, per_page=limit,
        display_msg=DISPLAY_MSG, bs_version='3')
    return posts, pagination
