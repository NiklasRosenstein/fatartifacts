
import collections
import threading


class ThreadedRWIO(object):
  """
  A file-like object that can be written from one thread and read from
  another. Allows piping data using #write() to another thread that uses
  #read() on the same file.
  """

  def __init__(self, type=bytes):
    assert type in (bytes, str)
    self._type = type
    self._deque = collections.deque()
    self._lock = threading.Lock()
    self._cond = threading.Condition(self._lock)
    self._write_closed = False
    self._read_pos = 0
    self._write_pos = 0

  def read(self, num_bytes=None):
    result = []
    bytes_read = 0
    with self._cond:
      while num_bytes is None or bytes_read < num_bytes:
        if not self._deque and self._write_closed:
          break
        elif not self._deque:
          self._cond.wait()  # wait for more data
        else:
          data = self._deque.popleft()
          if num_bytes and len(data) > num_bytes - bytes_read:
            delta = num_bytes - bytes_read
            data, remainder = data[:delta], data[delta:]
            self._deque.appendleft(remainder)
          result.append(data)
          bytes_read += len(data)
    data = self._type().join(result)
    self._read_pos += len(data)
    return data

  def write(self, data):
    if not isinstance(data, self._type):
      raise TypeError('expected {}, got {}'.format(self._type.__name__, type(data).__name__))
    with self._cond:
      if self._write_closed:
        raise RuntimeError('writing is closed')
      self._deque.append(data)
      self._cond.notify()
    self._write_pos += len(data)
    return len(data)

  def seekable(self):
    return False

  def readable(self):
    return True

  def writable(self):
    return True

  def tell(self):
    return self._read_pos

  def closed(self):
    return False

  def close(self):
    with self._cond:
      self._write_closed = True
      self._cond.notify_all()
