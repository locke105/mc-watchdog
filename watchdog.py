#!/usr/bin/env python

# author: Mathew Odden <locke105@gmail.com>
# license: Apache 2.0

import logging
import shlex
import socket
import subprocess
import time

import mc_info

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

SERVER_CMD = 'java -Xms512M -Xmx1G -jar ftbserver.jar'

# interval in seconds between server status checks
POLL_INTERVAL = 30


class Service(object):

    def __init__(self, start_cmd):
        self.start_cmd = start_cmd
        self.process = None

    def run(self):
        """Begin main monitoring loop of service.

        Starts the service if not already running.
        """
        try:
            while True:
                if not self.check_server():
                    if not self._process_dead():
                        LOG.warning("Server dead but process still around. "
                                    "Attempting to kill process...")
                        self.stop()
                    LOG.warning("Server process dead. Restarting...")
                    self.start()

                # wait awhile for next poll
                time.sleep(POLL_INTERVAL)
        except:
            # catch keyboard interrupt
            self.stop()

    def start(self):
        args = shlex.split(self.start_cmd)
        LOG.info("Starting service with command: %s" %
                 ' '.join(args))
        self.process = subprocess.Popen(args)

    def _process_dead(self):
        if self.process is None:
            return True

        self.process.poll()
        if self.process.returncode is not None:
            return True
        return False

    def stop(self):
        """Stop the underlying service process."""
        # no process running
        if self.process is None:
            return

        self.process.poll()
        if self.process.returncode is not None:
            return self.process.returncode

        # send first stop signal
        LOG.warning("Sending SIGTERM...")
        self.process.terminate()
        time.sleep(15)

        self.process.poll()
        if self.process.returncode is not None:
            return self.process.returncode

        # send kill signal and wait
        LOG.warning("Process still running. Sending SIGKILL...")
        self.process.kill()
        self.process.wait()

        return self.process.returncode

    def check_server(self):
        try:
            sinfo = mc_info.get_info(host='localhost', port=35565)
        except socket.error:
            LOG.warning("Couldn't get server info!")
            return False

        LOG.info("Server info: %s" % sinfo)
        return True


if __name__ == '__main__':
    LOG = logging.getLogger('watchdog')
    server = Service(SERVER_CMD)
    server.run()
