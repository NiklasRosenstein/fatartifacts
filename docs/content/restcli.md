+++
title = "REST-Cli"
+++

The `fatartifacts-rest-cli` allows you to retrieve, upload and delete
artifact-objects via the FatArtifacts REST-Api.

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
