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

from werkzeug import Response
from lodgeit import local

mtdb = MimeTypes()

def filetype(filename):
    mime = mtdb.guess_type(filename)
    if not mime or not mime[0]:
        return None
    mt = mime[0].split('/')
    return mt


def unique_filename(filename):
    _,ext = path.splitext(filename)
    filename = str(uuid4()) + ext
    return filename


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in \
        local.application.config["allowed_files"]
