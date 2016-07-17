#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import copy
import datetime
import textwrap
import traceback
from rosetta import *

scorefxn = None


class Solution:
	def __init__(self, config, sequence, pose = None):
		if pose == None:
			global scorefxn
			scorefxn = create_score_function('talaris2013')
			
			self.score_weight = 100
			self.sasa_weight = 100
			self.sequence = sequence
			self.generate_random_solution = False
			self.pose = Pose()
			self.energy_value = None
			self.score = None
			self.sasa = None
			self.t_score = datetime.timedelta(0)
			self.t_sasa = datetime.timedelta(0)
			self.t_total = datetime.timedelta(0)
			self.energy_calls = 0
		else:
			self.pose = copy.deepcopy(pose)
			self.calculate_energy()
	
	def __str__(self):
		return textwrap.dedent('%s' % (str(self.energy_value)))
	
	def __repr__(self):
		return textwrap.dedent('%s' % (str(self.energy_value)))
	
	# Possible unused function
	def __cmp__(self, other):
		if other == None or other.energy_value > self.energy_value:
			return -1
		elif other.energy_value == self.energy_value:
			return 0
		elif other.energy_value < self.energy_value:
			return 1
	
	def calculate_energy_old(self):
		self.energy_value = scorefxn(self.pose)
		self.energy_calls += 1
	
	def set_scores(self, score, sasa):
		self.score_weight = score
		self.sasa_weight = sasa
		
	def calculate_energy(self):
		t_total_start = datetime.datetime.now()
		
		if self.sasa_weight == 0:
			self.energy_value = scorefxn(self.pose)
		elif self.score_weight == 0:
			self.energy_value = calc_total_sasa(self.pose, 1.5)
		else:
			t_score_start = datetime.datetime.now()
			score = scorefxn(self.pose) #talaris
			self.t_score = datetime.datetime.now() - t_score_start
		
			t_sasa_start = datetime.datetime.now()
			sasa = (calc_total_sasa(self.pose, 1.5)) #solvent-accessible surface area term
			self.t_sasa = datetime.datetime.now() - t_sasa_start
		
			self.energy_value = (score * self.score_weight + sasa * self.sasa_weight) / 100
			self.score = score
			self.sasa = sasa
		
		self.energy_calls += 1
		
		self.t_total = datetime.datetime.now() - t_total_start
	
	def init_solution(self, hist):
		self.pose = Pose()
		self.pose = pose_from_sequence(self.sequence.primary_amino_sequence, 'fa_standard')
		self.generate_first_angles(hist)
		self.calculate_energy()
	
	def generate_first_angles(self, hist):
		if self.generate_random_solution:
			random.seed()
			
			# First psi
			psi = random.uniform(-180,180)
			self.pose.set_psi(1, psi)
			self.pose.set_phi(1, 0)
			self.pose.set_omega(1, 180)
			
			for k in range(self.pose.residue(1).nchi()):
				chi = random.uniform(-180, 180)
				self.pose.set_chi(k+1, 1, chi)
			
			for i in range(1, len(self.pose.sequence())):
				if (i+1) == len(self.pose.sequence()):
					break
				
				# The other aminos
				phi = random.uniform(-180, 180)
				self.pose.set_phi(i+1, phi)
				psi = random.uniform(-180, 180)
				self.pose.set_psi(i+1, psi)
				self.pose.set_omega(1, 180)
				
				# Set chi angles			
				for k in range(self.pose.residue(i+1).nchi()):
					chi = random.uniform(-180, 180)
					self.pose.set_chi(k+1, i+1, chi)
			
			# Last phi
			phi = random.uniform(-180, 180)
			self.pose.set_phi(len(self.pose.sequence()), phi)
			self.pose.set_psi(len(self.pose.sequence()), 0)
			self.pose.set_omega(len(self.pose.sequence()), 180)
			
			for k in range(self.pose.residue(len(self.pose.sequence())).nchi()):
				chi = random.uniform(-180, 180)
				self.pose.set_chi(k+1, len(self.pose.sequence()), chi)
		
		else:
			#Histogram based solutions
			i = 0
			aa_angles = []
			angles = []
			
			for aminoacid in self.sequence.primary_amino_sequence:
				if (i != 0) and (i != len(self.sequence.primary_amino_sequence) - 1):
					
					if hist.use_angle_range: #false
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
							sys.exit('Error getting the first angles')
						
						proba = []
						proba2 = []
						name = ''
						try:
							proba = hist.prob_hist[AA_Ant+SS_Ant+AA+SS+AA_Prox+SS_Prox]
							proba2 = hist.prob_hist[aminoacid][self.sequence.secondary_sequence_list[i]]
							name = AA_Ant+SS_Ant+AA+SS+AA_Prox+SS_Prox
						
						except:
							try:
								# #50% for each combination
								if (random.randint(1, 10) <= 5):
									proba = hist.prob_hist[AA_Ant+SS_Ant+AA+SS]
									proba2 = hist.prob_hist[aminoacid][self.sequence.secondary_sequence_list[i]]
									name = AA_Ant+SS_Ant+AA+SS
								else:
									proba = hist.prob_hist[AA+SS+AA_Prox+SS_Prox]
									proba2 = hist.prob_hist[aminoacid][self.sequence.secondary_sequence_list[i]]
									name = AA+SS+AA_Prox+SS_Prox
							except:
								proba = hist.prob_hist[aminoacid][self.sequence.secondary_sequence_list[i]]
								name = AA+SS
						
						aa_angles = hist.use_histogram(self.sequence.maxmin_angles[i], proba, proba2, name)
				else:
					proba = hist.prob_hist[aminoacid][self.sequence.secondary_sequence_list[i]]
					aa_angles = hist.use_histogram(self.sequence.maxmin_angles[i], proba, [], str(self.sequence.sigla[self.sequence.primary_amino_sequence[i]]) + str(self.sequence.siglaSS[str(self.sequence.secondary_sequence_list[i])]))
				
				angles.append(copy.deepcopy(aa_angles))
				i += 1
			
			# First amino
			self.pose.set_phi(1, 0) # Indiferente
			self.pose.set_psi(1, angles[0][1])
			self.pose.set_omega(1, angles[0][2])
			for kk in range(1, self.pose.residue(1).nchi() + 1):
				try:
					self.pose.set_chi(kk, 1, angles[0][2+kk])
				except:
					break;
			
			i = 1
			for aminoacid in self.sequence.primary_amino_sequence:
				try:
					if (i+1) == len(self.pose.sequence()):
						# Last amino
						self.pose.set_phi(i+1, angles[i][0])
						self.pose.set_psi(i+1, 0) # Indiferente
						self.pose.set_omega(i+1, angles[i][2])
						for kk in range(1, self.pose.residue(i+1).nchi() + 1):
							try:
								self.pose.set_chi(kk, i+1, angles[i][2+kk])
							except:
								break;
						break;
					
					# The other aminos
					self.pose.set_phi(i+1, angles[i][0])
					self.pose.set_psi(i+1, angles[i][1])
					self.pose.set_omega(i+1, angles[i][2])
					for kk in range(1, self.pose.residue(i+1).nchi() + 1):
						try:
							self.pose.set_chi(kk, i+1, angles[i][2+kk])
						except:
							break;
					
					i += 1
				except:
					print('ERROR')
					traceback.print_exc()
					print('Line '+'- Error while creating geometry structure - Index '+str(i))
