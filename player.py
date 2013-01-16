"""
Pokerbot 2013
Julian Chaidez, Katie Laverty, Varun Ramaswamy
"""

import argparse
import socket
import sys

from pbots_calc import calc
from random import random
from numpy import polyfit

#GLOBAL MACROS#

#Basic deck, used to track contents of deck, might be useful for other things
DECK = set(['Ah','2h','3h','4h','5h','6h','7h','8h','9h','Th','Jh','Qh','Kh',
             'Ad','2d','3d','4d','5d','6d','7d','8d','9d','Td','Jd','Qd','Kd',
             'Ac','2c','3c','4c','5c','6c','7c','8c','9c','Tc','Jc','Qc','Kc',
             'As','2s','3s','4s','5s','6s','7s','8s','9s','Ts','Js','Qs','Ks'])

#BODY CODE#

#OPPONENT CLASS#

class Opponent:
    #This class models the behavior of an opponent using data like the opponent
    #hand history and folding behavior.
    
    #Assuming that the opponent players are determining betting values in the same
    #way that we are, we can reconstruct a vague model for their betting strategy by
    #using a polynomial approximation of their behavior.
    
    #The libary structures intilialized in the constructor below will store families
    #of 
    
    #Constructor method
    def __init__(self, name):
        self.name = name
        self.e_to_b_lib = {}
        self.b_to_e_lib = {}
        self.equit_floor_lib = {}

    #Loads any saved data about a player bot
    def load_history(self, 
    
    #
    def add_hand_data_pt(self, hand, board, bet_sequence, 

#END OF OPPONENT CLASS

#PLAYER CLASS#

class Player:
    
    #Constructor method
    def __init__(self, test = False):
        self.socket = None
        self.saved_data = {}
        self.test = test

    #Utility function for turning sets and lists into strings. Used to make lists for
    #input into 'calc' equity function
    def to_str(self,i): return str(i).split('[')[1].split(']')[0].replace(' ','').replace("'",'').replace(',','')
    
    #Main runtime method
    def run(self, input_socket):
        # Get a file-object for reading packets from the socket.
        # Using this ensures that you get exactly one packet per read.
        self.socket = input_socket
        f_in = self.socket.makefile()
        while True:
            # Block until the engine sends us a packet.
            input_str = f_in.readline()
            message = self.process_input(input_str)
            if message == 'BREAK':
                break
            elif message:
                message += '\n'
                self.socket.send(message)
        # Clean up the socket.
        self.socket.close()

    #This function takes in message strings and returns the appropriate response
    def process_input(self,input_str):
        data = input_str.split()
        message = None
        # If data is None, connection has closed.
        if not data: return 'BREAK'
        else:
            command = data[0]
            # Otherwise, execute play based on recieved data
            if command == "NEWGAME":
                #Executes game initialization procedure
                self.init_game(*data)
                return None
            elif command == "KEYVALUE":
                #Processes key/value pair
                return self.store_value(*data)
            elif command == "REQUESTKEYVALUES":
                #Returns key/value pairs for storage and finishes
                return self.finish(*data)
            elif command == "NEWHAND":
                #Executes hand initialization procedure
                self.init_hand(*data)
                return None
            elif command == "GETACTION":
                #Executes main logic and performs relevant action
                return self.play(data)
            elif command == "HANDOVER":
                #Executes end hand procedure
                self.end_hand(data)
                return None
            else:
                #Invalid command causes abort
                return 'BREAK'

    #Executes game initialization procedure
    def init_game(self, command, name, oppName, stackSize, bb, numHands, timeBand):
        self.name = name
        self.opponent = Opponent(oppName)
        self.stackSize, self.bigBlind, self.numHands = int(stackSize), int(bb), int(numHands)
        self.timeBand = float(timeBand)

    #SAVING METHODS SECTION#
    #This section contains the methods handling value storage and recovery. Nothing is really implemented here
    #right now.
    
    #Processes key/value pair
    def store_value(self,command,key,val):
        self.saved_data[key] = val

    #Returns key/value pairs for storage and finishes
    def finish(self, command, bytesLeft):
        return 'FINISH'
    
    #END OF SAVING METHODS SECTION#
    
    #HAND INITIALIZATION METHOD SECTION#
    #This section contains init_hand, the method handling NEWHAND calls, as well as
    #all of the methods on which it is dependent.
    
    #Executes hand initialization procedure
    def init_hand(self, command, handId, button, holeCard1, holeCard2, holeCard3, yourBank, oppBank, timeBank):
        self.handId, self.button, self.bank, self.oppBank, self.timeBank = handId, button, yourBank, oppBank, timeBank
        self.holeCards = set([holeCard1, holeCard2, holeCard3])
        self.deck = DECK.copy()
        for c in self.holeCards: self.deck.remove(c)
        self.discards = set()

    #END OF HAND INITIALIZATION METHOD SECTION#
    
    #PLAY METHOD SECTION#
    #This section contains play, the method handling GETACTION calls, as well as
    #all of the methods on which it is dependent.
    
    #Executes main logic and performs relevant action
    def play(self, data):
        #Parses data string into dictionary d
        d = self.parse_getcommand(data)
        #Identifies discard phase or betting phase
        if d['legalActions'] == ['DISCARD']: return self.discard(**d)
        else: return self.bet(**d)

    #Parses getcommand data list into data dictionary
    def parse_getcommand(self, data):
        #Computes position of end of boardCards list
        a = int(data[2]) + 3
        #Computes position of end of lastActions list
        b = a + int(data[a]) + 1
        #Initializes the return dictionary and populates it
        d = {}
        d['potSize'] = data[1]
        d['boardCards'] = data[3:a]
        d['lastActions'] = data[a+1:b]
        d['legalActions'] = data[b+1:-1]
        d['timebank'] = data[-1]
        return d

    #Computes correct card to discard
    def discard(self, potSize, boardCards, lastActions, legalActions, timebank):
        #LOCAL MACROS#
        CALC_ITERS = 100000
        
        #MAIN CODE#
        #Seeks to keep the cards that afford the maximum equity against an arbitrary pair of cards
        #by computing the equity of 2 card subsets of hand
        v, l, discard = 0, list(self.holeCards), None
        for i in xrange(3):
            j = (i + 1) % 3
            k = (i + 2) % 3
            h = l[i] + l[j] + ':xx'
            b = self.to_str(boardCards)
            d = l[k]
            c = calc(h,b,d,CALC_ITERS)
            if c.ev[0] > v:
                discard = l[k]
        self.holdCards.remove(discard)
        self.discards.add(discard)
        return 'DISCARD:' + discard

    #BET DETERMINATION METHOD SECTION#
    #This section contains methods used to determine whether to fold and how much to bet#
            
    #Computes correct bet (at the moment using only equity)
    def bet(self, potSize, boardCards, lastActions, legalActions,timebank):
        #LOCAL MACROS#
        CALC_ITERS = 50000
        
        #MAIN CODE#
        #Initial equity calculation
        hole_cards_str = self.holeCards) + ':xxx'
        board_cards_str = self.to_str(boardCards)
        discard_str = self.to_str(self.discards)
        e = calc(self.to_str(hole_cards_str, board_cards_str, discard_str, CALC_ITERS).ev
                 
        #Gathers variables for input into threshold and bet functions
        opponent = self.opponent_model
        if len(boardCards) == 0: betting_round = 0
        else: betting_round = len(boardCards) - 2
        r1, r2 = random(), random()
        
        #Applies threshold function
        if e < self.threshold_function(opponent, ,betting_round ,r1):
            return self.try_fold(legalActions)
        #If threshold is met, makes bet  
        else:
            bet_amount = self.bet_function(opponent, )
            return 'BET:' + bet_amount

    #Tries to fold by taking the next best option if fold cannot be performed.
    def try_fold(self, legalActions):
        if 'FOLD' in legalActions: return 'FOLD'
        elif 'CHECK' in legalActions: return 'CHECK'
        elif 'CALL' in legalActions: return 'CALL'
        else: return 'BET:' + str(self.bigBlind)
                 
    #END OF BET DETERMINATION METHOD SECTION#

    #END OF PLAY METHOD SECTION#
    
    #END HAND METHOD SECTION#
    #This section contains end_hand, the method handling HANDOVER calls, as well as the functions on which
    #it is dependent

    #Executes end hand procedure
    def end_hand(self, data):
        d = self.parse_handover(data)

    #Parses handover data list into data dictionary
    def parse_handover(self, data):
        #Computes position of end of boardCards list
        a = int(data[3]) + 4
        #Initializes the return dictionary and populates it
        d = {}
        d['yourBank'] = data[1]
        d['oppBank'] = data[2]
        d['boardCards'] = data[4:a]
        d['lastActions'] = data[a+1:-1]
        d['timeBank'] = data[-1]
        return d

    #END OF PLAY METHOD SECTION#

#END OF PLAYER CLASS$
                 
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
