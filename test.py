import io
import sys
import subprocess
import tempfile

class MyFile(io.FileIO):

    def __init__(self, name):
        if type(name) == io.FileIO:
            self.__dict__.update(io.FileIO.__dict__)
        else:
            io.FileIO.__init__(self, name)

def main():
    # myFile = MyFile('/home/papaja/third')
    # print(myFile.readline().decode("UTF-8"))
    # dst = open('/home/mint/Diplomovka/first', 'wb')
    # src = open('second', 'rb')
    # synced = open('/home/papaja/third', 'wb')
    # signatureFile = open('signature', 'wb')
    # deltaFile = open('/home/papaja/delta', 'rb');
    # hashes = pyrsync2.blockchecksums(dst)
    # hashes_save = {
    #     weak: (index, strong) for index, (weak, strong)
    #     in enumerate(hashes)
    # }
    # signature.write(bytes('gz\n', "UTF-8"))
    # pickle.dump(hashes_save, signature, pickle.HIGHEST_PROTOCOL)
    # type = signature.readline().decode("UTF-8")
    # print("Typ {}".format(type.strip()))
    # signature.readline()
    # hashes_save = pickle.load(signature)
    # print(hashes_save)
    # delta = pyrsync2.rsyncdelta(src, hashes_save)
    # pyrsync2.patchstream(dst, synced, delta)
    # io.FileIO
    # signature = librsync.signature(dst)
    # delta = librsync.delta(src, signature)
    # librsync.patch(dst, delta, synced)
    # synced.close()
    temp = tempfile.NamedTemporaryFile()
    skuska = open(temp.name, "wb")
    dst = open('/home/mint/Diplomovka/first', 'rb')
    velkost = open('/home/mint/Diplomovka/velkost', 'rb')
    retazec = 'ahoj'
    print(len(retazec))
    print(velkost.readline())
    print(velkost.read(3))
    #velkost.write(str(sys.getsizeof(retazec)))
    dst_data = dst.read(16)
    while dst_data:
        skuska.write(dst_data)
        dst_data = dst.read(16)
    skuska.close()
    patchProcess = subprocess.Popen(['rdiff', 'patch', temp.name, '/home/mint/Diplomovka/delta'], stdout=subprocess.PIPE)
    patchFile, patchError = patchProcess.communicate()
    # print patchFile
    # dst_data = dst.read(16)
    while dst_data:
        #patchProcess.stdin.write(dst_data)
        dst_data = dst.read(16)
    # # patchProcess.stdin.write(dst_data)
    #patchProcess.stdin.write(dst_data)
    #patchProcess.stdin.close()
    # while True:
    #     print('******')
    #     patchData = patchProcess.stdout.read(16)
    #     if patchData:
    #         print(patchData)
    #     else:
    #         break
    dst.close()
    #sigProcess = subprocess.Popen(['rdiff', 'signature', dst.name], stdout=subprocess.PIPE)
    # patchProcess = subprocess.Popen(['rdiff', 'patch', dst.name, deltaFile.name], stdout=subprocess.PIPE)
    #signature, signatureErr = sigProcess.communicate()
    #if (signatureErr is None):
        # signatureFile.write("gz\n")
        # signatureFile.write("signature\n")
        # signatureFile.write(str(signature.__sizeof__()) + "\n")
        #signatureFile.write(signature)
        #signatureFile.close()
        # signatureFile = open('/home/papaja/signature', 'rb')
        # signatureFile.readline()
        # signatureFile.readline()
        # sizeOfSignature = signatureFile.readline()
        # print(sizeOfSignature)
        #with open('signature','r') as sig:
            #pass
            # sigdata = sig.read(256)
            # deltaProcess = subprocess.Popen(['rdiff', 'delta', '-', src.name], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            # deltaProcess.stdin.write(sigdata)
            # deltaProcess.stdin.close()
            # while True:
            #     print('-----')
            #     deltaData = deltaProcess.stdout.read(16)
            #     if deltaData:
            #         #print(deltaData)
            #         pass
            #     else:
            #         break
        # deltaProcess = subprocess.Popen(['rdiff', 'delta', signatureFile.name, src.name], stdout=subprocess.PIPE)
        # delta, deltaErr = deltaProcess.communicate()
        # if (deltaErr is None):
        #      print(delta)
            # patch, patchError = patchProcess.communicate()
            # if (patchError is None):
            # print("hello")
    # signature.write()
    # signature.close()
    # subprocess.call(['rdiff', 'signature', '/home/papaja/Diplomovka/first', '/home/papaja/Diplomovka/signature'])
    # subprocess.call(['rdiff', 'delta', '/home/papaja/Diplomovka/signature', '/home/papaja/Diplomovka/second', '/home/papaja/Diplomovka/delta'])
    # subprocess.call(['rdiff', 'patch', '/home/papaja/Diplomovka/first', '/home/papaja/Diplomovka/delta', '/home/papaja/Diplomovka/third'])

if __name__ == '__main__':
    main()
