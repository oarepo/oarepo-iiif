from PIL import Image
from io import BytesIO

from oarepo_iiif import current_oarepo_iiif


def test_rest_opener(app, db, client):
    def test_opener(image_id, **kwargs):
        img = Image.new('RGB', (int(image_id), int(image_id)), color='red')
        f = BytesIO()
        img.save(f, format='PNG')
        f.seek(0)
        return f

    def test_object_validator(uuid=None, **kwargs):
        return True

    current_oarepo_iiif.openers.append(test_opener)
    current_oarepo_iiif.checks.append(test_object_validator)

    resp = client.get('/iiif/v2/10/info.json')
    assert resp.content_type == 'application/json'
    assert resp.json == {
        '@context': 'http://iiif.io/api/image/2/context.json',
        '@id': 'http://localhost:5000/iiif/v2/10',
        'height': 10,
        'profile': ['http://iiif.io/api/image/2/level2.json'],
        'protocol': 'http://iiif.io/api/image',
        'tiles': [{'scaleFactors': [1, 2, 4, 8, 16, 32, 64], 'width': 256}],
        'width': 10
    }

    resp = client.get('/iiif/v2/10/full/400,/0/default.png')
    assert resp.content_type == 'image/png'
    img = Image.open(BytesIO(resp.data))
    assert img.size == (400, 400)
    assert img.getpixel((0,0)) == (255, 0, 0)

