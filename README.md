# OAREPO IIIF

[![image][]][1]
[![image][2]][3]
[![image][4]][5]
[![image][6]][7]

This package adds support for input loaders for IIIF server

## Rationale

We would like to add support for loading images from non-image source. For example,
loading n-th image from a PDF file, converting data into graphs etc.

## Invenio support for IIIF

Invenio has support for IIIF server via invenio-iiif package. Unfortunately there is no 
extensibility mechanism for loading images from non-image sources.

This package adds this support.

## Usage

### Opener functions

Create an opener and register it to entry point ``oarepo_iiif.openers`` . The ``uuid``
contains an identification of the image. It is up to you to parse and interpret it.

```
def pdf_opener(uuid, app=None, **kwargs):   # kwargs currently empty but keep them for extensibility
    return binary stream of image data or None if can not handle the uuid  
```

### Check functions

If the opener loads data not from file buckets but from another location,
you have to register a function that checks access (and raises werkzeug exception
if the access is denied). The entry point for this function is ``oarepo_iiif.checks``.

```
def pdf_check(uuid, app=None, **kwargs):        # kwargs might contain 'version', 'region', 'size', 'rotation', 'quality', 'image_format'
    """
        check permissions and return 
            * True if the access is ok 
            * None if can not handle
            * raise an exception if access denied
    """
    return True
```

See [rest test](tests/test_rest.py) for an example of these functions.

### Indentifier creating functions (optional)

Optionally register an identifier creating function under entrypoint ``oarepo_iiif.identifier_makers``.
The function gets invenio-record-files' FileObject and Record and should produce identifier
used in checks & openers.

```
def pdf_identifier(record: Record, file:FileObject, pid:PersistentIdentifier, app=None, **kwargs):
    """
        return crafted PDF identifier
    """
    return 'pdf-images:{recid}:{key}'.format(recid=record.id, key=file['key'])
```

 

Then power up the server and hit IIIF url:

```bash

curl https://127.0.0.1:5000/api/iiif/v2/<uuid>/<region>/<size>/<rotation>/<quality>.<format>

```

## Integration with ``oarepo-records-draft``

``oarepo-records-draft`` adds support for uploading attachments with easier security checks than
those in ``invenio-files-rest`` or ``invenio-record-files``.

Moreover, it provides a set of callbacks that are called whenever a file is associated to a record.
If ``oarepo-records-draft`` is detected, a custom handler is registered for ``attachment_uploaded_before_commit``.

The handler 

## How it works (for library developers)

As extensibility mechanism is not available, this library overrides invneio-iiif ``uuid_to_image_opener`` 
and ``api_decorator_callback`` in the ``app_loaded`` callback. Keep this in mind if you have libraries
that perform similar task.

```python
@app_loaded.connect
def loaded(sender, app=None, **kwargs):
    with app.app_context():
        current_oarepo_iiif = app.extensions['oarepo-iiif']
        iiif_ext = current_app.extensions['invenio-iiif'].iiif_ext
    
        # replace opener
        prev_opener = iiif_ext.uuid_to_image_opener
        iiif_ext.uuid_to_image_opener_handler(
            lambda *args, **akwargs: current_oarepo_iiif.open(*args, app=app, **akwargs) or prev_opener(*args, **akwargs)
        )
    
        # replace decorator handler
        prev_decorator_handler = iiif_ext.api_decorator_callback
        def decorator_handler(*args, **akwargs):
            ret = current_oarepo_iiif.check(*args, app=app, **akwargs)
            if ret is not None:
                return ret
            return prev_decorator_handler(*args, **akwargs)

        iiif_ext.api_decorator_handler(decorator_handler)
```


  [image]: https://img.shields.io/github/license/oarepo/oarepo-iiif.svg
  [1]: https://github.com/oarepo/oarepo-iiif/blob/master/LICENSE
  [2]: https://img.shields.io/travis/oarepo/oarepo-iiif.svg
  [3]: https://travis-ci.org/oarepo/oarepo-iiif
  [4]: https://img.shields.io/coveralls/oarepo/oarepo-iiif.svg
  [5]: https://coveralls.io/r/oarepo/oarepo-iiif
  [6]: https://img.shields.io/pypi/v/oarepo-iiif.svg
  [7]: https://pypi.org/pypi/oarepo-iiif