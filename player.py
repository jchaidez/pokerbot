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

from json import loads, dumps
json_loads, json_dumps = loads, dumps
del loads, dumps

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
    #of polynomials parameterized as so. Let button be a variable indicating whether
    #or not the opponent is the button, and let bet_round be the round of betting
    #(0,1,2,3) taking place. Then
    
    #self.history[button][bet_round]['bet' or 'equity'] = [list of bet or equity data points]
    
    #self.e_to_b_lib[button][bet_round] = [polynomial array modeling equity to bet function]
    #self.b_to_e_lib[button][bet_round] = [polynomial array modeling equity to bet function]
    #self.equity_floor_lib[button][bet_round] = |estimated equity floor for these parameters|
    
    #Constructor method
    def __init__(self, name, bigBlind):
        
        #LOCAL MACROS#
        INITIAL_FOLDING_FREQUENCY = .3 
        INITIAL_FOLDING_SAMPLE_SIZE = 10
        INIT_B_FLOOR, INIT_N_FLOOR = .4, .3 #These are the initial values for the 
        
        #MAIN CODE#
        #Stores name
        self.name = name
        
        #Initializes history storage data structure
        self.play_history = self.init_history()
        
        #Initializes polynomial library data structure
        self.e_to_b_lib = self.init_lib()
        self.b_to_e_lib = self.init_lib()
        self.equity_floor_lib = self.init_lib(INIT_B_FLOOR, INIT_N_FLOOR)
        
        #Calculates 
        self.redetermine_libs()
    
        #Initializes current bet sequence variable
        self.bet_sequence = [0,0,0,0]
    
        #Initializes folding frequency variables
        self.folding_frequency = INITIAL_FOLDING_FREQUENCY
        self.folding_sample_size = INITIAL_FOLDING_SAMPLE_SIZE
        
        #Stores half big blind value
        self.bigBlind = bigBlind

    #Utility function for turning sets and lists into strings. Used to make lists for
    #input into 'calc' equity function. This might be better as a global function
    def to_str(self,i): return str(i).split('[')[1].split(']')[0].replace(' ','').replace("'",'').replace(',','')
    
    #Constructor for history dictionary
    def init_history(self):
        d = {}
        d[True], d[False] = [], []
        for i in xrange(4):
            d[True].append({'bet':[0,1],'equity':[0,1]})
            d[False].append({'bet':[0,1],'equity':[0,1]})
        return d
    
    #Constructor for library dictionaries
    def init_lib(self):
        d = {}
        d[True], d[False] = [[],[],[],[]], [[],[],[],[]]
        return d

    #Constructor for library dictionaries
    def init_eq_lib(self):
        d = {}
        d[True], d[False] = [i,i,i,i], [j,j,j,j]
        return d
    
    #Exports data from this player in json format and returns it
    def export_history(self):
        d = dict()
        d['name'] = self.name
        d['play_history'] = self.play_history
        d['e_to_b_lib'] = self.e_to_b_lib
        d['b_to_e_lib'] = self.b_to_e_lib
        d['equity_floor_lib'] = self.equity_floor_lib
        d['folding_frequency'] = self.folding_frequency
        d['foldin_sample_size'] = self.foldin_sample_size
        
        return json_dump(d)
    
    #Loads a saved data set about a player bot
    def load_history(self, data):
        d = json_loads(data)
        self.name = d['name']
        self.play_history = d['play_history']
        self.e_to_b_lib = d['e_to_b_lib']
        self.b_to_e_lib = d['b_to_e_lib']
        self.equity_floor_lib = d['equity_floor_lib']
        self.folding_frequency = d['folding_frequency']
        self.folding_sample_size = d['foldin_sample_size']
    
    #Adds single card point, and performs necessary recalculations to
    #determine 
    def add_hand_data_pt(self, hand, board, bet_seq, button):
        #LOCAL MACROS#
        CALC_ITERS = 10000
        POLY_DEGREE = 5

        #MAIN CODE#
        #Makes hand inut for equity calculation
        h = hand + ':xx'
        #For each betting phase with board cards
        for i in xrange(0,4):
            
            #Stores total bet made on that phase
            self.play_history[button][i]['bet'].append(bet_seq[i])
            
            #Stores equity of the hand that the opponent possesed at the time of the bet
            if i == 0: b = ''
            else: b = self.to_str(board[:3+i])
            d = ''
            e = calc(h,b,d,CALC_ITERS)
            self.play_history[button][i]['equity'].append(e)

            #Performs polynomial regression to determine the equity to bet function and a bet to equity function
            self.e_to_b_lib[button][i] = \
            polyfit(self.play_history[button][i]['equity'], self.play_history[button][i]['bet'], POLY_DEGREE)

            self.b_to_e_lib[button][i] = \
            polyfit(self.play_history[button][i]['bet'], self.play_history[button][i]['equity'], POLY_DEGREE)

            #Checks to see if equity threshold should change based on new betting evidence.
            if e < self.equity_floor_lib[button][i]: self.equity_floor_lib[button][i] = e

    #Recalculates the polynomial functions based on current play history
    def redetermine_libs(self):
        for i in [True, False]:
            for j in xrange(0,4):
            
                #Performs polynomial regression to determine the equity to bet function and a bet to equity function
                self.e_to_b_lib[button][i] = \
                polyfit(self.play_history[i][j]['equity'], self.play_history[button][i]['bet'], POLY_DEGREE)
            
                self.b_to_e_lib[button][i] = \
                polyfit(self.play_history[i][j]['bet'], self.play_history[button][i]['equity'], POLY_DEGREE)
                    
    #Gets estimated opponent bet amount given equity, button and betting round.
    def get_bet_amount(self, equity, round, button):
        r = 0
        p = self.e_to_b_lib[button][round]
        for i in range(len(p)): r += p[-i - 1] * (equity ** i)
        return r

    #Gets estimated opponent equity given bet amount, button and betting round.
    def get_equity(self, bet, round, button):
        r = 0
        p = self.b_to_e_lib[button][round]
        for i in range(len(p)): r += p[-i - 1] * (bet ** i)
        return r

    #Gets estimated opponent equity threshold given round and button
    def get_equity_threshold(self, round, button):
        return self.equity_floor_lib[button][round]

    #BET SEQUENCE STORAGE AND PROCESSING#
    
    #Resets the bet sequence for a new hand
    def reset_bet_sequence(self):
        self.bet_sequence = [0,0,0,0]        
    
    #Gets sequence of final bets by turn
    def get_bet_sequence(self):
        return self.bet_sequence
    
    #Gets current opponent bet given round number
    def get_current_bet(self, round):
        return self.bet_sequence[round]
    
    #Updates bet sequence given total pot contents, current bet and the betting round.
    def update_bet_sequence(self, pot, player_bet, round):
        self.bet_sequence[round] = (pot - player_bet) - (3 * (self.bigBlind / 2))

    #END OF BET SEQUENCE STORAGE AND PROCESSING#

    #FOLDING FREQUENCY STORAGE AND PROCESSING#

    #Gets current folding frequency
    def get_folding_frequency(self):
        return self.folding_frequency

    #Updates folding frequency
    def update_folding_frequency(self, folded):
        self.folding_frequency = ((self.folding_frequency * self.folding_sample_size) + folded)\
        /(self.folding_sample_size + 1)

    #END OF FOLDING FREQUENCY AND PROCESSING#

#END OF OPPONENT CLASS

#PLAYER CLASS#

class Player:
    
    #Constructor method
    def __init__(self, test = False):
        self.socket = None
        self.saved_data = {}
        self.test = test

    #CLASS UTILITIES#
    
    #Utility function for turning sets and lists into strings. Used to make lists for
    #input into 'calc' equity function
    def to_str(self,i): return str(i).split('[')[1].split(']')[0].replace(' ','').replace("'",'').replace(',','')
    
    #Utility function that looks in list of actions and returns all actions of a given type
    def find_actions(self, actions, type):
        l = []
        for action in actions:
            if action[0] == type[0] and action[1] == type[1]: l.append(action)
        return l
    
    #Utility functions for normalizing and denormalizing value of total bet (to make it fraction of entire stack)
    def normalize_bet(self, bet):
        return bet / self.stackSize
    
    def denormalize_bet(self, bet):
        return round(bet * self.stackSize)
    
    #END CLASS UTILITIES#
    
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
    def init_game(self, command, name, oppName, stackSize, bb, numHands, timeBank):
        self.name = name
        self.opponent = Opponent(oppName, int(bb))
        self.stackSize, self.bigBlind, self.numHands = int(stackSize), int(bb), int(numHands)
        self.timeBank = float(timeBank)

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
        
        #Resets current bet count to 0
        self.current_bet = 0
    
        #Resets bet sequence of opponent model
        self.opponent.reset_bet_sequence()

    #END OF HAND INITIALIZATION METHOD SECTION#
    
    #PLAY METHOD SECTION#
    #This section contains play, the method handling GETACTION calls, as well as
    #all of the methods on which it is dependent.
    
    #Executes main logic and performs relevant action
    def play(self, data):
        #Parses data string into dictionary d
        d = self.parse_getcommand(data)
        #Identifies discard phase or betting phase
        if 'DISCARD' in d['legalActions']: return self.discard(**d)
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
    def bet(self, potSize, boardCards, lastActions, legalActions, timebank):
        #LOCAL MACROS#
        CALC_ITERS = 50000
        
        #MAIN CODE#
        #Initial equity calculation
        hole_cards_str = self.holeCards + ':xxx'
        board_cards_str = self.to_str(boardCards)
        discard_str = self.to_str(self.discards)
        e = calc(hole_cards_str, board_cards_str, discard_str, CALC_ITERS).ev
                 
        #Gathers variables for input into threshold and bet functions
        opponent = self.opponent_model
        button = self.button
        if len(boardCards) == 0: betting_round = 0
        else: betting_round = len(boardCards) - 2
        r1, r2 = random(), random()
        
        #Updates current opponent bet
        opponent.update_bet_sequence(lastActions, self.current_bet, betting_round)
        
        #Applies threshold function
        if e < self.threshold_function(opponent, button, betting_round, r1):
            return self.try_fold(legalActions)
        #If threshold is met, makes bet  
        else:
            bet_amount = self.denormalize_bet(self.bet_function(opponent, e, button, betting_round, r2))
            return self.try_bet(bet_amount, potSize, legalActions)

    #Tries to bet a certain amount
    def try_bet(new_amount, potSize, legalActions):
                 
        #Ensures that bet is not above stack size or below big blind
        if self.current_bet - new_amount < self.bigBlind: new_amount = self.current_bet
        elif new_amount > self.stackSize: new_amount = self.stackSize
        
        #If new amount is too low, tries to perform checks and calls
        if new_amount <= self.current_bet:
            if 'CHECK' in legal_actions: return 'CHECK'
            elif 'CALL' in legalActions: return 'CALL'
        #Otherwise, tries to implement bet to the level intended, if possible.
        else:
            if 'BET' in legalActions: return 'BET:' + str(new_amount - self.current_bet)
            elif 'RAISE' in legalActions: return 'RAISE:' + str(potSize + new_amount - self.current_bet)
            elif 'CALL' in legalActions: return 'CALL'
            elif 'CHECK' in legalActions: return 'CHECK'
            self.current_bet = new_amount
                 
    #Tries to fold by taking the next best option if fold cannot be performed.
    def try_fold(self, legalActions):
        if 'FOLD' in legalActions: return 'FOLD'
        elif 'CHECK' in legalActions: return 'CHECK'
        elif 'CALL' in legalActions: return 'CALL'
        else: return 'BET:' + str(self.bigBlind)
                 
    #Outputs lowest acceptable equity given current situation
    def threshold_function(self, opp, opp_bet, self_button, round, r):
        
        #LOCAL MACROS#
        A = 1
        B = .1
        C = .1
        D = .5
        E = -.5
        F = .2
        G = .01
        H = .2
        
        #MAIN CODE#
                 
        #Gathering important data for actual metric function (variables numbered and lettered below)
        opp_button = not self_button #1
        opp_thresh = opp.get_equity_threshold(round, opp_button) #2
        
        opp_bet = self.normalize_bet(opp.get_current_bet(betting_round))
        opp_equity = opp.get_equity_amount(opp_bet, round, opp_button) #3
        
        opp_fold_freq = opp.get_folding_frequency() #4
        #Variables round and r (random variable in range 0-1) are metric variables 5 and 6 respectively
    
        #Actual calculation takes place here
        return (A + (B * round)) * ((C * opp_thresh) + (D * (opp_equity ** 2)))\
             + (A - (B * round)) * ((F * opp_button)  + (E * (opp_fold_freq ** 2)))\
             + (G * r) + H
    
    
    #Outputs amount that should be bet given current situation
    def bet_function(self, opp, equity, self_button, round, r):
        
        #LOCAL MACROS#
        A = 0
        B = .25
        C = 1
        D = .25
        E = .1
        F = .1
        
        #MAIN CODE#
        
        #Gathering important data for actual metric function (variables numbered and lettered below)
        opp_button = not self_button #1
        opp_real_bet = self.normalize_bet(opp.get_current_bet(betting_round))
        opp_equity = opp.get_equity_amount(opp_real_bet, round, opp_button) #2
        opp_rvrs_bet = opp.get_bet_amount(equity, round, button) #3
        #Variables equity, round and r (random variable in range 0-1) are metric variables 4, 5 and 6 respectively
    
        #Actual calculation takes place here
        return (A + (B * (round + 1))) * ((C * (equity - opp_equity)) + (D * opp_rvrs_bet))\
             + (E * (button - .5) / (round + 1)) + (F * (r - .5))
                 
    #END OF BET DETERMINATION METHOD SECTION#

    #END OF PLAY METHOD SECTION#
    
    #END HAND METHOD SECTION#
    #This section contains end_hand, the method handling HANDOVER calls, as well as the functions on which
    #it is dependent

    #Executes end hand procedure
    def end_hand(self, data):
        #Parses input string
        d = self.parse_handover(data)
        #Finds all show actions given in final part of hand
        l1 = self.find_actions(d['lastActions'],'SHOW')
        if l1:
            #If cards were shown, logs data in opponent model
            for show in l1:
                action, c1, c2, actor = show.split(':')
                if actor == self.opponent.name:
                    h = c1 + c2
                    b = d['boardCards']
                    opp_bet_seq = []
                    for b in self.opponent.get_bet_sequence():
                        opp_bet_seq.append(self.normalize_bet(b))

                    #Normalizes bets to account for current 
                    opp_button = not self.button
                    self.opponent.add_hand_data_pt(h, b, opp_bet_seq, opp_button)
        l2 = self.find_actions(d['lastActions'],'FOLD')
        opp_folded = (l2 and l2[0].split(':')[1] == self.opponent.name)
        self.opponent.update_fold_frequency(opp_folded)

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
