class MyFile(file):

    def __init__(self, name):
        if type(name) == file:
            self.__dict__.update(file.__dict__)
        else:
            file.__init__(self, name)


    def read(self, size=None):
        print("Moj Read")
        print(super(MyFile, self).read(size))


def main():
    test = MyFile("/home/papaja/Downloads/myfuse.py")
    test.read(10)

if __name__ == '__main__':
    main()