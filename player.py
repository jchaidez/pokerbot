"""
Pokerbot 2013
Julian Chaidez, Katie Laverty, Varun Ramaswamy
"""

import argparse
import socket
import sys

class Player:
    #Constructor method
    def __init__(self):
        self.socket = None
        self.saved_data = {}

    #Main runtime method
    def run(self, input_socket):
        # Get a file-object for reading packets from the socket.
        # Using this ensures that you get exactly one packet per read.
        self.socket = input_socket
        f_in = self.socket.makefile()
        while True:
            # Block until the engine sends us a packet.
            data = f_in.readline().split()
            command = data[0]
            # If data is None, connection has closed.
            if not data: break
            else:
                # Otherwise, execute play based on recieved data
                if command == "NEWGAME":
                    #Executes game initialization procedure
                    self.init_game(*data)
                elif command == "KEYVALUE":
                    #Processes key/value pair
                    message = self.store_value(*data)
                    self.socket.send(message)
                elif command == "REQUESTKEYVALUES":
                    #Returns key/value pairs for storage and finishes
                    message = self.finish(*data)
                    self.socket.send(message)
                elif command == "NEWHAND":
                    #Executes hand initialization procedure
                    self.init_hand(*data)
                elif command == "GETACTION":
                    #Executes main logic and performs relevant action
                    message = self.play(data)
                    self.socket.send(message)
                elif command == "HANDOVER":
                    #Executes end hand procedure
                    self.end_hand(data)
                else:
                    #Invalid command causes abort
                    break
        # Clean up the socket.
        self.socket.close()

    #Executes game initialization procedure
    def init_game(self, command, name, oppName, stackSize, bb, numHands, timeBand):
        pass

    #Processes key/value pair
    def store_value(self,command,key,val):
        pass

    #Returns key/value pairs for storage and finishes
    def finish(self, command, bytesLeft):
        pass

    #Executes hand initialization procedure
    def init_hand(self, command, handId, button, holeCard1, holeCard2, holeCard3, yourBank, oppBank, timeBank):
        pass

    #Executes main logic and performs relevant action
    def play(self, data):
        pass

    #Executes end hand procedure
    def end_hand(self, data):
        pass

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
