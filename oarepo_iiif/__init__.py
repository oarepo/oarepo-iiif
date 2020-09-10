from flask import current_app
from werkzeug.local import LocalProxy

current_oarepo_iiif = LocalProxy(
    lambda: current_app.extensions['oarepo-iiif'])  # type: oarepo_iiif.ext.OARepoIIIFExtState
