"""
    lodgeit.attachment
"""
from os import path
from mimetypes import MimeTypes, guess_type
from uuid import uuid4

try:
    from PIL import ImageFont, ImageDraw, Image, ImageChops, ImageColor
except ImportError:
    import ImageFont, ImageDraw, Image, ImageChops, ImageColor

from werkzeug import Response, secure_filename
from lodgeit import local

mtdb = MimeTypes()

def filetype(filename):
    mime = mtdb.guess_type(filename)
    if not mime or not mime[0]:
        return None
    mt = mime[0]
    return mt


def unique_filename(filename):
    filename = secure_filename(filename)
    _, ext = path.splitext(filename)
    filename = str(uuid4()) + ext
    return filename


def allowed_file(filename):
    if local.application.attach_config["allowed_files"]:
        return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in
            local.application.attach_config["allowed_files"])


def file_preview_name(filename):
    return "%s_t.jpg" % path.splitext(filename)[0]


def file_preview(filename):
    filename = path.join(local.application.attach_config["upload_folder"], filename)
    destfn = file_preview_name(filename)
    filter = Image.ANTIALIAS
    img = Image.open(filename)
    img.thumbnail(local.application.attach_config["thumbnail_size"], filter)
    img.save(destfn, 'jpg')
