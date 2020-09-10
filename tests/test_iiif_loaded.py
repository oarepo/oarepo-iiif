from oarepo_iiif import current_oarepo_iiif


def test_iiif_loaded(app):
    assert current_oarepo_iiif.openers == []
