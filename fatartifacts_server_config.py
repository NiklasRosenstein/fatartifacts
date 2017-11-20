
from fatartifacts.contrib.simpleac import SimpleAccessControl
from fatartifacts.contrib.ponydb import PonyDatabase
from fatartifacts.contrib.fsstorage import FsStorage
import os

storage_dir = os.path.abspath('_storage')

accesscontrol = SimpleAccessControl()
database = PonyDatabase()
database.connect('sqlite', os.path.join(storage_dir, 'db.sqlite'), create_db=True)
storage = FsStorage(storage_dir)
