GRETINA archiver script
=======================

Setting up a usb drive
----------------------

1. Plug in the usb drive.

2. If the usb drive mounts automatically, nothing more needs to be
   done.  In this case, you can go to "Running the archiver".

3. `ls /dev` to determine the device id of the usb drive.
   It should be something of the form /dev/sdb, where b could be any
   letter.  For the rest of these instructions, replace "/dev/sdb"
   with the device id.  Unplug the usb drive to verify that this is
   the correct device id.  It should disappear when the disk is
   unplugged.

4. If the drive is 2 TB or smaller, use `sudo fdisk /dev/sdb` to format the disk.

   a. 'p', print the existing file table.
   b. 'd', delete the existing partition.
   c. 'n', create a new partition.
      When prompted, the partition should start at 0,
      and should use all the space on the drive.
   d. 't'
      When prompted, use '83', for a ext3 partition.
   e. 'w', write the partition table.
   
5. If the drive is larger than 2 TB, use `sudo parted /dev/sdb` to format the disk.
   (If you want to align the partition, use the guide at
    http://rainbow.chard.org/2013/01/30/how-to-align-partitions-for-best-performance-using-parted/)

  a. mklabel gpt
  b. mkpart primary ext3 0 100%
  c. q

6. Run 'sudo mkfs -t ext3 /dev/sdb1'.

7. Run 'sudo mount /dev/sdb1 /mnt/usb'.

8. Run 'sudo chown tigress /mnt/usb'.


Running the archiver
--------------------

The archiver can be started with a single command.

   ~/archiver/archiver.py -i /path/to/data -o /mnt/usb

The input path should contain the various *.mid files.
The output path should point to the archive folder,
  to which the *.mid files will be copied.

The script will run continually, archiving each run as it is
completed.
