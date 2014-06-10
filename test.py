import librsync

class MyFile(file):

    def __init__(self, name):
        if type(name) == file:
            self.__dict__.update(file.__dict__)
        else:
            file.__init__(self, name)

def main():
    dst = file('/home/papaja/first', 'rb')
    src = file('/home/papaja/second', 'rb')
    synced = file('/home/papaja/third', 'wb')
    signature = librsync.signature(dst)
    delta = librsync.delta(src, signature)
    librsync.patch(dst, delta, synced)
    synced.close()

if __name__ == '__main__':
    main()
