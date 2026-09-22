#!/usr/bin/python3
# encoding: utf-8
# Copyright (c) 2026 Luan Pestana
# SPDX-License-Identifier: MIT

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, Ellipse, Triangle, PushMatrix, PopMatrix, Rotate, RoundedRectangle, StencilPush, StencilUse, StencilUnUse, StencilPop
from kivy.core.image import Image as CoreImage
from kivy.core.audio import SoundLoader
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.screenmanager import FadeTransition
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
import numpy as np
from collections import deque
from random import randrange
import random
from enum import IntEnum
import time
from kivy.uix.image import Image


# Variaveis globais
width, height = Window.size

fps_limit = 60
fps_print_delay = 1#frames
# Dicionario que armazena os dados do touch
click_data = {}

# Cria uma classe de constantes que se comportam como inteiros (IntEnum) para armazenar o numero de cada direcao, pois comparacao de inteiros eh mais rapida doque comparacao de strings
class Direction(IntEnum):
	RIGHT = 0
	DOWN = 1
	LEFT = 2
	UP = 3


# Classe Click captura dados do clique
class Click(Widget):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	# on_touch_down() poe os dados do clique no dicionario
	def on_touch_down(self, touch):
		# (estado, posicao_inicial, posicao_atual)
		# estado 1 (por o dedo na tela)
		# estado 2 (mover o dedo na tela)
		# estado 3 (tirar o dedo da tela)
		click_data[touch.uid] = (1, touch.pos, touch.pos)
		return super().on_touch_down(touch)
	# on_touch_move() atualiza os dados do clique no dicionario
	def on_touch_move(self, touch):
		if touch.uid not in click_data.keys():
			click_data[touch.uid] = (2, touch.pos, touch.pos)
		click_data[touch.uid] = (2, click_data[touch.uid][1], touch.pos)
		return super().on_touch_move(touch)
	# on_touch_up() atualiza os dados do clique no dicionario
	def on_touch_up(self, touch):
		if touch.uid not in click_data.keys():
			click_data[touch.uid] = (3, touch.pos, touch.pos)
		click_data[touch.uid] = (3, click_data[touch.uid][1], touch.pos)
		return super().on_touch_up(touch)


# Cria a classe do Screen Manager
class MyScreenManager(ScreenManager):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		# Poe a transicao por fade
		self.transition = FadeTransition(duration=0.2)



##### Telas e suas funcoes #####

# Cria a classe da tela base, que contem tudo de comum que todas as telas terao
class BaseScreen(Screen):
	# ui - Variavel que guarda o menor tamanho da tela, sendo width ou height
	ui = min(Window.width, Window.height)
	
# Cria a classe de jogo base, que contem tudo que os dois modos de jogo tera
class SnakeBaseScreen(BaseScreen):
	# ui - Variavel que guarda o menor tamanho da tela, sendo width ou height
	ui = min(Window.width, Window.height)
	# Cria numeros que podem ser acessados pelo system.kv em tempo real
	score = NumericProperty(0)
	timer = NumericProperty(0.0)
	game_running = BooleanProperty(False)
	time_event = None
	# Variacao que sera usada para guardar a velocidade da serpente para amostragem e o limite de velocidade
	move_speed = NumericProperty(0)
	moves_speed_limit = NumericProperty(0)
	# Variavel que define se o jogo acabou ou nao
	game_over = BooleanProperty(False)
	game_win = BooleanProperty(False)
	# Variavel que se positivo, a serpente tera um gradiente de cores
	color_gradient = BooleanProperty(1)
	
	def update_ui(self):
		self.ui = min(Window.width, Window.height)
		
	# Ao iniciar a classe, isso individualiza as variaveis para cada tela
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		# Evento ao segurar algum botao seguravel
		self.hold_button_event = None
		
		# Variavel que se positivo, o jogo sera jogado por algoritmo
		self.solver = 0
		
		# Direcao da serpente
		self.direction = Direction.RIGHT
		self.oppositive_direction = Direction.LEFT
		
		# Contagem de movimentos ate atingir 1 segundo
		self.moves_count = 0
		self.moves_count_timer = 0
		
		# Limite de velocidade inicial
		self.moves_speed_limit = 5
	
		# Tamanho do tabuleiro em quantidade de celulas de largura e altura
		self.board_size = 20
		
		self.board_total_size = self.board_size**2
		
		# Objetos que guardam o estado de cada celula do tabuleiro
		
		# deque() eh utilizado para armazenar e acessar de forma rapida as posicoes do corpo da serpente
		self.snake_deque = deque([(0,1), (1,1), (2,1)])
		
		# set() nao preserva ordem, eh utilizado para verificar de forma rapida se algo ja existe dentro dele
		self.snake_set = set([(0,1), (1,1), (2,1)])
		
		# Tamanho da serpente para acesso rapido
		self.snake_lenght = 3
		
		# Gera uma posicao aleatoria para a maca
		self.apple = (randrange(18)+2, randrange(20))
		
		# Um dicionario que vai guardar os objetos do rect e color de cada celula do tabuleiro
		self.board_canvas = None
		
		# Futuro evento que movimentara a serpente periodicamente
		self.game_event = None
		
		# Calcula o raio das bordas dos quadrados do tabuleiro 
		self.radius = self.ui*0.015*(20/self.board_size)
		
		
		# Lista de movimentos para cada quadrado que se seguidos como setas a serpente nao morrera
		self.board_arrows = []
		# Loop que varre o tabuleiro listando os movimentos seguros para cada quadrado
		for x in range(self.board_size):
			column = []
			for y in range(self.board_size)[::-1]:
				# Celula em lista que ficara na lista maior armazenando ate dois movimentos para o seu respectivo quadrado
				cell = []
				# Nestas verificacoes as contagens sao feitas de baixo a cima
				# Se x for par
				if x % 2 == 0:
					# Se y nao for o ultimo
					if y > 0:
						# Permite descer ao estar nesta celula
						cell.append(Direction.DOWN)
				# Se x for impar
				else:
					# Se y nao for o primeiro
					if y < self.board_size-1:
						# Permite subir ao estar nesta celula
						cell.append(Direction.UP)
				# Se y for par
				if y % 2 == 0:
					# Se x nao for o ultimo
					if x < self.board_size-1:
						# Permite ir a direita ao estar nesta celula
						cell.append(Direction.RIGHT)
				# Se y for impar
				else:
					# Se x nao for o primeiro
					if x > 0:
						# Permite ir a esquerda ao estar nesta celula
						cell.append(Direction.LEFT)
				
				column.append(cell)
			self.board_arrows.append(column)
			
	# Alterna entre gradiente ativado e desativado
	def toggle_gradient(self):
		if self.color_gradient:
			self.color_gradient = 0
			
			# Atualiza as cores da serpente removendo o gradiente
			
			color = (0, 0.87, 0.584, 1)
			# Percorre todas as celulas do corpo para aplicar efeitos
			for current_body in reversed(self.snake_deque):
				if current_body != self.snake_deque[-1]:
					color = (
						color[0],
						color[1],
						color[2],
						color[3],
					)
					self.board_canvas[current_body]["color"].rgba = color
		else:
			self.color_gradient = 1
			
			# Atualiza as cores da serpente aplicando o gradiente
			
			head_color =  (0, 0.87, 0.584, 1)
			tail_color =  (0.36, 0.003, 1, 1)
					
			color_diff = (
				tail_color[0]-head_color[0],
				tail_color[1]-head_color[1],
				tail_color[2]-head_color[2],
				tail_color[3]-head_color[3]
			)
					
			color_progress = (
				color_diff[0]/self.snake_lenght,
				color_diff[1]/self.snake_lenght,
				color_diff[2]/self.snake_lenght,
				color_diff[3]/self.snake_lenght
			)
					
			color = head_color
			# Percorre todas as celulas do corpo para aplicar efeitos
			for current_body in reversed(self.snake_deque):
				if current_body != self.snake_deque[-1]:
					color = (
						color[0]+color_progress[0],
						color[1]+color_progress[1],
						color[2]+color_progress[2],
						color[3]+color_progress[3],
					)
					self.board_canvas[current_body]["color"].rgba = color
	
	# Altera a direcao da serpente sem violar as regras
	def move_direction(self, next_direction):
		# Verifica se o movimento nao eh oposto ao que a serpente esta andando
		if self.oppositive_direction != next_direction:
			# Altera o movimento da serpente para a direcao desejada
			self.direction = next_direction
			return 1
		return 0
	
	# Inicia o cronometro
	def start_timer(self):
		# Se time_event for None
		if self.time_event is None:
			# Inicia o loop para atualizar o cronometro
			self.time_event = Clock.schedule_interval(self.update_timer, 0)
			# Alerta que o jogo esta jogando (visivel em tempo real para o system.kv)
			self.game_running = True
	
	# Funcao que atualiza o cronometro, fica em loop
	def update_timer(self, dt):
		self.timer += dt
		
		if self.timer - self.moves_count_timer >= 1:
			self.moves_count_timer = self.timer
			self.move_speed = self.moves_count
			self.moves_count = 0
	
	# Para o cronometro
	def stop_timer(self):
		# Se time_event nao for None
		if self.time_event is not None:
			# Cancela e poe a variavel como None
			self.time_event.cancel()
			self.time_event = None
			# Alerta que o jogo nao esta jogando (visivel em tempo real para o system.kv)
			self.game_running = False
			# Poe a velocidade mostrada na tela como 0
			self.move_speed = 0
			
		
	
	# Funcao para alternar entre pausado e despausado
	def toggle_pause(self):
		# Se o jogo nao acabou
		if not self.game_over and not self.game_win:
			# Se o evento nao for None
			if self.game_event is not None:
				# Cancela o evento
				self.game_event.cancel()
				# O transforma em None
				self.game_event = None
				# Para o cronometro
				self.stop_timer()
				# Poe a velocidade mostrada na tela como 0
				self.move_speed = 0
				# Alerta que o jogo nao esta jogando (visivel em tempo real para o system.kv)
				self.game_running = False
			else:
				# Se for igual a None cria o evento
				self.game_event = Clock.schedule_interval(self.move_snake, 1/self.moves_speed_limit)
				# Inicia o cronometro
				self.start_timer()
				# Alerta que o jogo esta jogando (visivel em tempo real para o system.kv)
				self.game_running = True
	
	# Funcao para parar o jogo
	def stop_game(self):
		if self.game_event is not None:
			# Para o cronometro
			self.stop_timer()
			# Cancela o evento
			self.game_event.cancel()
			# O transforma em None
			self.game_event = None
			# Alerta que o jogo nao esta jogando (visivel em tempo real para o system.kv)
			self.game_running = False
	
	# Funcao para resetar o jogo
	def reset_game(self):
		self.stop_game()
		self.score = 0
		self.timer = 0
		self.moves_count_timer = 0
		self.game_over = False
		self.game_win = False
		self.snake_lenght = 3
		self.snake_deque = deque([(0,1), (1,1), (2,1)])
		self.snake_set = set([(0,1), (1,1), (2,1)])
		self.draw_board()
		self.new_apple()
		self.direction = Direction.RIGHT
		self.oppositive_direction = Direction.LEFT
		self.move_snake(0)
	
	# Funcao que reseta e comecao jogo
	def replay_game(self):
		self.reset_game()
		self.toggle_pause()
		
	# Funcao para que ao pressionar o botao de aumentar a velocidade limite, a mesma aumente em um, e ao segurar por mais 400ms a velocidade limite comeca a aumentar em 14 a cada segundo
	def speed_limit_up_button_press(self, dt):
		# Se o delta-time for igual a -1 (impossivel com um clock event) significa que foi executado pela primeira vez sendo chamado com o argumento -1
		if dt == -1:
			# Aumenta um nivel na velocidade limite
			self.up_speed_limit(-1)
			# Poe a mesma funcao para executar apos 400ms
			self.hold_button_event = Clock.schedule_once(self.speed_limit_up_button_press, 0.4)
		else:
			# Ao ter um delta-time diferente significa que foi chamado pelo clock event apos os 400ms, entao inicia o loop aumentando a velocidade limite progressivamente
			self.hold_button_event = Clock.schedule_interval(self.up_speed_limit, 1/14)
	
	# Funcao para que ao pressionar o botao de diminuir a velocidade limite, a mesma diminua em um, e ao segurar por mais 400ms a velocidade limite comeca a diminuir em 14 a cada segundo
	def speed_limit_down_button_press(self, dt):
		# Se o delta-time for igual a -1 (impossivel com um clock event) significa que foi executado pela primeira vez sendo chamado com o argumento -1
		if dt == -1:
			# Subtrai um nivel na velocidade limite
			self.down_speed_limit(-1)
			# Poe a mesma funcao para executar apos 400ms
			self.hold_button_event = Clock.schedule_once(self.speed_limit_down_button_press, 0.4)
		else:
			# Ao ter um delta-time diferente significa que foi chamado pelo clock event apos os 400ms, entao inicia o loop reduzindo a velocidade limite progressivamente
			self.hold_button_event = Clock.schedule_interval(self.down_speed_limit, 1/14)
	
	# Funcao para cancelar qualquer loop criado ao segurar algum botao
	def hold_button_release(self):
		if self.hold_button_event is not None:
			self.hold_button_event.cancel()
			self.hold_button_event = None
	
	# Funcoes que aumenta e diminue o limite de velocidade da serpente
	def up_speed_limit(self, dt):
		self.moves_speed_limit += 1
	def down_speed_limit(self, dt):
		self.moves_speed_limit -= 1
		self.moves_speed_limit = max(self.moves_speed_limit, 1)
		
		
	# Gera uma maca numa posicao nova
	def new_apple(self):
		# Cria uma lista para armazenar todas as posicoes livres
		free = []
		# Percorre todo o tabuleiro
		for x in range(self.board_size):
			for y in range(self.board_size):
				# Cria uma tupla com a posicao atual da varredura
				pos = (x,y)
				# Se a posicao atual da varredura nao estiver no set de posicoes do corpo da serpente
				if not pos in self.snake_set:
					# Adiciona a posicao na lista de posicoes livres
					free.append(pos)
					
		# Gera um indice aleatorio pra lista free, sorteando uma posicao livre
		self.apple = free[randrange(len(free))]
		# Poe a celula da maca vermelha
		self.board_canvas[self.apple]["color"].rgba = (1,0,0,1)
		
		radius = self.radius
		
		# Arredonda todas as bordas da celula da maca
		self.board_canvas[self.apple]["rect"].radius = [radius,radius,radius,radius]
	
	## Implementacao de algoritimo de setas com distancia euclidiana ##	
	def solver_direction(self):
			# Obtem as coordenadas da serpente e da maca no tabuleiro
			x, y = self.snake_deque[-1]
			apple_x, apple_y = self.apple
			# Obtem a lista de direcoes seguras para a coordenada atual da serpente
			directions = self.board_arrows[x][y]
			
			# Se soh tiver um unica direcao segura
			if len(directions) == 1:
				# Se movimentar a essa direcao
				self.move_direction(directions[0])
			# Se tiver duas
			else:
				# Cria uma variavel para armazenar a distancia do primeiro movimento ate a maca
				first_dist = -1
				# Lista de melhores direcoes sendo a primeira a melhor
				best_directions = []
				# Percorre as duas direcoes
				for d in directions:
					# Preve a proxima posicao de acordo a direcao atual do loop
					if d == Direction.RIGHT:
						next_pos = (x+1,y)
					elif d == Direction.LEFT:
						next_pos = (x-1,y)
					elif d == Direction.UP:
						next_pos = (x,y-1)
					elif d == Direction.DOWN:
						next_pos = (x,y+1)
					next_x, next_y = next_pos
					
					# Se a proxima posicao nao existir na lista com as celulas da serpente
					if next_pos not in self.snake_set or next_pos == self.snake_deque[0]:
						# Calcula a distancia ao quadrado
						dist = (next_x-apple_x)**2+(next_y-apple_y)**2
						# Se a primeira distancia nao foi definida
						if first_dist == -1:
							# Define a primeira distancia e poe a direcao atual do loop na lista de melhores direcoes
							first_dist = dist
							best_directions.append(d)
						# Se a primeira distancia ja foi definida
						else:
							# Se a distancia da direcao atual do loop for maior que a primeira distancia
							if dist > first_dist:
								# Adiciona a direcao atual do loop em segunda posicao
								best_directions.append(d)
							# Se as distancias forem iguais
							elif dist == first_dist:
								# Adiciona a direcao atual do loop em segunda posicao
								best_directions.append(d)
								# Embaralha a lista aleatoriamente
								random.shuffle(best_directions)
							# Se a distancia da direcao atual do loop for menor que a primeira distancia
							else:
								# Adiciona a direcao atual do loop em primeira posicao
								best_directions.insert(0, d)
								
				# Percorre a lista de melhores posicoes
				for d in best_directions:
					# Move a serpente e verifica se a direcao nova foi aceita (nao sera aceita se a mesma for oposta a direcao atual da serpente)
					if self.move_direction(d):
						# Se for aceita, quebra o loop for
						break
			
	
	# Aplica um movimento na serpente
	def move_snake(self, dt):
		# Verifica se o jogo acabou
		if self.game_over:
			# Para a serpente
			self.stop_game()
		# Se nao acabou
		else:
			# Obtem a posicao da cabeca da serpente
			pos = self.snake_deque[-1]
			
			# Se estiver em modo solver
			if self.solver:
				self.solver_direction()
			
			# Obtem a posicao seguinte da cabeca e a direcao oposta de acordo com o movimento
			match self.direction:
				case Direction.RIGHT:
					next_pos = (pos[0]+1, pos[1])
					self.oppositive_direction = Direction.LEFT
				case Direction.LEFT:
					next_pos = (pos[0]-1, pos[1])
					self.oppositive_direction = Direction.RIGHT
				case Direction.DOWN:
					next_pos = (pos[0], pos[1]+1)
					self.oppositive_direction = Direction.UP
				case Direction.UP:
					next_pos = (pos[0], pos[1]-1)
					self.oppositive_direction = Direction.DOWN
			
			# Obtem x e y da posicao seguinte
			x,y = next_pos
			
			# Verifica se a posicao seguinte saiu da tela ou se ha corpo da serpente la
			if x >= self.board_size or x < 0 or y >= self.board_size or y < 0 or (next_pos in self.snake_set and next_pos != self.snake_deque[0]):
				# O jogo acaba
				self.game_over = True
			else:
				# Move a serpente #
				
				
				# Aumenta a contagem de movimentos em 1 segundo
				self.moves_count += 1
				
				new_apple_commit = False
				
				# Se o proximo movimento nao for para a mesma posicao da maca
				if next_pos != self.apple:
					# Remove a primeira posicao do deque (a ultima celula do corpo da serpente, a calda da serpente) e obtem a posicao removida
					last = self.snake_deque.popleft()
					# Remove do set a posicao removida do deque
					self.snake_set.remove(last)
					# Poe a ultima celula do corpo da serpente como invisivel
					self.board_canvas[last]["color"].rgba = (0,0,0,0)
				elif not self.game_win:
					new_apple_commit = True
				else:
					# Remove a primeira posicao do deque (a ultima celula do corpo da serpente, a calda da serpente) e obtem a posicao removida
					last = self.snake_deque.popleft()
					# Remove do set a posicao removida do deque
					self.snake_set.remove(last)
					# Poe a ultima celula do corpo da serpente como invisivel
					self.board_canvas[last]["color"].rgba = (0,0,0,0)
				
				# Adiciona a posicao seguinte da cabeca no objeto deque e set
				self.snake_deque.append(next_pos)
				self.snake_set.add(next_pos)
				
				# Calcula o raio da borda
				radius = self.radius
				
				# Arredonda as bordas da cabeca de acordo com o movimento
				match self.direction:
					case Direction.RIGHT:
						self.board_canvas[next_pos]["rect"].radius = [0,radius,radius,0]
					case Direction.LEFT:
						self.board_canvas[next_pos]["rect"].radius = [radius,0,0,radius]
					case Direction.UP:
						self.board_canvas[next_pos]["rect"].radius = [radius,radius,0,0]
					case Direction.DOWN:
						self.board_canvas[next_pos]["rect"].radius = [0,0,radius,radius]
				
				# Poe a celula seguinte (posicao da nova cabeca) como visivel e de cor especifica
				self.board_canvas[next_pos]["color"].rgba = (0, 0.87, 0.584, 1)
					
				# Tira as bordas arredondadas da celula que no movimento passado era a cabeca
				self.board_canvas[pos]["rect"].radius = [0,0,0,0]
				# Obtem o x e y da posicao da antiga cabeca
				px, py = pos
					
				# Arredonda a borda entre duas faces se nao tiver celula de corpo ( que seja sucessora ou antecessora a celula que esta sendo avaliada) tocando ambas as faces da borda
				# Se nao 