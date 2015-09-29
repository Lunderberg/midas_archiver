#!/usr/bin/env python

import glob
import optparse
import os
import shutil
import subprocess
import time

def main():
    parser = optparse.OptionParser()
    parser.add_option('-i','--input', dest='input',
                      help='Input directory.  This directory should contain all Run#### folders')
    parser.add_option('-o','--output', dest='output',
                      help='Output directory.  This directory will be created if it does not exist')
    #TODO MINIMUM RUN NUMBER
    options,args = parser.parse_args()

    if not options.input or not options.output:
        parser.print_help()
        return

    continual_watch(options.input, options.output)


def continual_watch(source, dest):
    if os.path.exists(dest) and not os.path.isdir(dest):
        print '{} exists and is not a directory'.format(dest)
        return

    if not os.path.isdir(dest):
        subprocess.call(['mkdir','-p',dest])

    while True:
        sleep(10)
        single_iteration(source, dest)


def single_iteration(source, dest):
    src_numbers = set(run_numbers(source))
    dest_numbers = set(run_numbers(dest))

    new_numbers = sorted(list(src_numbers - dest_numbers))

    # The new folder is made at the end of the last run.
    # We want to ignore this folder.
    if new_numbers:
        new_numbers.pop()

    for run_number in new_numbers:
        archive_run_folder(source, dest, run_number)


def run_numbers(directory):
    for filename in os.listdir(directory):
        if (os.path.isdir(filename) and
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

    if not os.path.isdir(run_source):
        print 'Directory {} does not exist.  Skipping'.format(run_source)
        return

    if not os.path.isdir(run_dest):
        os.mkdir(run_dest)

    src_files = os.listdir(run_source)

    for filename in src_files:
        handle_single_file(run_source, run_dest, filename)


def handle_single_file(source, dest, filename):
    dest_files = os.listdir(dest)
    if filename in dest_files:
        print '{} already exists in {}'.format(filename, dest)
        resp = raw_input('  Do you want to overwrite? y/[n]')
        if not resp.startswith('y'):
            print 'Skipping {}'.format(filename)
            return

    if filename in ['Global.dat','GlobalRaw.dat']:
        zip_copy(source, dest, filename)
    elif os.path.isdir(filename):
        directory_copy(source, dest, filename)
    else:
        regular_copy(source, dest, filename)

def zip_copy(source, dest, filename):
    subprocess.call('gzip < {} > {}'.format(os.path.join(source,filename),
                                            os.path.join(dest,filename+'.gz')),
                    shell=True)


def regular_copy(source, dest, filename):
    shutil.copy(os.path.join(source, filename),
                dest)


def directory_copy(source, dest, filename):
    shutil.copytree(os.path.join(source, filename),
                    dest)


if __name__=='__main__':
    main()
