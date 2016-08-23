#!/usr/bin/env python

import datetime
import optparse
import os
import shutil
import subprocess
import sys
import time

import cursor

pv = os.path.join(os.path.dirname(__file__),
                  'pv')
num_prev_lines = 0

class chmod_temp(object):
    def __init__(self, filename, temporarily, return_to=None):
        self.filename = filename
        self.temporarily = temporarily
        self.return_to = return_to
        if self.return_to is None and os.path.exists(filename):
            self.return_to = os.stat(filename).st_mode

    def __enter__(self):
        if os.path.exists(self.filename):
            os.chmod(self.filename, self.temporarily)
        return self

    def __exit__(self, type, value, traceback):
        if self.return_to is not None:
            os.chmod(self.filename, self.return_to)
        return False


def last_modified(filename):
    return datetime.datetime.fromtimestamp(os.path.getmtime(filename))

def print_and_log(string):
    logfile.write(string+'\n')
    print string

def main():
    parser = optparse.OptionParser()
    parser.add_option('-i','--input', dest='input',
                      help='Input directory.  This directory should contain all Run#### folders.')
    parser.add_option('-o','--output', dest='output',
                      help='Output directory.  This directory will be created if it does not exist.')
    parser.add_option('-l','--log-file', dest='log_file', type='str',
                      help='The output log file.  If not set, defaults to output_dir/Log.txt', default='')
    options,args = parser.parse_args()

    if not options.input or not options.output:
        parser.print_help()
        return

    # Don't clobber a file if a file is there
    if os.path.exists(options.output) and not os.path.isdir(options.output):
        print_and_log('{0} exists and is not a directory'.format(options.output))
        return

    # Make the directory if it doesn't already exist
    if not os.path.isdir(options.output):
        subprocess.call(['mkdir','-p',options.output])

    # Open the logfile
    if options.log_file:
        log_filename = options.log_file
    else:
        log_filename = os.path.join(options.output, 'Log.txt')

    # Make sure that we have write privileges while opening the logfile
    global logfile
    with chmod_temp(os.path.dirname(log_filename),0755):
        logfile = open(log_filename,'a')



    continual_watch(options.input, options.output)

def md5sum(filename):
    print_and_log('Computing md5sum of {0}'.format(filename))
    large_file = os.stat(filename).st_size > 1024*1024
    is_zipped = filename.endswith('.gz')

    if is_zipped:
        command = '{pv} {file} | zcat | md5sum -'
    elif large_file:
        command = '{pv} {file} | md5sum -'
    else:
        command = 'md5sum {file}'

    res = subprocess.check_output(command.format(pv=pv, file=filename),
                                  shell=True)

    return res.split()[0]

def continual_watch(source, dest):
    while True:
        single_iteration(source, dest)
        time.sleep(1)


def single_iteration(source, dest):
    src_files = set(os.listdir(source))

    all_lines = []
    something_printed = False

    for filename in src_files:
        this_printed,msg = handle_single_file(source, dest, filename)
        something_printed = (something_printed or this_printed)
        all_lines.extend(msg)

    msg = '\n'.join(all_lines) + '\n'
    num_lines = msg.count('\n')
    global num_prev_lines
    if not something_printed:
        erase_prev_line = cursor.up_line + cursor.start_line + cursor.clear_to_endl
        sys.stdout.write(erase_prev_line*num_prev_lines)
    num_prev_lines = num_lines

    sys.stdout.write(msg)
    sys.stdout.flush()


def handle_single_file(source_folder, dest_folder, filename):
    source_filename = os.path.join(source_folder,filename)
    dest_filename = os.path.join(dest_folder,filename)

    if dest_filename.endswith('.mid'):
        dest_filename += '.gz'

    minimum_unmodified_time = datetime.timedelta(minutes=3)

    should_copy_file = True
    printed_message = False
    status_updates = []

    output_already_exists = os.path.exists(dest_filename)
    output_is_good = (output_already_exists and
                      last_modified(dest_filename) > last_modified(source_filename))
    time_since_modified = datetime.datetime.now() - last_modified(source_filename)
    safe_to_copy = time_since_modified > minimum_unmodified_time

    # if filename=='run38853_000.mid':
    #     import code; code.interact(local=dict(globals(),**locals()))

    if safe_to_copy and not output_is_good:
        if output_already_exists:
            print_and_log('{0} was modified since backing it up.'.format(filename))
            print_and_log('{0} will be copied over again'.format(filename))
            printed_message = True
        archive_file(source_filename, dest_filename)
        printed_message = True

    elif not safe_to_copy:
        msg = '{0} was last modified {1} seconds ago, waiting {2} more seconds'.format(
            filename, time_since_modified.seconds,
            (minimum_unmodified_time - time_since_modified).seconds)
        status_updates.append(msg)

    return printed_message,status_updates


def archive_file(source_filename, dest_filename):
    dest_folder = os.path.dirname(dest_filename)
    #md5file = os.path.join(dest_folder,'md5_checksums.txt')

    for i in range(3):
        print_and_log('Copying {0} to {1}'.format(source_filename, dest_filename))

        # The chmod_temp will temporarily change file permissions, then change them back
        # While writing, we grant ourselves write permissions to folder/file
        # Once done, we change them right back to read-only.

        with chmod_temp(dest_folder, 0755, 0555):
            with chmod_temp(dest_filename, 0644, 0444):
                if dest_filename.endswith('.gz'):
                    zip_copy(source_filename, dest_filename)
                else:
                    shutil.copy(source_filename, dest_filename)


        # source_md5sum = md5sum(source_filename)
        # dest_md5sum = md5sum(dest_filename)

        # if source_md5sum == dest_md5sum:
        #     with open(md5file,'a') as f:
        #         f.write(filename + '\t' + source_md5sum + '\n')
        #     break
        break

        print_and_log('md5sum mismatch transferring {0}'.format(source_filename))
        print_and_log('Retrying')
    else:
        print_and_log('------------------------------------------------------')
        print_and_log('Could not copy {0}'.format(source_filename))
        print_and_log('Waiting for human interaction to figure out what went wrong')
        print_and_log('------------------------------------------------------')
        raw_input()

    # Set file permissions accordingly
    # Return whether something was printed, along with continual updates



def zip_copy(source_filename, dest_filename):
    command = '{pv} {input} | gzip > {output}'.format(pv=pv,
                                                      input=source_filename,
                                                      output=dest_filename)
    subprocess.call(command, shell=True)


if __name__=='__main__':
    main()
