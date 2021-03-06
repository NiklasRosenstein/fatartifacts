
from fatartifacts.database.ponyorm import PonyDatabase
from fatartifacts.accesscontrol.userspace import UserSpaceAccessControl
from fatartifacts.storage.fs import FsStorage
from fatartifacts.web.auth import HardcodedAuthorizer
import os
import hashlib

storage_dir = os.path.abspath('_storage')

# User authorization layer. Note that the username returned by the authorizer
# must be understood by the accesscontrol.
auth = HardcodedAuthorizer({
  'root': 'sha1:' + hashlib.sha1('alpine'.encode('utf8')).hexdigest()
})

# Artifact access-control layer. Gives full permissions only to group IDs
# that are prefixed with the current user ID.
accesscontrol = UserSpaceAccessControl(isolate=False)

# Artifact database layer, with 4 levels (eg. group:artifact:version:tag).
database = PonyDatabase(num_levels=4)
database.connect('sqlite', os.path.join(storage_dir, 'db.sqlite'), create_db=True)

# Artifact storage layer.
storage = FsStorage(storage_dir)

#from fatartifacts.storage.azureblob import AzureBlobStorage
#storage = AzureBlobStorage.with_block_blob_service(
#  container = 'artifacts',
#  account_name = 'yellowunicorns',
#  account_key = 'rs41bCH1B1jHrsIQ122X4t+fVq9BvJ9zXzlDEy58EY/PKZKef4ew0WeA8PDoQDnRW5ZQSKgIKaaSISyvxZ1k7g=='
#)

# Set this to false if the Web URLs generated by the storage backend are not
# accesible without authentication. The REST API will generate URLs to the
# /read endpoint which will pipe the content of the storage to the user using
# their artifact repository credentials.
web_urls_are_public = True

# REST-Api prefix.
rest_prefix = '/api'

# HTML app prefix.
html_prefix = '/'
