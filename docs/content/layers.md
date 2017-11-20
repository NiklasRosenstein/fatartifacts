+++
title = "Layers"
+++

## Database

### `fatartifacts.base.database.Database`

### `fatartifacts.contrib.ponydb.PonyDatabase`

A database implementation using Pony-ORM. Can be connected to anything that
Pony supports, for example SQLite, PostgreSQL and MySQL.

## Storage

### `fatartifacts.base.storage.Storage`

### `fatartifacts.contrib.fsstorage.FsStorage`

Manages objects on the local-filesystem under one common directory.

### `fatartifacts.contrib.azureblobstorage.AzureBlobStorage`

Manages objects on an Azure Blob Storage account.

## AccessControl

### `fatartifacts.base.accesscontrol.AccessControl`

### `fatartifacts.contrib.simpleac.SimpleAccessControl`

Global read, user-bound write/delete, optionally group IDs must be prefixed
with the user ID.

## REST Api Authentication

### `fatartifacts.web.auth.Authorizer`

### `fatartifacts.web.auth.HardcodedAuthorizer`

Hardcode usernames and password-hashes with a Python dictionary. Example:

```python
auth = HardcodedAuthorizer({
  'root': 'md5:7c9fb847d117531433435b68b61f91f6'
})
```
