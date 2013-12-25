# -*- coding: utf-8 -*-
"""
    lodgeit.controllers.pastes
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    The paste controller

    :copyright: 2007-2008 by Armin Ronacher, Christopher Grebs.
    :license: BSD
"""
from os import path
from werkzeug import redirect, Response, secure_filename
from werkzeug.exceptions import NotFound
from lodgeit import local
from lodgeit.lib import antispam, attachment
from lodgeit.i18n import list_languages as i18n_list_languages, _
from lodgeit.utils import render_to_response, sha1
from lodgeit.models import Paste, Attachment
from lodgeit.database import db
from lodgeit.lib.highlighting import LANGUAGES, STYLES, get_style
from lodgeit.lib.pagination import generate_pagination


class PasteController(object):
    """Provides all the handler callback for paste related stuff."""
    def __init__(self):
        self.disable_captcha = local.application.config.get("disable_captcha") or False
        if not self.disable_captcha:
            global check_hashed_solution, Captcha
            from lodgeit.lib.captcha import check_hashed_solution, Captcha

    def new_paste(self, language=None):
        """The 'create a new paste' view."""
        language = local.request.args.get('language', language)
        if language is None:
            language = local.request.session.get('language', 'text')

        code = error = ''
        show_captcha = private = False
        parent = None
        req = local.request
        getform = req.form.get
        enable_attachments = local.application.attach_config.get("enabled")
        attach = dict()

        if local.request.method == 'POST':
            code = getform('code', u'')
            language = getform('language')
            passwd = getform('password')

            parent_id = getform('parent')
            if parent_id is not None:
                parent = Paste.get(parent_id)

            if not self.disable_captcha:
                spam = getform('webpage') or antispam.is_spam(code)
                if spam:
                    error = _('your paste contains spam')
                    captcha = getform('captcha')
                    if captcha:
                        if check_hashed_solution(captcha):
                            error = None
                        else:
                            error = _('your paste contains spam and the '
                                      'CAPTCHA solution was incorrect')
                    show_captcha = True

            if enable_attachments:
                files = [req.files[fname] for fname in req.files if fname.startswith("file_")]
                for file in files:
                    if file and attachment.allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        attach[filename] = file

            if code and language and passwd and not error:
                paste = Paste(code, language, passwd,
                              parent=parent, user_hash=req.user_hash,
                              private=('private' in req.form))
                db.session.add(paste)

                for filename in attach:
                    atchobj = Attachment(filename)
                    paste.attachments.append(atchobj)
                    db.session.add(atchobj)
                    fdest = path.join(local.application.attach_config['upload_folder'], filename)
                    attach[filename].save(fdest)

                db.session.commit()
                local.request.session['language'] = language
                return redirect(paste.url)

        else:
            if local.request.args.get('private', '0') != '0':
                private = True
            parent_id = req.values.get('reply_to')
            if parent_id is not None:
                parent = Paste.get(parent_id)
                if parent is not None:
                    code = parent.code
                    language = parent.language
                    private = parent.private

        return render_to_response('new_paste.html',
            languages=LANGUAGES,
            parent=parent,
            code=code,
            language=language,
            error=error,
            show_captcha=show_captcha,
            private=private,
            password=local.request.session.get('user_passwd'),
            enable_attachments=enable_attachments,
        )

    def show_paste(self, identifier, raw=False):
        """Show an existing paste."""
        linenos = local.request.args.get('linenos') != 'no'
        paste = Paste.get(identifier)
        if paste is None:
            raise NotFound()
        if raw:
            return Response(paste.code, mimetype='text/plain; charset=utf-8')

        style, css = get_style(local.request)
        return render_to_response('show_paste.html',
            paste=paste,
            style=style,
            css=css,
            styles=STYLES,
            linenos=linenos,
            password=local.request.session.get('user_passwd'),
        )

    def delete_paste(self, identifier):
        """Delete an existing paste"""
        if local.request.method == 'POST':
            paste = Paste.get(identifier)
            passwd = local.request.form.get('password')
            if sha1(passwd).hexdigest() != paste.password_hash:
                return NotFound()
            db.session.delete(paste)
            db.session.commit()
            return redirect('/')
        return NotFound()

    def raw_paste(self, identifier):
        """Show an existing paste in raw mode."""
        return self.show_paste(identifier, raw=True)

    def show_tree(self, identifier):
        """Display the tree of some related pastes."""
        paste = Paste.resolve_root(identifier)
        if paste is None:
            raise NotFound()
        return render_to_response('paste_tree.html',
            paste=paste,
            current=identifier
        )

    def show_all(self, page=1):
        """Paginated list of pages."""
        def link(page):
            if page == 1:
                return '/all/'
            return '/all/%d' % page

        form_args = local.request.args
        query = Paste.find_all()

        pastes = query.limit(10).offset(10 * (page - 1)).all()
        if not pastes and page != 1:
            raise NotFound()

        return render_to_response('show_all.html',
            pastes=pastes,
            pagination=generate_pagination(page, 10, query.count(), link),
            css=get_style(local.request)[1],
            show_personal='show_personal' in form_args
        )

    def compare_paste(self, new_id=None, old_id=None):
        """Render a diff view for two pastes."""
        getform = local.request.form.get
        # redirect for the compare form box
        if old_id is None:
            old_id = getform('old', '-1').lstrip('#')
            new_id = getform('new', '-1').lstrip('#')
            return redirect('/compare/%s/%s' % (old_id, new_id))

        old = Paste.get(old_id)
        new = Paste.get(new_id)
        if old is None or new is None:
            raise NotFound()

        return render_to_response('compare_paste.html',
            old=old,
            new=new,
            diff=old.compare_to(new, template=True)
        )

    def unidiff_paste(self, new_id=None, old_id=None):
        """Render an udiff for the two pastes."""
        old = Paste.get(old_id)
        new = Paste.get(new_id)

        if old is None or new is None:
            raise NotFound()

        return Response(old.compare_to(new), mimetype='text/plain')

    def set_colorscheme(self):
        """Minimal view that updates the style session cookie. Redirects
        back to the page the user is coming from.
        """
        style_name = local.request.form.get('style')
        resp = redirect(local.request.environ.get('HTTP_REFERER') or '/')
        if style_name in STYLES:
            resp.set_cookie('style', style_name)
        return resp

    def set_language(self, lang='en'):
        """Minimal view that sets a different language. Redirects
        back to the page the user is coming from."""
        for key, value in i18n_list_languages():
            if key == lang:
                local.request.set_language(lang)
                break
        return redirect(local.request.headers.get('referer') or '/')

    def show_captcha(self):
        """Show a captcha."""
        return Captcha().get_response(set_cookie=True)

    def return_uploaded_file(self, filename):
        return send_from_directory(local.application.attach_config['upload_folder'], filename)

controller = PasteController
