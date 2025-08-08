# Unused; Will likely be included in version 2
import requests

def get_best_move(FEN, depth=15):
    url = "https://stockfish.online/api/s/v2.php?fen="+FEN+"&depth="+str(depth)
    print(requests.get(url).content)
