from network import NetworkManager
    #++++++
from Card import Card
from Player import Player

#networkManager = NetworkManager()
#jugador1 = networkManager.connected_players[0]
players = []

# --- Jugador 1 ---
player1 = Player(1, "Louis")
player1.playerHand = [
    Card("2","♥"), Card("3","♥"), Card("4","♥"), Card("5","♥"), 
    Card("9","♦"), Card("9","♠"), Card("9","♠"), Card("7", "♦"),
    Card("Joker","",joker=True), Card("9","♦")
]
players.append(player1)
player1.isHand = True
# --- Jugador 2 ---
player2 = Player(2, "Fernando")
player2.playerHand = [
    Card("Joker","",joker=True), Card("Q","♣"), Card("K","♣"), Card("A","♣"), Card("Joker","",joker=True),
    Card("7","♠"), Card("7","♥"), Card("7","♦")
]
player2.isHand = True
players.append(player2)
player2.playMade = [[Card("7","♠"), Card("7","♥"), Card("7","♦")], [Card("Joker","",joker=True), Card("Q","♣"), Card("K","♣"), Card("A","♣")]]  # Simulamos que ya ha hecho una jugada

# --- Jugador 3 ---
player3 = Player(3, "Ricardo")
player3.playerHand = [
    Card("4","♠"), Card("5","♠"), Card("6","♠"), Card("7","♠"), Card("Joker","",joker=True),
    Card("10","♥"), Card("J","♥")
]
player3.isHand = True
players.append(player3)

# --- Jugador 4 ---
player4 = Player(4, "Luiggy")
player4.playerHand = [
    Card("A","♥"), Card("2","♥"), Card("3","♥"), Card("4","♥"), 
    Card("Joker","",joker=True), Card("Joker","",joker=True),
    Card("8","♦")
]
player4.isHand = True
players.append(player4)

player5 = Player(5, "Carlos")
player5.playerHand = [
     Card("2","♣"), Card("2","♦"), Card("Joker","",joker=True),
     Card("3","♣"), Card("4","♣"), Card("5","♣"), Card("Joker","",joker=True),
 ]
player5.isHand = True
players.append(player5)

player6 = Player(6, "Maria")
player6.playerHand = [
     Card("2","♣"), Card("2","♦"), Card("Joker","",joker=True),
     Card("3","♣"), Card("4","♣"), Card("5","♣"), Card("Joker","",joker=True),
]
player6.isHand = True
players.append(player6)

player7 = Player(7, "Juan")
player7.playerHand = [
     Card("3","♣"), Card("4","♣"), Card("5","♣"), Card("Joker","",joker=True), Card("Joker","",joker=True)
]
player7.isHand = True
players.append(player7)

def mega_test():
    print("\n========== MEGA TEST CON JUGADORES DINÁMICOS ==============\n")
    for p in players:
        print(f"\n--- {p.playerName} ---")
        print("Mano inicial:", [str(c) for c in p.playerHand])
        print(f"Cartas totales: {len(p.playerHand)}")
        #print(f" Jugador {jugador1}")
        #print(f" los players {str(p)}")

if __name__ == "__main__":
    mega_test()
    