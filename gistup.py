
import importlib.util
import os
import json
import shutil
import sys
import uuid

import appdirs
import requests

CACHE_FOLDER = appdirs.user_cache_dir('gistup')
FILES = os.path.join(CACHE_FOLDER, 'files')


# The database maps URL to UUID
DB_FILE = os.path.join(CACHE_FOLDER, 'files.json')


def load_db():
    """Load database from disk
    """
    if not os.path.exists(DB_FILE):
        return dict()

    with open(DB_FILE, 'r', encoding='utf-8') as fi:
        return json.load(fi)


def save_db(db):
    """Save database to disk
    """
    with open(DB_FILE, 'w', encoding='utf-8') as fo:
        return json.dump(db, fo)


def download(remote, local):

    r = requests.get(remote)

    if r.status_code == requests.codes.ok:
        os.makedirs(os.path.dirname(local), exist_ok=True)
        with open(local, 'wb') as fo:
            fo.write(r.content)
    else:
        raise Exception('Could not download %s' % remote)


def from_file(local, mod=None):
    """Load a module from file.

    Parameters
    ----------
    local : str
        File path

    mod : str, optional
        Name of the module. (Default: basename of the file)

    Return
    ------
    module
        Loaded module
    """
    mod = mod or os.path.splitext(os.path.basename(local))[0]

    spec = importlib.util.spec_from_file_location(mod, local)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    sys.modules[mod] = module

    return module


def from_url(remote, force_download=False, mod=None):
    """Load a module from URL.

    Parameters
    ----------
    remote
        File URL

    force_download : bool, optional
        Download the module even if found in the cache (default: False)

    mod : str, optional
        Name of the module. (Default: basename of the file)

    Return
    ------
    module
        Loaded module
    """
    db = load_db()

    if force_download or remote not in db:
        id = uuid.uuid4().hex
        local = os.path.join(FILES, id) + '.py'
        download(remote, local)
        db[remote] = id
        save_db(db)
    else:
        id = db[remote]
        local = os.path.join(FILES, id) + '.py'

    mod = mod or os.path.splitext(os.path.basename(remote))[0]

    return from_file(local, mod)


def from_github(user, repo, mod, branch_commit='master', force_download=False):
    """Load a module from a GitHub specification.

    Parameters
    ----------
    user
        GitHub username

    repo
        Repository name

    mod
        Module name (the filename without '.py')

    branch_commit : str, optional
        Branch name or commit sha1 (default: 'master')

    force_download : bool, optional
        Download the module even if found in the cache (default: False)

    Return
    ------
    module
        Loaded module
    """

    filename = '%s.py' % mod

    remote = 'https://raw.githubusercontent.com/%s/%s/%s/%s' % (user, repo, branch_commit, filename)
    return from_url(remote, force_download, mod)


def clean_cache():
    """Delete the cache.
    """
    shutil.rmtree(CACHE_FOLDER)
