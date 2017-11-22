<img src=".assets/fa-logo.png" height="128px">

## FatArtifacts

FatArtifacts is a general-purpose, highly customizable and extensible artifact
repository.

__Features__

* High level of abstraction
* Fine-grain permission control
* Configurable namespace-depth
* Allows you to associate arbitrary JSON metadata with every namespace
* Built-in support for Azure Blob Storage and standard SQL databases
* REST-Api included

__Deployment__

1. **Clone the repository** and install the requirements with Pip or Pipenv
2. **Update the configuration file** named `fatartifacts_server_config.py`
3. **Start the server** with `FLASK_APP=fatartifacts/web/server.py flask run`

You may want to choose a different production server than the standard Flask
WSGI server (eg. eventlet or gunicorn).

---

Check out the [Documentation] for more information.

  [Documentation]: https://niklasrosenstein.github.io/fatartifacts
