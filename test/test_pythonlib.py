#!/usr/bin/env python
# emacs-mode: -*-python-*-

"""
test_pythonlib.py -- compile, uncompyle, and verify Python libraries

Usage-Examples:

  # decompile, and verify base set of python 2.7 byte-compiled files
  test_pythonlib.py --base-2.7 --verify

  # Same as above but compile the base set first
  test_pythonlib.py --base-2.7 --verify --compile

  # Same as above but use a longer set from the python 2.7 library
  test_pythonlib.py --ok-2.7 --verify --compile

  # Just deompile the longer set of files
  test_pythonlib.py --ok-2.7

Adding own test-trees:

Step 1) Edit this file and add a new entry to 'test_options', eg.
  test_options['mylib'] = ('/usr/lib/mylib', PYOC, 'mylib')
Step 2: Run the test:
  test_pythonlib.py --mylib	  # decompile 'mylib'
  test_pythonlib.py --mylib --verify # decompile verify 'mylib'
"""

from __future__ import print_function

import getopt, os, py_compile, sys, shutil, tempfile, time

from uncompyle6 import main, PYTHON_VERSION
from fnmatch import fnmatch

def get_srcdir():
    filename = os.path.normcase(os.path.dirname(__file__))
    return os.path.realpath(filename)

src_dir = get_srcdir()


#----- configure this for your needs

lib_prefix = [src_dir, '/usr/lib/', '/usr/local/lib/']

target_base = tempfile.mkdtemp(prefix='py-dis-')

PY = ('*.py', )
PYC = ('*.pyc', )
PYO = ('*.pyo', )
PYOC = ('*.pyc', '*.pyo')

test_options = {
    # name:   (src_basedir, pattern, output_base_suffix, pythoin_version)
    'test':
        ['test', PYC, 'test'],

    'bytecode-2.5':
        ['bytecode_2.5', PYC, 'bytecode_2.5', 2.5],

    'bytecode-2.7':
        ['bytecode_2.7', PYC, 'bytecode_2.7', 2.7],

    'bytecode-3.4':
        ['bytecode_3.4', PYC, 'bytecode_3.4', 3.4],

    '2.7':
        ['python2.7', PYC, 'python2.7', 2.7],

    'ok-2.6':
        [os.path.join(src_dir, 'ok_2.6'),
         PYC, 'ok-2.6', 2.6],

    'ok-2.7':    [os.path.join(src_dir, 'ok_lib2.7'),
                 PYC, 'ok-2.7', 2.7],

    'base-2.7':  [os.path.join(src_dir, 'base_tests', 'python2.7'),
                  PYC, 'base_2.7', 2.7],
}

#-----

def help():
    print("""Usage-Examples:

  # compile, decompyle and verify short tests for Python 2.7:
  test_pythonlib.py --base-2.7 --verify --compile

  # decompile and verify known good python 2.7
  test_pythonlib.py --ok-2.7 --verify

  # decompile all of Python's installed lib files
  test_pythonlib.py --2.7
""")
    sys.exit(1)


def do_tests(src_dir, obj_patterns, target_dir, opts):

    def file_matches(files, root, basenames, patterns):
        files.extend(
            [os.path.normpath(os.path.join(root, n))
                 for n in basenames
                    for pat in patterns
                        if fnmatch(n, pat)])

    files = []
    # Change directories so use relative rather than
    # absolute paths. This speeds up things, and allows
    # main() to write to a relative-path destination.
    cwd = os.getcwd()
    os.chdir(src_dir)

    if opts['do_compile']:
        compiled_version = opts['compiled_version']
        if compiled_version and PYTHON_VERSION != compiled_version:
            print("Not compiling: desired Python version is %s but we are running %s" %
                  (compiled_version, PYTHON_VERSION), file=sys.stderr)
        else:
            for root, dirs, basenames in os.walk(src_dir):
                file_matches(files, root, basenames, PY)
                for sfile in files:
                    py_compile.compile(sfile)
                    pass
                pass
            files = []
            pass
        pass

    for root, dirs, basenames in os.walk('.'):
        # Turn root into a relative path
        dirname = root[2:]  # 2 = len('.') + 1
        file_matches(files, dirname, basenames, obj_patterns)

    if not files:
        print("Didn't come up with any files to test! Try with --compile?",
              file=sys.stderr)
        exit(1)

    os.chdir(cwd)
    files.sort()

    if opts['start_with']:
        try:
            start_with = files.index(opts['start_with'])
            files = files[start_with:]
            print('>>> starting with file', files[0])
        except ValueError:
            pass

    print(time.ctime())
    print('Source directory: ', src_dir)
    print('Output directory: ', target_dir)
    try:
        _, _, failed_files, failed_verify = \
          main(src_dir, target_dir, files, [],
               do_verify=opts['do_verify'])
        if failed_files != 0:
            exit(2)
        elif failed_verify != 0:
            exit(3)

    except (KeyboardInterrupt, OSError):
        print()
        exit(1)

if __name__ == '__main__':
    test_dirs = []
    checked_dirs = []
    start_with = None

    test_options_keys = list(test_options.keys())
    test_options_keys.sort()
    opts, args = getopt.getopt(sys.argv[1:], '',
                               ['start-with=', 'verify', 'all', 'compile'] \
                               + test_options_keys )
    if not opts: help()

    test_opts = {
        'do_compile': False,
        'do_verify': False,
        'start_with': None,
        }

    for opt, val in opts:
        if opt == '--verify':
            test_opts['do_verify'] = True
        elif opt == '--compile':
            test_opts['do_compile'] = True
        elif opt == '--start-with':
            test_opts['start_with'] = val
        elif opt[2:] in test_options_keys:
            test_dirs.append(test_options[opt[2:]])
        elif opt == '--all':
            for val in test_options_keys:
                test_dirs.append(test_options[val])
        else:
            help()
            pass
        pass

    last_compile_version = None
    for src_dir, pattern, target_dir, compiled_version in test_dirs:
        if os.path.isdir(src_dir):
            checked_dirs.append([src_dir, pattern, target_dir])
        else:
            print("Can't find directory %s. Skipping" % src_dir,
                  file=sys.stderr)
            continue
        if last_compile_version and last_compile_version != compiled_version:
            print("Warning: mixed python version decompylation")
        else:
            last_compile_version = compiled_version
        pass

    if not checked_dirs:
        print("No directories found to check", file=sys.stderr)
        sys.exit(1)

    test_opts['compiled_version'] = last_compile_version

    for src_dir, pattern, target_dir in checked_dirs:
        target_dir = os.path.join(target_base, target_dir)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir, ignore_errors=1)
        do_tests(src_dir, pattern, target_dir, test_opts)