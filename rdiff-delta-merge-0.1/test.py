__author__ = 'papaja'

import subprocess

def main():
    mergedDelta = open('mergedDela', 'wb')
    deltaMergeProcess = subprocess.Popen(['./a.out', 'd1', 'd2'], stdout=subprocess.PIPE)
    deltaFile, deltaError = deltaMergeProcess.communicate()
    if deltaError == None:
        mergedDelta.write(deltaFile)
    mergedDelta.close()
    patchProcess = subprocess.Popen(['rdiff', 'patch', 'signature', 'mergedDela'], stdout=subprocess.PIPE)
    patchFile, patchError = patchProcess.communicate()
    if patchError == None:
        print patchFile

if __name__ == '__main__':
    main()