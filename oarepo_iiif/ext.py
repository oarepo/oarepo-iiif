import sys
import traceback
from urllib.parse import quote

import pkg_resources
from flask import current_app, url_for
from invenio_base.signals import app_loaded
from invenio_iiif.utils import iiif_image_key
from werkzeug.utils import cached_property

from oarepo_iiif import current_oarepo_iiif


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
        for entry_point in pkg_resources.iter_entry_points('oarepo_iiif.openers'):
            openers.append(entry_point.load())
        openers.sort(key=lambda opener: -getattr(opener, '_priority', 10))
        return openers

    @cached_property
    def checks(self):
        checks = []
        for entry_point in pkg_resources.iter_entry_points('oarepo_iiif.checks'):
            checks.append(entry_point.load())
        checks.sort(key=lambda check: -getattr(check, '_priority', 10))
        return checks

    @cached_property
    def identifier_makers(self):
        identifier_makers = []
        for entry_point in pkg_resources.iter_entry_points('oarepo_iiif.identifier_makers'):
            identifier_makers.append(entry_point.load())
        identifier_makers.sort(key=lambda identifier: -getattr(identifier, '_priority', 10))
        return identifier_makers

    def get_iiif_urls(self, record=None, pid=None, file=None, **kwargs):
        for identifier_maker in self.identifier_makers:
            data = identifier_maker(record=record, pid=pid, file=file, **kwargs)
            if data is None:
                continue
            if isinstance(data, str):
                return make_iiif_url(data)
            elif isinstance(data, (list, tuple)):
                return [make_iiif_url(x) for x in data]
            elif isinstance(data, dict):
                return {k: make_iiif_url(v) for k, v in data}
            else:
                raise Exception('Unhandled IIIF identifier type %s' % type(data))

        obj = file.get_version()
        if not obj.mimetype.startswith('image/'):
            return
        return make_iiif_url(iiif_image_key(obj))


class OARepoIIIFExt:
    def __init__(self, app, db=None):
        self.init_app(app)

    def init_app(self, app):
        app.extensions['oarepo-iiif'] = OARepoIIIFExtState(app)


@app_loaded.connect
def loaded(sender, app=None, **kwargs):
    with app.app_context():
        current_oarepo_iiif = app.extensions['oarepo-iiif']
        _ = current_oarepo_iiif.openers  # read and discard to detect errors
        _ = current_oarepo_iiif.checks  # to openers and checks during app loading

        iiif_ext = current_app.extensions['invenio-iiif'].iiif_ext
        prev_opener = iiif_ext.uuid_to_image_opener

        iiif_ext.uuid_to_image_opener_handler(
            lambda *args, **akwargs: current_oarepo_iiif.open(*args, app=app, **akwargs) or prev_opener(*args,
                                                                                                        **akwargs)
        )

        prev_decorator_handler = iiif_ext.api_decorator_callback

        def decorator_handler(*args, **akwargs):
            ret = current_oarepo_iiif.check(*args, app=app, **akwargs)
            if ret is not None:
                return ret
            return prev_decorator_handler(*args, **akwargs)

        iiif_ext.api_decorator_handler(decorator_handler)


try:
    from oarepo_records_draft.signals import file_uploaded_before_flush, after_publish_record, file_copied
    from invenio_records_files.api import FileObject


    def make_iiif_url(identifier):
        return u'{scheme}://{server}{prefix}v2/{identifier}'.format(
            scheme=current_app.config["PREFERRED_URL_SCHEME"],
            server=current_app.config["SERVER_NAME"],
            prefix=current_app.config['IIIF_UI_URL'],
            identifier=quote(identifier.encode('utf8'), safe=':')
        )


    @file_uploaded_before_flush.connect
    def file_uploaded(sender, record=None, pid=None, file: FileObject = None, **kwargs):
        iiif_urls = current_oarepo_iiif.get_iiif_urls(record=record, pid=pid, file=file, **kwargs)
        if iiif_urls:
            file['iiif'] = iiif_urls


    @after_publish_record.connect
    def file_after_publish(sender, published_record, published_pid, **kwargs):
        # replace all IIIF urls with a new set
        files = published_record.files
        for file in files:
            iiif_urls = current_oarepo_iiif.get_iiif_urls(record=published_record, pid=published_pid,
                                                          file=file, **kwargs)
            if iiif_urls:
                file['iiif'] = iiif_urls
        files.flush()
        published_record.commit()


    @file_copied.connect
    def replace_urls(sender, source_record=None, target_record=None,
                     object_version=None, tags=None, metadata=None,
                     source_record_context=None, target_record_context=None,
                     **kwargs):
        if 'iiif' in metadata:
            metadata['iiif'] = metadata['iiif'].replace(
                f'api/iiif/v2/img:{source_record_context.record_pid.pid_type}',
                f'api/iiif/v2/img:{target_record_context.record_pid.pid_type}',
            )

except ImportError:
    pass
