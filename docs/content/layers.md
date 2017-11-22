+++
title = "Layers"
+++

This section describes the available layers and their implementations
delivered with FatArtifacts.

## Database

### `fatartifacts.database.base.Database`

### `fatartifacts.database.ponyorm.PonyDatabase`

A database implementation using Pony-ORM. Can be connected to anything that
Pony supports, for example SQLite, PostgreSQL and MySQL.

## Storage

### `fatartifacts.storage.base.Storage`

### `fatartifacts.storage.fs.FsStorage`

Manages objects on the local-filesystem under one common directory.

### `fatartifacts.storage.azureblob.AzureBlobStorage`

Manages objects on an Azure Blob Storage account.

```python
from fatartifacts.storage.azureblob import AzureBlobStorage
storage = AzureBlobStorage.with_blob_block_service(
  container = 'MyContainerName',
  account_name='MyFatArtifacts',
  account_key='AZUREACCOUNTAPIKEYHERE...'
)
```

## AccessControl

### `fatartifacts.accesscontrol.base.AccessControl`

### `fatartifacts.accesscontrol.userspace.UserSpaceAccessControl`

## REST Api Authentication

### `fatartifacts.web.auth.Authorizer`

### `fatartifacts.web.auth.HardcodedAuthorizer`

Hardcode usernames and password-hashes with a Python dictionary. Example:

```python
auth = HardcodedAuthorizer({
  'root': 'md5:7c9fb847d117531433435b68b61f91f6'
})
```
