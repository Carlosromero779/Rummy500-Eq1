import pygame
from Round import Round
from Turn import drawCard
from Card import Card
from itertools import combinations
class Player:

    def __init__(self, id, name):
        self.playerId = id
        self.playerName = name
        self.playerPoints = 0 #Nos contiene los puntos del jugador a lo largo de la partida
        self.isHand = False #Esto nos indica si el jugador es mano o no, o en otras palabras, si está en turno
        self.playerTurn = False #Este turno se utilizará para determinar si el jugador está en su turno para comprar la carta
        self.playerHand = [] #Lista que contendrá las cartas del jugador.
        self.playerCardsPos = {} #Atributo experimental, para conocer la posición de cada carta lógica.
        self.playerCardsSelect = [] #Atributo experimental, para guardar las cartas selecc. para un movimiento.
        self.playerCardsToEx = []   # Atrib. exp., para guardar cartas para intercambiar posiciones.
        self.playMade = [] #Este array nos guarda la jugada hecha al momento de bajarse. Esta se actualiza en getOff()
        self.jugadas_bajadas = []
        #self.cardTakend = []
        self.downHand = False #Este atributo nos indica si el jugador ya se bajó o no, mostrando True o False respectivamente
        self.playerBuy = False #Este atributo nos indica si el jugador decidió comprar la carta o no
        self.playerPass = False #Atrib. experimental, para saber si el jugador en turno pasó de la carta descartada.
        self.winner = False #Nos permitirá saber si el jugador fue el ganador
        self.cardDrawn = False #Nos permitirá saber si el jugador tomó una carta en su turno (definido por isHand)
        self.connected = False #Nos permitirá saber si el jugador está conectado al servidor o no
        self.carta_elegida = False  #NUEVO PARA PRUEBA
        self.discarded = False
        self.canDiscard = True # Atrib. que permite bloquear o desbloquear el descarte (para compra de cartas)

    def __str__(self):
        return f"({self.playerId}, {self.playerName})"
    
    def __repr__(self):
        return self.__str__()

    # Mét. para permitir que el jugador seleccione cartas para jugar.
    def chooseCard(self, clickPos):
        
        # Para cada carta en la mano del jugador, verificamos si se hace click en el rectángulo asociado
        # a una carta específica y si dicha carta ha sido previamente seleccionada.
        # Si la carta no está en la lista de seleccionadas, la incluimos; si resulta que está entre las
        # seleccionadas y se vuelve a hacer click en ella, la eliminamos de la lista.
        # NOTA: Con la inclusión de un ID a cada carta este proceso se simplifica, ya que las coincidencias
        #       sólo pueden darse entre cartas con un mismo valor para todos sus atributos.
        for card in self.playerHand:
            if self.playerCardsPos[card].collidepoint(clickPos) and card not in self.playerCardsSelect:
                print(f"Carta marcada: {card}{card.id}")
                self.playerCardsSelect.append(card)
            elif self.playerCardsPos[card].collidepoint(clickPos) and card in self.playerCardsSelect:
                print(f"Carta desmarcada: {card}{card.id}")
                self.playerCardsSelect.remove(card)

    # Mét. para permitir al jugador intercambiar el lugar de sus cartas para que pueda ordenarlas.
    # Trabaja casi igual que chooseCard(), pero almacena dos cartas a lo mucho.
    def exchangeCard(self, clickPos):
        for card in self.playerHand:
            if self.playerCardsPos[card].collidepoint(clickPos) and card not in self.playerCardsToEx:
                print(f"Carta marcada para intercambiar: {card}{card.id}")
                self.playerCardsToEx.append(card)
            elif self.playerCardsPos[card].collidepoint(clickPos) and card in self.playerCardsToEx:
                print(f"Carta desmarcada para intercambiar: {card}{card.id}")
                self.playerCardsToEx.remove(card)

        # Si el jugador marca dos cartas para intercambiar (con el click derecho)...
        if len(self.playerCardsToEx) == 2:
                
                # Tomamos la posición de cada carta en la mano del jugador.
                IndexFirstCard = self.playerHand.index(self.playerCardsToEx[0])
                IndexSecondCard = self.playerHand.index(self.playerCardsToEx[1])

                # Tomamos las cartas asociadas a cada posición.
                firstCard = self.playerHand[IndexFirstCard]
                secondCard = self.playerHand[IndexSecondCard]

                # Intercambiamos posiciones en la mano del jugador.
                self.playerHand[IndexFirstCard] = secondCard
                self.playerHand[IndexSecondCard] = firstCard

                # Limpiamos la lista de intercambio para reiniciar el proceso.
                self.playerCardsToEx.clear()    
                
    #empiezan cambios por aqui
    '''def canExtendTrio(self, card, plays):
        """
        Verifica si la carta puede extender algún trío en la lista de jugadas 'plays'.
        Incluye validación interna de si cada jugada es un trío válido.
        similar a la logica de ins
        """
        for play in plays:
            # Validación interna: verificar si 'play' es un trío válido
            if len(play) < 3:
                continue
            noJokers = [c.value for c in play if not c.joker]
            if len(set(noJokers)) != 1:  # No todos los valores no-Joker son iguales
                continue
            
            # Verificar si la carta puede extender este trío
            common_value = noJokers[0]
            if card.joker:
                jokersInTrio = sum(1 for c in play if c.joker)
                if jokersInTrio < 1:
                    return True
            else:
                if card.value == common_value:
                    return True
        return False
        
    def canExtendStraight(self, card, plays):
        """
        Verifica si la carta puede extender alguna seguidilla en la lista de jugadas 'plays'.
        Incluye validación interna de si cada jugada es una seguidilla válida.
        """
        valueToRank = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
                       "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13}
        
        def rank(c, highAs=False):
            if getattr(c, "joker", False):
                return -1
            if c.value == "A" and highAs:
                return 14
            return valueToRank.get(c.value, -1)
        
        for play in plays:
            # Validación interna: verificar si 'play' es una seguidilla válida
            if len(play) < 4:
                continue
            noJokerSuit = [c.type for c in play if not c.joker]
            if len(set(noJokerSuit)) != 1:  # Todos los palos no-Joker deben ser iguales
                continue
            
            # Verificar secuencia con ranks
            common_suit = noJokerSuit[0]
            isValidStraight = False
            for highAs in (False, True):
                ranks = [rank(c, highAs) for c in play if rank(c, highAs) != -1]
                if len(ranks) < len(play) - 1:  # Demasiados Jokers
                    continue
                ranks.sort()
                if all(ranks[i] + 1 == ranks[i+1] for i in range(len(ranks)-1)):
                    isValidStraight = True
                    break
            if not isValidStraight:
                continue
            
            # Verificar si la carta puede extender esta seguidilla
            if card.joker:
                suit = common_suit
            else:
                if card.type != common_suit:
                    continue
            
            for highAs in (False, True):
                sorted_straight = sorted([c for c in play if rank(c, highAs) != -1], key=lambda c: rank(c, highAs))
                if not sorted_straight:
                    continue
                firstRank = rank(sorted_straight[0], highAs)
                lastRank = rank(sorted_straight[-1], highAs)
                cardRank = rank(card, highAs)
                
                if cardRank == firstRank - 1 or cardRank == lastRank + 1:
                    return True
        return False'''
        
    #Mét. para descartar una carta de la playerHand del jugador. Sólo se ejecuta si el jugador tiene una única
    #carta seleccionada previamente.
    def discardCard(self, selectedDiscards, round):#def discardCard(self, selectedDiscards, round, otherPlayers): asi para lo de ana
        """
        Modificado para verificar si alguna carta seleccionada puede extender una jugada en la mesa.
        - otherPlayers: Lista de otros jugadores (excluyendo al actual) para acceder a sus jugadas bajadas.
        """
        # Verificar si alguna carta puede extender jugadas propias
        '''for card in selectedDiscards:
            if self.downHand and self.playMade and not card.joker:  # Solo si el jugador se ha bajado
                if self.canExtendTrio(card, self.playMade):
                    print(f"No se puede descartar {card}: puede extender tu trio.")
                    return None
                if self.canExtendStraight(card, self.playMade) and not card.joker:
                    print(f"No se puede descartar {card}: puede extender tu seguidilla.")
                    return None
        # Verificar si alguna carta puede extender una jugada bajada de otros jugadores
        for card in selectedDiscards:
            for player in otherPlayers:
                
                if player.downHand and player.playMade and not card.joker:  # Solo si se ha bajado y tiene jugadas
                    if self.canExtendTrio(card, player.playMade):
                        print(f"No se puede descartar {card}: puede extender un trío en la jugada de {player.playerName}.")
                        return None
                    elif self.canExtendStraight(card, player.playMade) and not card.joker:
                        print(f"No se puede descartar {card}: puede extender una seguidilla en la jugada de {player.playerName}.")
                        return None'''
        
        # hasta aqui los cambios :))))
        if len(selectedDiscards) == 2 and self.isHand and self.cardDrawn:

            #Si seleccionaron dos y la primera es un Joker, se retorna una lista con ambas cartas.
            if selectedDiscards[0].joker:

                cardDiscarded = selectedDiscards[1]
                jokerDiscarded = selectedDiscards[0]
                self.playerHand.remove(cardDiscarded)
                self.playerHand.remove(jokerDiscarded)
                selectedDiscards.remove(cardDiscarded)
                selectedDiscards.remove(jokerDiscarded)
                selectedDiscards = []
                round.discards.append(jokerDiscarded)
                round.discards.append(cardDiscarded)
                self.discarded = True
                # self.isHand = False

                return [jokerDiscarded, cardDiscarded]
            #Si seleccionó dos y la segunda es un Joker, volvemos a retornar ambas cartas.
            elif selectedDiscards[1].joker:

                jokerDiscarded = selectedDiscards[1]
                cardDiscarded = selectedDiscards[0]
                self.playerHand.remove(jokerDiscarded)
                self.playerHand.remove(cardDiscarded)
                selectedDiscards.remove(cardDiscarded)
                selectedDiscards.remove(jokerDiscarded)
                selectedDiscards = []
                round.discards.append(jokerDiscarded)
                round.discards.append(cardDiscarded)
                self.discarded = True
                # self.isHand = False

                return [cardDiscarded, jokerDiscarded]
        #Si el jugador sólo seleccionó una carta para descartar, retornamos dicha carta.
        elif len(selectedDiscards) == 1 and not selectedDiscards[0].joker and self.isHand and self.cardDrawn:

            cardDiscarded = selectedDiscards[0]
            try:
                self.playerHand.remove(cardDiscarded)
                round.discards.append(cardDiscarded)
                selectedDiscards.remove(cardDiscarded)
                selectedDiscards = []
                self.discarded = True
                # self.isHand = False

                return [cardDiscarded]
            except ValueError:
                print("La carta que intenta descartar no pertenece a la mano del jugador")
                return []
        #Si el jugador no seleccionó ninguna carta, retornamos None.
        else:
            if len(selectedDiscards) == 0:
                print("No se ha seleccionado ninguna carta en la zona de descartes")
            elif len(selectedDiscards) == 2 and (not any(c.joker for c in selectedDiscards) or all(c.joker for c in selectedDiscards)):
                print("Solo puedes bajar 2 cartas si *una* de ellas es un Joker")
            elif not self.isHand:
                print("El jugador no puede descartar porque no es su turno")
            elif not self.cardDrawn:
                print("El jugador debe tomar una carta antes de hacer cualquier jugada")
            elif len(selectedDiscards) == 1 and selectedDiscards[0].joker:
                print("Para poder descartar un joker, debes descartar también otra carta normal")
            #elif selectedDiscards[0] == takenCard or selectedDiscards[1] == takenCard:
                #print("No puedes descartar la carta que recién tomaste")
            return None
    
    def isValidTrioF(self,lista):
        """
        Valida si una lista específica de cartas (propuesta) es un grupo válido.
        Un grupo válido (trío, cuarteto, etc.) debe:
        1. Tener 3 o más cartas.
        2. Tener un máximo de 1 joker.
        3. Todas las cartas normales deben tener el mismo valor.
        """
        
        # 1. Verificar el tamaño (mínimo 3 cartas)
        # Tu código original buscaba de 3 en adelante.
        if not lista or len(lista) < 3:
            print(f"Error: La propuesta debe tener al menos 3 cartas. (Tiene {len(lista)})")
            return False

        # 2. Separar jokers y cartas normales de la propuesta
        jokers_en_propuesta = []
        cartas_normales = []
        for card in lista:
            # Asumiendo que tu objeto Card tiene un booleano 'joker'
            if card.joker:
                jokers_en_propuesta.append(card)
            else:
                cartas_normales.append(card)

        # 3. Verificar la regla del Joker (máximo 1)
        if len(jokers_en_propuesta) > 1:
            print(f"Error: La propuesta tiene más de 1 joker. (Tiene {len(jokers_en_propuesta)})")
            return False

        # 4. Verificar los valores de las cartas normales
        # Si hay 0 o 1 carta normal, es válido (ej: [Joker, 5, 5])
        # Si hay 2 o más cartas normales, TODAS deben ser iguales.
        if len(cartas_normales) >= 2:
            # Tomamos el valor de la primera carta normal como referencia
            # Asumiendo que tu objeto Card tiene un atributo 'value'
            valor_referencia = cartas_normales[0].value
            
            # Iteramos sobre el RESTO de cartas normales
            for i in range(1, len(cartas_normales)):
                if cartas_normales[i].value != valor_referencia:
                    print(f"Error: Las cartas normales no tienen el mismo valor.")
                    print(f"Se esperaba '{valor_referencia}', pero se encontró '{cartas_normales[i].value}'")
                    return False
                    
        # 5. Caso especial: ¿Propuesta de solo Jokers?
        # Ej: [Joker, Joker, Joker]. Esto fallaría en el paso 3 (len > 1).
        if not cartas_normales and len(jokers_en_propuesta) >= 3:
             # Esto solo puede pasar si la regla de jokers es > 1, pero
             # nuestro paso 3 ya lo habría bloqueado. Es una doble seguridad.
             print("Error: No se pueden formar grupos solo de Jokers (o la regla de max 1 joker lo impide).")
             return False

        # Si llegamos hasta aquí, la propuesta es válida.
        print(f"¡Propuesta válida!: {[str(c) for c in lista]}")
        return True
    
    def isValidStraightF(self,cards):
        """
        Verifica si una lista de objetos Card forma una seguidilla válida (Rummy).
        Requiere que las cartas estén en orden correcto.
        Reglas:
        - Mínimo 3 cartas.
        - Todas las cartas no-Joker deben ser del mismo palo.
        - Consecutivas (considerando As bajo o alto).
        - Máximo 2 Jokers, no consecutivos.
        - Lista debe venir ordenada.
        """

        if not cards or len(cards) < 4:
            return False
        if len(cards) >= 14:
            first, last = cards[0], cards[-1]
            if not first.joker and not last.joker and first.value == "A" and last.value == "A":
                inner = cards[1:-1]
                # Verificamos que el interior sea del mismo palo y consecutivo (2...K)
                suits = {c.type for c in inner if not c.joker}
                if len(suits) == 1:
                    expected_values = ["2","3","4","5","6","7","8","9","10","J","Q","K"]
                    inner_values = [c.value for c in inner if not c.joker]
                    if inner_values == expected_values:
                        return True
            jokers = [c for c in cards if c.joker]
            nonJokers = [c for c in cards if not c.joker]
        jokers = [c for c in cards if c.joker]
        nonJokers = [c for c in cards if not c.joker]

        # Máximo 2 jokers
        if len(jokers) > 2:
            return False

        # No 2 jokers consecutivos
        for a, b in zip(cards, cards[1:]):
            if a.joker and b.joker:
                return False

        # Todas las cartas no-Joker deben tener el mismo palo
        suits = {c.type for c in nonJokers}
        if len(suits) > 1:
            return False

        # Función para obtener valor numérico (según modo)
        def rank(card, highAs=False):
            if card.joker:
                return None
            if card.value == "A":
                return 14 if highAs else 1
            return card.numValue()

        # Verifica si la lista está ordenada y consecutiva en un modo
        def checkStraightInGivenOrder(highAsMode):
            needed_jokers = 0
            prev_rank = None
            prev_card = None
            for card in cards:
                if card.joker:
                    continue
                curr_rank = rank(card, highAsMode)
                if prev_rank is not None:
                    diff = curr_rank - prev_rank
                    if diff == 0:
                        return False  # duplicadas
                    elif diff < 0:
                        return False  # no está ordenada
                    elif diff > 1:
                        needed_jokers += (diff - 1)
                prev_rank = curr_rank
                prev_card = card

            return needed_jokers <= len(jokers)

        # Debe estar ordenada en al menos un modo (As bajo o As alto)
        if checkStraightInGivenOrder(False):
            if cards[0].joker and cards[1].value == "A":
                return False
            else:
                return True
        elif checkStraightInGivenOrder(True):
            if cards[-1].joker and cards[-2].value == "A":
                return False
            else:
                return True

        # Caso especial: secuencia con As al final después de K
        values = [c.value for c in cards if not c.joker]
        if "A" in values and "K" in values:
            # verificamos que A esté al final y orden ascendente hasta K
            try:
                last_non_joker = [c for c in cards if not c.joker][-1]
            except IndexError:
                return False
            if last_non_joker.value == "A":
                # permitir secuencia como 10 J Q K A
                prev_rank = None
                needed_jokers = 0
                for card in cards:
                    if card.joker:
                        continue
                    val = rank(card, True)
                    if prev_rank is not None:
                        diff = val - prev_rank
                        if diff <= 0:
                            return False
                        elif diff > 1:
                            needed_jokers += (diff - 1)
                    prev_rank = val
                return needed_jokers <= len(jokers)

        return False



    def insertCard(self, targetPlayer, targetPlayIndex, cardToInsert, position=None):
        """
        Inserta una carta en targetPlayer.playMade[targetPlayIndex].
        position: 'start', 'end' o None para sustitución de Joker.
        Requisitos: self.downHand == True y cardToInsert in self.playerHand
        """

        # 1) Validaciones básicas
        if not self.downHand:
            print(f"❌ {self.playerName} no puede insertar cartas: aún no se ha bajado.")
            return False
        
        if not self.isHand:
            print(f"❌ {self.playerName} no puede insertar cartas aún porque no es su turno.")

        if cardToInsert not in self.playerHand:
            print(f"❌ {self.playerName} no tiene la carta {cardToInsert} en su mano.")
            return False

        if targetPlayIndex < 0 or targetPlayIndex >= len(targetPlayer.playMade):
            print("❌ El índice dado para la jugada objetivo es inválido.")
            return False

        targetPlay = targetPlayer.playMade[targetPlayIndex]
        temporalPlay = targetPlay.copy()



        # Mapa para ranks (A tratado luego según modo)
        valueToRank = {
            "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
            "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13
        }
        def string_to_card(c):
            if isinstance(c,str):
                if c == "Joker":
                    return Card("Joker", "", joker=True)
                else:
                    value = c[:-1]    # todo menos el último carácter (valor)
                    suit = c[-1]      # último carácter (palo)
                    return Card(value, suit)
            else:
                return c
        def isJoker(c):
            return getattr(c, "joker", False)

        # ---------- Validación TRÍO ----------
        def isValidTrio(play1):
            # Un trío debe tener exactamente 3 cartas (o 3 con 1 Joker)
            play = [c for c in play1["trio"]] if isinstance(play1,dict) else play1
            if len(play) < 3:
                return False
            jokers = [c for c in play if isJoker(c)]
            nonJokers = [c for c in play if not isJoker(c)]
            # Regla: no más de 1 joker en trío
            if len(jokers) > 1:
                return False
            if len(nonJokers) == 0:
                return False
            values = [c.value for c in nonJokers]
            return len(set(values)) == 1

        # ---------- Validación SEGUIDILLA ----------
        def isValidStraight(play):
            # Debe tener al menos 4 cartas totales
            if len(play) < 4:
                return False

            # No permitir jokers adyacentes
            for i in range(len(play) - 1):
                if isJoker(play[i]) and isJoker(play[i + 1]):
                    return False

            # Validar palos (los no-jokers deben pertenecer al mismo palo)
            suits = [c.type for c in play if not isJoker(c)]
            if len(suits) == 0:
                return False
            if len(set(suits)) > 1:
                return False

            # Intentaremos ambos modos: As como bajo (A=1) y As como alto (A=14)
            for highAs in (False, True):
                # Construir lista de ranks (None para jokers)
                ranks = []
                okMode = True #
                for c in play:
                    if isJoker(c):
                        ranks.append(None)
                    else:
                        if c.value == "A":
                            r = 14 if highAs else 1
                        else:
                            if c.value not in valueToRank:
                                okMode = False
                                break
                            r = valueToRank[c.value]
                        ranks.append(r)
                if not okMode:
                    continue

                # Debe haber al menos un non-joker para fijar la base
                nonIndex = [i for i, r in enumerate(ranks) if r is not None]
                if not nonIndex:
                    continue

                # Calcular el "base" candidato: r - pos para cada non-joker
                baseSet = set(ranks[i] - i for i in nonIndex)
                if len(baseSet) != 1:
                    continue
                base = baseSet.pop()

                # Comprobar que los expected ranks estén en 1..14 y coincidan con non-jokers
                expectedOk = True
                for pos, r in enumerate(ranks):
                    expected = base + pos
                    if expected < 1 or expected > 14:
                        expectedOk = False
                        break
                    if r is not None and r != expected:
                        expectedOk = False
                        break
                if not expectedOk:
                    continue

                # Reglas específicas con As:
                # Si hay un As en play:
                for i, c in enumerate(play):
                    if not isJoker(c) and c.value == "A":
                        # As como bajo: no debe haber ningún Joker antes de esa A
                        if not highAs:
                            if any(isJoker(play[j]) for j in range(0, i)):
                                expectedOk = False
                                break
                        # As como alto: no debe haber ningún Joker después de esa A
                        else:
                            if any(isJoker(play[j]) for j in range(i + 1, len(play))):
                                expectedOk = False
                                break
                if not expectedOk:
                    continue

                # Si llegamos hasta aquí, el modo es válido => la secuencia es válida
                return True

            # Ningún modo válido
            return False

    # ---------- Detectar si la jugada objetivo "parece" trío ----------
        def isTrioLike(play):
            # heurística: si la mayoría de cartas no-joker comparten valor y longitud <= 4
            nonJokers = [c for c in play if not isJoker(c)]
            if not nonJokers:
                return False
            values = [string_to_card(c).value if isinstance(c,str) else c.value for c in nonJokers]
            return len(play) <= 4 and len(set(values)) == 1

        isTrioTarget = isTrioLike(targetPlay)

        # Helper: extrae la lista interna (y su clave en caso de dict) de una jugada
        def _extract_play_list(play):
            """Devuelve (lista, key) donde key es 'trio'|'straight' o None si play es lista.
            Si play es dict y no contiene las claves esperadas, devuelve el primer valor encontrado."""
            if isinstance(play, dict):
                if "trio" in play:
                    return play["trio"], "trio"
                if "straight" in play:
                    return play["straight"], "straight"
                # fallback: devolver primer valor
                for k, v in play.items():
                    return v, k
            return play, None

        # ---------- Simular la operación ----------
        temporal_list, temporal_key = _extract_play_list(temporalPlay)

        if position is None:
            # sustitución: buscar primer Joker en la lista interna
            jokerIndex = next((i for i, c in enumerate(temporal_list) if isJoker(c)), None)
            if jokerIndex is None:
                print("❌ No hay Joker para sustituir en esta jugada.")
                return False
            temporal_list[jokerIndex] = cardToInsert
        elif position == "start":
            temporal_list.insert(0, cardToInsert)
        elif position == "end":
            temporal_list.append(cardToInsert)
        else:
            print("❌ Posición inválida. Usa 'start', 'end' o None.")
            return False

        # ---------- Validar la jugada simulada (sin depender de findStraight/findTrios) ----------
        # Validar la jugada simulada (trabajando sobre la lista interna extraída)
        if isTrioTarget:
            valid = isValidTrio(temporal_list)
        else:
            valid = isValidStraight(temporal_list)

        if not valid:
            if isTrioTarget:
                print("❌ La sustitución/inserción rompe el trío: operación rechazada.")
                print(f"Trío si se agregase dicha carta: {[str(c) for c in temporal_list]}")
            else:
                print("❌ La carta no puede insertarse: la seguidilla resultante no es válida.")
                print(f"Seguidilla si se agregase dicha carta: {[str(c) for c in temporal_list]}")
            return False

        # ---------- Aplicar cambios reales ----------
        # ---------- Aplicar cambios reales ----------
        target_list, target_key = _extract_play_list(targetPlay)
        if position is None:
            # Reemplazar el Joker real y devolver esa instancia de Joker a la mano del que inserta
            jokerIndexReal = next((i for i, c in enumerate(target_list) if isJoker(c)), None)
            if jokerIndexReal is None:
                print("❌ (race) No hay Joker real para sustituir.")
                return False
            replacedJoker = target_list[jokerIndexReal]
            target_list[jokerIndexReal] = cardToInsert
            # quitar carta del que inserta y devolver el Joker real a su mano
            self.playerHand.remove(cardToInsert)
            self.playerHand.append(replacedJoker)
            print(f"🔄 {self.playerName} sustituyó un Joker con {cardToInsert} (Joker -> mano).")
            return True
        else:
            # Insert real al inicio o final (trabajando sobre la lista interna)
            if position == "start":
                target_list.insert(0, cardToInsert)
            else:
                target_list.append(cardToInsert)
            print(f"⬅️ {self.playerName} agregó {cardToInsert} al inicio de la jugada." if position == 'start' else f"➡️ {self.playerName} agregó {cardToInsert} al final de la jugada.")
            self.playerHand.remove(cardToInsert)
            return True

    # Mét. para cambiar el valor de "playerPass" para saber si, en un turno dado, pasó de la carta del
    # descarte y agarró del mazo de disponibles. Servirá para la compra de cartas de los siguientes
    # jugadores.
    def passCard(self):
        self.playerPass = not self.playerPass

    def buyCard(self, round):
        """Este método debe recibir como parámetro el objeto de la ronda actual.
        Eso se hará desde el ciclo principal del juego.
        Este método se utilizará en el botón de comprar carta, que solo se mostrará
        cuando isHand es False"""
        discardedCard = round.discards.pop()
        #Si el jugador decidió comprar la carta del descarte, se le entrega dicha carta y además se le da una del mazo como castigo
        if self.playerBuy and not self.isHand:
            extraCard = round.pile.pop()  #Sacamos la última carta del mazo
            round.hands[self.playerId].append(extraCard)  #Añadimos la carta a la mano del jugador
            # self.playerHand.append(discardedCard)
            round.hands[self.playerId].append(discardedCard)
            self.playerHand = round.hands[self.playerId]
            print(f"El jugador {self.playerName} compró la carta {discardedCard} y recibió una carta: {extraCard}, del mazo como castigo")
            return [discardedCard, extraCard]
            # return round
        else:
            print(f"El jugador {self.playerName} no compró la carta del descarte")
            return None
        
    def calculatePoints(self):
        """Esto añade los puntos al jugador. Se debe llamar este método al finalizar cada ronda.
        Los puntos van de la siguiente manera:
        -Cartas del 2 al 9: 5 puntos cada una
        -Cartas 10, J, Q, K: 10 puntos cada una
        -Cartas de Ases: 20 puntos
        -Cartas Joker: 25 puntos"""
        totalPoints = 0
        for card in self.playerHand:
            if card.joker:
                totalPoints += 25
            elif card.value in ["K", "Q", "J", "10"]:
                totalPoints += 10
            elif card.value == "A":
                totalPoints += 20
            else:
                totalPoints += 5
        self.playerPoints += totalPoints
        return totalPoints
