#!/bin/bash
# Testing script for compressing in backup
set -m
echo "=========== Creating directory structure =========="
echo ""
mkdir DataToBackup
mkdir Backup
mkdir MountPoint
cd DataToBackup
mkdir Data1
cd Data1
touch file1 && tr -dc A-Za-z0-9 < /dev/urandom | head -c 20 > file1
touch file2 && tr -dc A-Za-z0-9 < /dev/urandom | head -c 200 > file2
mkdir folder1 folder2
cd folder1
mkdir folder3
touch file3 && tr -dc A-Za-z0-9 < /dev/urandom | head -c 100 > file3
touch file4 && tr -dc A-Za-z0-9 < /dev/urandom | head -c 200 > file4
cd folder3
touch file5 && tr -dc A-Za-z0-9 < /dev/urandom | head -c 20 > file5
cd ../../folder2
cp ../../../python.pdf .
#no_of_files=3;
#counter=1;
#while [[ $counter -le $no_of_files ]];
#do echo Creating file number $counter with random data;
#  dd bs=1024 count=$RANDOM skip=$RANDOM if=/dev/urandom of=random-file.$counter;
#  let "counter += 1";
#done
cd ../../..
echo "=========== Backuping unchanged data =========="
echo ""
python backuper init DataToBackup Backup
cp -a DataToBackup DataToBackupCopy1
echo "=========== First changing of some data =========="
cd DataToBackup
mkdir Data2
cd ..
sleep 5
echo "=========== Backuping first changed data =========="
echo ""
python backuper backup DataToBackup Backup
cp -a DataToBackup DataToBackupCopy2
echo "=========== Second changing of some data =========="
cd DataToBackup
cd Data2
mkdir folder1
cd ../..
sleep 5
echo "=========== Backuping second changed data =========="
echo ""
python backuper backup DataToBackup Backup
cp -a DataToBackup DataToBackupCopy3
echo "=========== Third changing of some data =========="
cd DataToBackup/Data2/folder1
touch file1 && tr -dc A-Za-z0-9 < /dev/urandom | head -c 20 > file1
cd ../../..
sleep 5
echo "=========== Backuping third changed data =========="
echo ""
python backuper backup DataToBackup Backup
cp -a DataToBackup DataToBackupCopy4
echo "=========== Fourth changing of some data =========="
cd DataToBackup/Data1
tr -dc A-Za-z0-9 < /dev/urandom | head -c 20 >> file1
cd ../../
sleep 5
echo "=========== Backuping fourth changed data =========="
echo ""
python backuper backup DataToBackup Backup
cp -a DataToBackup DataToBackupCopy5
echo "=========== Fifth changing of some data =========="
cd DataToBackup/Data1
rm file2
cd ../../
sleep 5
echo "=========== Backuping fifth changed data =========="
echo ""
python backuper backup DataToBackup Backup
cp -a DataToBackup DataToBackupCopy6
echo "=========== Sixth changing of some data =========="
cd DataToBackup/Data1
mv folder2 folderWithData
cd ../../
sleep 5
echo "=========== Backuping sixth changed data =========="
echo ""
python backuper backup DataToBackup Backup
cp -a DataToBackup DataToBackupCopy7
echo "=========== Seventh changing of some data =========="
cd DataToBackup/Data1
cp folderWithData/* folder1/folder3
cd ../../
sleep 5
echo "=========== Backuping seventh changed data =========="
echo ""
python backuper backup DataToBackup Backup
cp -a DataToBackup DataToBackupCopy8
echo "=========== Mounting FUSE file system of backuped data =========="
echo ""
python myfuse.py Backup MountPoint &
sleep 10
cd MountPoint
DIRS=(`ls -d */`)
#for DIR in $DIRS
#do
#    echo ${DIR}
#done
for i in {1..8}
do
    echo "========== diff off DataToBackupCopy" ${i} " and " ${DIRS[$i - 1]} " =========="
    diff -r ../DataToBackupCopy${i} ${DIRS[$i - 1]}
    sleep 5
done
sleep 5
kill %1
sleep 5
echo "=========== Removing all created data =========="
cd ..
rm -r DataToBackup
for i in {1..8}
do
    rm -r DataToBackupCopy$i
done
rm -r Backup
rm -r MountPoint