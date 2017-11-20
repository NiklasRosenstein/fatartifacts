+++
title = "Layers"
+++

## Database

### BASE `fatartifacts.base.database.PonyDatabase`

### IMPL `fatartifacts.contrib.ponydb.PonyDatabase`

A database implementation using Pony-ORM. Can be connected to anything that
Pony supports, for example SQLite, PostgreSQL and MySQL.

## Storage

### BASE `fatartifacts.base.storage.Storage`

### BASE `fatartifacts.contrib.fsstorage.FsStorage`

Manages objects on the local-filesystem under one common directory.

### IMPL `fatartifacts.contrib.azureblobstorage.AzureBlobStorage`

Manages objects on an Azure Blob Storage account.

## AccessControl

### BASE `fatartifacts.base.accesscontrol.AccessControl`

### IMPL `fatartifacts.contrib.simpleac.SimpleAccessControl`

Global read, user-bound write/delete, optionally group IDs must be prefixed
with the user ID.

## REST Api Authentication

### BASE `fatartifacts.web.auth.Authorizer`

### IMPL `fatartifacts.web.auth.HardcodedAuthorizer`

Hardcode usernames and password-hashes with a Python dictionary. Example:

```python
auth = HardcodedAuthorizer({
  'root': 'md5:7c9fb847d117531433435b68b61f91f6'
})
```
