## Imports
import pygame, random
from config import *

## Pygame Setup
pygame.init()
window = pygame.display.set_mode((800, 800))
clock = pygame.time.Clock()
font = pygame.font.SysFont('', 32)
pygame.mixer.set_num_channels(1)

## Initialize Variables
hover_col = hover_row = 0
move_history = []
selected_piece = ''
selected_col = None
selected_row = None
turn = 'white'
time = 0
checkmate = False
stalemate = False
checked = False
promoting_color = ''
promoting_col = None
promoting_row = None


## Board & Piece Setup
pieces = [
    'white_pawn', 'white_rook', 'white_knight', 'white_bishop', 'white_queen', 'white_king',
    'black_pawn', 'black_rook', 'black_knight', 'black_bishop', 'black_queen', 'black_king'
]

board = [
    ['black_rook', 'black_knight', 'black_bishop', 'black_queen', 'black_king', 'black_bishop', 'black_knight', 'black_rook'],
    ['black_pawn' for i in range(8)],
    ['' for i in range(8)],
    ['' for i in range(8)],
    ['' for i in range(8)],
    ['' for i in range(8)],
    ['white_pawn' for i in range(8)],
    ['white_rook', 'white_knight', 'white_bishop', 'white_queen', 'white_king', 'white_bishop', 'white_knight', 'white_rook'],
]

images = {}

for piece in pieces: 
    if flip_black and piece.startswith('black'):
        images[piece] = pygame.transform.flip(pygame.image.load(f'pieces/{piece}.{IMAGE_FILE_FORMAT}'), False, True)
    else:
        images[piece] = pygame.image.load(f'pieces/{piece}.{IMAGE_FILE_FORMAT}')

## Helper Functions
def other(turn): 
    if turn == 'white': return 'black'
    if turn == 'black': return 'white'

def get_moves(piece, col, row, attacks_only=False):
    moves, takes = [], []
    if not piece:
        return moves, takes

    color = 'white' if piece.startswith('white') else 'black'
    enemy = 'black' if color == 'white' else 'white'

    ## Helper; Used for rook, bishop, and queen
    def slide(directions):
        for dx, dy in directions:
            for i in range(1, 8):
                x, y = col + dx * i, row + dy * i
                if not (0 <= x < 8 and 0 <= y < 8):
                    break
                target = board[y][x]
                if target == '':
                    if not attacks_only:
                        moves.append([dx * i, dy * i])
                    if attacks_only:
                        takes.append([dx * i, dy * i])  # mark attack square
                elif target.startswith(enemy):
                    takes.append([dx * i, dy * i])
                    break
                else:
                    break

    ## Helper; Used for knight, king, and pawn
    def leap(offsets):
        for dx, dy in offsets:
            x, y = col + dx, row + dy
            if 0 <= x < 8 and 0 <= y < 8:
                target = board[y][x]
                if target == '':
                    if not attacks_only:
                        moves.append([dx, dy])
                    if attacks_only:
                        takes.append([dx, dy])
                elif target.startswith(enemy):
                    takes.append([dx, dy])

    match piece:
        case 'white_pawn':
            if not attacks_only:
                ## Double Step
                if row == 6:
                    if board[row - 1][col] == '':
                        moves.append([0, -1])
                        if board[row - 2][col] == '':
                            moves.append([0, -2])
                ## Standard Move
                elif row > 0 and board[row - 1][col] == '':
                    moves.append([0, -1])
                
                ## En Passant
                if row == 3 and col > 0 and col < 7:
                    if board[row][col - 1] == f'black_pawn':
                        if move_history[-1][0] == [col - 1, 1] and move_history[-1][1] == [col - 1, 3]:
                            moves.append([-1, -1])
                    if board[row][col + 1] == f'black_pawn':
                        if move_history[-1][0] == [col + 1, 1] and move_history[-1][1] == [col + 1, 3]:
                            moves.append([1, -1])

            takes = [[-1, -1], [1, -1]]
            ## Promotion handled in MOUSEBUTTONDOWN

        case 'black_pawn':
            if not attacks_only:
                ## Double Step
                if row == 1:
                    if board[row + 1][col] == '':
                        moves.append([0, 1])
                        if board[row + 2][col] == '':
                            moves.append([0, 2])

                ## Standard Move
                elif row < 7 and board[row + 1][col] == '':
                    moves.append([0, 1])
                
                ## En Passant
                if row == 4 and col > 0 and col < 7:
                    if board[row][col - 1] == f'white_pawn':
                        if move_history[-1][0] == [col - 1, 6] and move_history[-1][1] == [col - 1, 4]:
                            moves.append([-1, 1])
                    if board[row][col + 1] == f'white_pawn':
                        if move_history[-1][0] == [col + 1, 6] and move_history[-1][1] == [col + 1, 4]:
                            moves.append([1, 1])
                    
            takes = [[-1, 1], [1, 1]]
            ## Promotion handled in MOUSEBUTTONDOWN

        case 'white_rook' | 'black_rook':
            slide([(-1, 0), (1, 0), (0, -1), (0, 1)])

        case 'white_bishop' | 'black_bishop':
            slide([(-1, -1), (1, -1), (-1, 1), (1, 1)])

        case 'white_queen' | 'black_queen':
            slide([(-1, 0), (1, 0), (0, -1), (0, 1),
                   (-1, -1), (1, -1), (-1, 1), (1, 1)])

        case 'white_knight' | 'black_knight':
            leap([(-2, -1), (-1, -2), (1, -2), (2, -1),
                  (2, 1), (1, 2), (-1, 2), (-2, 1)])

        case 'white_king' | 'black_king':
            leap([(-1, 0), (1, 0), (0, -1), (0, 1),
                  (-1, -1), (1, -1), (-1, 1), (1, 1)])
            

    ## Pawn Capture Logic
    if piece in ('white_pawn', 'black_pawn'):
        pawn_takes = []
        for dx, dy in takes:
            x, y = col + dx, row + dy
            if 0 <= x < 8 and 0 <= y < 8:
                target = board[y][x]
                if attacks_only:
                    pawn_takes.append([dx, dy])
                elif target.startswith(enemy):
                    pawn_takes.append([dx, dy])
        takes = pawn_takes
    
    ## Castling (Rook move is handled in MOUSEBUTTONDOWN)
    if col > 0 and col < 7:
        if piece == 'white_king':
            if board[row][col + 1] == '':
                if board[7][7] == 'white_rook':
                    if not ([4, 7] in [move[0] for move in move_history] or [7, 7] in [move[0] for move in move_history]):
                        moves.append([2, 0])
            if board[row][col - 1] == '' and board[row][col - 2] == '':
                if board[7][0] == 'white_rook':
                    if not ([4, 7] in [move[0] for move in move_history] or [0, 7] in [move[0] for move in move_history]):
                        moves.append([-2, 0])
        
        if piece == 'black_king':
            if board[row][col + 1] == '':
                if board[0][7] == 'black_rook':
                    if not ([4, 0] in [move[0] for move in move_history] or [7, 0] in [move[0] for move in move_history]):
                        moves.append([2, 0])
            if board[row][col - 1] == '' and board[row][col - 2] == '':
                if board[0][0] == 'black_rook':
                    if not ([4, 0] in [move[0] for move in move_history] or [0, 0] in [move[0] for move in move_history]):
                        moves.append([-2, 0])


    ## Skip Legality Filtering
    if attacks_only:
        return moves, takes

    ## Find King Position
    king_x = king_y = None
    for y in range(8):
        if f'{color}_king' in board[y]:
            king_x = board[y].index(f'{color}_king')
            king_y = y
            break

    ## Legality Filtering (Removes moves that will end with the king in check)
    safe_moves = []; safe_takes = []
    for dx, dy in moves + takes:
        moving_piece = board[row][col]
        captured_piece = board[row + dy][col + dx]

        ## Make the move
        board[row + dy][col + dx] = moving_piece
        board[row][col] = ''

        # #Special case: en passant — remove the pawn behind the target square
        ep_removed_piece = None
        if moving_piece.endswith('_pawn') and dx != 0 and captured_piece == '':
            if moving_piece.startswith('white'):
                ep_row = row + dy + 1  # black pawn is one square down from target
            else:
                ep_row = row + dy - 1  # white pawn is one square up from target
            ep_col = col + dx
            ep_removed_piece = board[ep_row][ep_col]
            board[ep_row][ep_col] = ''

        ## If king moved, update king position for the check test
        if moving_piece.endswith('_king'):
            test_king_x, test_king_y = col + dx, row + dy
        else:
            test_king_x, test_king_y = king_x, king_y

        if not get_checked(test_king_x, test_king_y, color):
            if [dx, dy] in moves:
                safe_moves.append([dx, dy])
            else:
                safe_takes.append([dx, dy])
            

        ## Undo en passant pawn removal
        if ep_removed_piece:
            board[ep_row][ep_col] = ep_removed_piece

        ## Undo move
        board[row][col] = moving_piece
        board[row + dy][col + dx] = captured_piece
    return safe_moves, safe_takes

def get_checked(col, row, color):
    for y in range(8):
        for x in range(8):
            if board[y][x].startswith(other(color)):
                _, takes = get_moves(board[y][x], x, y, attacks_only=True)
                take_locations = [[x + dx, y + dy] for dx, dy in takes]
                if [col, row] in take_locations:
                    return True
    return False

while True:
    ## Clear Screen
    window.fill((0, 0, 0))

    ## Mouse Handling
    mouse_x, mouse_y = pygame.mouse.get_pos()
    hover_col = mouse_x // 100
    hover_row = mouse_y // 100
    hover_piece = board[hover_row][hover_col]

    ## Label Window Based on Board State
    if checkmate: pygame.display.set_caption(f'{turn.title()} in checkmate')
    elif stalemate: pygame.display.set_caption(f'{turn.title()} in stalemate')
    else: pygame.display.set_caption(f'{turn.title()} to move')

    ## Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT: quit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            ## PvP Mode
            if turn == 'white' or mode == 'player':
                ## Pawn Promotion
                if promoting_color:
                    if hover_row == queen_y // 100 and hover_col == promoting_col:
                        piece = f'{promoting_color}_queen'
                    if hover_row == knight_y // 100 and hover_col == promoting_col:
                        piece = f'{promoting_color}_knight'
                    if hover_row == rook_y // 100 and hover_col == promoting_col:
                        piece = f'{promoting_color}_rook'
                    if hover_row == bishop_y // 100 and hover_col == promoting_col:
                        piece = f'{promoting_color}_bishop'
                    
                    board[promoting_row][promoting_col] = piece

                    promoting_col = promoting_row = promoting_color = None

                ## NOT Pawn Promotion
                else:
                    ## Normal Game State
                    if not (checkmate or stalemate): 
                        ## Selection Handling
                        if selected_piece:
                            # If clicking another of your own pieces, instantly switch selection
                            if hover_piece.startswith(turn):
                                selected_piece = hover_piece
                                selected_col = hover_col
                                selected_row = hover_row
                                continue  # Skip rest of click handling this frame

                            moved = False
                            wasempty = False
                            ## Moving
                            if board[hover_row][hover_col] == '':
                                if [hover_col, hover_row] in move_locations:
                                    board[hover_row][hover_col] = board[selected_row][selected_col]
                                    board[selected_row][selected_col] = ''
                                    pygame.mixer.music.load(f'sounds/move.{SOUND_FILE_FORMAT}')
                                    pygame.mixer.music.play()
                                    turn = other(turn)
                                    moved = True
                                    wasempty = True
                                    move = [[selected_col, selected_row], [hover_col, hover_row]]
                                    if move == [[4, 7], [6, 7]]:
                                        board[7][7] = ''
                                        board[7][5] = 'white_rook'
                                    if move == [[4, 7], [2, 7]]:
                                        board[7][0] = ''
                                        board[7][3] = 'white_rook'
                                    if move == [[4, 0], [6, 0]]:
                                        board[0][7] = ''
                                        board[0][5] = 'black_rook'
                                    if move == [[4, 0], [2, 0]]:
                                        board[0][0] = ''
                                        board[0][3] = 'black_rook'

                            ## Capturing
                            else:
                                if [hover_col, hover_row] in take_locations and board[hover_row][hover_col].startswith(other(turn)):
                                    board[hover_row][hover_col] = board[selected_row][selected_col]
                                    board[selected_row][selected_col] = ''
                                    pygame.mixer.music.load(f'sounds/capture.{SOUND_FILE_FORMAT}')
                                    pygame.mixer.music.play()
                                    turn = other(turn)
                                    moved = True

                            ## Pawn Promotion & En Passant
                            if moved and selected_piece.endswith('_pawn'):

                                color = 'white' if selected_piece.startswith('white') else 'black'

                                if (color == 'white' and hover_row == 0) or (color == 'black' and hover_row == 7):
                                    promoting_color = color
                                    promoting_row = hover_row
                                    promoting_col = hover_col
                                if wasempty:
                                    if color == 'white': board[hover_row + 1][hover_col] = ''
                                    if color == 'black': board[hover_row - 1][hover_col] = ''

                            if moved:
                                move_history.append([[selected_col, selected_row], [hover_col, hover_row]])

                            selected_piece = ''
                            selected_col = selected_row = None

                        ## Select Square
                        else:
                            if hover_piece.startswith(turn):
                                selected_piece = hover_piece
                                selected_col = hover_col
                                selected_row = hover_row
    
    ## Black Makes a Random Legal Moves
    if mode == 'random' and turn == 'black':
        legal_moves = legal_takes = []
        while not legal_moves + legal_takes:
            black_pieces = [(row, col) for row in range(8) for col in range(8) if board[row][col].startswith('black')]
            row, col = random.choice(black_pieces)
            p = board[row][col]
            legal_moves, legal_takes = get_moves(p, col, row)
        legal_move_locations = [[col + dx, row + dy] for dx, dy in legal_moves]
        legal_take_locations = [[col + dx, row + dy] for dx, dy in legal_takes]
        target_col, target_row = random.choice(legal_move_locations + legal_take_locations)

        board[target_row][target_col] = board[row][col]
        board[row][col] = ''

        turn = 'white'

    ## Getting Moves
    moves, takes = get_moves(selected_piece, selected_col, selected_row)
    move_locations = [[selected_col + dx, selected_row + dy] for dx, dy in moves]
    take_locations = [[selected_col + dx, selected_row + dy] for dx, dy in takes]

    ## Finding King Location
    for y in range(8):
        if f'{turn}_king' in board[y]:
            king_x = board[y].index(f'{turn}_king')
            king_y = y
            break
    
    ## Checkmate & Stalemate Checking
    has_moves = False
    for y in range(8):
        for x in range(8):
            if board[y][x].startswith(turn):
                moves, takes = get_moves(board[y][x], x, y)
                if moves or takes:
                    has_moves = True
                    break
        if has_moves:
            break
    
    if (not (checkmate or stalemate)) and (not has_moves):
        if get_checked(king_x, king_y, turn):
            checkmate = True
        else:
            stalemate = True
        pygame.mixer.music.load(f'sounds/end.{SOUND_FILE_FORMAT}')
        pygame.mixer.music.play()

    ## Check
    elif not checked and get_checked(king_x, king_y, turn):
        pygame.mixer.music.load(f'sounds/check.{SOUND_FILE_FORMAT}')
        pygame.mixer.music.play()
    checked = get_checked(king_x, king_y, turn)

    ## Drawing Loop
    for x in range(8):
        for y in range(8):
            color = list(LIGHT_SQUARE) if not (x + y) % 2 else list(DARK_SQUARE)
            border = [c - 20 for c in color]

            ## Highlight Checked Kings
            if board[y][x] in ('white_king', 'black_king'):
                color_of_king = 'white' if board[y][x].startswith('white') else 'black'
                if get_checked(x, y, color_of_king):
                    color[0] = 255
                    border[0] = 255

            ## Hover Color
            if (x == hover_col and y == hover_row):
                color = [c - 20 for c in color]
                border = [c - 20 for c in border]
            
            ## Selection Color
            if (x == selected_col and y == selected_row):
                color[1] += 20
                border[1] += 20
            
            color = [min(255, max(0, c)) for c in color]

            pygame.draw.rect(window, color, (x * 100, y * 100, 100, 100), 0)
            pygame.draw.rect(window, border, (x * 100, y * 100, 100, 100), 12)

            piece = board[y][x]
            if piece:
                image = images[piece]
                window.blit(image, ((x * 100) + 5, (y * 100) + 5))

            ## Drawing Legal Moves & Captures
            if ([x, y] in move_locations) and not board[y][x]: 
                pygame.draw.circle(window, border, ((x * 100) + 50, (y * 100) + 50), 7)
            elif ([x, y] in take_locations) and board[y][x].startswith(other(turn)):
                pygame.draw.circle(window, [161, 180, 79], ((x * 100) + 50, (y * 100) + 50), 7)

    ## Drawing Promotion UI
    if promoting_color:
        if promoting_color == 'white':
            queen_y = 0
            knight_y = 100
            rook_y = 200
            bishop_y = 300
        else:
            queen_y = 700
            knight_y = 600
            rook_y = 500
            bishop_y = 400
        
        c = [180, 190, 115] if (hover_col == promoting_col and hover_row == queen_y // 100) else [200, 210, 135]
        pygame.draw.rect(window, c, (promoting_col * 100, queen_y, 100, 100))
        pygame.draw.rect(window, [v-20 for v in c], (promoting_col * 100, queen_y, 100, 100), 12)
        window.blit(images[f'{promoting_color}_queen'], ((promoting_col * 100) + 5, queen_y + 5))

        c = [180, 190, 115] if (hover_col == promoting_col and hover_row == knight_y // 100) else [200, 210, 135]
        pygame.draw.rect(window, c, (promoting_col * 100, knight_y, 100, 100))
        pygame.draw.rect(window, [v-20 for v in c], (promoting_col * 100, knight_y, 100, 100), 12)
        window.blit(images[f'{promoting_color}_knight'], ((promoting_col * 100) + 5, knight_y + 5))

        c = [180, 190, 115] if (hover_col == promoting_col and hover_row == rook_y // 100) else [200, 210, 135]
        pygame.draw.rect(window, c, (promoting_col * 100, rook_y, 100, 100))
        pygame.draw.rect(window, [v-20 for v in c], (promoting_col * 100, rook_y, 100, 100), 12)
        window.blit(images[f'{promoting_color}_rook'], ((promoting_col * 100) + 5, rook_y + 5))

        c = [180, 190, 115] if (hover_col == promoting_col and hover_row == bishop_y // 100) else [200, 210, 135]
        pygame.draw.rect(window, c, (promoting_col * 100, bishop_y, 100, 100))
        pygame.draw.rect(window, [v-20 for v in c], (promoting_col * 100, bishop_y, 100, 100), 12)
        window.blit(images[f'{promoting_color}_bishop'], ((promoting_col * 100) + 5, bishop_y + 5))
    
    ## Update Screen
    pygame.display.flip()

    ## Timing Control
    clock.tick(60)
    time += 1