from __future__ import with_statement
import gzip
from backup_lib import *
from store import Store
from stat import *

__author__ = 'papaja'

import os
import sys
import errno
import fuse
from threading import Lock
import contextlib
import logging

counter = 0

class BackupFS(fuse.LoggingMixIn, fuse.Operations):
    def __init__(self, root, mountpoint,  allbackups):
        self.root = root
        self.allbackups = allbackups
        self.mountpoint = mountpoint
        self.gzipFiles = {}
        self.fileslock = Lock()

    # Helpers
    # =======

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    def _parse_path(self, path):
        dictOfExistingBackups = self.allbackups.getAllBackups()
        head, file = os.path.split(path)
        folders = []
        backup = None
        while 1:
            head, folder = os.path.split(head)
            if folder != "" and folder not in dictOfExistingBackups:
                folders.append(folder)
            elif folder in dictOfExistingBackups:
                backup = folder
            elif head in dictOfExistingBackups:
                backup = folder
            else:
                if head != "" and head != "/" and head not in dictOfExistingBackups:
                    folders.append(path)
                break
        folders.reverse()
        return file, folders, backup

    def _get_object(self, path):
        dictOfExistingBackups = self.allbackups.getAllBackups()
        file, folders, backup = self._parse_path(path)
        if backup is None:
            backup = file
        if backup in dictOfExistingBackups and len(folders) == 0 and backup == file:
            object = dictOfExistingBackups[backup]
        elif backup in dictOfExistingBackups and len(folders) == 0 and backup != file:
            object = dictOfExistingBackups[backup].get_object_by_path(folders, file)
        elif backup in dictOfExistingBackups and len(folders) > 0:
            object = dictOfExistingBackups[backup].get_object_by_path(folders, file)
        else:
            object = None
        return object

    @contextlib.contextmanager
    def _patch_gzip_for_partial(self):
        """
        Context manager that replaces gzip.GzipFile._read_eof with a no-op.

        This is useful when decompressing partial files, something that won't
        work if GzipFile does it's checksum comparison.

        """
        _read_eof = gzip.GzipFile._read_eof
        gzip.GzipFile._read_eof = lambda *args, **kwargs: None
        yield
        gzip.GzipFile._read_eof = _read_eof

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise fuse.FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
         raise IOError(errno.EROFS, 'Read only filesystem')

    def chown(self, path, uid, gid):
        raise IOError(errno.EROFS, 'Read onposix.stat_resultly filesystem')

    def getattr(self, path, fh=None):
        st = {}
        if path == '/':
            st['st_mode'] = fuse.S_IFDIR | 0755
            st['st_ino'] = 0
            st['st_dev'] = 0
            st['st_nlink'] = 2
            st['st_uid'] = 0
            st['st_gid']= 0
            st['st_size'] = 4096
            st['st_atime'] = 0
            st['st_mtime'] = 0
            st['st_ctime'] = 0
            return st
        else:
            object = self._get_object(path)
        if object is not None:
            st['st_atime'] = object.lstat[ST_ATIME]
            st['st_mtime'] = object.lstat[ST_MTIME]
            st['st_ctime'] = object.lstat[ST_CTIME]
            st['st_mode'] = object.lstat[ST_MODE]
            st['st_nlink'] = object.lstat[ST_NLINK]
            st['st_size'] = object.lstat[ST_SIZE]
            st['st_uid'] = object.lstat[ST_UID]
            st['st_gid'] = object.lstat[ST_GID]
        return st

    def readdir(self, path, fh):
        dictOfExistingBackups = self.allbackups.getAllBackups()
        dirents = ['.', '..']
        if path == '/':
            dirents += dictOfExistingBackups.keys();
            object = None
        else:
            object = self._get_object(path)
        if object is not None:
            dirents += object.loaded_dict.keys()
        for r in dirents:
            yield r

    def readlink(self, path):
        object = self._get_object(path)
        return object.read_backuped_lnk()
        # pathname = os.readlink(self._full_path(path))
        # if pathname.startswith("/"):
        #     return os.path.relpath(pathname, self.root)
        # else:
        #     return pathname

    def mknod(self, path, mode, dev):
        raise IOError(errno.EROFS, 'Read only filesystem')

    def rmdir(self, path):
         raise IOError(errno.EROFS, 'Read only filesystem')

    def mkdir(self, path, mode):
         raise IOError(errno.EROFS, 'Read only filesystem')

    def statfs(self, path):
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
         raise IOError(errno.EROFS, 'Read only filesystem')

    def symlink(self, target, name):
         raise IOError(errno.EROFS, 'Read only filesystem')

    def rename(self, old, new):
         raise IOError(errno.EROFS, 'Read only filesystem')

    def link(self, target, name):
        raise IOError(errno.EROFS, 'Read only filesystem')

    def utimens(self, path, times=None):
         raise IOError(errno.EROFS, 'Read only filesystem')

    # File methods
    # ============

    def open(self, path, flags):
        object = self._get_object(path)
        if object is not None:
            #file_name = object.store.get_object_path(object.side_dict['hash'])
            #f = gzip.open(file_name, 'rb3')
            with self.fileslock:
                global counter
                counter += 1
                self.gzipFiles[counter] = object
                #object.rewind()
                #f.rewind()
                fh = counter
            return fh
            # return open(file_name, 'rb')
            #return None
            #return gzip.open(file_name, 'rb')
        else:
            raise IOError(errno.EINVAL, 'Invalid file path')

    def create(self, path, mode, fi=None):
         raise IOError(errno.EROFS, 'Read only filesystem')

    def read(self, path, length, offset, fh):
        #os.lseek(fh, offset, os.SEEK_SET)
        #return os.read(fh, length)
        #return zlib.decompress(os.read(fh, length))
        #print("read({},{},{},{})".format(path,length,offset,fh))
        with self.fileslock:
            if self.gzipFiles[fh].closed:
                self.gzipFiles[fh].open()
            self.gzipFiles[fh].seek(offset)
            #with self._patch_gzip_for_partial(): pre gzip vratit spat
            return self.gzipFiles[fh].read(length)
        #return None

    def write(self, path, buf, offset, fh):
         raise IOError(errno.EROFS, 'Read only filesystem')

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        # return self.gzipFiles[fh].flush()
        # return os.fsync(fh)
        return 0

    def release(self, path, fh):
        ##os.close(fh);
        with self.fileslock:
            cf = self.gzipFiles[fh].close()
            del self.gzipFiles[fh]
        return cf
        #return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return 0

class Backups:
    def __init__(self, path, mountPoint):
        self.path = path
        self.mountPoint = mountPoint
        self.targetPath = os.path.join(path, "target/backups/")
        self.allBackups = {}
        self.initExistingBackups()
        # self.cache = {}

    def _parse_path(self, path):
        dictOfExistingBackups = self.getAllBackups()
        head, file = os.path.split(path)
        folders = []
        backup = None
        while 1:
            head, folder = os.path.split(head)
            if folder != "" and folder not in dictOfExistingBackups:
                folders.append(folder)
            elif folder in dictOfExistingBackups:
                backup = folder
            elif head in dictOfExistingBackups:
                backup = folder
            else:
                if head != "" and head != "/" and head not in dictOfExistingBackups:
                    folders.append(path)
                break
        folders.reverse()
        print("file je: " + file + "folders su: " + ', '.join(folders) + "backup je: ")
        return file, folders, backup
    #()xcsadasdadadsadasda
    # def _get_object(self, path):
    #     dictOfExistingBackups = self.getAllBackups()
    #     file, folders, backup = self._parse_path(path)
    #     if backup is None:
    #         backup = file
    #     if path in self.cache:
    #         object = self.cache[path]
    #     elif backup in dictOfExistingBackups and len(folders) == 0 and backup == file:
    #         object = dictOfExistingBackups[backup]
    #     elif backup in dictOfExistingBackups and len(folders) == 0 and backup != file:
    #         object = dictOfExistingBackups[backup].get_object_by_path(folders, file)
    #     elif backup in dictOfExistingBackups and len(folders) > 0:
    #         object = dictOfExistingBackups[backup].get_object_by_path(folders, file)
    #     else:
    #         object = None
    #     if object is not None and path not in self.cache:
    #         for key in self.cache.iterkeys():
    #             print key
    #         self.cache[path] = object
    #     return object

    def initExistingBackups(self):
        self.cache = {}
        myList = os.listdir(self.targetPath)
        for f in myList:
            self.allBackups[f] = ExistingBackup(self.mountPoint, Store(self.path), f).get_root_object()
        sa = "sas"
        # head, file_name = os.path.split('/bin/idea.properties')
        # folders = []
        # while 1:
        #     head, folder = os.path.split(head)
        #     if folder != "":
        #         folders.append(folder)
        #     else:
        #         if head != "" and head != "/":
        #             folders.append(head)
        #         break
        #     folders.reverse()
        # file_name, folders, backup = self._parse_path('/test/test/test')
        #test = se;f
        # block_size = constants.CONST_BLOCK_SIZE
        # test = self.allBackups['latest'].get_object_by_path(folders, file_name)
        # test3 = self.allBackups['latest'].get_object_by_path(folders, file_name)
        # test = self._get_object('/latest/uvdl/uvdl/uvdl')
        # test2 = self._get_object('/latest/uvdl/uvdl/uvdl')
        # # file_name = test.target.get_object_path(test.side_dict['hash'])
        # test3 = os.open(file_name, os.O_RDONLY)
        # with open(file_name, "rb") as TF:
        #     return TF.read(block_size)
        # test2 = 2

    def getAllBackups(self):
        return self.allBackups



def main(root, mountPoint):
    # logging.basicConfig(level=logging.DEBUG)
    allbackups = Backups(root, mountPoint)
    fuse.FUSE(BackupFS(os.path.join(root, "target/backups/"), mountPoint, allbackups), mountPoint, foreground=True, default_permissions=True)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])