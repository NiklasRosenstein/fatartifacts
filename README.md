<img src=".assets/fa-logo.png" height="128px">

## FatArtifacts

FatArtifacts is a general-purpose artifact repository application with a
REST-Api. It's granular design makes it very scalable and a great choice to
fit your custom requirements. If you just want a simple artifact repository
though, rolling with the standard layers will get you rolling quickly!

With FatArtifact's abstraction layers, you have fine-grained control over
the following aspects (standard implementations available in FatArtifacts
in parentheses):

* Database-store method (eg. `PonyDatabase` which supports many SQL database)
* Artifact-object store method (eg. `FsStorage` or `AzureBlobStorage`)
* User authentication and permissions (eg. `HardcodedAuthorizer`)
* Rate and object-size limiting (**TODO**)

It is very likely that you'll be able to roll with the default layers, except
maybe for the permission-layer, which you might want to connect to your own
authorization method (eg. authorization with existing user credentials from
another application).

Check out the [Documentation] for more information.

  [Documentation]: https://niklasrosenstein.github.io/fatartifacts
