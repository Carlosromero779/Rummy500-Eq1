from Card import Card
from Player import Player

# --- Jugador 1 --- (debe estar fuera de la función)
player1 = Player(1, "Louis")
player1.playerHand = [
    Card("2","♥"), Card("3","♥"), Card("4","♥"), Card("5","♥"), 
    Card("9","♦"), Card("9","♠"), Card("Joker","",joker=True), Card("Joker","",joker=True),
    Card("2","♥"), Card("3","♥"), Card("4","♥"), Card("5","♥"), 
]

def mega_test():
    print("\n========== MEGA TEST CON 5 JUGADORES ==============\n")

    # --- Jugador 2 ---
    player2 = Player(2, "Fernando")
    player2.playerHand = [
        Card("Joker","",joker=True), Card("Q","♣"), Card("K","♣"), Card("A","♣"), Card("Joker","",joker=True),
        Card("7","♠"), Card("7","♥"), Card("7","♦")
    ]

    # --- Jugador 3 ---
    # Mano con dos seguidillas posibles y dos Jokers, para probar múltiples combinaciones
    player3 = Player(3, "Ricardo")
    player3.playerHand = [
        Card("4","♠"), Card("5","♠"), Card("6","♠"), Card("7","♠"), Card("Joker","",joker=True),
        Card("10","♥"), Card("J","♥"), Card("Q","♥"), Card("K","♥"), Card("Joker","",joker=True)
    ]

    # --- Jugador 4 ---
    #Mano con A bajo + Jokers, para probar seguidillas complejas
    player4 = Player(4, "Luiggy")
    player4.playerHand = [
        Card("A","♥"), Card("2","♥"), Card("3","♥"), Card("4","♥"), 
        Card("Joker","",joker=True), Card("Joker","",joker=True),
        Card("8","♦"), Card("8","♠"), Card("8","♥")
    ]

    # --- Jugador 5 ---
    #Mano que mezcla todo: trío con Joker y seguidilla con Joker intermedio + una seguidilla con As alto
    player5 = Player(5, "Carlos")
    player5.playerHand = [
        Card("2","♣"), Card("2","♦"), Card("Joker","",joker=True),
        Card("3","♣"), Card("4","♣"), Card("5","♣"), Card("Joker","",joker=True),
        Card("K","♠"), Card("A","♠"), Card("Q","♠")
    ]

    players = [player1, player2, player3, player4, player5]

    #Ejecutamos el test
    for p in players:
        print(f"\n--- {p.playerName} ---")
        print("Mano inicial:", [str(c) for c in p.playerHand])
        
        # Seguidillas encontradas
        #straights = p.findStraight()
        #print("\nSeguidillas encontradas:")
        #for s in straights:
         #   print("  ", [str(c) for c in s])
        
        # Tríos encontrados
        #trios = p.findTrios()
        #print("\nTríos encontrados:")
        #for t in trios:
         #   print("  ", [str(c) for c in t])
        
        #Verificar si se puede bajar
        can_get_off = p.canGetOff()
        if isinstance(can_get_off, tuple) and len(can_get_off) == 2:
            resultado, combos = can_get_off
        else:
            resultado, combos = can_get_off, []
        if resultado:
            print(f"\n✅ {p.playerName} se puede bajar con {len(combos)} combinación(es):")
            for i, combo in enumerate(combos, 1):
                print(f"   Opción {i}:")
                print(f"     Trío -> {[str(c) for c in combo['trio']]}")
                print(f"     Seguidilla -> {[str(c) for c in combo['straight']]}")
        else:
            print(f"\n❌ {p.playerName} no se puede bajar.")

mega_test()
