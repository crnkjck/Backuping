__author__ = 'papaja'

import pickle
import os
import hashlib
import gzip
import constants
from stat import *
from backup_lib import BackupObject
from backup_lib import objects_init

class Store():

    def __init__(self, pathname):
        self.target_path = os.path.join(pathname, "target")
        if not os.path.exists(self.target_path):
            os.mkdir(self.target_path)

    def init_target_dir(self):
        if not os.path.exists(self.target_path):
            os.mkdir(self.target_path)
        objects_path = os.path.join(self.target_path, "objects")
        if not os.path.exists(objects_path):
            os.mkdir(objects_path)
        backups_path = os.path.join(self.target_path, "backups")
        if not os.path.exists(backups_path):
            os.mkdir(backups_path)

    def get_path(self):
        return self.target_path #volania napr. BackupObject.new...(... , target.get_path())

    def get_backup_path(self, backup_name):
        backup_path = os.path.join(self.target_path, "backups")
        return os.path.join(backup_path, backup_name)

    def get_object_path(self, hash):
        object_path = os.path.join(self.target_path, "objects")
        return os.path.join(object_path, hash + ".data")

    def get_object_header_path(self, hash):
        object_header_path = os.path.join(self.target_path, "objects")
        return os.path.join(object_header_path, hash + ".meta")

    def get_latest_path(self):
        latest_tmp_path = os.path.join(self.target_path, "backups")
        return os.path.join(latest_tmp_path, "latest")

    @staticmethod
    def file_rename(old_name, new_name):
        new_file_name = os.path.join(os.path.dirname(old_name), new_name)
        os.rename(old_name, new_file_name)

    def save_file(self, source_path, name, block_size = constants.CONST_BLOCK_SIZE, previous_hash = None):
        file_hash = hashlib.sha1()
        with open(source_path, "rb") as SF:
            target_file = self.get_object_path(name)
            target_file_header = self.get_object_header_path(name)
            with gzip.open(target_file, "wb") as TF:
                while True:
                    block = SF.read(block_size)
                    file_hash.update(block)
                    TF.write(block)
                    if not block:
                        self.file_rename(target_file, file_hash.hexdigest() + ".data")
                        with open(target_file_header, "wb") as THF:
                            THF.write("gz\n")
                            THF.write("signature\n")
                            THF.write(str(0))
                            THF.write("\n")
                            self.file_rename(target_file_header, file_hash.hexdigest() + ".meta")
                            THF.close()
                        break
                TF.close()
            SF.close()
        return file_hash.hexdigest()

    def get_object_file(self, hash, mode):
        return open(self.get_object_path(hash), mode)

    def get_object_file_header(self, hash, mode):
        return open(self.get_object_header_path(hash), mode)

    def get_object_type(self, hash):
        with self.get_object_file_header(hash, "rb") as HF:
            object_type = HF.readline()
            HF.close()
            return object_type

    def get_object(self, source_path ,hash, side_dict):
        return StoreObject.create(source_path, self, side_dict)

    def get_hash(self, src_file, block_size = constants.CONST_BLOCK_SIZE):
        file_hash = hashlib.sha1()
        with open(src_file, "rb") as SF :
            while True:
                block = SF.read(block_size)
                file_hash.update(block)
                if not block : break
        return file_hash.hexdigest()


class StoreObject(BackupObject):

    @staticmethod
    def create(source_path, store, side_dict):
        #print side_dict
        lstat = side_dict['lstat']
        object_hash = side_dict['hash']
        object_type = store.get_object_type(object_hash).rstrip('\n')
        mode = lstat.st_mode
        if S_ISDIR(mode) and object_type == "directory":
            return StoreDir(source_path, store, lstat, side_dict)
        elif S_ISREG(mode) and object_type == "gz":
            return StoreGzipFile(source_path, store, lstat, side_dict, store.get_object_path(side_dict['hash']))
        elif S_ISREG(mode) and object_type == "raw":
            return StoreRawFile(source_path, store, lstat, side_dict, store.get_object_path(side_dict['hash']))
        elif S_ISREG(mode) and object_type == "delta":
            return StoreDeltaFile(source_path, store, lstat, side_dict, store.get_object_path(side_dict['hash']))
        elif S_ISLNK(mode) and object_type == "link":
            return StoreLnk(source_path, store, lstat, side_dict)
        else:
            # Unknown file
            return None

    def recovery_stat(self, object_path, lstat):
        #os.lchmod(object_path, lstat.st_mode)  AttributeError: 'module' object has no attribute 'lchmod'
        try :
            time = lstat.st_atime, lstat.st_mtime
            os.utime(object_path, time)
        except OSError:
            pass
        try:
            os.chmod(object_path, S_IMODE(lstat.st_mode))
        except OSError:
            pass
        try:
            os.lchown(object_path, lstat.st_uid, lstat.st_gid)
        except OSError:
            pass # doplnit printy / handle exceptetion

    def __init__(self, source_path, store, lstat, side_dict):
        if objects_init : print("Initializing TargetObject ", source_path)
        #print source_path
        BackupObject.__init__(self, source_path, store, lstat)
        self.side_dict = side_dict
        #print self.side_dict
        #print self.name

class StoreFile(StoreObject):

    def __init__(self, source_path, store, lstat, side_dict):
        if objects_init : print("Initializing TargetFile (%s)") % source_path
        #print source_path
        StoreObject.__init__(self, source_path, store, lstat, side_dict)

    def recover(self, block_size = constants.CONST_BLOCK_SIZE):
        # reverse file_copy()
        with self.store.get_object_file(self.side_dict['hash'], "rb") as TF:
            #recovery_file = os.path.join(self.source_path)#name)
            with open(self.source_path, "wb") as RF:
                while True:
                    block = TF.read(block_size)
                    RF.write(block)
                    if not block:
                        break
                RF.close()
            TF.close()
        self.recovery_stat(self.source_path, self.side_dict['lstat'])

class StoreDir(StoreObject):

    #Pomocou tejto metody treba nacitat slovnik objektov v adresari
    #do vhodnej instancnej premennej objektu triedy TargetDir napriklad v konstruktore.
    #Do tohto slovnika (nie do side_dict!) potom pristupuje metoda get_object().
    def __init__(self, source_path, store, lstat , side_dict):
        if objects_init : print("Initializing TargetDir ", source_path)
        #print source_path
        #print target_path
        #print side_dict
        #path = os.path.join(target_path, side_dict['hash'])
        #print path
        self.loaded_dict = self.unpickling(store.get_object_path(side_dict['hash']))
        self.loaded_obj = {}
        StoreObject.__init__(self, source_path, store, lstat, side_dict)
        #print self.side_dict

    def get_object(self, name):
        # zisti, ci objekt "name" existuje v zalohovanej verzii
        # tohto adresara
        # ak ano, vyrobi prislusny TargetObject
        # ak nie, vrati None
        if name in self.loaded_dict:
            if ('object_' + name) in self.loaded_obj:
                return self.loaded_obj['object_' + name]
            else:
                new_target_object = StoreObject.create(os.path.join(self.source_path, name), self.store, self.loaded_dict[name])
                self.loaded_obj['object_' + name] = new_target_object
                return new_target_object
        else:
            return None

    def get_object_by_path(self, folders, file_name):
        size = len(folders)
        if len(folders) > 0:
            folder = folders.pop(0)
            name = folder
        else:
            name = file_name
        if name in self.loaded_dict:
            if ('object_' + name) in self.loaded_obj:
                if (name == file_name and size == 0):
                    return self.loaded_obj['object_' + name]
                else:
                    return self.loaded_obj['object_' + name].get_object_by_path(folders, file_name)
            else:
                new_store_object = StoreObject.create(os.path.join(self.source_path, name), self.store, self.loaded_dict[name])
                self.loaded_obj['object_' + name] = new_store_object
                if (name == file_name and size == 0):
                    return self.loaded_obj['object_' + name]
                else:
                    return self.loaded_obj['object_' + name].get_object_by_path(folders, file_name)
        else:
            return None

    def unpickling(self, store_path):
        #unpkl_file = os.path.join(target_path, file_name)
        with open(store_path, "rb") as UPF:
                pi = UPF.read()
                UPF.close()
        return_dict = pickle.loads(pi)
        #print return_dict
        return return_dict

    def recover(self):
        #prejst slovnik
        # ak dir tak rekurzia
        #inak .recovery_backup
        #passdef recovery_backup(self):
        #for name , in self.side_dict.iteritems():
        # if IS_REG(self.side_dict[key]['lstat'].st_mode):
        if not os.path.exists(self.source_path):
            os.mkdir(self.source_path)
        for store_object_name in self.loaded_dict.iterkeys():
            new_store_object = self.get_object(store_object_name)
            new_store_object.recover()#os.path.join(self.source_path, target_object_name))
        # obnovit metadata adresara!!!!!!!!!!!
        self.recovery_stat(self.source_path, self.side_dict['lstat'])

class StoreLnk(StoreObject):

    def __init__(self, source_path, store, lstat, side_dict):
        if objects_init : print("Initializing StoreLnk (%s)") % source_path
        #print source_path
        StoreObject.__init__(self, source_path, store, lstat, side_dict)

    def read_backuped_lnk(self):
        with self.store.get_object_file(self.side_dict['hash'], "rb") as TF:
            backuped_link_name = TF.read()
        return backuped_link_name

    def recovery_stat(self, object_path, lstat):
        try:
            os.lchown(object_path, lstat.st_uid, lstat.st_gid)
        except OSError:
            pass # dolnit printy / handle exceptetion

    def recover(self):
        os.symlink(self.read_backuped_lnk(), self.source_path )
        self.recovery_stat(self.source_path, self.side_dict['lstat'])


class StoreRawFile(StoreFile, file):

    def __init__(self, source_path, store, lstat, side_dict, file_name):
        if objects_init : print("Initializing StoreRawFile (%s)") % source_path
        StoreObject.__init__(self, source_path, store, lstat, side_dict)
        if type(file_name) == file:
            self.__dict__.update(file.__dict__)
        else:
            file.__init__(self, file_name)


class StoreGzipFile(StoreFile, gzip.GzipFile):

    def __init__(self, source_path, store, lstat, side_dict, file_name):
        if objects_init : print("Initializing StoreGzipFile (%s)") % source_path
        StoreObject.__init__(self, source_path, store, lstat, side_dict)
        if type(file_name) == gzip.GzipFile:
            self.__dict__.update(file.__dict__)
        else:
            gzip.GzipFile.__init__(self, file_name)


class StoreDeltaFile(StoreFile, file):

    def __init__(self, source_path, store, lstat, side_dict, file_name):
        if objects_init : print("Initializing StoreDeltaFile (%s)") % source_path
        StoreObject.__init__(self, source_path, store, lstat, side_dict)
        if type(file_name) == file:
            self.__dict__.update(file.__dict__)
        else:
            file.__init__(self, file_name)