import threading
import _mysql
from settings import Settings

database_lock = threading.Lock()

try:
  # Although SQLAlchemy is optional, it is highly recommended
  import sqlalchemy.pool as pool  
  _mysql = pool.manage( module = _mysql,
                        pool_size = Settings.DATABASE_POOL_SIZE,
                        max_overflow = Settings.DATABASE_POOL_OVERFLOW)
  Settings._.USING_SQLALCHEMY = True
except ImportError:
  pass

def ConnectDb():
  """
  Get a connection to the database
  """
  return _mysql.connect(host = Settings.DATABASE_HOST,
                        user = Settings.DATABASE_USERNAME,
                        passwd = Settings.DATABASE_PASSWORD,
                        db = Settings.DATABASE_DB)

def FetchAll(query, method=1):
  """
  Query and fetch all results as a list
  """
  db = ConnectDb()
  try:
    db.query(query)
    r = db.use_result()
    return r.fetch_row(0, method)
  finally:
    db.close()

def FetchOne(query, method=1):
  """
  Query and fetch only the first result
  """
  db = ConnectDb()
  try:
    db.query(query)
    r = db.use_result()
    try:
      return r.fetch_row(1, method)[0]
    except:
      return None
  finally:
    db.close()

def UpdateDb(query):
  """
  Update the DB (UPDATE/DELETE) and return # of affected rows
  """
  db = ConnectDb()
  try:
    db.query(query)
    return db.affected_rows()
  finally:
    db.close()
    
def InsertDb(query):
  """
  Insert into the DB and return the primary key of new row
  """
  db = ConnectDb()
  try:
    db.query(query)
    return db.insert_id()
  finally:
    db.close()
