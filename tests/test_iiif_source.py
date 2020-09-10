from io import BytesIO

import pytest
import werkzeug
from PIL import Image
from werkzeug.exceptions import NotFound

from oarepo_iiif import current_oarepo_iiif


def test_iiif_source(app):
    def test_opener(image_id, **kwargs):
        img = Image.new('RGB', (10, 10), color='red')
        f = BytesIO()
        img.save(f, format='PNG')
        return f.getvalue()

    current_oarepo_iiif.openers.append(test_opener)

    iiif_ext = app.extensions['invenio-iiif'].iiif_ext
    opener = iiif_ext.uuid_to_image_opener

    assert opener('test') == test_opener('test')


def test_unavailable_source(app, db):
    def test_opener(image_id, **kwargs):
        if image_id != 'test':
            return None
        img = Image.new('RGB', (10, 10), color='red')
        f = BytesIO()
        img.save(f, format='PNG')
        return f.getvalue()

    current_oarepo_iiif.openers.append(test_opener)

    iiif_ext = app.extensions['invenio-iiif'].iiif_ext
    opener = iiif_ext.uuid_to_image_opener

    assert opener('test') == test_opener('test')
    with pytest.raises(NotFound):
        opener('7b1a05fe-c703-470e-b44d-97d3895bb9c5:f582d95e-507e-49a4-ae06-4d19ce4f6d0a:key')


