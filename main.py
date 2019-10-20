"""Upload the contents of your Downloads folder to Dropbox.

This is an example app for API v2.
"""

from __future__ import print_function

import logging
import logging.config
import ConfigParser
import yaml
import argparse
import contextlib
import datetime
import os
import six
import sys
import time
import unicodedata

if sys.version.startswith('2'):
    input = raw_input  # noqa: E501,F821; pylint: disable=redefined-builtin,undefined-variable,useless-suppression

import dropbox


parser = argparse.ArgumentParser(description='Sync Dropbox content to a specified folder')
parser.add_argument('folder', nargs='?', default='/',
                    help='Folder name in your Dropbox. Default is /')
parser.add_argument('--yes', '-y', action='store_true',
                    help='Answer yes to all questions')
parser.add_argument('--no', '-n', action='store_true',
                    help='Answer no to all questions')
parser.add_argument('--default', '-d', action='store_true',
                    help='Take default answer on all questions')

def main():
    """Main program.

    Parse command line, then iterate over files and directories under
    rootdir and upload all files.  Skips some temporary files and
    directories, and avoids duplicate uploads by comparing size and
    mtime with the server.
    """
    with open('logging.conf', 'r') as f:
        log_cfg = yaml.safe_load(f.read())
        logging.config.dictConfig(log_cfg)

    current_folder = ''
    current_file = ''
    folders_checked = 0
    files_checked = 0
    files_downloaded = 0

    try:
        args = parser.parse_args()
        if sum([bool(b) for b in (args.yes, args.no, args.default)]) > 1:
            logging.error('At most one of --yes, --no, --default is allowed')
            sys.exit(2)

        folder = args.folder

        config = ConfigParser.ConfigParser()
        config.read("config.ini")
        token = config.get("dropbox", "token")
        directory = config.get("local", "localdirectory")

        dbx = dropbox.Dropbox(token)

        logging.info('Connected!')

        for filename in os.listdir(directory):
            path = '%s/%s' % (directory.replace(os.path.sep, '/'), filename)
            while '//' in path:
                path = path.replace('//', '/')

            if os.path.isfile(path):
                upload(dbx, path, '/Personal Documents', 'test', filename, False)
                uploadedpath = '%s/uploaded/%s' % (directory.replace(os.path.sep, '/'), filename)
                while '//' in path:
                    uploadedpath = uploadedpath.replace('//', '/')
                os.rename(path, uploadedpath)
        

    except Exception:
        logging.exception("While handling %s/%s :", current_folder, current_file)
        logging.error("folders_checked = %i; files_checked = %i; files_downloaded = %i", folders_checked, files_checked, files_downloaded)



def upload(dbx, fullname, folder, subfolder, name, overwrite=False):
    """Upload a file.

    Return the request response, or None in case of error.
    """
    path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
    while '//' in path:
        path = path.replace('//', '/')
    mode = (dropbox.files.WriteMode.overwrite
            if overwrite
            else dropbox.files.WriteMode.add)
    mtime = os.path.getmtime(fullname)
    with open(fullname, 'rb') as f:
        data = f.read()
    with stopwatch('upload %d bytes' % len(data)):
        try:
            res = dbx.files_upload(
                data, path, mode,
                client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
                mute=True)
        except dropbox.exceptions.ApiError as err:
            logging.error('*** API error', err)
            return None
    # logging.info('uploaded as', res.name.encode('utf8'))
    return res

def yesno(message, default, args):
    """Handy helper function to ask a yes/no question.

    Command line arguments --yes or --no force the answer;
    --default to force the default answer.

    Otherwise a blank line returns the default, and answering
    y/yes or n/no returns True or False.

    Retry on unrecognized answer.

    Special answers:
    - q or quit exits the program
    - p or pdb invokes the debugger
    """
    if args.default:
        print(message + '? [auto]', 'Y' if default else 'N')
        return default
    if args.yes:
        print(message + '? [auto] YES')
        return True
    if args.no:
        print(message + '? [auto] NO')
        return False
    if default:
        message += '? [Y/n] '
    else:
        message += '? [N/y] '
    while True:
        answer = input(message).strip().lower()
        if not answer:
            return default
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False
        if answer in ('q', 'quit'):
            print('Exit')
            raise SystemExit(0)
        if answer in ('p', 'pdb'):
            import pdb
            pdb.set_trace()
        print('Please answer YES or NO.')

@contextlib.contextmanager
def stopwatch(message):
    """Context manager to print how long a block of code took."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        logging.debug('Total elapsed time for %s: %.3f' % (message, t1 - t0))

if __name__ == '__main__':
    main()
