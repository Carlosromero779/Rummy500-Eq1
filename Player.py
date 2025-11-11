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
                

        
    #Mét. para descartar una carta de la playerHand del jugador. Sólo se ejecuta si el jugador tiene una única
    #carta seleccionada previamente.
    def discardCard(self, selectedDiscards, round):

        #Verificamos la cantidad de cartas seleccionadas.
        if len(selectedDiscards) == 2 and self.isHand and self.cardDrawn and self.downHand:

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
            self.playerHand.remove(cardDiscarded)
            round.discards.append(cardDiscarded)
            selectedDiscards.remove(cardDiscarded)
            selectedDiscards = []
            self.discarded = True
            # self.isHand = False

            return [cardDiscarded]
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
    
    def canGetOff(self):
        trios = self.findTrios()
        straights = self.findStraight()
        jokers = [c for c in self.playerHand if c.joker]

        valid_combos = []

        # Probar cada combinación de trío + seguidilla
        for trio in trios:
            for straight in straights:
                jokersInTrio = sum(1 for c in trio if c.joker)
                jokersInStraight = sum(1 for c in straight if c.joker)
                usedJokers = jokersInTrio + jokersInStraight
                # Verificamos que no compartan cartas (verificando si tienen la misma instancia)
                conflict = any(c1.id == c2.id for c1 in trio for c2 in straight if not c1.joker and not c2.joker)
                conflict2 = usedJokers > len(jokers) #El segundo conflicto es para evitar que se dupliquen jokers en las jugadas
                if not conflict and not conflict2 and len(trio) >= 3 and len(straight) >= 4: #Esto nos filtra las combinaciones en las que hay conflictos y en las que haya seguidillas de 3 o menos cartas
                    valid_combos.append({
                        "trio": trio,
                        "straight": straight
                    })

        if valid_combos:
            print(f"\n✅ El jugador {self.playerName} SI SE PUEDE BAJAR con {len(valid_combos)} combinación(es):")
            for i, combination in enumerate(valid_combos, 1): #Simplemente nos imprime en pantalla las combinaciones disponibles en la mano del jugador
                print(f"   Opción {i}:")
                print(f"     Trío -> {[str(c) for c in combination['trio']]}")
                print(f"     Seguidilla -> {[str(c) for c in combination['straight']]}")
            return valid_combos
        else:
            print(f"\n❌ El jugador {self.playerName} NO se puede bajar aún.")
            return None
        #NOTA: Al final, tengo pensado que para que un jugador se pueda bajar, deba organizar su jugada
        #de tal manera que la combinación de cartas que va a bajar coincida con alguna de las combinaciones
        #que retorna este método canGetOff().

    def canGetOff2(self): #Por favor, no modificar.
        #Hay algunas cosas que aquí dicen "trio" y eso, pero deben dejarse así, para que siga funcio-
        #nando el insertCard independientemente de la ronda.
        straights = self.findStraight()
        jokers = [c for c in self.playerHand if c.joker]

        valid_combos = []

        # Probar cada combinación de 2 seguidillas
        for straight1 in straights:
            for straight2 in straights:
                jokersInStraights = sum(1 for c in straight1 if c.joker) + sum(1 for c in straight2 if c.joker)
                usedJokers = jokersInStraights
                # Verificamos que no compartan cartas (verificando si tienen la misma instancia)
                conflict = any(c1.id == c2.id for c1 in straight1 for c2 in straight2 if not c1.joker and not c2.joker)
                conflict2 = usedJokers > len(jokers) #El segundo conflicto es para evitar que se dupliquen jokers en las jugadas
                if not conflict and not conflict2 and len(straight1) >= 4 and len(straight2) >= 4: #Esto nos filtra las combinaciones en las que hay conflictos y en las que haya seguidillas de 3 o menos cartas
                    valid_combos.append({
                        "trio": straight1,
                        "straight": straight2
                    })

        if valid_combos:
            print(f"\n✅ El jugador {self.playerName} SI SE PUEDE BAJAR con {len(valid_combos)} combinación(es):")
            for i, combination in enumerate(valid_combos, 1): #Simplemente nos imprime en pantalla las combinaciones disponibles en la mano del jugador
                print(f"   Opción {i}:")
                print(f"     Seguidilla 1 -> {[str(c) for c in combination["trio"]]}")
                print(f"     Seguidilla 2 -> {[str(c) for c in combination["straight"]]}")
            return valid_combos
        else:
            print(f"\n❌ El jugador {self.playerName} NO se puede bajar aún.")
            return None

    def getOff(self, visualStraight, visualTrio):
        """Con este método, el jugador podrá bajarse.
        Tengamos en cuenta que:
        +visualTrio corresponde a las cartas colocadas en la zona de tríos de la interfaz
        +visualStraight corresponde, por su parte, a las cartas de la zona de seguidillas dentro de la interfaz"""
        combinations = self.canGetOff()
        availableTrios = [combination["trio"] for combination in combinations] if combinations != None else [] #Esto nos crea una lista con todas las combinaciones de tríos disponibles
        prepareTrio = []
        jokersInTrio = sum(1 for c in visualTrio if c.joker)
        availableStraights = [combination["straight"] for combination in combinations] if combinations != None else [] #Nos crea una lista con todas las combinaciones de seguidillas válidas disponibles
        prepareStraight = []
        chosenCards = visualTrio + visualStraight #Esta lista contendrá las cartas que el jugador ha seleccionado para bajarse
        if not chosenCards:
            print("El jugador aún no ha seleccionado cartas")
            return None
        if len(chosenCards) >= 7:
            for trio in availableTrios: #Esto nos crea una lista con todas las cartas que se van a descartar
                for straight in availableStraights:
                    for card in chosenCards:
                        #Agregamos cartas al posible trío y seguidilla dependiendo de si 
                        #están en la mano del jugador y si coinciden con alguna carta del trío o seguidilla válidos
                        if card in trio and card in self.playerHand and card not in prepareTrio and card in visualTrio:
                            prepareTrio.append(card)
                        elif card in straight and card in self.playerHand and card not in prepareStraight and card in visualStraight:
                            prepareStraight.append(card)
            #Si existe alguna carta en el trío o en la seguidilla que no estén dentro de alguna jugada válida
            if any(card not in prepareTrio and card not in prepareStraight for card in chosenCards):
                print("Alguna de las cartas seleccionadas no se encuentra en el trío o en la seguidilla")
                return None
            #Si el jugador ya se bajó, no le permitimos que lo vuelva a hacer
            elif self.downHand:
                print("El jugador ya se bajó en esta ronda. No puede volver a bajarse")
                return None
            #Si la seguidilla armada no coincide con el orden de alguna seguidilla válida, no se puede bajar
            elif not any(straight == visualStraight for straight in availableStraights):
                print("La seguidilla organizada no coincide con alguna seguidilla válida")
                return None
            #Si hay más de un joker en el trío, no se puede bajar
            elif jokersInTrio > 1:
                print("El trío organizado tiene más de un Joker. No es válido")
                return None
            elif not self.isHand:
                print("El jugador no puede bajarse aún porque no es su turno")
                return None
            elif not self.cardDrawn:
                print("El jugador debe tomar una carta antes de hacer cualquier jugada")
            #Analizamos el trío armado y, si tiene alguna carta que no corresponda con algún trío válido,
            #no podrá bajarse (para el trío no importa el orden en que se coloquen las cartas)
            for card in visualTrio:
                if not any(card in trio for trio in availableTrios):
                    print("El trío organizado no coincide con el trío válido")
                    return None
            else:
                #Analizamos, si el trío tiene al menos 3 cartas, la seguidilla tiene al menos 4 cartas,
                #Y a la vez se han seleccionado al menos 7 cartas entre el trío y la seguidilla, el jugador
                #SI Se podrá bajar
                if len(prepareTrio) >= 3 and len(prepareStraight) >= 4 and len(chosenCards) >= 7 and self.isHand:
                    #La jugada se guardará en playMade.
                    #NOTA: playMade es un array dividido en 2 renglones: organiza los tríos en el primer renglón ["trios"]
                    #y las seguidillas en el segundo ["straight"]
                    self.playMade.append({"trio": prepareTrio, "straight": prepareStraight})
                    #Eliminamos las cartas de los espacios visuales, para que desaparezcan al pulsar el botón de bajarse
                    for card in prepareTrio:
                        visualTrio.remove(card)
                        self.playerHand.remove(card)
                    for card in prepareStraight:
                        visualStraight.remove(card)
                        self.playerHand.remove(card)
                    #enviamolainmformnacionalcervidor
                    #enviar playerhand y playmade
                    #El booleano que indica si se bajó, cambia a True
                    self.downHand = True
                    print(f"El jugador {self.playerName} se bajó con: \n     Trío -> {[str(c) for c in prepareTrio]}\n     Seguidilla -> {[str(c) for c in prepareStraight]}")
                    print(f"Trio guardado: {[str(c) for c in prepareTrio]}")
                    print(f"Seguidilla guardada: {[str(c) for c in prepareStraight]}")
                    return prepareTrio, prepareStraight

        #Por último, si la jugada tiene menos de 7 cartas, claramente el jugador no puede bajarse
        elif len(chosenCards) < 7:
            print(f"Se han seleccionado {len(chosenCards)} cartas, no son suficientes aún.")
            return None

    def getOff2(self, visualStraight, visualStraight2):
        #Por favor, tampoco lo modifiquen xd
        """Con este método, el jugador podrá bajarse (en la segunda ronda).
        Tengamos en cuenta que:
        +visualStraight2 corresponde a las cartas colocadas en la "zona de tríos" de la interfaz
        +visualStraight corresponde, por su parte, a las cartas de la "zona de seguidillas" dentro de la interfaz"""
        combinations = self.canGetOff2()
        prepareStraight1 = []
        #availableStraights1 = [combination["trio"] for combination in combinations] if combinations != None else [] #Nos crea una lista con todas las combinaciones de seguidillas válidas disponibles
        availableStraights1 = [combination["straight"] for combination in combinations] if combinations != None else [] #Nos crea una lista con todas las combinaciones de seguidillas válidas disponibles
        availableStraights2 = [combination["straight"] for combination in combinations] if combinations != None else [] #Nos crea una lista con todas las combinaciones de seguidillas válidas disponibles
        prepareStraight2 = []
        chosenCards = visualStraight2 + visualStraight #Esta lista contendrá las cartas que el jugador ha seleccionado para bajarse
        if not chosenCards:
            print("El jugador aún no ha seleccionado cartas")
            return None
        if len(chosenCards) >= 8:   # Dos sguidillas tienen minimo 8 cartas...
            for straight1 in availableStraights1: #Esto nos crea una lista con todas las cartas que se van a descartar
                for straight2 in availableStraights2:
                    for card in chosenCards:
                        #Agregamos cartas al posible trío y seguidilla dependiendo de si 
                        #están en la mano del jugador y si coinciden con alguna carta del trío o seguidilla válidos
                        if card in straight2 and card in self.playerHand and card not in prepareStraight2 and card in visualStraight2:
                            prepareStraight2.append(card)
                        elif card in straight1 and card in self.playerHand and card not in prepareStraight1 and card in visualStraight:
                            prepareStraight1.append(card)
            #Si existe alguna carta en el trío o en la seguidilla que no estén dentro de alguna jugada válida
            if any(card not in prepareStraight2 and card not in prepareStraight1 for card in chosenCards):
                print("Alguna de las cartas seleccionadas no se encuentra en alguna de las seguidillas armadas")
                return None
            #Si el jugador ya se bajó, no le permitimos que lo vuelva a hacer
            elif self.downHand:
                print("El jugador ya se bajó en esta ronda. No puede volver a bajarse")
                return None
            #Si la seguidilla armada no coincide con el orden de alguna seguidilla válida, no se puede bajar
            elif not any(straight == visualStraight for straight in availableStraights1):
                print("La seguidilla organizada (1) no coincide con alguna seguidilla válida")
                return None
            #Si la segunda seguidilla armada no coincide con el orden de alguna seguidilla válida, no se puede bajar
            elif not any(straight == visualStraight2 for straight in availableStraights2):
                print("La seguidilla organizada (2) no coincide con alguna seguidilla válida")
                return None
            elif not self.isHand:
                print("El jugador no puede bajarse aún porque no es su turno")
                return None
            elif not self.cardDrawn:
                print("El jugador debe tomar una carta antes de hacer cualquier jugada")
                return None
            else:
                #Analizamos, si ambas seguidillas tienen al menos 4 cartas c/u,
                #Y a la vez se han seleccionado al menos 8 cartas entre estas, el jugador
                #SI Se podrá bajar
                if len(prepareStraight2) >= 4 and len(prepareStraight1) >= 4 and len(chosenCards) >= 8 and self.isHand:
                    #La jugada se guardará en playMade.
                    self.playMade.append({"straight2": prepareStraight2, "straight": prepareStraight1})
                    #self.playMade.append(prepareStraight1)
                    #self.playMade.append(prepareStraight2)
                    #Eliminamos las cartas de los espacios visuales, para que desaparezcan al pulsar el botón de bajarse
                    for card in prepareStraight2:
                        visualStraight2.remove(card)
                        self.playerHand.remove(card)
                    for card in prepareStraight1:
                        visualStraight.remove(card)
                        self.playerHand.remove(card)
                    #El booleano que indica si se bajó, cambia a True
                    self.downHand = True
                    print(f"El jugador {self.playerName} se bajó con: \n     Seguidilla 1 -> {[str(c) for c in prepareStraight1]}\n     Seguidilla 2 -> {[str(c) for c in prepareStraight2]}")
                    print(f"Straight1 guardado: {[str(c) for c in prepareStraight1]}")
                    print(f"Straight2 guardada: {[str(c) for c in prepareStraight2]}")
                    return prepareStraight1, prepareStraight2

        #Por último, si la jugada tiene menos de 8 cartas, claramente el jugador no puede bajarse
        elif len(chosenCards) < 8:
            print(f"Se han seleccionado {len(chosenCards)} cartas, no son suficientes aún.")
            return None

    def findTrios(self):
        trios = []  #Esta lista va a almacenar todos los tríos posibles en la mano del jugador
        cardsPerValue = {}  #Diccionario para almacenar las cartas por valor
        jokers = []  #Jokers que hay en la mano del jugador

        #Clasificamos las cartas en normales y jokers
        for card in self.playerHand:
            if card.joker:
                jokers.append(card)
            else:
                if card.value not in cardsPerValue:
                    cardsPerValue[card.value] = []
                cardsPerValue[card.value].append(card)

        #Incluimos los jokers como valor especial para más adelante hacer combinaciones
        if jokers:
            cardsPerValue["Joker"] = jokers

        #A partir de aquí comenzamos a generar posibles tríos, partiendo de los grupos de cartas en el diccionario
        for value, cards in cardsPerValue.items():
            if value == "Joker":
                continue  #No se pueden formar tríos solo con jokers

            totalCards = cards.copy()  #Creamos una copia de las cartas (con su valor) para no modificar la original
            if jokers:
                totalCards += jokers  #Añadimos los jokers a la lista temporal

            #Creamos todas las combinaciones de tamaño 3 o más (independientemente de la cantidad de cartas
            #del mismo valor que tenga el jugador en su mano)
            for size in range(3, len(totalCards) + 1):
                for combination in combinations(totalCards, size):
                    jokerCount = sum(1 for c in combination if c.joker)

                    # Restricción: máximo 1 Joker por trío
                    if jokerCount <= 1:
                        sortedCombo = sorted(combination, key=lambda c: (c.joker, c.value, c.type))

                        if sortedCombo not in trios:
                            trios.append(sortedCombo)
        return trios

    
    def findStraight(self, highAsMode=False):
        straights = []
        jokers = [c for c in self.playerHand if c.joker]
        nonJokers = [c for c in self.playerHand if not c.joker]

        #Diccionario de valores a número (A=1, J=11, Q=12, K=13)
        valueToRank = {
            "A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
            "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13
        }

        #Rank local: devuelve 14 para A cuando highAsMode = True
        def rank(card, highAs = False):
            if getattr(card, "joker", False):
                return -1
            if card.value == "A" and highAs:
                return 14
            return valueToRank[card.value]

        #Ordenamos las cartas por palo y por valor (colocando el As como bajo para el orden inicial)
        nonJokers.sort(key=lambda c: (c.type, rank(c, False)))

        #Agrupamos las cartas por palo
        palos = {}
        for c in nonJokers:
            palos.setdefault(c.type, []).append(c)

        #Función para evitar Jokers consecutivos
        def noConsecJokers(seq):
            return all(not (getattr(a, "joker", False) and getattr(b, "joker", False))
                    for a, b in zip(seq, seq[1:]))

        # Reglas para insertar Jokers al inicio/fin
        def canInsertAtStart(seq, highAsMode):
            """Función que controla si podemos colocar un Joker al inicio de la secuencia"""
            if not seq:
                return False

            # Si es As bajo y la primera carta es A, NO permitir Joker antes
            if seq[0].value == "A" and not highAsMode:
                return False

            # Caso As alto o cualquier otra carta, sí se permite Joker antes
            return True


        def canInsertAtEnd(seq, highAsMode):
            """Esta función controla si podemos colocar un Joker al final de la secuencia"""
            if not seq:
                return False

            #Si es una seguidilla con As alto y la última carta es A, NO permitir un Joker después
            if seq[-1].value == "A" and highAsMode:
                return False

            #Caso As bajo o cualquier otra carta, sí se permite Joker después
            return True


        #Función para insertar jokers en las seguidillas existentes
        def expandWithJokers(seq, jokersList, highAs):
            variants = []

            if not jokersList:
                return variants

            def helper(currSequence, remainingJokers, startAllowed, endAllowed):
                """Esta función inserta Jokers en todas las posiciones posibles (respetando las reglas)"""
                #Si ya no hay Jokers que insertar, validamos la secuencia final
                if not remainingJokers:
                    if len(currSequence) >= 4 and noConsecJokers(currSequence):
                        variants.append(currSequence[:])
                    return

                #Tomamos el siguiente Joker
                nextJoker = remainingJokers[0]
                restJokers = remainingJokers[1:]

                # 1)Probamos la inserción de cartas al inicio de la secuencia
                if startAllowed and canInsertAtStart(currSequence, highAs):
                    helper([nextJoker] + currSequence, restJokers, startAllowed, endAllowed)

                # 2)Ahora intentamos insertar en el medio como reemplazo de alguna otra carta
                for i in range(len(currSequence)):
                    newSequence = currSequence[:i] + [nextJoker] + currSequence[i+1:]
                    if noConsecJokers(newSequence):
                        helper(newSequence, restJokers, startAllowed, endAllowed)

                # 3)Por último, intentamos insertar un joker al final de la seguidilla
                if endAllowed and canInsertAtEnd(currSequence, highAs):
                    helper(currSequence + [nextJoker], restJokers, startAllowed, endAllowed)

            #Llamada inicial
            helper(seq, jokersList, True, True)

            #Eliminamos secuencias duplicadas
            unique = []
            seen = set()
            for v in variants:
                key = tuple(id(c) for c in v)
                if key not in seen:
                    seen.add(key)
                    unique.append(v)

            return unique


        #Función que comprueba si dos cartas (c1 y c2) son consecutivas en el modo actual
        def isConsecutive(c1, c2, highAs):
            return rank(c2, highAs) - rank(c1, highAs) == 1

        def isConsecutiveWithJokers(c1, c2, highAs):
            return rank(c2, highAs) - rank(c1, highAs) == 2

        #Con el siguiente ciclo, recorremos todos los palos y las secuencias que puedan formarse con ellos
        for palo, cartas in palos.items():
            if not cartas:
                continue
            

            #Evaluamos las secuencias en ambos modos: As bajo y As alto
            for highMode in (False, True):
                #Ordenamos las cartas para este modo (As como 1 o 14 según highMode)
                sortedCards = sorted(cartas, key=lambda c: rank(c, highMode))

                if not sortedCards:
                    continue

                currentSequence = [sortedCards[0]] #currentSequence nos permite ir construyendo secuencias de carta en carta

                for i in range(1, len(sortedCards)):
                    prev = sortedCards[i - 1]
                    curr = sortedCards[i]
                    usedJokers = sum(1 for card in currentSequence if getattr(card, "joker", False))

                    #Caso A->2, que es manejado por rank() cuando highMode = False
                    if isConsecutive(prev, curr, highMode):
                        currentSequence.append(curr)
                    elif isConsecutiveWithJokers(prev, curr, highMode) and usedJokers < len(jokers):
                        currentSequence.append(jokers[usedJokers])
                        jokers.remove(jokers[usedJokers])
                        currentSequence.append(curr)
                        
                    else:
                        #Guardamos la secuencia si alcanza mínimo 3 (para luego añadirle jokers)
                        if len(currentSequence) >= 3:
                            straights.append(currentSequence)
                            remainingJokers = jokers[:]  # jokers disponibles para esta secuencia
                            for v in expandWithJokers(currentSequence, remainingJokers, highMode):
                                straights.append(v)
                        #Reiniciamos la secuencia
                        currentSequence = [curr]

                #Al terminar el palo, procesamos la última secuencia
                if len(currentSequence) >= 3 and currentSequence not in straights:
                    straights.append(currentSequence)
                    remainingJokers = jokers[:]
                    for v in expandWithJokers(currentSequence, remainingJokers, highMode):
                        if v not in straights:
                            straights.append(v)
                for s in straights: #Con esto, construimos secuencias alternas
                    #Se utilizará para construir seguidillas heredadas de algunas seguidillas mayores
                    #Ejemplo: Si nuestra seguidilla tiene 5 cartas, de allí podremos construir seguidillas de 4 cartas
                    #Otro ejemplo: Si nuestra seguidilla tiene 6 cartas, se podrán construir seguidillas de 5 cartas o 4 cartas,
                    #Según lo desee el jugador
                    if len(s) >= 5:
                        for i in range(len(s)):
                            altSeq1 = s[i+1:]
                            altSeq2 = s[:-i-1]
                            if len(altSeq1) >= 4 and altSeq1 not in straights:
                                straights.append(altSeq1)
                            if len(altSeq2) >= 4 and altSeq2 not in straights:
                                straights.append(altSeq2)
    
        return straights


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

        # ---------- Simular la operación ----------
        if position is None:
            # sustitución: buscar primer Joker
            jokerIndex = next((i for i, c in enumerate(temporalPlay) if isJoker(c)), None)
            if jokerIndex is None:
                print("❌ No hay Joker para sustituir en esta jugada.")
                return False
            temporalPlay[jokerIndex] = cardToInsert
        elif position == "start":
            if isinstance(temporalPlay,dict):
                temporalPlay["trio"].insert(0, cardToInsert)
            else:
                temporalPlay.insert(0, cardToInsert)
        elif position == "end":
            if isinstance(temporalPlay,dict):
                temporalPlay["trio"].append(cardToInsert)
            else:
                temporalPlay.append(cardToInsert)
        else:
            print("❌ Posición inválida. Usa 'start', 'end' o None.")
            return False

        # ---------- Validar la jugada simulada (sin depender de findStraight/findTrios) ----------
        if isTrioTarget:
            if isinstance(temporalPlay,dict):
                valid = isValidTrio(temporalPlay["trio"])
            else:
                valid = isValidTrio(temporalPlay)
        else:
            if isinstance(temporalPlay,dict):
                valid = isValidStraight(temporalPlay["straight"])
            else:
                valid = isValidStraight(temporalPlay)

        if not valid:
            if isTrioTarget:
                print("❌ La sustitución/inserción rompe el trío: operación rechazada.")
                print(f"Trío si se agregase dicha carta: {[str(c) for c in temporalPlay['trio']]}")
            else:
                print("❌ La carta no puede insertarse: la seguidilla resultante no es válida.")
                print(f"Seguidilla si se agregase dicha carta: {[str(c) for c in temporalPlay['trio']]}")
            return False

        # ---------- Aplicar cambios reales ----------
        if position is None:
            # Reemplazar el Joker real y devolver esa instancia de Joker a la mano del que inserta
            jokerIndexReal = next((i for i, c in enumerate(targetPlay) if isJoker(c)), None)
            if jokerIndexReal is None:
                print("❌ (race) No hay Joker real para sustituir.")
                return False
            replacedJoker = targetPlay[jokerIndexReal]
            targetPlay[jokerIndexReal] = cardToInsert
            # quitar carta del que inserta y devolver el Joker real a su mano
            self.playerHand.remove(cardToInsert)
            self.playerHand.append(replacedJoker)
            print(f"🔄 {self.playerName} sustituyó un Joker con {cardToInsert} (Joker -> mano).")
            return True
        else:
            # Insert real al inicio o final
            if position == "start":
                if isinstance(targetPlay,dict):
                    targetPlay["straight"].insert(0, cardToInsert)
                else:
                    targetPlay.insert(0,cardToInsert)
                print(f"⬅️ {self.playerName} agregó {cardToInsert} al inicio de la jugada.")
            else:
                if isinstance(targetPlay,dict):
                    targetPlay["straight"].append(cardToInsert)
                else:
                    targetPlay.append(cardToInsert)
                print(f"➡️ {self.playerName} agregó {cardToInsert} al final de la jugada.")
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
