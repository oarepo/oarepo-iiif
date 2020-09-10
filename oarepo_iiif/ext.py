import pkg_resources
from flask import current_app
from invenio_base.signals import app_loaded
from werkzeug.utils import cached_property


class OARepoIIIFExtState:
    def __init__(self, app):
        self.app = app

    def open(self, *args, **kwargs):
        for opener in self.openers:
            ret = opener(*args, **kwargs)
            if ret is not None:
                return ret
        return None

    def check(self, *args, **kwargs):
        for checker in self.checks:
            ret = checker(*args, **kwargs)
            if ret is not None:
                return ret
        return None

    @cached_property
    def openers(self):
        openers = []
        for entry_point in pkg_resources.iter_entry_points('oarepo-iiif.openers'):
            openers.append(entry_point.load())
        openers.sort(key=lambda opener: -getattr(opener, '_priority', 10))
        return openers

    @cached_property
    def checks(self):
        checks = []
        for entry_point in pkg_resources.iter_entry_points('oarepo-iiif.checks'):
            checks.append(entry_point.load())
        checks.sort(key=lambda opener: -getattr(opener, '_priority', 10))
        return checks


class OARepoIIIFExt:
    def __init__(self, app, db=None):
        self.init_app(app)

    def init_app(self, app):
        app.extensions['oarepo-iiif'] = OARepoIIIFExtState(app)


@app_loaded.connect
def loaded(sender, app=None, **kwargs):
    with app.app_context():
        current_oarepo_iiif = app.extensions['oarepo-iiif']

        iiif_ext = current_app.extensions['invenio-iiif'].iiif_ext
        prev_opener = iiif_ext.uuid_to_image_opener

        iiif_ext.uuid_to_image_opener_handler(
            lambda *args, **akwargs: current_oarepo_iiif.open(*args, app=app, **akwargs) or prev_opener(*args, **akwargs)
        )

        prev_decorator_handler = iiif_ext.api_decorator_callback

        def decorator_handler(*args, **akwargs):
            ret = current_oarepo_iiif.check(*args, app=app, **akwargs)
            if ret is not None:
                return ret
            return prev_decorator_handler(*args, **akwargs)

        iiif_ext.api_decorator_handler(decorator_handler)
