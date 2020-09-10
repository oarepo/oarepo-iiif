import os
import shutil
import sys

import invenio_iiif.previewer
import pytest
from flask import Flask
from invenio_base.signals import app_loaded
from invenio_db import InvenioDB
from invenio_db import db as _db
from invenio_iiif import InvenioIIIFAPI
from invenio_rest import InvenioREST
from sqlalchemy_utils import create_database, database_exists

from oarepo_iiif.ext import OARepoIIIFExt


@pytest.fixture()
def app():
    """Flask applicat-ion fixture."""
    instance_path = os.path.join(sys.prefix, 'var', 'test-instance')

    # empty the instance path
    if os.path.exists(instance_path):
        shutil.rmtree(instance_path)
    os.makedirs(instance_path)

    os.environ['INVENIO_INSTANCE_PATH'] = instance_path

    app_ = Flask('invenio-records-draft-testapp', instance_path=instance_path)
    app_.config.update(
        TESTING=True,
        JSON_AS_ASCII=True,
        SERVER_NAME='localhost:5000',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI',
            'sqlite:///:memory:'),
        SECURITY_PASSWORD_SALT='TEST_SECURITY_PASSWORD_SALT',
        SECRET_KEY='TEST_SECRET_KEY',
        INVENIO_INSTANCE_PATH=instance_path,
        RECORDS_REST_ENDPOINTS={},
    )

    InvenioDB(app_)
    InvenioREST(app_)
    InvenioIIIFAPI(app_)
    OARepoIIIFExt(app_)

    app_.register_blueprint(invenio_iiif.previewer.blueprint, url_prefix='/api/iiif/')

    app_loaded.send(None, app=app_)

    with app_.app_context():
        yield app_


@pytest.fixture
def db(app):
    """Create database for the tests."""
    with app.app_context():
        if not database_exists(str(_db.engine.url)) and \
                app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite://':
            create_database(_db.engine.url)
        _db.create_all()

    yield _db

    # Explicitly close DB connection
    _db.session.close()
    _db.drop_all()


@pytest.yield_fixture()
def client(app):
    """Get test client."""
    with app.test_client() as client:
        print(app.url_map)
        yield client
