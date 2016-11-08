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
		self.id 				= id
		self.config				= config
		self.id_supporters 		= [id * config.num_sup + i for i in range(1, config.num_sup+1)] if id * config.num_sup + 1 < config.num_agents else None
		self.id_leader			= int((id-1) / config.num_sup) if id > 0 else None
		self.pockets 			= [None for i in range(0, config.num_pockets)]
		self.leader_pockets		= [None for i in range(0, config.num_pockets)]
		self.supporter_pockets	= [[None for i in range(0, config.num_pockets)] for i in range(1, config.num_sup+1)] if self.id_supporters else None
		self.population_pockets	= [[None for i in range(0, config.num_pockets)] for i in range(1, config.num_agents)] if self.id_leader == None else None
		self.den_pockets		= 0
		self.den_subpopulation	= 0
		self.den_population 	= 0
		self.current 			= Solution(config, sequence)
		self.sequence			= sequence
		self.generation 		= 0
		self.restarts			= 0
		self.time_ls			= datetime.timedelta(0)
		self.time_send			= datetime.timedelta(0)
		self.time_receive		= datetime.timedelta(0)
		self.time_div			= datetime.timedelta(0)
		self.trx_send			= 0
		self.trx_receive		= 0
		self.status_log			= []
	
	def __str__(self):
		return  textwrap.dedent('''\
				Agent %d:
				--- leader: %s
				--- supporters: %s
				--- current_energy: %s
				--- pockets_energy: %s
				--- leader_pockets: %s
				--- den_pockets: %s
				--- den_subpopulation: %s
				--- den_population: %s''' % (
					self.id,
					str(self.id_leader),
					str(self.id_supporters),
					str(self.current),
					str(self.pockets),
					str(self.leader_pockets),
					str(self.den_pockets),
					str(self.den_subpopulation),
					str(self.den_population)
					)
				)
	
	def total_seconds(self, timedelta):
		return (timedelta.microseconds + 0.0 + (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) / 10 ** 6
	
	def status_log_append(self, time, energy_calls):
		self.status_log.append([str(self.pockets[0]), self.trx_send, self.trx_receive, self.total_seconds(self.time_send), self.total_seconds(self.time_receive),
								self.generation, self.restarts, self.total_seconds(self.time_ls), energy_calls, str(self.pockets[0].score), str(self.pockets[0].sasa),
								self.total_seconds(self.pockets[0].t_score), self.total_seconds(self.pockets[0].t_sasa), self.total_seconds(self.pockets[0].t_total), self.total_seconds(time),
								str(self.den_pockets), str(self.den_subpopulation), str(self.den_population), self.total_seconds(self.time_div)])
	
	def status_write(self, status_log_file_path):
		f = open(status_log_file_path, 'a')
		for line in self.status_log:
			for item in line:
				f.write(str(item) + '\t')
			f.write('\n')
		f.close()
	
	def diversity_old(self, agent_pocket_1, agent_pocket_2):
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
	
	def diversity(self, agent_pocket_1, agent_pocket_2):
		div = CA_rmsd(agent_pocket_1.pose, agent_pocket_2.pose, 3, len(agent_pocket_1.pose.sequence())-2)
		return div
	
	def mean(self, numbers):
		numbers_length = len(numbers)
		numbers_sum = 0
		
		if numbers_length > 0:
			for i in range(0, numbers_length):
				numbers_sum += float(numbers[i])

			numbers_mean = numbers_sum / numbers_length
			return numbers_mean
		else:
			return 0
	
	def std_dev(self, numbers):
		numbers_length = len(numbers)
		numbers_mean = self.mean(numbers)
		numbers_square_deviations = []
		
		if numbers_length > 0:
			for i in range(0, numbers_length):
				deviation = (numbers[i] - numbers_mean) ** 2
				numbers_square_deviations.append(deviation)

			numbers_variance = self.mean(numbers_square_deviations)
			numbers_std_dev = numbers_variance ** 0.5
			return numbers_std_dev
		else:
			return 0
		
	def calculate_densities(self):
		pockets_rmsd = []
		num_pockets = len(filter(lambda p: p!=None, self.pockets))
		
		for i in range(0, num_pockets):
			for j in range(i+1, num_pockets):
				rmsd = self.diversity(self.pockets[i], self.pockets[j])
				pockets_rmsd.append(rmsd)
		
		pockets_mean = self.mean(pockets_rmsd)
		pockets_std_dev = self.std_dev(pockets_rmsd)
		
		if pockets_mean > 0:
			self.den_pockets = pockets_std_dev / abs(pockets_mean)
		else:
			self.den_pockets = float(0)
		# print '\n> Agent %d calculate pockets density:\n>> Pockets: %s\n>> Pockets diversity: %s\n>> Pockets density: %s\n' % (self.id, filter(lambda p: p!=None, self.pockets), pockets_rmsd, self.den_pockets)
		
		if self.id_supporters:
			subpopulation_pockets = []
			subpopulation_pockets += filter(lambda p: p!=None, self.pockets)
			for i in range(0, self.config.num_sup):
				subpopulation_pockets += filter(lambda p: p!=None, self.supporter_pockets[i])
			
			subpopulation_rmsd = []
			num_pockets = len(subpopulation_pockets)
			
			for i in range(0, num_pockets):
				for j in range(i+1, num_pockets):
					rmsd = self.diversity(subpopulation_pockets[i], subpopulation_pockets[j])
					subpopulation_rmsd.append(rmsd)
			
			subpopulation_mean = self.mean(subpopulation_rmsd)
			subpopulation_std_dev = self.std_dev(subpopulation_rmsd)

			if subpopulation_mean > 0:
				self.den_subpopulation = subpopulation_std_dev / abs(subpopulation_mean)
			else:
				self.den_subpopulation = float(0)
			# print '\n> Agent %d calculate subpopulation density:\n>> Pockets: %s\n>> Pockets diversity: %s\n>> Subpopulation density: %s\n' % (self.id, subpopulation_pockets, subpopulation_rmsd, self.den_subpopulation)
		
		if self.id_leader == None:
			population_pockets = []
			population_pockets += filter(lambda p: p!=None, self.pockets)
			for i in range(0, self.config.num_agents-1):
				population_pockets += filter(lambda p: p!=None, self.population_pockets[i])
			
			population_rmsd = []
			num_pockets = len(population_pockets)
			
			for i in range(0, num_pockets):
				for j in range(i+1, num_pockets):
					rmsd = self.diversity(population_pockets[i], population_pockets[j])
					population_rmsd.append(rmsd)
			
			population_mean = self.mean(population_rmsd)
			population_std_dev = self.std_dev(population_rmsd)

			if population_mean > 0:
				self.den_population = population_std_dev / abs(population_mean)
			else:
				self.den_population = float(0)
			# print '\n> Agent %d calculate population density:\n>> Pockets: %s\n>> Pockets diversity: %s\n>> Population density: %s\n' % (self.id, population_pockets, population_rmsd, self.den_population)
	
	def update(self, solution = None):
		if solution == None:
			solution = self.current
		pocket_worst = -1
		div_flag = True
		div_worst = -1
		i = 0
		div_parameter = 2.0
		# div_parameter = len(solution.pose.sequence()) * 6.0
		for pocket in self.pockets:
			if pocket == None:
				if div_flag:
					pocket_worst = i
				break
			else:
				if solution.energy_value <= pocket.energy_value:
					div = self.diversity(solution, pocket)
				# Change introduced by Ivan and Mario on 1-04-2016 to fullfill replace rules. Updated by Ivan on 20-10-2016 to add diversity by RMSD and fix error in replacements
					if div >= div_parameter:
						if div_flag:
							pocket_worst = i
				#	elif div < div_parameter and div > 0:
					else:
						if div_flag:
							div_worst = div
							div_flag = False
							pocket_worst = i
						else:
							if div <= div_worst:
								div_worst = div
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
	
	def crossover(self, chromosome1, chromosome2, cross_prob):
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
	
	# Simulated Annealing original
	
	def simulated_annealing_old(self, ls_prob_ss, fact_ls, prob_jump, radius_jump, temp_init, hist):
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
					bit_start = -1.0
					bit_end = 1.0
					
					backup_phi = self.current.pose.phi(i+1)
					backup_psi = self.current.pose.psi(i+1)
					
					# phi
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
								self.current.energy_value = best_energy
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
								self.current.energy_value = best_energy
								psi = psi_ant
						else:
							psi = psi_ant
						temperature = temperature * fact_ls
					
					# chi angles
					backup_chi_list = [] # List of chi angles
					for k in range(self.current.pose.residue(i+1).nchi()):
						try:
							backup_chi_list.append(self.current.pose.chi(k+1, i+1))
						except:
							break;
					
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
												self.current.energy_value = best_energy
												control = 999
											else:
												if control < 0:
													chi_value = chi_ant
													self.current.pose.set_chi(n_chi+1, i+1, chi_value)
													self.current.energy_value = best_energy
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
											self.current.energy_value = best_energy
											chi_value = chi_ant
											control = 9991
									else:
										control = 9991
						except:
							break
	
	# Simulated Annealing that combines jumps to better neighbourhoods, phi & psi tunning at the same time and move radius to the new angles found.
	# Implementation of state and global best. State vary throughout execution to  maintain good exploration of the search space.
	
	def simulated_annealing(self, ls_prob_ss, fact_ls, prob_jump, radius_jump, temp_init, hist):
		# LS only in agent's self.current pocket
		for i in range (1, len(self.current.pose.sequence())):
			
			if (i+1) != len(self.current.pose.sequence()):
				name_res = self.current.pose.residue(i+1).name3()
				random.seed()
				
				if random.random() <= ls_prob_ss[self.sequence.secondary_sequence_list[i]]:
					random.seed()
					
					best_energy = self.current.energy_value
					energy_temp = best_energy
					
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
						phi = aa_angles[0] + self.current.pose.phi(i+1) - int(self.current.pose.phi(i+1))
						psi = aa_angles[1] + self.current.pose.psi(i+1) - int(self.current.pose.psi(i+1))
						
						# Manhattan distance
						int_x = abs(self.current.pose.phi(i+1) - phi)
						int_y = abs(self.current.pose.psi(i+1) - psi)
						if(int_x > int_y):
							distance = int_x
						else:
							distance = int_y
						
						if (distance < radius_jump) and (radius_jump > 1.0):
							
							phi_ant = copy.copy(phi)
							psi_ant = copy.copy(psi)
							
							self.current.pose.set_phi(i+1, phi)
							self.current.pose.set_psi(i+1, psi)
							self.current.calculate_energy()
							energy_temp = self.current.energy_value
							
							if energy_temp < best_energy:
								best_energy = energy_temp
							else:
								energy_temp = best_energy
								self.current.pose.set_phi(i+1, phi_ant)
								self.current.pose.set_psi(i+1, psi_ant)
								self.current.energy_value = energy_temp
					
					
					# phi & psi angles
					
					best_phi = copy.copy(self.current.pose.phi(i+1))
					best_psi = copy.copy(self.current.pose.psi(i+1))
					energy_state = best_energy
					
					bit_start = -0.5
					bit_end = 0.5
					
					if self.id_leader != None:
						temperature = temp_init
					else:
						temperature = temp_init * 2
					
					while(temperature > 0.1):
						bit = random.uniform(bit_start, bit_end)
						phi = self.current.pose.phi(i+1)
						phi_ant = copy.copy(phi) # Valor anterior de phi
						phi += bit
						
						bit = random.uniform(bit_start, bit_end)
						psi = self.current.pose.psi(i+1)
						psi_ant = copy.copy(psi) # Valor anterior de psi
						psi += bit
						
						# Alteracao temporaria
						self.current.pose.set_phi(i+1, phi)
						self.current.pose.set_psi(i+1, psi)
						self.current.calculate_energy()
						energy_temp = self.current.energy_value
							
						if(energy_temp < energy_state) or (random.random() <= exp((energy_state - energy_temp) / temperature)):
							energy_state = energy_temp
							
							if energy_state < best_energy:
								best_energy = energy_state
								best_phi = copy.copy(self.current.pose.phi(i+1))
								best_psi = copy.copy(self.current.pose.psi(i+1))
								
						else:
							self.current.pose.set_phi(i+1, phi_ant)
							self.current.pose.set_psi(i+1, psi_ant)
							self.current.energy_value = energy_state
							phi = phi_ant
							psi = psi_ant
						
						temperature = temperature * fact_ls
					
					# Update phi & psi with the best found in SA
					
					self.current.pose.set_phi(i+1, best_phi)
					self.current.pose.set_psi(i+1, best_psi)
					self.current.energy_value = best_energy
					
					# chi angles
					
					backup_chi_list = [] # List of chi angles
					for k in range(self.current.pose.residue(i+1).nchi()):
						try:
							backup_chi_list.append(self.current.pose.chi(k+1, i+1))
						except:
							break;
					
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
												self.current.energy_value = best_energy
												control = 999
											else:
												if control < 0:
													chi_value = chi_ant
													self.current.pose.set_chi(n_chi+1, i+1, chi_value)
													self.current.energy_value = best_energy
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
											self.current.energy_value = best_energy
											chi_value = chi_ant
											control = 9991
									else:
										control = 9991
						except:
							break
	
	# Simulated Annealing that combines jump to a new neighbourhood for iterations with radius > 1 and bit jump for iterations with radius < 1.
	
	def simulated_annealing_new(self, ls_prob_ss, fact_ls, prob_jump, radius_jump, temp_init, hist):
		# LS only in agent's self.current pocket
		for i in range (1, len(self.current.pose.sequence())):
			
			if (i+1) != len(self.current.pose.sequence()):
				name_res = self.current.pose.residue(i+1).name3()
				random.seed()
				
				if random.random() <= ls_prob_ss[self.sequence.secondary_sequence_list[i]]:
					best_phi = copy.copy(self.current.pose.phi(i+1))
					best_psi = copy.copy(self.current.pose.psi(i+1))
					
					best_energy = self.current.energy_value
					energy_state = best_energy
					energy_temp = best_energy
					
					current_radius = radius_jump
					bit_start = -0.5
					bit_end = 0.5
					
					if self.id_leader != None:
						temperature = temp_init
					else:
						temperature = temp_init * 2
					
					aa_angles = []
					random.seed()
					
					if (current_radius > 1.0):
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
						
					# phi & psi angles
					
					while(temperature > 0.1):
						
						if (current_radius > 1.0):
							phi = self.current.pose.phi(i+1)
							psi = self.current.pose.psi(i+1)
							phi_ant = copy.copy(phi)
							psi_ant = copy.copy(psi)

							aa_angles = hist.use_histogram(self.sequence.maxmin_angles[i], proba, proba2, name)

							# Baseado nos dados do histograma
							phi = aa_angles[0] + self.current.pose.phi(i+1) - int(self.current.pose.phi(i+1))
							psi = aa_angles[1] + self.current.pose.psi(i+1) - int(self.current.pose.psi(i+1))

							# Manhattan distance
							int_x = abs(self.current.pose.phi(i+1) - phi)
							int_y = abs(self.current.pose.psi(i+1) - psi)
							if(int_x > int_y):
								distance = int_x
							else:
								distance = int_y

							if (distance < current_radius):
								self.current.pose.set_phi(i+1, phi)
								self.current.pose.set_psi(i+1, psi)
								self.current.calculate_energy()
								energy_temp = self.current.energy_value
							
						else:
							bit = random.uniform(bit_start, bit_end)
							phi = self.current.pose.phi(i+1)
							phi_ant = copy.copy(phi) # Valor anterior de phi
							phi += bit

							bit = random.uniform(bit_start, bit_end)
							psi = self.current.pose.psi(i+1)
							psi_ant = copy.copy(psi) # Valor anterior de psi
							psi += bit

							# Alteracao temporaria
							self.current.pose.set_phi(i+1, phi)
							self.current.pose.set_psi(i+1, psi)
							self.current.calculate_energy()
							energy_temp = self.current.energy_value

						if(energy_temp < energy_state) or (random.random() <= exp((energy_state - energy_temp) / temperature)):
							energy_state = energy_temp

							if energy_state < best_energy:
								best_energy = energy_state
								best_phi = copy.copy(self.current.pose.phi(i+1))
								best_psi = copy.copy(self.current.pose.psi(i+1))

						else:
							self.current.pose.set_phi(i+1, phi_ant)
							self.current.pose.set_psi(i+1, psi_ant)
							self.current.energy_value = energy_state
							phi = phi_ant
							psi = psi_ant

						temperature = temperature * fact_ls
						current_radius = current_radius * 0.85
					
					# Update phi & psi with the best found in SA

					self.current.pose.set_phi(i+1, best_phi)
					self.current.pose.set_psi(i+1, best_psi)
					self.current.energy_value = best_energy

					# chi angles
					
					backup_chi_list = [] # List of chi angles
					for k in range(self.current.pose.residue(i+1).nchi()):
						try:
							backup_chi_list.append(self.current.pose.chi(k+1, i+1))
						except:
							break;

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
												self.current.energy_value = best_energy
												control = 999
											else:
												if control < 0:
													chi_value = chi_ant
													self.current.pose.set_chi(n_chi+1, i+1, chi_value)
													self.current.energy_value = best_energy
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
											self.current.energy_value = best_energy
											chi_value = chi_ant
											control = 9991
									else:
										control = 9991
						except:
							break
