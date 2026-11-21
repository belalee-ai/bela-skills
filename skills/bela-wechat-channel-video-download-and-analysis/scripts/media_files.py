"""Publish a verified file staged on the destination filesystem."""

import errno
import hashlib
import os
from pathlib import Path


def publish_file(staged, destination):
    destination = Path(destination)
    if os.name == "nt":
        # Windows rename fails if destination already exists.
        os.rename(staged, destination)
        return
    try:
        os.link(staged, destination)
        return
    except OSError as error:
        if error.errno not in (errno.EPERM, errno.EXDEV, errno.ENOSYS, errno.ENOTSUP, errno.EOPNOTSUPP):
            raise

    # On mounts without hard links, serialize this filename's final rename.
    # A short hash also works for destination names near the filesystem limit.
    key = hashlib.sha256(os.fsencode(destination.name)).hexdigest()[:24]
    reservation = destination.parent / (".bela-publish-" + key)
    reservation.mkdir()
    try:
        if os.path.lexists(destination):
            raise FileExistsError(errno.EEXIST, "destination already exists", destination)
        os.rename(staged, destination)
    finally:
        reservation.rmdir()
