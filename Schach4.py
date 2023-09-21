import copy
import datetime
"""rules: 
- if a coordinate is mentioned, the file is always the first number
- rank and file numbers start at 0 and go up to 7
- should_work in the comments after a line means that it might not work

todo:
- better way to store castling
- make that piece_on() in Position doesnt always call get_piece_list()
- make Coordinates not store the same value in two different ways
- use getters and setters
- find a better way to store the initial position
- use a class to store colours and put colour_multiplier and swith_colour inside it (then its a mutable obj so gotta pay attention
- make the pieces not have the position as a variable
- evaluation: castling + check and mate threads 
- bonus eval if pawns are supported by other pawns
- make the king untakeable (eval funcs do weird stuff to prevent crash)
- make underpromotion
- use pos.is_move_possible to check for opponents move -> implement it for pawns
x fix hanging pieces
"""

class Coordinate:
    def __init__(self, index=None, rank=None, letter_file=None, number_file=None):
#        breakpoint()
        self.letters = ("a", "b", "c", "d", "e", "f", "g", "h")
        if index is not None: #this makes it work when index is 0 because from some reason it doesnt work then
            self.file = index % 8
            self.rank = int((index - self.file) / 8)
        elif rank is not None:
            self.rank = int(rank)
            if number_file is not None:
                self.file = number_file
            elif letter_file:
                self.file = self.letters.index(letter_file)
        else:
            raise RuntimeError()
    def get_numbers(self):
        return {"file":self.file, "rank": self.rank}
    def get_coordinate(self):
        return self.letters[self.file] + str(self.rank + 1) #this is not wrong
    def get_index(self):
        try:
            return self.rank * 8 + self.file
        except AttributeError:
            breakpoint()
    def __str__(self):
        return self.get_coordinate()



class Move:
    def __init__(self, start=None, end=None, take=None, special=None):
        """special can be: two_pawn (pawn moves two squares, EnPassant object must be created), kcastle, qcastle"""
        self.start = start
        self.end = end
        self.take = take
        self.special = special
    def __str__(self):
        self.connector = "x" if self.take == True else "-"
        if self.special ==  None:
            return self.start.get_coordinate() + self.connector + self.end.get_coordinate()

class Piece:
    def __init__(self, pos, colour, own_pos, attackers=0, defenders=0, possible_moves=None):
        """the current position class is passed as position so that the piece can delete itself"""
        self.pos = pos
        self.own_pos = own_pos
        self.colour = colour
        self.possible_moves = possible_moves
        self.attackers = attackers
        self.highest_attacker = 0
        self.defenders = defenders
        self.lowest_defender = 0
        self.number_of_moves = 0
    def disappear(self):
        self.pos.pieces[self.colour][type(self).__name__].remove(self)        
    def get_mobility_value(self):
        pass
    def check_and_append_move(self, start, target_square, append_moves = True):
        self.move_is_take = False
        self.target_piece = self.pos.piece_on(target_square) #checks if theres a piece on the targeted square
        self.start_piece = self.pos.piece_on(start)
        if self.target_piece is not None:
            if self.target_piece.colour == self.colour: #if the targeted piece has the own colour
                self.target_piece.defenders += 1
                if self.start_piece.value < self.target_piece.lowest_defender:
                    self.target_piece.lowest_defender = self.start_piece.value
                return False #we dont want to take our own piece
            else:
                
                self.move_is_take = True
                self.target_piece.attackers += 1
                if self.start_piece.value > self.target_piece.highest_attacker:
                    self.target_piece.highest_attacker = self.start_piece.value
                if append_moves:
                    self.pos.possible_moves.append(Move(start = start, end = target_square, take = self.move_is_take)) #adding the moves, because theres an enemy piece on the target square
                return False #was opponents piece, so infinite pieces must stop
        if append_moves:
            self.pos.possible_moves.append(Move(start = start, end = target_square, take = self.move_is_take)) #adding the moves, because the target square is empty
            self.number_of_moves += 1
        return True
    def __str__(self):
        return self.colour + type(self).__name__ + " on " + self.own_pos.get_coordinate()

class InfinitePiece(Piece):
    """a piece whose move radius is only limited by the dimensions of the chess board"""
    def find_possible_moves(self, append_moves=True, append_moves_to_pos=True): #.isinstance(specific piece, Piece class)
        self.possible_moves = []
        if append_moves_to_pos == False:
            append_moves = True
        for move in self.move_matrix:
            self.target_square = Coordinate(number_file = self.own_pos.get_numbers()["file"] + move[0], rank = self.own_pos.get_numbers()["rank"] + move[1])
            while self.pos.does_square_exist(self.target_square):
                if self.check_and_append_move(self.own_pos, self.target_square, append_moves = False) == False:
                    break
                elif append_moves_to_pos == False:
                    self.pos.possible_moves.append(Move(self.own_pos, self.target_square))
                else:
                    self.possible_moves.append(Move(self.own_pos, self.target_square))
                self.target_square = Coordinate(number_file = self.target_square.get_numbers()["file"] + move[0], rank = self.target_square.get_numbers()["rank"] + move[1])

                
class FinitePiece(Piece):
    """a piece whose move radius is limited"""
    def find_possible_moves(self,append_moves=True, append_moves_to_pos = True):
        if not append_moves_to_pos:
            self.possible_moves = [] #doesn't empty automatically
        for move in self.move_matrix:
            self.target_square = Coordinate(number_file = self.own_pos.get_numbers()["file"] + move[0], rank = self.own_pos.get_numbers()["rank"] + move[1]) #adds the move from the matrix to own pos and checks if its within the boundaries of the chessboard
            if self.pos.does_square_exist(self.target_square):
                if append_moves:
                    self.check_and_append_move(self.own_pos, self.target_square, append_moves = True)
                elif not append_moves_to_pos:
                    if self.check_and_append_move(self.own_pos, self.target_square, append_moves = False) == True:
                        self.possible_moves.append(move)
        if isinstance(self, King):
            self.check_castling() #maybe this could be done from the king using super(), but then the variables from the king woudnt be there
                


class Pawn(Piece):
    value = 1
    def __init__(self, pos, colour, own_pos, attackers=0, defenders=0, possible_moves=None, has_moved=False):
        super().__init__(pos, colour, own_pos, attackers, defenders, possible_moves) #calls the init function from the parent
        self.has_moved = has_moved        
    def find_possible_moves(self, append_moves=True, append_moves_to_pos=True):
        if append_moves:
            #check if it can move forward
            self.target_square = Coordinate(index = (self.own_pos.get_index() + 8 * colour_multiplier[self.colour]))
            if not self.pos.piece_on(self.target_square, w_EnPassant = True) and self.pos.does_square_exist(self.target_square): #check if the square infront of it is empty
                self.pos.possible_moves.append(Move(self.own_pos, self.target_square))
                if self.has_moved == False:
                    self.target_square = Coordinate(index = (self.own_pos.get_index() + 16 * colour_multiplier[self.colour]))
                    if not self.pos.piece_on(self.target_square, w_EnPassant = True):
                        self.pos.possible_moves.append(Move(self.own_pos, self.target_square))
        #checks if it can take
        for i in [(-1, 1), (1, 1)]: #file, rank the pawn moves when it takes
            self.target_square = Coordinate(number_file = (self.own_pos.get_numbers()["file"]) + i[0], rank = self.own_pos.get_numbers()["rank"] + i[1] * colour_multiplier[self.colour])
            if not self.pos.does_square_exist(self.target_square):
                continue #with the next iteration of the loop
            self.target_piece = self.pos.piece_on(self.target_square, w_EnPassant = True)
            if self.target_piece:
                if self.target_piece.colour != self.colour:
                    self.target_piece.attackers += 1
                    if self.target_piece.highest_attacker < 1:#self.value=1
                        self.target_piece.highest_attacker = 1
                    if append_moves:
                        self.pos.possible_moves.append(Move(self.own_pos, self.target_square))
                        self.pos.possible_moves[-1].take = True
                elif self.target_piece.colour == self.colour:
                    self.target_piece.defenders += 1
                    if self.target_piece.lowest_defender > 1: #self.value=1
                        self.target_piece.lowest_defender = 1
                        
        

class Knight(FinitePiece):
    value = 3
    letter = "N"
    move_matrix = ((2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2), (1, -2), (2, -1))

class Bishop(InfinitePiece):
    value = 3.5
    move_matrix = ((1, 1), (-1, 1), (-1, -1), (1, -1))

class Rook(InfinitePiece):
    value = 5
    move_matrix = ((0, 1), (1, 0), (0, -1), (-1, 0))

class Queen(InfinitePiece):
    value = 9
    move_matrix = ((1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0))

class King(FinitePiece):
    value = 200
    move_matrix = ((1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0))
    def check_castling(self):
        pass
    

class EnPassant:
    """maybe this must only be allowed to be created if theres actually a pawn that can take en passant to not mess up the evaluation if there is an En Passant that cant be taken and adds 500 points to the eval. maybe even solve this conpletely different by checking for en passant when making a move and ading it to the possible moves immediately aka making the move and changing the colour."""
    value = 0
    """this has value 0 to avoid the above mentioned problems. It kinda has the value of the pawn to, because theire linkd to each other.  I just have to figure out how to make the rest of the moves in possible_moves disappear when theres en passant"""
    def __init__(self,  colour, own_pos, corresponding_pawn):
        self.corresponding_pawn = corresponding_pawn
        self.own_pos = own_pos
        self.colour = colour



        
class Position:
    def __init__(self, colour = "white", pieces = None):
        self.pieces = pieces if pieces else {"white": {"Pawn": [Pawn(self, "white", Coordinate(index = 8)), Pawn(self, "white", Coordinate(index = 9)), Pawn(self, "white", Coordinate(index = 10)), Pawn(self, "white", Coordinate(index = 11)), Pawn(self, "white", Coordinate(index = 12)), Pawn(self, "white", Coordinate(index = 13)), Pawn(self, "white", Coordinate(index = 14)), Pawn(self, "white", Coordinate(index = 15))], "Knight": [Knight(self, "white", Coordinate(index = 1)), Knight(self, "white", Coordinate(index = 6))], "Bishop": [Bishop(self, "white", Coordinate(index = 2)), Bishop(self, "white", Coordinate(index = 5))], "Rook": [Rook(self, "white", Coordinate(index = 0)), Rook(self, "white", Coordinate(7))], "Queen": [Queen(self, "white", Coordinate(index = 3))], "King": [King(self, "white", Coordinate(index = 4))], "EnPassant": []}, "black": {"Pawn": [Pawn(self, "black", Coordinate(index=48)), Pawn(self, "black", Coordinate(index=49)), Pawn(self, "black", Coordinate(index=50)), Pawn(self, "black", Coordinate(index=51)),Pawn(self, "black", Coordinate(index=52)),Pawn(self, "black", Coordinate(index=53)),Pawn(self, "black", Coordinate(index=54)), Pawn(self, "black", Coordinate(index=55)),], "Knight": [Knight(self, "black", Coordinate(index=57)), Knight(self, "black", Coordinate(index=62))], "Bishop": [Bishop(self, "black", Coordinate(index=58)), Bishop(self, "black", Coordinate(index=61))], "Rook": [Rook(self, "black", Coordinate(index=56)), Rook(self, "black", Coordinate(index=63))], "Queen": [Queen(self, "black", Coordinate(index=59))], "King": [King(self, "black", Coordinate(index=60))], "EnPassant": []}}#"black": {"Pawn": [], "Knight": [], "Bishop": [], "Rook": [], "Queen": [], "King": [], "EnPassant": [] for backup reasons
#        self.pieces = {"white": {"Pawn": [Pawn(self, "white", Coordinate(index = 47))], "Knight": [], "Bishop": [], "Rook": [], "Queen": [Queen(self, "white", Coordinate(index = 2))], "King": [], "EnPassant": []}, "black": {"Pawn": [], "Knight": [], "Bishop": [], "Rook": [Rook(self, "black", Coordinate(index = 11)), Rook(self, "black", Coordinate(index = 24))], "Queen": [Queen(self, "black", Coordinate(index = 16))], "King": [], "EnPassant": []}}
        self.possible_moves = []
        self.children = []
        self.evaluation = None
        self.colour = colour
        self.last_move = None
        self.best_move = None
    def piece_on(self, square, w_EnPassant=False):
        for piece in self.get_piece_list(w_EnPassant = w_EnPassant):
            if piece.own_pos.get_index() == square.get_index():
                return piece
        return None
    def is_move_possible(self, move):
        self.moving_piece = self.piece_on(move.start)
        if  move.start.get_index() >= 0 and move.end.get_index() <= 63 and self.moving_piece:
            self.moving_piece.find_possible_moves(append_moves_to_pos)
            if move in self.moving_piece.possible_moves:
                if move.take == True:
                    if not self.piece_on(move.end) or self.moving_piece.colour == self.piece_on(move.end.colour):
                        return False
                if self.moving_piece.colour == self.colour:
                    return True
        return False
    def make_move(self, move):
        self.colour = switch_colour[self.colour]
        for piece in self.get_piece_list(): #this is also done in pos.find_possible_moves() so most likely this is useless
            piece.attackers = 0
            piece.defenders = 0
            piece.highest_attacker = 0
            piece.lowest_defender = 0
            piece.number_of_moves = 0
        if isinstance(self.piece_on(move.start), Pawn):
            self.piece_on(move.start).has_moved = True
        if not move.special:
            if move.take == True:
                try:
                    self.piece_on(move.end, w_EnPassant=True).disappear()
                except AttributeError:
                    print("make_move() failed #1")
                    breakpoint()
            try:
                self.moving_piece = self.piece_on(move.start)
                self.moving_piece.own_pos = copy.deepcopy(move.end)
                if isinstance(self.moving_piece, Pawn) and move.end.get_numbers()["rank"] == 3.5 + 3.5 * colour_multiplier[self.moving_piece.colour]: #pawn that has reached the last rank
                    self.pieces[self.moving_piece.colour]["Queen"].append(Queen(self, self.moving_piece.colour, self.moving_piece.own_pos))
                    self.moving_piece.disappear()
            except AttributeError:
                print("make_move() failed #2")
                breakpoint()
        elif move.special == "two_pawn":
            self.pieces[self.piece_on(move.start)]["EnPawnsant"].append(EnPassant(self.piece_on(move.start).colour, Coordinate(index = self.piece_on(move.start).own_pos + 8 *colour_multiplier(self.piece_on(move.start).colour)), self.piece_on(move.start))) #creating new EnPassant one square behind the pawn
            
            self.piece_on(move.start).own_pos = copy.deepcopy(move.end)
        self.last_move = move
    def does_square_exist(self, square):
        return True if 0 <= square.file <= 7 and 0 <= square.rank <= 7 else False
    def find_possible_moves(self):
        for piece in self.get_piece_list():
            piece.attackers = 0
            piece.defenders = 0
            piece.highest_attacker = 0
            piece.lowest_defender = 0
            piece.number_of_moves = 0
        #get the attackers and defenders from the opponents pieces
        for piece in self.get_piece_list(switch_colour[self.colour]):
            piece.find_possible_moves(append_moves = False)
        #get the actual moves
        self.possible_moves = []
        for piece in self.get_piece_list(self.colour):
            piece.find_possible_moves()
        #remove EnPassants
        self.pieces[self.colour]["EnPassant"] = []
    def material(self):
        self.material_value = 0
        for piece in self.get_piece_list():
            self.material_value += piece.value * colour_multiplier[piece.colour]
#        print("material: ", self.material_value)
        return self.material_value
    def space(self):
        self.space_value = 0
        for pawn in self.pieces[self.colour]["Pawn"]:
            self.space_value += ((pawn.own_pos.get_numbers()["rank"] - (3.5 - 2.5 * colour_multiplier[self.colour])) / 5) #0.2 points for every step a pawn has taken 3.5 - 2.5 * colour_multiplier gives the starting rank of the pawn, rappel rank goes from 0 to 7
        for pawn in self.pieces[switch_colour[self.colour]]["Pawn"]:
            self.space_value -= ((pawn.own_pos.get_numbers()["rank"] - (3.5 - 2.5 * colour_multiplier[switch_colour[self.colour]])) / 5)
#        print("space:", self.space_value)
        return self.space_value
    def mobility_protection_hanging_pieces_king_mobility_and_safety(self):
        self.protection = 0
        self.king_mobility = 0
        self.mobility = 0
        self.king_safety = 0
        self.hanging_pieces = 0
        self.colour = switch_colour[self.colour]
        self.find_possible_moves()
        #protection
        for piece in self.get_piece_list(self.colour):
            if type(piece) in [Pawn, Knight, Bishop, Rook, Queen]:  #should_work
                if piece.attackers < piece.defenders:
                    self.protection -= 1 * colour_multiplier[switch_colour[self.colour]]
#        print("opponents", self.colour, " prot: ", self.protection)
        #mobility
        for piece in self.get_piece_list(self.colour):
            self.mobility += pow(piece.number_of_moves, 0.5) * colour_multiplier[self.colour]
        #king mobility
        for move in self.possible_moves:
            try:
                if move.start == self.pieces[switch_colour[self.colour]]["King"][0].own_pos:
                    self.king_mobility += 1 * colour_multiplier[self.colour]
            except IndexError:
                pass
        #king safety (negative)
        try:
            self.possible_moves = []
            self.queen_at_kings_position = Queen(self, switch_colour[self.colour], self.pieces[switch_colour[self.colour]]["King"][0].own_pos)
            self.queen_at_kings_position.find_possible_moves()
            self.king_safety -= len(self.possible_moves) * colour_multiplier[self.colour]
        except IndexError:
            pass
        #hanging pieces
        for piece in self.get_piece_list(self.colour):
            if (piece.highest_attacker > piece.lowest_defender) or (piece.highest_attacker == piece.lowest_defender and piece.attackers > piece.defenders):
                self.hanging_pieces -= piece.value * colour_multiplier[piece.colour]
                #only check hanging pieces of the side that just made a move, because the other one has time to save it. say, white moves, then make_move switches the colour to black, but it was already switched back to white in this function.
        #real colour
        self.colour = switch_colour[self.colour]
        #king safety (bad -> negative)
        self.possible_moves = []
        try:
            self.queen_at_kings_position = Queen(self, self.colour, self.pieces[self.colour]["King"][0].own_pos)
            self.queen_at_kings_position.find_possible_moves()
            self.king_safety -= len(self.possible_moves) * colour_multiplier[self.colour]
        except IndexError:
            pass
        #end of king safety
        self.find_possible_moves()
        #protection
        for piece in self.get_piece_list(self.colour):
            if type(piece) in [Pawn, Knight, Bishop, Rook, Queen]:
                if piece.attackers < piece.defenders:
                    self.protection += 1 * colour_multiplier[self.colour]
        #mobility
        for piece in self.get_piece_list(self.colour):
            self.mobility += pow(piece.number_of_moves, 0.5) * colour_multiplier[self.colour]
        #king mobility
        try:
            for move in self.possible_moves:
                if move.start == self.pieces[switch_colour[self.colour]]["King"][0].own_pos:
                    self.king_mobility += 1 * colour_multiplier[self.colour]
        except IndexError:
            pass
#        print(self.mobility, self.protection, pow(self.king_mobility, 0.5), self.king_safety, self.hanging_pieces)
        return self.mobility + self.protection + pow(self.king_mobility, 0.5) + self.king_safety + self.hanging_pieces
    def evaluate(self):
        self.evaluation = round(self.material() + self.mobility_protection_hanging_pieces_king_mobility_and_safety() + self.space(), 1)
    def copy_pieces(self, new_pos):
        self.new_pieces = {"white": {"Pawn": [], "Knight": [], "Bishop": [], "Rook": [], "Queen": [], "King": [], "EnPassant": []}, "black": {"Pawn": [], "Knight": [], "Bishop": [], "Rook": [], "Queen": [], "King": [], "EnPassant": []}}
        for colour in self.pieces:
            for piece_type in self.pieces[colour]:
                for piece in self.pieces[colour][piece_type]:
                    self.new_pieces[colour][piece_type].append(type(piece)(new_pos, colour, Coordinate(index = piece.own_pos.get_index())))
        return self.new_pieces        
    def build_next_tree_layer(self):
        self.evaluation = -10000 * colour_multiplier[self.colour] #must be done because the value is now inaccurate
        if self.children == []:
            if self.possible_moves == []: #this might cause errors when bugs but should not
                self.find_possible_moves()            
            for move in self.possible_moves:
                self.moved_pos = Position(colour = switch_colour[self.colour])
                self.moved_pos.pieces = self.copy_pieces(self.moved_pos)                  
                self.moved_pos.make_move(move)
                self.moved_pos.colour = switch_colour[self.colour]
                self.children.append(self.moved_pos)
            for child in self.children:
                child.evaluate()
                if child.evaluation * colour_multiplier[self.colour] >= self.evaluation * colour_multiplier[self.colour]:
                    self.evaluation = child.evaluation
                    self.best_move = child.last_move
        else:
            for child in self.children:
                child.build_next_tree_layer()
                if child.evaluation * colour_multiplier[self.colour] >= self.evaluation * colour_multiplier[self.colour]:
                    self.evaluation = child.evaluation
                    self.best_move = child.last_move
    def build_tree(self, depth):
        self.find_possible_moves()
        self.evaluate()
        for i in range(0, depth):
            self.build_next_tree_layer()
        self.children = []
    def get_piece_list(self, colour=None, w_EnPassant=False):
        self.piece_list = [j for i in list(self.pieces["white"].values()) for j in i] if colour == "white" else [j for i in list(self.pieces["black"].values()) for j in i] if colour else [j for i in list(self.pieces["white"].values()) + list(self.pieces["black"].values()) for j in i] #i love python
            #filter out EnPassants
        return [piece for piece in self.piece_list if not isinstance(piece, EnPassant)] if w_EnPassant == False else self.piece_list


class Game:
    def __init__(self, pos, depth = 3, always_display_pos = False):
        self.colour = ""
        self.pos = pos
        self.depth = depth
        self.log = {"head": {"white": "", "black": "", "date": datetime.datetime.now().strftime("%d.%m.%Y"), "depth": self.depth}, "game": []}
        self.show_own_moves = False
        self.always_display_pos = always_display_pos
    def init_game(self):
        while self.colour != "white" and self.colour != "black":
            self.colour = input("What colour do you want to play with?\n")
        self.colour = switch_colour[self.colour]
        print("Then I play",self.colour,".")
        self.log["head"][self.colour] = "self"
        self.log["head"][self.colour] = "opponent"
        self.log["head"]["depth"] = self.depth
        self.change_depth()
        self.play()
    def play(self):
        if self.colour == "black":
            self.opponents_turn()
        while True:
            self.own_turn()
            if self.always_display_pos:
                self.display_position()
            if self.check_for_mate() == True:
                break
            self.opponents_turn()
            if self.always_display_pos:
                self.display_position()
            if self.check_for_mate() == True:
                break
    def own_turn(self):
        if self.show_own_moves == True:
            self.pos.find_possible_moves()
            for move in self.pos.possible_moves:
                print(move)
            self.show_own_moves = False
        print("Thinking...")
        self.pos.build_tree(self.depth)
        print("I move my", type(self.pos.piece_on(self.pos.best_move.start)).__name__, "from", self.pos.best_move.start, "to", self.pos.best_move.end)
#        print("I play ", type(self.pos.piece_on(self.pos.best_move.start)).__name__[0] if not hasattr(self.pos.piece_on(self.pos.best_move.start), "letter") else self.pos.piece_on(self.pos.best_move.start).letter, self.pos.best_move)
        self.pos.make_move(self.pos.best_move)
        self.log["game"].append(self.pos.best_move)
    def opponents_turn(self):
        self.opponents_move = self.get_opponents_move()
        print("You played ", self.opponents_move)
        self.pos.make_move(self.opponents_move)
        self.log["game"].append(self.opponents_move)
    def get_opponents_move(self):
        self.raw_move = input("Your turn. Input help for help. \n")
        if self.raw_move == "position":
            self.display_position()
        elif self.raw_move == "log":
            for move in self.log["game"]:
                print(move)
        elif self.raw_move == "moves":
            self.pos.colour = switch_colour[self.pos.colour]
            self.pos.find_possible_moves()
            for move in self.pos.possible_moves:
                print(move)
            self.pos.colour == switch_colour[self.pos.colour]
            self.pos.possible_moves = []
        elif self.raw_move == "bp":
            breakpoint()
            return self.get_opponents_move()
        elif self.raw_move == "your moves":
            self.show_own_moves = True
            return self.get_opponents_move()
        elif self.raw_move == "always display position":
            self.display_position()
            self.always_display_pos = not self.always_display_pos
            print("always_display_pos is ", self.always_display_pos, "now.")
            return self.get_opponents_move()
        elif self.raw_move == "change depth":
            self.change_depth()
        elif self.raw_move == "help":
            print("\nThe game ends by capturing the opponents king.\nFormatting of moves: square on wich the move starts, - or x (if the move takes something), square on wich the move ends.\nExample: You move your Knight from b1 to c3. Write this as b1-c3.\n\nList of avaliable commands: \nlog: shows all the moves played so far.\nposition: displays the current position. White pieces are uppercased, black pieces are lowercased.\nalways display position: toggles always_display_position and outputs its current value. If its true, the position will always be displayed when a move is made.\nchange depth: Change the calculation depth of the bot.\n")
            return self.get_opponents_move()
        else:
            try:
                self.move = Move(Coordinate(letter_file = self.raw_move[0], rank = int(self.raw_move[1])-1), Coordinate(letter_file = self.raw_move[3], rank = int(self.raw_move[4])-1))#-1 because human ranks go from 1 to 8 but here they go from 0 to 7
                self.move.take = self.raw_move == "x" or self.pos.piece_on(self.move.end) != None
                return self.move
            except ValueError:
                print("Typo? Try again.")
                return self.get_opponents_move()
        return self.get_opponents_move()
    def change_depth(self):
        self.new_depth = input("enter a new depth. (recomended: 1-4)")
        try:
            self.new_depth = int(self.new_depth)
        except ValueError:
            print("Type? Try again")
            self.change_depth()
            return
        if self.new_depth < 0:
            self.change_depth()
            return
        else:
            self.depth = self.new_depth
    def display_position(self):
        self.pos_display = [[".", ".", ".", ".", ".", ".", ".", "."], [".", ".", ".", ".", ".", ".", ".", "."], [".", ".", ".", ".", ".", ".", ".", "."], [".", ".", ".", ".", ".", ".", ".", "."], [".", ".", ".", ".", ".", ".", ".", "."], [".", ".", ".", ".", ".", ".", ".", "."], [".", ".", ".", ".", ".", ".", ".", "."], [".", ".", ".", ".", ".", ".", ".", "."]]
        for piece in self.pos.get_piece_list():
            self.pos_display[piece.own_pos.get_numbers()["rank"]][piece.own_pos.get_numbers()["file"]] = (type(piece).__name__[0] if piece.colour == "white" else type(piece).__name__[0].lower()) if not hasattr(piece, "letter") else piece.letter if piece.colour == "white" else piece.letter.lower()
        for rank in reversed(self.pos_display):
            print(rank)
    def end_game(self, winner):
        if winner == "opponent":
            print("You lost.")
        elif winner == "self":
            print("You beat me.\gg")
        if input("Do you want to save our game? y/n") == "y":
            self.save_log()
    def check_for_mate(self):
        if len(self.pos.pieces[self.colour]["King"]) == 0:
            self.end_game("opponent")
            return True
        if len(self.pos.pieces[switch_colour[self.colour]]["King"]) == 0:
            self.end_game("self")
            return True
    def save_log(self):
        with open(self.log["head"]["date"], "w") as f:
            json.dumps(self.log, f)

    
colour_multiplier = {"white": 1, "black": -1}
switch_colour = {"white": "black", "black": "white"}

game = Game(Position(), depth = 2)
game.init_game()
