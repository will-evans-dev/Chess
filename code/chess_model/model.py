from chess_model.pieces import King, Queen, Rook, Bishop, Knight, Pawn
from chess_model.move import Move

from copy import deepcopy

class Model:
    
    fen_piece_codes = {"k": King, "q": Queen, "r": Rook, "b": Bishop, "n": Knight, "p": Pawn}
    
    def __init__(self, fen) -> None:
        
        self.ranks = self.get_ranks(fen)
        self.files = self.get_files(fen)

        # game state
        self.board, self.pieces = self.populate_board(fen)

        self.turn = self.get_turn(fen)
        self.castling = "KQkq"
        self.en_passant = self.get_en_passant(fen)
        self.halfmoves = 0
        self.moves = 1
        
        # controlled squares
        self.w_controlled_squares, self.b_controlled_squares = self.get_controlled_squares(self.board)

    def __str__ (self) -> str:

        fen = ""
        empty_num = 0

        # board
        for rank in self.board:
            for square in rank:
                if square:
                    if empty_num != 0:
                        fen += str(empty_num)
                        empty_num = 0
                    fen += str(square)
                else:
                    empty_num += 1

            if empty_num != 0:
                fen += str(empty_num)
            
            fen += "/"
            empty_num = 0
        
        fen += " "

        # turn
        fen += self.turn
        fen += " "

        # castling
        fen += self.castling
        fen += " "

        # en passant
        fen += f'{self.en_passant if self.en_passant else "-"} '

        # halfmove clock
        fen += str(self.halfmoves)
        fen += " "

        # fullmove number
        fen += str(self.moves)

        return fen

    def get_ranks(self, fen):
        return 8

    def get_files(self, fen):
        return 8

    def populate_board (self, fen):

        #   populate board
        file_num = 0
        rank_num = 0

        board = [[None for _ in range(self.files)] for _ in range (self.ranks)]
        pieces = {"p": [], "P": []}

        for char in fen:
            piece_class = self.fen_piece_codes.get(char.lower())

            if piece_class:
                piece = piece_class(char, file_num, rank_num)
                board[rank_num][file_num] = piece
                if char.lower() == "p":
                    pieces[char].append(piece)
                else:
                    pieces.update({char: piece})

                file_num += 1

            elif char.isdigit():
                file_num += int(char)
            
            elif char == "/":
                rank_num += 1
                file_num = 0
            else:
                break

        return board, pieces

    def get_turn(self, fen):
        return fen.split()[1]

    def get_en_passant(self, fen):
        en_passant = fen.split()[3]

        if en_passant != "-":
            return en_passant

    def to_rf(self, code):
        return int(code[1]) - 1, ord(code[0]) - 97
    
    def from_rf(self, rank, file):
        return f'{chr(file+97)}{int(rank + 1)}'

    def get_controlled_squares (self, board):

        # idea go back and add the piece names again (so dict instead of set), then can remove negative numbers when loooping through to separate colours.
        w_controlled_squares = set()
        b_controlled_squares = set()

        for rank in board:
            for piece in rank:
                if piece:
                    if type(piece) in [Queen, Bishop]:
                        # diagonal
                        #   north-east, south-east, south-west, north-west
                        directions = [ [-1, 1],  [1, 1], [1, -1], [-1, -1] ]

                        if piece.get_colour() == "w":
                            w_controlled_squares = self.check_directions(board, piece, directions, w_controlled_squares)
                        else:
                            b_controlled_squares = self.check_directions(board, piece, directions, b_controlled_squares)
                    
                    if type(piece) in [Queen, Rook]:
                        # vertical / horizontal
                        #   north, east, south, west
                        directions = [ [-1, 0], [0, 1], [1, 0], [0, -1] ]

                        if piece.get_colour() == "w":
                            w_controlled_squares = self.check_directions(board, piece, directions, w_controlled_squares)
                        else:
                            b_controlled_squares = self.check_directions(board, piece, directions, b_controlled_squares)
                    
                    if type(piece) is Pawn:
                        if piece.get_colour() == "w":
                            w_controlled_squares.add( (piece.rank - 1, piece.file + 1) )
                            w_controlled_squares.add( (piece.rank - 1, piece.file - 1) )
                        else:
                            b_controlled_squares.add( (piece.rank + 1, piece.file + 1) )
                            b_controlled_squares.add( (piece.rank + 1, piece.file - 1) )

                    if type(piece) is King:
                        for rank_offset in range(-1, 2):
                            for file_offset in range (-1, 2):
                                if piece.get_colour() == "w":
                                    w_controlled_squares.add ( (piece.rank + rank_offset, piece.file + file_offset) )
                                else:
                                    b_controlled_squares.add ( (piece.rank + rank_offset, piece.file + file_offset) )

                    if type(piece) is Knight:
                        for rank_offset, file_offset in [ [1, 2], [1, -2], [-1, 2], [-1, -2], [2, 1], [2, -1], [-2, 1], [-2, -1] ]:
                            if piece.get_colour() == "w":
                                w_controlled_squares.add ( (piece.rank + rank_offset, piece.file + file_offset) )
                            else:
                                b_controlled_squares.add ( (piece.rank + rank_offset, piece.file + file_offset) )

        return w_controlled_squares, b_controlled_squares

    def check_directions (self, board, piece, directions, controlled_squares):
        for direction in directions:
            rank_offset, file_offset = direction

            check_rank = piece.rank + rank_offset
            check_file = piece.file + file_offset

            while 0 <= check_rank < self.ranks and 0 <= check_file < self.ranks:
                
                check_piece = board[check_rank][check_file]
                
                controlled_squares.add((check_rank, check_file))
                
                if check_piece:
                    break

                check_rank += rank_offset
                check_file += file_offset

        return controlled_squares

    def move(self, old, new) -> None:
        
        _move = Move(old, new, self.board)

        if _move.old_piece:
            if _move.old_piece.valid_move(_move):
                if self.valid_move(_move):
                    
                    # update board
                    self.board = self.get_board_move(self.board, _move)

                    # update piece
                    _move.old_piece.rank, _move.old_piece.file = _move.new_rank, _move.new_file

                    # update game state
                    #   turn
                    self.turn = "b" if self.turn == "w" else "w"
                    
                    #   castling
                    self.update_castling(_move)

                    #   en passant
                    self.update_enpassant(_move)

                    # half moves
                    if _move.new_piece or type(_move.old_piece) is Pawn:
                        self.halfmoves = 0
                    else:
                        self.halfmoves += 1
                        
                    # moves 
                    if self.turn == "w":
                        self.moves += 1

                    #   controlled_squares
                    self.w_controlled_squares, self.b_controlled_squares = self.get_controlled_squares(self.board)
                    
                    print(self)

    def update_castling(self, _move):

        # castling rights
        if _move.old == (0, 0):
            self.castling = self.castling.replace("q", "")
        elif _move.old == (0, self.files - 1):
            self.castling = self.castling.replace("k", "")
        elif _move.old == (self.ranks - 1, 0):
            self.castling = self.castling.replace("Q", "")
        elif _move.old == (self.ranks - 1, self.files - 1):
            self.castling = self.castling.replace("K", "")

        if _move.type is King:
            if _move.old_piece_colour == "w":
                self.castling = self.castling.replace("K", "")
                self.castling = self.castling.replace("Q", "")
            else:
                self.castling = self.castling.replace("k", "")
                self.castling = self.castling.replace("q", "")

        # castling move
        if _move.type is King: 
            if abs(_move.file_dif) == 2:

                if type(self.board[_move.old_rank][_move.old_file + int(_move.file_dif * 1.5)]) is Rook:
                    old_rook_square = ( _move.old_rank, _move.old_file + int(_move.file_dif * 1.5) )
                else:
                    old_rook_square = ( _move.old_rank, _move.old_file + int(_move.file_dif * 2) )

                new_rook_square = ( _move.old_rank, _move.old_file + int(_move.file_dif / 2) )


                rook_move = Move(old_rook_square, new_rook_square, self.board)
                self.board = self.get_board_move(self.board, rook_move)

    def update_enpassant(self, _move):
        self.en_passant = None if self.en_passant else self.en_passant

        if _move.type is Pawn:
            if abs(_move.rank_dif) == 2:
                
                left_piece = self.board [_move.new_rank][_move.new_file + 1]
                right_piece = self.board [_move.new_rank][_move.new_file - 1]

                # white
                if _move.old_piece_colour == "w":
                    if  type(left_piece) is Pawn and left_piece and left_piece.get_colour() == "b" or \
                        type(right_piece) is Pawn and right_piece and right_piece.get_colour() == "b":
                        self.en_passant = self.from_rf(_move.new_rank - (_move.rank_dif / 2), _move.new_file)

                # black
                if _move.old_piece_colour == "b":
                    if  type(left_piece) is Pawn and left_piece and left_piece.get_colour() == "w" or \
                        type(right_piece) is Pawn and right_piece and right_piece.get_colour() == "w":
                        self.en_passant = self.from_rf(_move.new_rank - (_move.rank_dif / 2), _move.new_file)

    def get_board_move(self, board, _move):
        
        #   en passant
        if self.en_passant and _move.type is Pawn:
            if (_move.new_rank, _move.new_file) == self.to_rf(self.en_passant):
                board [_move.old_rank][_move.new_file] = None

        board [_move.old_rank][_move.old_file] = None
        board [_move.new_rank][_move.new_file] = _move.old_piece
        return board

    def valid_move(self, _move) -> bool:

        if _move.type is Pawn:
            if not self.check_pawn_capture(_move):
                return False
            
            if not self.check_pawn_two_square_rule(_move):
                return False

            if not self.check_pawn_forward_move(_move):
                return False

        if _move.type is King:
            if not self.check_castling(_move):
                return False

        return  self.check_turn(_move) and \
                self.check_friendly_capture(_move) and \
                self.check_blocking_pieces(_move) and \
                self.check_king_checks(_move) 
                
    def check_turn (self, _move):
        return _move.old_piece_colour == self.turn

    def check_friendly_capture(self, _move) -> bool:
        if not _move.new_piece:
            return True
        return _move.old_piece_colour != _move.new_piece_colour

    def check_blocking_pieces(self, _move) -> bool:
        if not _move.type is Knight:
            
            # diagonal
            if abs(_move.rank_dif) == abs(_move.file_dif):
                if _move.rank_dif < 0:
                    if _move.file_dif > 0:
                        # north-east
                        for square_dif in range(1, abs(_move.rank_dif)):
                            if self.board[_move.old_rank - square_dif][_move.old_file + square_dif]:
                                return False
                    else:
                        # north-west
                        for square_dif in range(1, abs(_move.rank_dif)):
                            if self.board[_move.old_rank - square_dif][_move.old_file - square_dif]:
                                return False
                else:
                    if _move.file_dif > 0:
                        # south-east
                        for square_dif in range(1, abs(_move.rank_dif)):
                            if self.board[_move.old_rank + square_dif][_move.old_file + square_dif]:
                                return False
                    else:
                        # south-west
                        for square_dif in range(1, abs(_move.rank_dif)):
                            if self.board[_move.old_rank + square_dif][_move.old_file - square_dif]:
                                return False
                    
            # vertical & horizontal
            if (_move.rank_dif != 0 and _move.file_dif == 0) or (_move.rank_dif == 0 and _move.file_dif != 0):
                if _move.rank_dif < 0:
                    # north
                    for square_dif in range(1, abs(_move.rank_dif)):
                        if self.board[_move.old_rank - square_dif][_move.old_file]:
                            return False

                elif _move.rank_dif > 0:
                    # south
                    for square_dif in range(1, abs(_move.rank_dif)):
                        if self.board[_move.old_rank + square_dif][_move.old_file]:
                            return False

                elif _move.file_dif > 0:
                    # east
                    for square_dif in range(1, abs(_move.file_dif)):
                        if self.board[_move.old_rank][_move.old_file + square_dif]:
                            return False

                else:
                    # west
                    for square_dif in range(1, abs(_move.file_dif)):
                        if self.board[_move.old_rank][_move.old_file - square_dif]:
                            return False
        return True

    def check_pawn_capture(self, _move) -> bool:

        if abs(_move.rank_dif) == 1 and abs(_move.file_dif) == 1:
            if self.en_passant:
                if (_move.new_rank, _move.new_file) == self.to_rf(self.en_passant):
                    return True
            return self.board[_move.new_rank][_move.new_file]

        return True
    
    def check_pawn_two_square_rule(self, _move) -> bool:

        if abs(_move.rank_dif) == 2:
            if _move.old_rank == 1 or _move.old_rank == self.ranks - 2:
                return True
            else:
                return False

        return True

    def check_pawn_forward_move(self, _move) -> bool:
        
        if 0 <= abs(_move.rank_dif) <= 2 and _move.file_dif == 0:
            if _move.new_piece:
                return False
        return True

    def check_king_checks(self, _move) -> bool:
        
        # get proposed move
        proposed_board = self.get_board_move(deepcopy(self.board), _move)
        w_proposed_controlled_squares, b_proposed_controlled_squares = self.get_controlled_squares(proposed_board)
        
        # get kings
        for rank in self.board:
            for piece in rank:
                if type(piece) is King:

                    if _move.old_piece_colour == "w":

                        if _move.type is King:
                            if (_move.new_rank, _move.new_file) in b_proposed_controlled_squares:
                                return False

                        else:
                            if piece.get_colour() == "w":
                                if (piece.rank, piece.file) in b_proposed_controlled_squares:
                                    return False
                    
                    else:
                        if _move.type is King:
                            if (_move.new_rank, _move.new_file) in w_proposed_controlled_squares:
                                return False
                        else:
                            if piece.get_colour() == "b":
                                if (piece.rank, piece.file) in w_proposed_controlled_squares:
                                    return False
                            
        return True

    def check_king_checks(self, _move) -> bool:
        
        # get proposed move
        proposed_board = self.get_board_move(deepcopy(self.board), _move)
        w_proposed_controlled_squares, b_proposed_controlled_squares = self.get_controlled_squares(proposed_board)
        
        w_king = self.pieces["K"]
        b_king = self.pieces["k"]

        if self.turn == "w":
            if _move.type is King:
                if _move.new in b_proposed_controlled_squares:
                    return False
            else:
                if w_king.get_square() in b_proposed_controlled_squares:
                    return False
        
        else:
            if _move.type is King:
                if _move.new in w_proposed_controlled_squares:
                    return False
            else:
                if b_king.get_square() in w_proposed_controlled_squares:
                    return False

        return True

    def check_castling(self, _move) -> bool:
        if abs(_move.file_dif) == 2:
            
            
            if _move.old_piece_colour == "w":
                # white
                if _move.file_dif > 0:
                    # king side
                    if "K" in self.castling:
                        pass
                else:
                    # queen
                    if "Q" in self.castling:
                        pass
            else:
                # black
                if _move.file_dif > 0:
                    # queen side
                    if "q" in self.castling:
                        pass
                else:
                    # king side
                    if "k" in self.castling:
                        pass


        return True

