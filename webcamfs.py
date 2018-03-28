#!/usr/bin/python

import os
import sys
import errno
import cv2
import scipy.misc
import io
import time
import stat
from fuse import FUSE, FuseOSError, Operations


file_name = "webcam.bmp"

class WebCamFS(Operations):
    def __init__(self, root):
        self.root = root
        self.file_size = 0
        self.take_image()

    def take_image(self):
        vc = cv2.VideoCapture(0)
        vc.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        vc.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        rval, frame = vc.read()
        conv = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        inframe = scipy.misc.toimage(conv)
        
        self.file = io.BytesIO()
        inframe.save(self.file, 'bmp')
        self.file.seek(0, os.SEEK_END)
        self.file_size = self.file.tell()
        self.file.seek(0, os.SEEK_SET)      

    def _full_path(self, partial):
        partial = partial.lstrip("/")
        path = os.path.join(self.root, partial)
        return path

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        print("access", path, mode)
        if path not in ['.', '/', '/' + file_name]:
            raise FuseOSError(errno.ENOENT)
        if os.path.basename(path) == file_name and mode != os.R_OK:
            raise FuseOSError(errno.EACCES)
        if path in ['/', '.'] and mode == os.R_OK or mode == os.X_OK or mode == os.R_OK | os.X_OK:
            print("Access OK")
            return
        else:
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        if path != file_name:
            raise FuseOSError(errno.ENOENT)
        #Dissalow chmod? What error to raise?
        raise FuseOSError(errno.EACCES)

    def chown(self, path, uid, gid):
        if path != file_name:
            raise FuseOSError(errno.ENOENT)
        raise FuseOSError(errno.EACCES)

    def getattr(self, path, fh=None):
        print("getattr", path, fh)
        if path not in ['/' + file_name, '.', '/']:
            raise FuseOSError(errno.ENOENT)
        if os.path.basename(path) == file_name:
            # return {
            #     'st_atime': 0,
            #     'st_ctime': 0,
            #     'st_gid': 0,
            #     'st_uid': 0,
            #     'st_mode': 33024,
            #     'st_mtime': 0,
            #     'st_size': 1024
            # }
            return dict(st_mode=(stat.S_IFREG | 0o444), st_ctime=time.time(),
                               st_mtime=time.time(), st_atime=time.time(), st_nlink=2, st_size=self.file_size) 
        else:
            return dict(st_mode=(stat.S_IFDIR | 0o555), st_ctime=time.time(),
                               st_mtime=time.time(), st_atime=time.time(), st_nlink=2)


    def readdir(self, path, fh):

        return ['.', '..', file_name]

    def readlink(self, path):
        raise FuseOSError(errno.EACCES)

    def mknod(self, path, mode, dev):
        raise FuseOSError(errno.EACCES)

    def rmdir(self, path):
        raise FuseOSError(errno.EACCES)

    def mkdir(self, path, mode):
        raise FuseOSError(errno.EACCES)

    def statfs(self, path):
        
        return {
            'f_bavail': 0,
            'f_bfree': 0,
            'f_blocks': 1,
            'f_bsize': 4096,
            'f_favail': 0,
            'f_ffree': 0,
            'f_files': 1,
            'f_flag': os.ST_RDONLY | os.ST_NOEXEC | os.ST_NOSUID,
            'f_frsize': 4096,
            'f_namemax': 255

        }


    def unlink(self, path):
        raise FuseOSError(errno.EACCES)

    def symlink(self, name, target):
        raise FuseOSError(errno.EACCES)

    def rename(self, old, new):
        raise FuseOSError(errno.EACCES)

    def link(self, target, name):
        raise FuseOSError(errno.EACCES)

    def utimens(self, path, times=None):
        raise FuseOSError(errno.EACCES)

    # File methods
    # ============

    def open(self, path, flags):
        print("open", path, flags)
        if os.path.basename(path) != file_name:
            raise FuseOSError(errno.ENOENT)
        self.take_image()
        
        return 1

    def create(self, path, mode, fi=None):
        raise FuseOSError(errno.EACCES)

    def read(self, path, length, offset, fh):
        print("read", path, length, offset, fh)
        if not self.file.closed:
            self.file.seek(offset, io.SEEK_SET)
            return self.file.read(length)
        else:
            #Probably not the right error code
            raise FuseOSError(errno.EACCES)

    def write(self, path, buf, offset, fh):
        raise FuseOSError(errno.EROFS)

    def truncate(self, path, length, fh=None):
        raise FuseOSError(errno.EROFS)

    def flush(self, path, fh):
        print('flush', path, fh)
        # raise FuseOSError(errno.EROFS)
        pass

    def release(self, path, fh):
        print('release', path, fh)
        if not self.file.closed:
            return self.file.close()
        else:
            raise FuseOSError(errno.EACCES)


    def fsync(self, path, fdatasync, fh):
        # raise FuseOSError(errno.EROFS)
        print('fsync', path, fdatasync, fh)
        pass

def main(root):
    FUSE(WebCamFS(root), root, nothreads=True, foreground=True)

if __name__ == '__main__':
    main(sys.argv[1])