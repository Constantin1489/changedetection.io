#!/usr/bin/python3

# Entry-point for running from the CLI when not installed via Pip, Pip will handle the console_scripts entry_points's from setup.py
# It's recommended to use `pip3 install changedetection.io` and start with `changedetection.py` instead, it will be linkd to your global path.
# or Docker.
# Read more https://github.com/dgtlmoon/changedetection.io/wiki

import signal
import multiprocessing
import sys
import os
from changedetectionio import changedetection

def sigchld_handler(_signo, _stack_frame):
    import sys
    print('Shutdown: Got SIGCHLD')
    # https://stackoverflow.com/questions/40453496/python-multiprocessing-capturing-signals-to-restart-child-processes-or-shut-do
    pid, status = os.waitpid(-1, os.WNOHANG | os.WUNTRACED | os.WCONTINUED)

    print('Sub-process: pid %d status %d' % (pid, status))
    if status != 0:
        sys.exit(1)

    raise SystemExit

def sigterm_handler(_signo, _stack_frame):
    raise SystemExit
def sigint_handler(_signo, _stack_frame):
    # Is sigint a keyboardinterrupt?
    raise KeyboardInterrupt

if __name__ == '__main__':

    #signal.signal(signal.SIGCHLD, sigchld_handler)

    # The only way I could find to get Flask to shutdown, is to wrap it and then rely on the subsystem issuing SIGTERM/SIGKILL
    try:
        # signal 용 file 만들고 changedetection.py와 changedetectionio/changedetection.py에 import 하기.
        signal.signal(signal.SIGTERM, sigterm_handler)
        signal.signal(signal.SIGINT, sigint_handler)
        parse_process = multiprocessing.Process(target=changedetection.main)
        #parse_process.daemon = True
        parse_process.start()
        import time

        while True:
            time.sleep(1)
            if not parse_process.is_alive():
                # Process died/crashed for some reason, exit with error set
                #parse_process.join()
                sys.exit(1)


    except SystemExit:
        print("Gracefully exiting")
        #parse_process.kill()
        parse_process.terminate()
        print(f'{parse_process=}')
        print(f'{parse_process.exitcode=}')
        print(f'{parse_process.is_alive=}')
        print(f'{dir(parse_process)=}')
        import time
        while parse_process.exitcode is None:
            print(f'{parse_process=}')
            print(f'{parse_process.exitcode=}')
            print(f'{parse_process.is_alive=}')
            time.sleep(0.5)
        #parse_process.join()
        print("Gracefully exited")
        sys.exit(parse_process.exitcode)
    except KeyboardInterrupt:
        #parse_process.terminate() not needed, because this process will issue it to the sub-process anyway
        print ("Exited - CTRL+C")
        print("Gracefully exiting")
        #parse_process.kill()
        parse_process.terminate()
        parse_process.join()
        print("Gracefully exited")
        sys.exit(0)
