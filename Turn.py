from Deck import Deck

def drawCard(player, roundPlayed, fromDiscards = False):
    if fromDiscards: #Si se indica que se quiere sacar una carta del montón de descartes y se proporciona un índice válido
        card = roundPlayed.discards.pop()  #Sacamos la carta del montón de descartes
        roundPlayed.hands[player.playerId].append(card)  #Añadimos la carta tomada a la mano del jugador
        player.cardDrawn = True
        return card
    else:
        card = roundPlayed.pile.pop()  #Sacamos la última carta del mazo
        roundPlayed.hands[player.playerId].append(card)  #Añadimos la carta a la mano del jugador
        player.playerPass = True
        player.cardDrawn = True
        return card

def discardCard(player, roundPlayed, card):
    roundPlayed.hands[player.playerId].remove(card)  #Quitamos la carta de la mano del jugador
    roundPlayed.discards.append(card)  #Añadimos la carta al montón de descartes

def refillDeck(roundPlayed):
    if len(roundPlayed.pile) == 0 and len(roundPlayed.discards) == 0:
        roundPlayed.deck = Deck()
        roundPlayed.deck.shuffleCards()
        roundPlayed.pile = roundPlayed.deck.cards[:]
        roundPlayed.deck.cards.clear()
        # roundPlayed.discards.append(roundPlayed.pile.pop())
        print("Nuevo mazo creado y anexado al juego!")
    elif len(roundPlayed.pile) == 0:  #Si el mazo se queda sin cartas, sacamos las cartas del montón de descartes y las ponemos en el mazo
        roundPlayed.pile = roundPlayed.discards[:-1]
        roundPlayed.discards = [roundPlayed.pile.pop()] #roundPlayed.discards[-1:]  #Dejamos la última carta del montón de descartes como la única carta en el montón de descartes
        print("Mazo recargado con las cartas quemadas!")
