<img src=".assets/fa-logo.png" height="128px">

## FatArtifacts

FatArtifacts is a modular abstraction  of a general-purpose artifact
repository, plus standard implementations. The following stuff comes
out-of-the-box with FatArtifacts:

__Database__

* `PonyDatabase` (database implementation using Pony-ORM, connectible to
  anything that Pony supports, eg. SQLite, PostgreSQL, MySQL)

__Storage__

* `FsStorage` (store artifacts on the local filesystem)

__AccessControl__

* `SimpleAccessControl` (global read, user-bound write/delete, optionally
  group IDs must be prefixed with the user ID)

__Flask REST API__

* `fatartifacts.web.rest` (REST API Flask Blueprint)
* `HardcodedAuthorizer` (specify usernames and (hashed-) passwords directly
  in the server configuration)

__CLI__

* `fatartifacts-rest-cli` (Uses the Flask REST API to upload objects to the
  repository)

__Todo__

* `StorageLimits` (Control rate and size limits of the storage in the Flask REST API)
* `AzureBlobStorage` (Store files on Azure Blob Storage)

### REST API

The REST API can be embedded into existing Flask applications using the
`fatartifacts.web.rest.app` blueprint. Alternatively, you can serve the
REST API using the `fatartifacts.web.server.app` Flask application.

> **Important**: Make sure you update the `fatartifacts_server_config.py`
> before you use the built-in server.
>
> The `HardcodedAuthorizer` (from the `fatartifacts.web.auth` module)
> uses HTTP BasicAuth and the information passed to it's constructor.

Get it running:

    $ FLASK_APP=fatartifacts/web/server.py flask run

Example requests:

    $ curl localhost:5000/
    ["com.coolinc"]
    $ curl localhost:5000/com.coolinc
    ["coolsoftware"]
    $ curl localhost:5000/com.coolinc/coolsoftware
    ["1.0.0", "1.1.0", "1.1.1", "1.1.2", "1.2.0", "1.3.0"]
    $ curl localhost:5000/com.coolinc/coolsoftware/1.3.0
    {
      "win32-x86_64": {
        "filename": "coolsoftware-1.3.0-win32-x86_64.exe",
        "mime": "application/octet",
        "url": "/read/com.coolinc/coolsoftware/1.3.0/win32-x86_64"
      },
      "darwin-x86_64": {
        "filename": "coolsoftware-1.3.0-darwin-x86_64.dmg",
        "mime": "application/octet",
        "url": "/read/com.coolinc/coolsoftware/1.3.0/darwin-x86_64"
      }
    }
    $ curl -X PUT http://com.coolinc:PleaseDontStealMySecrets@localhost:5000/com.coolinc/coolsoftware/1.3.0/linux-x86_64 \
      -H 'Content-Type: application/octet' \
      -H 'Content-Name: coolsoftware-1.3.0-linux-x86_64.deb' \
      -d @build/dist.deb
    {
      "message": "Object com.coolinc:coolsoftware:1.3.0:linux-x86_64 created."
    }


#### GET `/`

List all available artifact group IDs with read-access.

#### GET `/<group_id>`

List all available artifacts in the group *group_id* with read-access.

#### GET `/<group_id>/<artifact_id>`

List all available artifact versions of the artifact *artifact_id* in the
group *group_id*. Returns 404 if you do not have read-access to the group
or artifact.

#### GET `/<group_id>/<artifact_id>/<version>`

Returns an object that maps tag-names to an ObjectWithoutTag. Returns 404
if you do not have read-access to the group or artifact.

_ObjectWithoutTag_

* `filename`: The filename of the object.
* `mime`: The mimetype of the object.
* `url`: The download URL of the object.

#### GET `/<group_id>/<artifact_id>/<version>/<tag>`

Returns an ObjectWithTag. Returns 404 if you do not have read-access to the
group or artifact.

_ObjectWithTag extends ObjectWithoutTag_

* `tag`: The tag of the object.

#### PUT `/<group_id>/<artifact_id>/<version>/<tag>`

Upload an artifact object. Returns 403 if you do not have write-access to the
group or artifact.

_Headers_

* `Content-Name`: The filename of the uploaded object.
* `Content-Type`: The mimetype of the file.

#### DELETE `/<group_id>/<artifact_id>/<version>/<tag>`

Deletes an artifact object. Returns 403 if you do not have delete-access to
the group or artifact.

### `fatartifacts-rest-cli`

```
usage: fatartifacts-rest-cli [-h] [-n NAME] [-m MIME] [-u AUTH] [-d]
                             [-o OUTPUT] [--test] [--forward-auth]
                             apiurl object [file]

The FatArtifacts CLI for the REST API to upload artifacts.

positional arguments:
  apiurl                The FatArtifacts REST API base url.
  object                The object ID in the format
                        <group>:<artifact>:<version>:<tag>.
  file                  The file that is to be uploaded to the repository.

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  The filename to save with the object. If not
                        specified, the name of the input file is used.
  -m MIME, --mime MIME  The mimetype. If not specified, it will be
                        automatically determined from the input file suffix.
                        If it can not be determined, an error will be printed
                        and 1 will be returned as exit-code. If you're unsure
                        whether the guesser works correctly with your
                        filetype, you can use the --test argument dump all the
                        information that would be sent.
  -u AUTH, --auth AUTH  HTTP BasicAuth parameters in the format
                        <user>:<password>. The :<password> part can be
                        omitted, in which case the password will be requested
                        via stdin.
  -d, --delete          Delete the object from the repository. Do not specify
                        a FILE argument when using this option.
  -o OUTPUT, --output OUTPUT
                        Download an object to the specified file. Use -o- to
                        download to stdout.
  --test                Print the information that would be sent to the
                        repository and exit.
  --forward-auth        Pass the same HTTP BasicAuth information when
                        downloading the file. This may be necessary for
                        private artifact repositories.
```
