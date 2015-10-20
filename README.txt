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

4. Use `sudo fdisk /dev/sdb` to format the disk.

   a. 'p', print the existing file table.
   b. 'd', delete the existing partition.
   c. 'n', create a new partition.
      When prompted, the partition should start at 0,
      and should use all the space on the drive.
   d. 't'
      When prompted, use '83', for a ext3 partition.
   e. 'w', write the partition table.

5. Run 'sudo mkfs -t ext3 /dev/sdb1'.

6. Run 'sudo mount /dev/sdb1 /mnt/usb'.

7. Run 'sudo chown gretina /mnt/usb'.


Running the archiver
--------------------

The archiver can be started with a single command.

   ~/archiver/archiver.py -i /path/to/data -o /mnt/usb

The input path should contain the various Run0000 folders.
The output path should point to the desired archive folder.

The script will run continually, archiving each run as it is
completed.  After each file is transferred, the script will compute an
md5 checksum to ensure that there were no errors in the transfer.

If the disk runs out of space, and you need to switch to a new disk,
use the optional argument '-m NUMBER'.  The script will then archive
only runs starting with the given number.
