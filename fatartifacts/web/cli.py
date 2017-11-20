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
  ''',
  nargs='?'
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
parser.add_argument('-d', '--delete', action='store_true', help='''
  Delete the object from the repository. Do not specify a FILE argument
  when using this option.
  '''
)
parser.add_argument('-o', '--output', help='''
  Download an object to the specified file. Use -o- to download to stdout.
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

  # Split the artifact object identifier into parts.
  parts = args.object.split(':')
  if len(parts) != 4:
    print('error: invalid artifact object id:', args.object)
    return 1

  # Ensure the URL has a schema (adds HTTPS).
  args.apiurl = args.apiurl.rstrip('/') + '/{}/{}/{}/{}'.format(*parts)
  if not urllib.parse.urlparse(args.apiurl).scheme:
    args.apiurl = 'https://' + url

  # Ensure only one operation is specified (get, put, delete).
  if sum(map(bool, (args.output, args.file, args.delete))) != 1:
    print('error: incompatible arguments, specify one operation only.')
    return 1

  if args.file:
    # Create a default value for the -n, --name option.
    if not args.name:
      args.name = os.path.basename(args.file.name)

    # Try to guess the MIME type.
    args.mime = mimetypes.guess_type(args.name)[0] or mimetypes.guess_type(args.file.name)[0]
    if not args.mime:
      print('error: unable to guess MIME type. Specify -m, --mime')
      return 1

  # Create the request headers.
  headers = {}
  if args.output:
    method = 'GET'
  elif args.file:
    method = 'PUT'
    headers['Content-Name'] = args.name
    headers['Content-Type'] = args.mime
  elif args.delete:
    method = 'DELETE'

  # Split username and password. Request the password if it was omitted.
  # Then add the Authorization header.
  auth_only_headers = {}
  if args.auth:
    username, password = args.auth.partition(':')[::2]
    if ':' not in args.auth:
      password = getpass.getpass('Password for {}:'.format(username))
      if not password:
        return 1
    auth_only_headers['Authorization'] = build_basicauth(username, password)
    headers.update(auth_only_headers)

  # If this is just a test, build a cURL command-line and print it.
  if args.test:
    command = ['curl', '-X', method, args.apiurl]
    for key, value in headers.items():
      command += ['-H', '{}: {}'.format(key, value)]
    if args.file:
      command += ['-d', '@' + args.file.name]
    print('$', ' '.join(map(shlex.quote, command)))
    return 0

  # Issue the request.
  response = requests.request(method, args.apiurl, headers=headers)
  data = response.json()
  if response.status_code != 200:
    print('error:', data['message'])
    return 2

  if args.output:
    data = response.json()
    download_url = urllib.parse.urljoin(args.apiurl, data['url'])
    response = requests.get(download_url, headers=auth_only_headers, stream=True)
    try:
      response.raise_for_status()
    except requests.exceptions.HTTException as exc:
      print('error:', exc)
      return 3

    if args.output == '-':
      for chunk in response.iter_content(1024):
        sys.stdout.buffer.write(chunk)
    else:
      with open(args.output, 'wb') as fp:
        for chunk in response.iter_content(1024):
          fp.write(chunk)


def main_and_exit(argv=None):
  sys.exit(main())


if __name__ == '__main__':
  main_and_exit()
