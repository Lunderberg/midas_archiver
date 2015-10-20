#!/usr/bin/env python

import glob
import optparse
import os
import shutil
import subprocess
import sys
import time

pv = os.path.join(os.path.dirname(__file__),
                  'pv')

def print_and_log(string):
    logfile.write(string+'\n')
    print string

def main():
    parser = optparse.OptionParser()
    parser.add_option('-i','--input', dest='input',
                      help='Input directory.  This directory should contain all Run#### folders.')
    parser.add_option('-o','--output', dest='output',
                      help='Output directory.  This directory will be created if it does not exist.')
    parser.add_option('-m','--first-run-number', dest='first_run', type='int',
                      help='The first run number to use.', default=-1)
    parser.add_option('-l','--log-file', dest='log_file', type='str',
                      help='The output log file.  If not set, defaults to output_dir/Log.txt', default='')
    options,args = parser.parse_args()

    if not options.input or not options.output:
        parser.print_help()
        return

    global logfile
    if options.log_file:
        logfile = open(options.log_file,'a')
    else:
        logfile = open(os.path.join(options.output, 'Log.txt'),'a')

    continual_watch(options.input, options.output, options.first_run)

def md5sum(filename):
    print_and_log('Computing md5sum of {}'.format(filename))
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

def continual_watch(source, dest, first_run):
    if os.path.exists(dest) and not os.path.isdir(dest):
        print_and_log('{} exists and is not a directory'.format(dest))
        return

    if not os.path.isdir(dest):
        subprocess.call(['mkdir','-p',dest])

    while True:
        single_iteration(source, dest, first_run)
        time.sleep(10)


def single_iteration(source, dest, first_run):
    src_numbers = set(run_numbers(source))
    dest_numbers = set(run_numbers(dest))

    new_numbers = sorted(list(src_numbers - dest_numbers))
    new_numbers = [runnum for runnum in new_numbers if runnum>=first_run]

    # The new folder is made at the end of the last run.
    # We want to ignore this folder.
    if new_numbers:
        new_numbers.pop()

    for run_number in new_numbers:
        archive_run_folder(source, dest, run_number)

    next_run_number = max(first_run, max(*src_numbers))
    print 'Waiting for Run{:04d} to finish     \r'.format(next_run_number),
    sys.stdout.flush()


def run_numbers(directory):
    for filename in os.listdir(directory):
        full_filename = os.path.join(directory,filename)
        if (os.path.isdir(full_filename) and
            filename.startswith('Run')):
            yield int(filename[3:])

def archive_run_folder(source, dest, run_number):
    '''
    Archives the contents of a single run's folder.
    Global.dat and GlobalRaw.dat will be zipped into Global.dat.gz and GlobalRaw.dat.gz
    All other files will be copied.
    '''

    run_source = os.path.join(source, 'Run{:04d}'.format(run_number))
    run_dest = os.path.join(dest, 'Run{:04d}'.format(run_number))

    print_and_log('Archiving {} into {}'.format(run_source, run_dest))

    if not os.path.isdir(run_source):
        print_and_log('Directory {} does not exist.  Skipping'.format(run_source))
        return

    if not os.path.isdir(run_dest):
        os.mkdir(run_dest)

    src_files = sorted(os.listdir(run_source))

    for filename in src_files:
        handle_single_file(run_source, run_dest, filename)

    #Allow read and execute on all archived directories
    subprocess.call('chmod 555 `find ' + run_dest + ' -type d`', shell=True)
    #Allow read on all archived files
    subprocess.call('chmod 444 `find ' + run_dest + ' -type f`', shell=True)

def handle_single_file(source_folder, dest_folder, filename):
    dest_files = os.listdir(dest_folder)
    if filename in dest_files:
        print_and_log('{} already exists in {}'.format(filename, dest_folder))
        resp = raw_input('  Do you want to overwrite? y/[n]')
        if not resp.startswith('y'):
            print_and_log('Skipping {}'.format(filename))
            return

    source_filename = os.path.join(source_folder,filename)
    dest_filename = os.path.join(dest_folder,filename)
    md5file = os.path.join(dest_folder,'md5_checksums.txt')

    if filename in ['Global.dat','GlobalRaw.dat']:
        dest_filename += '.gz'

    for i in range(3):
        print_and_log('Copying {} to {}'.format(source_filename, dest_filename))
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

        print_and_log('md5sum mismatch transferring {}'.format(source_filename))
        print_and_log('Retrying')
    else:
        print_and_log('------------------------------------------------------')
        print_and_log('Could not copy {}'.format(source_filename))
        print_and_log('Waiting for human interaction to figure out what went wrong')
        print_and_log('------------------------------------------------------')
        raw_input()



def zip_copy(source_filename, dest_filename):
    command = '{pv} {input} | gzip > {output}'.format(pv=pv,
                                                      input=source_filename,
                                                      output=dest_filename)
    subprocess.call(command, shell=True)


if __name__=='__main__':
    main()
