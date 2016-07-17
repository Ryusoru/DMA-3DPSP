#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import copy
import random
import datetime
import textwrap
import itertools
import traceback
from math import *

from solution import *


class Agent:
	def __init__(self, id, config, sequence):
		self.id 			= id
		self.id_supporters 	= [id * config.num_sup + i for i in range(1, config.num_sup+1)] if id * config.num_sup + 1 < config.num_agents else None
		self.id_leader		= int((id-1) / config.num_sup) if id > 0 else None
		self.pockets 		= [None for i in range(0, config.num_pockets)]
		self.leader_pockets	= [None for i in range(0, config.num_pockets)]
		self.current 		= Solution(config, sequence)
		self.sequence		= sequence
		self.generation 	= 0
		self.restarts		= 0
		self.time_ls		= datetime.timedelta(0)
		self.time_send		= datetime.timedelta(0)
		self.time_receive	= datetime.timedelta(0)
		self.trx_send		= 0
		self.trx_receive	= 0
		self.status_log		= []
	
	def __str__(self):
		return  textwrap.dedent('''\
				Agent %d:
				--- leader: %s
				--- supporters: %s
				--- current_energy: %s
				--- pockets_energy: %s
				--- leader_pockets: %s''' % (
					self.id,
					str(self.id_leader),
					str(self.id_supporters),
					str(self.current),
					str(self.pockets),
					str(self.leader_pockets)
					)
				)
	
	def total_seconds(self, timedelta):
		return (timedelta.microseconds + 0.0 + (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) / 10 ** 6
	
	def status_log_append(self, time, energy_calls):
		self.status_log.append([str(self.pockets[0]), self.trx_send, self.trx_receive, self.total_seconds(self.time_send), self.total_seconds(self.time_receive),
								self.generation, self.restarts, self.total_seconds(self.time_ls), energy_calls, str(self.pockets[0].score), str(self.pockets[0].sasa),
								self.total_seconds(self.pockets[0].t_score), self.total_seconds(self.pockets[0].t_sasa), self.total_seconds(self.pockets[0].t_total), self.total_seconds(time)])
	
	def status_write(self, status_log_file_path):
		f = open(status_log_file_path, 'a')
		for line in self.status_log:
			for item in line:
				f.write(str(item) + '\t')
			f.write('\n')
		f.close()
	
	def diversity(self, agent_pocket_1, agent_pocket_2):
		# This function isnt considering the first and last residue
		aux = 0
		primary_len = len(agent_pocket_1.pose.sequence())
		
		for i in range(1, primary_len):
			if (i+1) != primary_len:
				# Avalia apenas os angulos phi e psi
				for j in range(2):
					if j == 0:
						# phi
						# print 'phi: %s,%s' % (agent_pocket_1.pose.phi(i+1), agent_pocket_2.pose.phi(i+1))
						diff = abs(agent_pocket_1.pose.phi(i+1) - agent_pocket_2.pose.phi(i+1))
						if diff > 180.0:
							diff = 360 - diff;
					else:
						# psi
						# print 'psi: %s,%s' % (agent_pocket_1.pose.psi(i+1), agent_pocket_2.pose.psi(i+1))
						diff = abs(agent_pocket_1.pose.psi(i+1) - agent_pocket_2.pose.psi(i+1))
						if diff > 180.0:
							diff = 360 - diff			
					aux += diff
		
		return aux / (primary_len - 2)
	
	def update(self, solution = None):
		if solution == None:
			solution = self.current
		pocket_worst = -1
		div_flag = True
		i = 0
		div_parameter = len(solution.pose.sequence()) * 6.0
		# div_parameter = 7
		for pocket in self.pockets:
			if pocket == None:
				if pocket_worst == -1 or div_flag:
					pocket_worst = i
				break
			else:
				if solution.energy_value <= pocket.energy_value:
					div = self.diversity(solution, pocket)
				# Change introduced by Ivan and Mario on 1-04-2016 to fullfill replace rules
					if div >= div_parameter and div_flag:
						pocket_worst = i
				#	elif div < div_parameter and div > 0:
					else:
						div_flag = False
						pocket_worst = i
				#	else:
				#		pocket_worst = -1
				#		break
				# End modification	
				# Error case: Agente lider rechaza soluciones de su supporter con mejor energía (794) que todos sus pockets (820)
				# Problem: en las condiciones, si se encuentra una solución similar y luego una diferente, se pierde la posición de la similar que se iba a actualizar
				# Solution: quitar la condición que elimina la posición del elemento similar
			i +=1
		
		if pocket_worst != -1:
			self.pockets[pocket_worst] = copy.deepcopy(solution)
			self.pockets.sort()
			# Update executed
			return True
		# Nothing to update
		return False
	
	def crossover_old(self, chromosome1, chromosome2, cross_prob):
		for i in range (len(chromosome1.pose.sequence())):
			random.seed()
			if random.random() <= cross_prob: # leader_agent
				phi = chromosome1.pose.phi(i+1)
				self.current.pose.set_phi(i+1, phi)
				psi = chromosome1.pose.psi(i+1)
				self.current.pose.set_psi(i+1, psi)
				omega = chromosome1.pose.omega(i+1)
				self.current.pose.set_omega(i+1, omega)
				# Set chi angles
				for k in range(self.current.pose.residue(i+1).nchi()):
					try:
						chi = chromosome1.pose.chi(k+1, i+1) 
						self.current.pose.set_chi(k+1, i+1, chi)
					except:
						break;
			
			else:
				phi = chromosome2.pose.phi(i+1)
				self.current.pose.set_phi(i+1, phi)
				psi = chromosome2.pose.psi(i+1)
				self.current.pose.set_psi(i+1, psi)
				omega = chromosome2.pose.omega(i+1)
				self.current.pose.set_omega(i+1, omega)
				# Set chi angles
				for k in range(self.current.pose.residue(i+1).nchi()):
					try:
						chi = chromosome2.pose.chi(k+1, i+1)
						self.current.pose.set_chi(k+1, i+1, chi)
					except:
						break;
		
		self.current.calculate_energy()
	
	def crossover_new(self, chromosome1, chromosome2, cross_prob):
		flag1 = True
		flag2 = True
		while(flag1 or flag2):
			flag1 = True
			flag2 = True
			for n in range(0, len(self.sequence.secondary_section_index), 2):
				random.seed()
				if random.random() <= cross_prob: # leader_agent
					for i in range(self.sequence.secondary_section_index[n], self.sequence.secondary_section_index[n+1] + 1):
						phi = chromosome1.pose.phi(i+1)
						self.current.pose.set_phi(i+1, phi)
						psi = chromosome1.pose.psi(i+1)
						self.current.pose.set_psi(i+1, psi)
						omega = chromosome1.pose.omega(i+1)
						self.current.pose.set_omega(i+1, omega)
						# Set chi angles
						for k in range(self.current.pose.residue(i+1).nchi()):
							try:
								chi = chromosome1.pose.chi(k+1, i+1) 
								self.current.pose.set_chi(k+1, i+1, chi)
							except:
								break;
					flag1 = False

				else:
					for i in range(self.sequence.secondary_section_index[n], self.sequence.secondary_section_index[n+1] + 1):
						phi = chromosome2.pose.phi(i+1)
						self.current.pose.set_phi(i+1, phi)
						psi = chromosome2.pose.psi(i+1)
						self.current.pose.set_psi(i+1, psi)
						omega = chromosome2.pose.omega(i+1)
						self.current.pose.set_omega(i+1, omega)
						# Set chi angles
						for k in range(self.current.pose.residue(i+1).nchi()):
							try:
								chi = chromosome2.pose.chi(k+1, i+1)
								self.current.pose.set_chi(k+1, i+1, chi)
							except:
								break;
					flag2 = False
		
		self.current.calculate_energy()
	
	def crossover_all(self, chromosome1, chromosome2):
		combinations = list(itertools.product([0,1], repeat = (len(self.sequence.secondary_section_index) / 2)))
		if(chromosome1.energy_value <= chromosome2.energy_value):
			best_energy = chromosome1.energy_value
		else:
			best_energy = chromosome2.energy_value
		position = -1
		
		for c in range(1, len(combinations)):
			for n in range(0, len(self.sequence.secondary_section_index), 2):
				if combinations[c][n/2] == 0: # leader_agent
					for i in range(self.sequence.secondary_section_index[n], self.sequence.secondary_section_index[n+1] + 1):
						phi = chromosome1.pose.phi(i+1)
						self.current.pose.set_phi(i+1, phi)
						psi = chromosome1.pose.psi(i+1)
						self.current.pose.set_psi(i+1, psi)
						omega = chromosome1.pose.omega(i+1)
						self.current.pose.set_omega(i+1, omega)
						# Set chi angles
						for k in range(self.current.pose.residue(i+1).nchi()):
							try:
								chi = chromosome1.pose.chi(k+1, i+1) 
								self.current.pose.set_chi(k+1, i+1, chi)
							except:
								break;

				else:
					for i in range(self.sequence.secondary_section_index[n], self.sequence.secondary_section_index[n+1] + 1):
						phi = chromosome2.pose.phi(i+1)
						self.current.pose.set_phi(i+1, phi)
						psi = chromosome2.pose.psi(i+1)
						self.current.pose.set_psi(i+1, psi)
						omega = chromosome2.pose.omega(i+1)
						self.current.pose.set_omega(i+1, omega)
						# Set chi angles
						for k in range(self.current.pose.residue(i+1).nchi()):
							try:
								chi = chromosome2.pose.chi(k+1, i+1)
								self.current.pose.set_chi(k+1, i+1, chi)
							except:
								break;
			
				self.current.calculate_energy()
				if self.current.energy_value <= best_energy:
					best_energy = self.current.energy_value
					position = c
		
		for n in range(0, len(self.sequence.secondary_section_index), 2):
			if combinations[position][n/2] == 0: # leader_agent
				for i in range(self.sequence.secondary_section_index[n], self.sequence.secondary_section_index[n+1] + 1):
					phi = chromosome1.pose.phi(i+1)
					self.current.pose.set_phi(i+1, phi)
					psi = chromosome1.pose.psi(i+1)
					self.current.pose.set_psi(i+1, psi)
					omega = chromosome1.pose.omega(i+1)
					self.current.pose.set_omega(i+1, omega)
					# Set chi angles
					for k in range(self.current.pose.residue(i+1).nchi()):
						try:
							chi = chromosome1.pose.chi(k+1, i+1) 
							self.current.pose.set_chi(k+1, i+1, chi)
						except:
							break;

			else:
				for i in range(self.sequence.secondary_section_index[n], self.sequence.secondary_section_index[n+1] + 1):
					phi = chromosome2.pose.phi(i+1)
					self.current.pose.set_phi(i+1, phi)
					psi = chromosome2.pose.psi(i+1)
					self.current.pose.set_psi(i+1, psi)
					omega = chromosome2.pose.omega(i+1)
					self.current.pose.set_omega(i+1, omega)
					# Set chi angles
					for k in range(self.current.pose.residue(i+1).nchi()):
						try:
							chi = chromosome2.pose.chi(k+1, i+1)
							self.current.pose.set_chi(k+1, i+1, chi)
						except:
							break;
			
		self.current.calculate_energy()
				
	
	def point_center(self, coord):
		int_aux = coord
		float_aux = int_aux
		if(int_aux > 0):
			float_aux = int_aux + 0.5
		
		if(int_aux < 0):
			float_aux = int_aux - 0.5
		
		return float_aux
	
	def simulated_annealing(self, ls_prob_ss, fact_ls, prob_jump, radius_jump, temp_init, hist):
		# LS only in agent's self.current pocket
		for i in range (1, len(self.current.pose.sequence())):
			
			if (i+1) != len(self.current.pose.sequence()):
				name_res = self.current.pose.residue(i+1).name3()
				random.seed()
				
				if random.random() <= ls_prob_ss[self.sequence.secondary_sequence_list[i]]:
					random.seed()
					
					if random.random() <= prob_jump:
						# JUMP
						aa_angles = []
						
						if hist.use_angle_range:
							# Use ranges of max and min angles
							aa_angles = [round(random.uniform(self.sequence.maxmin_angles[i][0], self.sequence.maxmin_angles[i][1]), floatprecision),  # PHI
										 round(random.uniform(self.sequence.maxmin_angles[i][2], self.sequence.maxmin_angles[i][3]), floatprecision),  # PSI
										 round(random.uniform(self.sequence.maxmin_angles[i][4], self.sequence.maxmin_angles[i][5]), floatprecision),  # CHI1
										 round(random.uniform(self.sequence.maxmin_angles[i][6], self.sequence.maxmin_angles[i][7]), floatprecision),  # CHI2
										 round(random.uniform(self.sequence.maxmin_angles[i][8], self.sequence.maxmin_angles[i][9]), floatprecision),  # CHI3
										 round(random.uniform(self.sequence.maxmin_angles[i][10], self.sequence.maxmin_angles[i][11]), floatprecision)]# CHI4
						else:
							# Use histogram
							try:
								AA_Ant = self.sequence.sigla[self.sequence.primary_amino_sequence[i-1]]
								AA = self.sequence.sigla[self.sequence.primary_amino_sequence[i]]
								AA_Prox = self.sequence.sigla[self.sequence.primary_amino_sequence[i+1]]
								SS_Ant = self.sequence.siglaSS[str(self.sequence.secondary_sequence_list[i-1])]
								SS = self.sequence.siglaSS[str(self.sequence.secondary_sequence_list[i])]
								SS_Prox = self.sequence.siglaSS[str(self.sequence.secondary_sequence_list[i+1])]
							
							except:
								print('ERROR')
								traceback.print_exc()
								sys.exit('Error getting the angles in local search')
							
							proba = []
							proba2 = []
							name = ''
							try:
								proba = hist.prob_hist[AA_Ant+SS_Ant+AA+SS+AA_Prox+SS_Prox]
								proba2 = hist.prob_hist[self.sequence.primary_amino_sequence[i-1]][self.sequence.secondary_sequence_list[i]]
								name = AA_Ant+SS_Ant+AA+SS+AA_Prox+SS_Prox
							except:
								try:
									# 50% for each combination
									if (random.randint(1, 10) <= 5):
										proba = hist.prob_hist[AA_Ant+SS_Ant+AA+SS]
										proba2 = hist.prob_hist[self.sequence.primary_amino_sequence[i-1]][self.sequence.secondary_sequence_list[i]]
										name = AA_Ant+SS_Ant+AA+SS
									else:
										proba = hist.prob_hist[AA+SS+AA_Prox+SS_Prox]
										proba2 = hist.prob_hist[self.sequence.primary_amino_sequence[i-1]][self.sequence.secondary_sequence_list[i]]
										name = AA+SS+AA_Prox+SS_Prox
								except:
									proba = hist.prob_hist[self.sequence.primary_amino_sequence[i-1]][self.sequence.secondary_sequence_list[i]]
									name = AA+SS
							
							aa_angles = hist.use_histogram(self.sequence.maxmin_angles[i], proba, proba2, name)
						
						# Baseado nos dados do histograma
						phi = aa_angles[0] + random.random()	
						psi = aa_angles[1] + random.random()	
						
						# Manhattan distance
						int_x = abs(self.current.pose.phi(i+1) - phi)
						int_y = abs(self.current.pose.psi(i+1) - psi)
						if(int_x > int_y):
							distance = int_x
						else:
							distance = int_y
						
						if (distance < radius_jump) and (radius_jump > 1.0):	
							
							self.current.pose.set_phi(i+1, phi)
							self.current.pose.set_psi(i+1, psi)
							self.current.calculate_energy()
					
					best_energy = self.current.energy_value
					energy_temp = best_energy
					
					backup_phi = self.current.pose.phi(i+1)
					backup_psi = self.current.pose.psi(i+1)
					backup_chi_list = [] # List of chi angles
					for k in range(self.current.pose.residue(i+1).nchi()):
						try:
							backup_chi_list.append(self.current.pose.chi(k+1, i+1))
						except:
							break;
					
					# phi
					bit_start = -1.0
					bit_end = 1.0
					
					if self.id_leader != None:
						temperature = temp_init
					else:
						temperature = temp_init * 2
					
					while(temperature > 0.1):
						bit = random.uniform(bit_start, bit_end)
						phi = self.current.pose.phi(i+1)
						phi_ant = copy.copy(phi) # Valor anterior de phi
						
						phi += bit
						if (phi > self.point_center(backup_phi) - 0.5) and (phi < self.point_center(backup_phi) + 0.5):
							# Alteracao temporaria
							self.current.pose.set_phi(i+1, phi)
							self.current.calculate_energy()
							energy_temp = self.current.energy_value
							
							if(energy_temp < best_energy) or (random.random() <= exp((best_energy - energy_temp) / temperature)):
								best_energy = energy_temp
							else:
								self.current.pose.set_phi(i+1, phi_ant)
								self.current.calculate_energy()
								phi = phi_ant
						else:
							phi = phi_ant
						temperature = temperature * fact_ls
					
					# psi
					if self.id_leader != None:
						temperature = temp_init
					else:
						temperature = temp_init * 2
					
					while(temperature > 0.1):
						bit = random.uniform(bit_start, bit_end)
						psi = self.current.pose.psi(i+1)
						psi_ant = copy.copy(psi) # Valor anterior de psi
						
						psi += bit
						if (psi > self.point_center(backup_psi) - 0.5) and (psi < self.point_center(backup_psi) + 0.5):
							# Alteracao temporaria
							self.current.pose.set_psi(i+1, psi)
							self.current.calculate_energy()
							energy_temp = self.current.energy_value
							
							if(energy_temp < best_energy) or (random.random() <= exp((best_energy - energy_temp) / temperature)):
								best_energy = energy_temp
							else:
								self.current.pose.set_psi(i+1, psi_ant)
								self.current.calculate_energy()
								psi = psi_ant
						else:
							psi = psi_ant
						temperature = temperature * fact_ls
					
					# chi angles
					for n_chi in range(self.current.pose.residue(i+1).nchi()):
						try:
							control = 0
							best_energy = self.current.energy_value
							energy_temp = best_energy
							
							while(control != 9991):
								bit = random.random()
								chi_value = self.current.pose.chi(n_chi+1, i+1)
								chi_ant = copy.copy(chi_value)
								
								if (control <= 0):
									chi_value += bit
									if (chi_value > hist.min_rot_chi(name_res, n_chi+1)) and (chi_value < hist.max_rot_chi(name_res, n_chi+1)):
										self.current.pose.set_chi(n_chi+1, i+1, chi_value)
										self.current.calculate_energy()
										energy_temp = self.current.energy_value
										if energy_temp < best_energy:
											best_energy = energy_temp
											control -= 1
										else:
											if control == 0:
												chi_value = backup_chi_list[n_chi]
												self.current.pose.set_chi(n_chi+1, i+1, chi_value)
												self.current.calculate_energy()
												control = 999
											else:
												if control < 0:
													chi_value = chi_ant
													self.current.pose.set_chi(n_chi+1, i+1, chi_value)
													self.current.calculate_energy()
													control = 9991
									else:
										control = 999
								
								if (control == 999):
									chi_value = chi_ant
									chi_value -= bit
									if (chi_value > hist.min_rot_chi(name_res, n_chi+1)) and (chi_value < hist.max_rot_chi(name_res, n_chi+1)):
										self.current.pose.set_chi(n_chi+1, i+1, chi_value)
										self.current.calculate_energy()
										energy_temp = self.current.energy_value
										if energy_temp < best_energy:
											best_energy = energy_temp
										
										else:
											self.current.pose.set_chi(n_chi+1, i+1, chi_ant)
											self.current.calculate_energy()
											chi_value = chi_ant
											control = 9991
									else:
										control = 9991
						except:
							break
	