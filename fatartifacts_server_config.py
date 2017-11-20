
from fatartifacts.contrib.simpleac import SimpleAccessControl
from fatartifacts.contrib.ponydb import PonyDatabase
from fatartifacts.contrib.fsstorage import FsStorage
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
accesscontrol = SimpleAccessControl(enforce_prefix=True, isolate=False)

# Artifact database layer.
database = PonyDatabase()
database.connect('sqlite', os.path.join(storage_dir, 'db.sqlite'), create_db=True)

# Artifact storage layer.
storage = FsStorage(storage_dir)
