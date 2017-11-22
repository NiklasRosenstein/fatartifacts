+++
title = "REST-Api"
+++

## API Documentation

### GET `/info`

Returns REST-Api related information about the repository.

* `numLevels`: The number of levels as specified by the configured database.
  This value defines the maximum number of elements in a location string and
  the level at which objects are stored.

### GET `/location`
### GET `/location/<location>`

Returns the contents of the specified location and its child locations.

* `status`: The string `Result` on success
* `location`: A LocationInfo (if the location is not an object)
* `object`: An ObjectInfo (if the location is an object)

__LocationInfo__

* `location`: The absolute location string.
* `metadata`: A JSON object of the location's metadata.
* `dataCreated`:
* `dateUpdated`:
* `children`: list of LocationInfo (only if the children are not objects)
* `objects`: list of ObjectInfo (only if the children are objects)

__ObjectInfo__

* `location`: The absolute location string.
* `metadata`: A JSON object of the object's metadata.
* `dataCreated`:
* `dateUpdated`:
* `filename`:
* `mime`:
* `url`:

### PUT `/location/<location>`

Creates a location or updates it's metadata. Depending on whether *location*
is a namespace or an object, the format is different. The following headers
are supported/required:

* `X-Update-If-Exists`: `1` if the location's metadata should be updated if it exists.
* `Content-Type`: `application/json` or not-set for namespace PUT requests,
  otherwise `application/vnd.fatartifacts+putobject`.
* `Content-Length`: The length of the upload payload (combined metadata and
  object content for object PUT requests).
* `X-Metadata-Length`: The length of the metadata the preceedes the content
  of the object (for object PUT requests only).
* `X-File-Name`: The name of the file that is being uploaded (for object
  PUT requests only).
* `X-File-ContentType`: The MIME type of the file that is being uploaded (for object
  PUT requests only).

Example namespace PUT request:

    $ curl -X PUT example-repo.org/location/example:test \
      -H 'X-Update-If-Exists: 1' \
      -H 'Content-Type: application/json' \
      -d '{"description": "This is the example:test namespace."}'
    {"status": "Created", "at": "example:test"}

Example object PUT request:

    $ curl -X PUT example-repo.org/location/example:test:1.0:txt \
      -H 'X-Update-If-Exists: 1' \
      -H 'X-Metadata-Length: 37' \
      -H 'X-File-Name: hello.txt' \
      -H 'X-File-ContentType: text/plain' \
      -H 'Content-Type: application/vnd.fatartifacts+putobject' \
      -d '{"description": "This is an object."}Hello, World!'
    {"status": "Created", "at": "example:test:1.0:txt"}

### DELETE `/location/<location>`

Deletes a namespace or an object.

* `X-Recursive-Delete`: `1` if the location should be deleted recursively.

Example DELETE request:

    $ curl -X DELETE example-repo.org/location/example \
      -H 'X-Recursive-Delete: 1'
