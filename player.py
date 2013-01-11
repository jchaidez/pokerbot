"""
Pokerbot 2013
Julian Chaidez, Katie Laverty, Varun Ramaswamy
"""

import argparse
import socket
import sys

class Player:
    def run(self, input_socket):
        # Get a file-object for reading packets from the socket.
        # Using this ensures that you get exactly one packet per read.
        f_in = input_socket.makefile()
        while True:
            # Block until the engine sends us a packet.
            data = f_in.readline().strip()
            # If data is None, connection has closed.
            if not data: break
            # Otherwise, execute play based on recieved data
            word = data.split()
            if word == "GETACTION":
                # Currently CHECK on every move. You'll want to change this.
                s.send("CHECK\n")
            elif word == "REQUESTKEYVALUES":
                # At the end, the engine will allow your bot save key/value pairs.
                # Send FINISH to indicate you're done.
                s.send("FINISH\n")
        # Clean up the socket.
        s.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A Pokerbot.', add_help=False, prog='pokerbot')
    parser.add_argument('-h', dest='host', type=str, default='localhost', help='Host to connect to, defaults to localhost')
    parser.add_argument('port', metavar='PORT', type=int, help='Port on host to connect to')
    args = parser.parse_args()

    # Create a socket connection to the engine.
    try:
        s = socket.create_connection((args.host, args.port))
    except socket.error as e:
        exit()

    bot = Player()
    bot.run(s)
