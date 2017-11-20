"""
Command-line interface that uses the REST API.
"""

import argparse
import base64
import getpass
import mimetypes
import os
import urllib.parse
import requests
import shlex
import sys

parser = argparse.ArgumentParser(
  prog = 'fatartifacts-rest-cli',
  description = '''
    The FatArtifacts CLI for the REST API to upload artifacts.
  '''
)
parser.add_argument('apiurl', help='The FatArtifacts REST API base url.')
parser.add_argument('object', help='''
  The object ID in the format <group>:<artifact>:<version>:<tag>.
  '''
)
parser.add_argument('file', type=argparse.FileType('rb'), help='''
  The file that is to be uploaded to the repository.
  '''
)
parser.add_argument('-n', '--name', help='''
  The filename to save with the object. If not specified, the name of the
  input file is used.
  '''
)
parser.add_argument('-m', '--mime', help='''
  The mimetype. If not specified, it will be automatically determined from
  the input file suffix. If it can not be determined, an error will be
  printed and 1 will be returned as exit-code.

  If you're unsure whether the guesser works correctly with your filetype,
  you can use the --test argument dump all the information that would be
  sent.
  '''
 )
parser.add_argument('-u', '--auth', help='''
  HTTP BasicAuth parameters in the format <user>:<password>. The :<password>
  part can be omitted, in which case the password will be requested via stdin.
  '''
)
parser.add_argument('--test', action='store_true', help='''
  Print the information that would be sent to the repository and exit.
  '''
)

def build_basicauth(username, password):
  data = ('%s:%s' % (username, password)).encode('ISO-8859-1')
  return (b'Basic ' + base64.standard_b64encode (data)).decode('ascii')


def main(argv=None):
  args = parser.parse_args(argv)
  parts = args.object.split(':')
  if len(parts) != 4:
    print('error: invalid object ID:', args.object)
    return 1
  if not args.name:
    args.name = os.path.basename(args.file.name)
  if not args.mime:
    args.mime = mimetypes.guess_type(args.name)[0] or mimetypes.guess_type(args.file.name)[0]
    if not args.mime:
      print('error: MIME type could not be guess. Specify -m, --mime')
      return 1
  username = password = None
  if args.auth:
    username, password = args.auth.partition(':')[::2]
    if ':' not in args.auth:
      password = getpass.getpass('Password for {}:'.format(username))
      if not password:
        return 1

  headers = {'Content-Type': args.mime, 'Content-Name': args.name}
  if args.auth:
    headers['Authorization'] = build_basicauth(username, password)
  url = args.apiurl.rstrip('/') + '/{}/{}/{}/{}'.format(*parts)
  if not urllib.parse.urlparse(url).scheme:
    url = 'https://' + url

  if args.test:
    command = ['curl', '-X', 'PUT', url]
    for key, value in headers.items():
      command += ['-H', '{}: {}'.format(key, value)]
    command += ['-d', '@' + args.file.name]
    print('$', ' '.join(map(shlex.quote, command)))
    return 0

  response = requests.put(url, data=args.file, headers=headers)
  print(response.json()['message'])
  if response.status_code != 200:
    return 2
  return 0


def main_and_exit(argv=None):
  sys.exit(main())


if __name__ == '__main__':
  main_and_exit()
