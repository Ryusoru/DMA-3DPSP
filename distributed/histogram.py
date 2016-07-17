#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import random
import string
import traceback


class HistogramFiles:
	def __init__(self, sequence, error, use_angle_range, prob_radius, histograms_path):
		self.sequence = sequence
		self.error = error
		self.float_precision = 2
		self.use_angle_range = use_angle_range
		self.prob_radius = prob_radius
		self.histograms_path = histograms_path
		
		# Amino constants
		self.GLY = 'G'
		self.ALA = 'A'
		self.PRO = 'P'
		self.SER = 'S'
		self.CYS = 'C'
		self.THR = 'T'
		self.VAL = 'V'
		self.ILE = 'I'
		self.LEU = 'L'
		self.ASP = 'D'
		self.ASN = 'N'
		self.HIS = 'H'
		self.PHE = 'F'
		self.TYR = 'Y'
		self.TRP = 'W'
		self.MET = 'M'
		self.GLU = 'E'
		self.GLN = 'Q'
		self.LYS = 'K'
		self.ARG = 'R'
		self.ASX = 'ASX'
		self.UNK = 'UNK'
		self.GLX = 'GLX'
		
		self.histogram = {self.ALA:[], self.ARG:[], self.ASN:[], self.ASP:[], self.ASX:[],
						  self.CYS:[], self.GLN:[], self.GLU:[], self.GLX:[], self.GLY:[],
						  self.HIS:[], self.ILE:[], self.LEU:[], self.LYS:[], self.MET:[],
						  self.PHE:[], self.PRO:[], self.SER:[], self.THR:[], self.TRP:[],
						  self.TYR:[], self.UNK:[], self.VAL:[]}
		
		self.prob_hist = {self.ALA:[], self.ARG:[], self.ASN:[], self.ASP:[], self.ASX:[],
						  self.CYS:[], self.GLN:[], self.GLU:[], self.GLX:[], self.GLY:[],
						  self.HIS:[], self.ILE:[], self.LEU:[], self.LYS:[], self.MET:[],
						  self.PHE:[], self.PRO:[], self.SER:[], self.THR:[], self.TRP:[],
						  self.TYR:[], self.UNK:[], self.VAL:[]}
		
		# Define files names
		name = ''
		for key in self.histogram:
			for ss in ['B', 'C', 'E', 'G', 'H', 'I', 'T']:
				if key == self.GLY:
					name = 'GLY'
				elif key == self.ALA:
					name = 'ALA'
				elif key == self.PRO:
					name = 'PRO'
				elif key == self.SER:
					name = 'SER'
				elif key == self.CYS:
					name = 'CYS'
				elif key == self.THR:
					name = 'THR'
				elif key == self.VAL:
					name = 'VAL'
				elif key == self.ILE:
					name = 'ILE'
				elif key == self.LEU:
					name = 'LEU'
				elif key == self.ASP:
					name = 'ASP'
				elif key == self.ASN:
					name = 'ASN'
				elif key == self.HIS:
					name = 'HIS'
				elif key == self.PHE:
					name = 'PHE'
				elif key == self.TYR:
					name = 'TYR'
				elif key == self.TRP:
					name = 'TRP'
				elif key == self.MET:
					name = 'MET'
				elif key == self.GLU:
					name = 'GLU'
				elif key == self.GLN:
					name = 'GLN'
				elif key == self.LYS:
					name = 'LYS'
				elif key == self.ARG:
					name = 'ARG'
				self.histogram[key].append(name+'_'+ss+'_histogram'+'.dat')
		
		# Probs list		
		for key in self.prob_hist:
			for ss in ['B', 'C', 'E', 'G', 'H', 'I', 'T']:
				self.prob_hist[key].append([])
	
	
	def histogram3_read(self, hist_file, aminoacid, flag1, flag2, AA_Ant, SS_Ant, AA, SS, AA_Prox, SS_Prox):
		hist_line = hist_file.readline()
		
		while (hist_line):
			if(hist_line.startswith('#') or hist_line.strip() == ''):
				hist_line = hist_file.readline()
				continue
			hist_data = string.split(hist_line)
			try:
				hist_phi = float(hist_data[0])
				hist_psi = float(hist_data[1])
				hist_prob = float(hist_data[2])
			except:
				print('ERROR')
				traceback.print_exc()
				sys.exit(self.error.ERROR_CODE_incompletefile + ' ' + self.histogram[aminoacid][self.sequence.secondary_sequence_list[i]])
			try:
				if (hist_prob != 0.0):
					if flag1 and flag2:
						try:
							self.prob_hist[AA_Ant+SS_Ant+AA+SS+AA_Prox+SS_Prox].append((hist_phi, hist_psi, hist_prob))
						except:
							self.prob_hist[AA_Ant+SS_Ant+AA+SS+AA_Prox+SS_Prox] = []
							self.prob_hist[AA_Ant+SS_Ant+AA+SS+AA_Prox+SS_Prox].append((hist_phi, hist_psi, hist_prob))
					
					elif (not flag1 or not flag2):
						try:
							self.prob_hist[AA_Ant+SS_Ant+AA+SS].append((hist_phi, hist_psi, hist_prob))
						except:
							self.prob_hist[AA_Ant+SS_Ant+AA+SS] = []
							self.prob_hist[AA_Ant+SS_Ant+AA+SS].append((hist_phi, hist_psi, hist_prob))
						try:
							self.prob_hist[AA+SS+AA_Prox+SS_Prox].append((hist_phi, hist_psi, hist_prob))
						except:
							self.prob_hist[AA+SS+AA_Prox+SS_Prox] = []
							self.prob_hist[AA+SS+AA_Prox+SS_Prox].append((hist_phi, hist_psi, hist_prob))
			except:
				print('ERROR')
				traceback.print_exc()
				sys.exit('Line ' + ': ' + 'Failed while loading data from histogram: ' + aminoacid + ' ' + self.sequence.secondary_amino_sequence[i])
			
			hist_line = hist_file.readline()
	
	def read_histograms(self):
		i = 0
		# Gets the angles from 'Histogramas/PhiPsi1-1'
		while (i < len(self.sequence.primary_amino_sequence)):
			try:
				print 'Opening ' + str(self.histogram[self.sequence.primary_amino_sequence[i]][self.sequence.secondary_sequence_list[i]])
				hist_file = open(str(self.histograms_path + '/PhiPsi1-1/') + self.histogram[self.sequence.primary_amino_sequence[i]][self.sequence.secondary_sequence_list[i]])
			except:
				print('ERROR')
				sys.exit(self.error.ERROR_CODE_fileopening + self.histogram[self.sequence.primary_amino_sequence[i]][self.sequence.secondary_sequence_list[i]])
			
			hist_line = hist_file.readline()
			while (hist_line):
				if(hist_line.startswith('#') or hist_line.strip() == ''):
					hist_line = hist_file.readline()
					continue
				hist_data = re.findall('\[[^\]]*\]|\{[^}}]*\}|\'[^\']*\'|\S+', hist_line)
				
				try:
					#read the angles values
					hist_phi = float(hist_data[0])
					hist_psi = float(hist_data[1])
					hist_prob = float(hist_data[2])
					hist_omega = ''
					hist_chi1 = ''
					hist_chi2 = ''
					hist_chi3 = ''
					hist_chi4 = ''
					num_chi = -1
					if len(hist_data) == 8:
						hist_omega = str(hist_data[3][1:-1])
						hist_chi1 = str(hist_data[4][1:-1])
						hist_chi2 = str(hist_data[5][1:-1])
						hist_chi3 = str(hist_data[6][1:-1])
						hist_chi4 = str(hist_data[7][1:-1])
						num_chi = 4
					elif len(hist_data) == 7:
						hist_omega = str(hist_data[3][1:-1])
						hist_chi1 = str(hist_data[4][1:-1])
						hist_chi2 = str(hist_data[5][1:-1])
						hist_chi3 = str(hist_data[6][1:-1])
						num_chi = 3
					elif len(hist_data) == 6:
						hist_omega = str(hist_data[3][1:-1])
						hist_chi1 = str(hist_data[4][1:-1])
						hist_chi2 = str(hist_data[5][1:-1])
						num_chi = 2
					elif len(hist_data) == 5:
						hist_omega = str(hist_data[3][1:-1])
						hist_chi1 = str(hist_data[4][1:-1])
						num_chi = 1
					elif len(hist_data) == 4:
						hist_omega = str(hist_data[3][1:-1])
						num_chi = 0	
								
				except:
					print('ERROR')
					sys.exit(self.error.ERROR_CODE_incompletefile + ' ' + self.histogram[self.sequence.primary_amino_sequence[i]][self.sequence.secondary_sequence_list[i]] + ' ' + str(hist_data))
				
				try:
					if (hist_prob != 0.0):
						if num_chi == -1:
							self.prob_hist[self.sequence.primary_amino_sequence[i]][self.sequence.secondary_sequence_list[i]].append((hist_phi, hist_psi, hist_prob))
						elif num_chi == 0:
							self.prob_hist[self.sequence.primary_amino_sequence[i]][self.sequence.secondary_sequence_list[i]].append((hist_phi, hist_psi, hist_prob, hist_omega))
						elif num_chi == 1:
							self.prob_hist[self.sequence.primary_amino_sequence[i]][self.sequence.secondary_sequence_list[i]].append((hist_phi, hist_psi, hist_prob, hist_omega, hist_chi1))
						elif num_chi == 2:
							self.prob_hist[self.sequence.primary_amino_sequence[i]][self.sequence.secondary_sequence_list[i]].append((hist_phi, hist_psi, hist_prob, hist_omega, hist_chi1, hist_chi2))
						elif num_chi == 3:
							self.prob_hist[self.sequence.primary_amino_sequence[i]][self.sequence.secondary_sequence_list[i]].append((hist_phi, hist_psi, hist_prob, hist_omega, hist_chi1, hist_chi2, hist_chi3))
						elif num_chi == 4:
							self.prob_hist[self.sequence.primary_amino_sequence[i]][self.sequence.secondary_sequence_list[i]].append((hist_phi, hist_psi, hist_prob, hist_omega, hist_chi1, hist_chi2, hist_chi3, hist_chi4))																		
				except:
					print('ERROR')
					sys.exit('Line ' + ': ' + 'Failed while loading data from histogram: ' + self.sequence.primary_amino_sequence[i] + ' ' + self.sequence.secondary_amino_sequence[i])
				
				hist_line = hist_file.readline()
			
 			# Sort the prob list from the most probably to the less
			self.prob_hist[self.sequence.primary_amino_sequence[i]][self.sequence.secondary_sequence_list[i]].sort(key = lambda x: x[2], reverse = True)
			
			try:
				hist_file.close()
			except:
				print('ERROR')
				sys.exit(self.error.ERROR_CODE_fileclosing + self.histogram[self.sequence.primary_amino_sequence[i]][self.sequence.secondary_sequence_list[i]])
			
			i += 1
		
		i = 0
		# Gets the angles from 'Histogramas/HistogramasFinal', 'Histogramas/FinalDuploVai' and 'Histogramas/FinalDuploVolta'
		for aminoacid in self.sequence.primary_amino_sequence:
			if i == 0 or i == len(self.sequence.primary_amino_sequence)-1: 
				# Jump the first and last residue
				i += 1 
				continue
			else:
				flag3Hist = True
				flag3Hist2 = True
				flag3Hist3 = True
				hist_file1 = ''
				hist_file2 = ''
				try:
					AA_Ant = self.sequence.sigla[self.sequence.primary_amino_sequence[i-1]]
					AA = self.sequence.sigla[self.sequence.primary_amino_sequence[i]]
					AA_Prox = self.sequence.sigla[self.sequence.primary_amino_sequence[i+1]]
					
					SS_Ant = self.sequence.siglaSS[str(self.sequence.secondary_sequence_list[i-1])]
					SS = self.sequence.siglaSS[str(self.sequence.secondary_sequence_list[i])]
					SS_Prox = self.sequence.siglaSS[str(self.sequence.secondary_sequence_list[i+1])]
								
					try:
						hist_file = open(str(self.histograms_path + '/HistogramasFinal/') + str(AA_Ant+SS_Ant+AA+SS+AA_Prox+SS_Prox).lower() + '_histogram.dat', 'r')
						print 'Opening ' + str(AA_Ant+SS_Ant+AA+SS+AA_Prox+SS_Prox).lower() + '_histogram.dat'
					
					except:
						try:
							hist_file1 = open(str(self.histograms_path + '/FinalDuploVai/') + str(AA_Ant+SS_Ant+AA+SS).lower() + '_histogram.dat', 'r')
							print 'Opening ' + str(AA_Ant+SS_Ant+AA+SS).lower() + '_histogram.dat'
							flag3Hist2 = False
							hist_file1.close()
							
							hist_file2 = open(str(self.histograms_path + '/FinalDuploVolta/') + str(AA+SS+AA_Prox+SS_Prox).lower() + '_histogram.dat', 'r')
							print 'Opening ' + str(AA+SS+AA_Prox+SS_Prox).lower() + '_histogram.dat'
							flag3Hist3 = False
							hist_file2.close()
						except:
							flag3Hist = False
				
				except:
					print('ERROR')
					traceback.print_exc()
				
				if flag3Hist:
					if hist_file1 != '' and hist_file2 != '':
						# Histograma Duplo Vai
						hist_file1 = open(str(self.histograms_path + '/FinalDuploVai/') + str(AA_Ant+SS_Ant+AA+SS).lower() + '_histogram.dat', 'r')
						hist_file = hist_file1
						self.histogram3_read(hist_file, aminoacid, flag3Hist2, flag3Hist3, AA_Ant, SS_Ant, AA, SS, AA_Prox, SS_Prox)
						
						# Histograma Duplo Volta
						hist_file2 = open(str(self.histograms_path + '/FinalDuploVolta/') + str(AA+SS+AA_Prox+SS_Prox).lower() + '_histogram.dat', 'r')
						hist_file = hist_file2
						self.histogram3_read(hist_file, aminoacid, flag3Hist2, flag3Hist3, AA_Ant, SS_Ant, AA, SS, AA_Prox, SS_Prox)
					
					else:
						# Histograma Final
						self.histogram3_read(hist_file, aminoacid, flag3Hist2, flag3Hist3, AA_Ant, SS_Ant, AA, SS, AA_Prox, SS_Prox)
					
					if flag3Hist2 and flag3Hist3:
						self.prob_hist[AA_Ant+SS_Ant+AA+SS+AA_Prox+SS_Prox].sort(key = lambda x: x[2], reverse = True) # Sort the prob list from the most probably to the less
					elif (not flag3Hist2 or not flag3Hist3):
						self.prob_hist[AA_Ant+SS_Ant+AA+SS].sort(key = lambda x: x[2], reverse = True)
						self.prob_hist[AA+SS+AA_Prox+SS_Prox].sort(key = lambda x: x[2], reverse = True)
					
					try:
						hist_file.close()
					except:
						try:
							hist_file1.close()
							hist_file2.close()
						except:
							print('ERROR')
							traceback.print_exc()
							sys.exit(self.error.ERROR_CODE_fileclosing+'Error 2')
				
				i += 1
		
		if self.use_angle_range == False:
			i = 0
			for aminoacid in self.sequence.primary_amino_sequence:
				# Palliative measure for the local search when using probabilities instead of defined angle ranges
				if(hist_phi == -180.0):
					p_phi_min = hist_phi
				else:
					p_phi_min = hist_phi - self.prob_radius
				if(hist_phi == 180.0):
					p_phi_max = hist_phi
				else:
					p_phi_max = hist_phi + self.prob_radius
				# Adjust the psi range borders, can't be greater than 180 or smaller than -180
				if(hist_psi == -180.0):
					p_psi_min = hist_psi
				else:
					p_psi_min = hist_psi - self.prob_radius
				if(hist_psi == 180.0):
					p_psi_max = hist_psi
				else:
					p_psi_max = hist_psi + self.prob_radius

				self.sequence.maxmin_angles[i][0] = -180.0
				self.sequence.maxmin_angles[i][1] = 180.0
				self.sequence.maxmin_angles[i][2] = -180.0
				self.sequence.maxmin_angles[i][3] = 180.0
				
				i += 1
	
	def get_angle_chis(self, probs):
		angles = []
		for i in range(3, len(probs)):
			aux = probs[i]
			anglesc = re.findall(r'[^[]*\[([^]]*)\]', aux)
			x1 = random.randint(0, len(anglesc) - 1)
			x2 = random.randint(0, len(anglesc[x1].split(', ')) - 1)
			angle = float(anglesc[x1].split(', ')[x2])
			p_chi_min = angle - self.prob_radius
			p_chi_min = -180.0 if p_chi_min < -180.0 else 180.0 if p_chi_min > 180.0 else p_chi_min
			p_chi_max = angle + self.prob_radius
			p_chi_max = -180.0 if p_chi_max < -180.0 else 180.0 if p_chi_max > 180.0 else p_chi_max
			if i == 3:
				angles.append(angle)
			else:
				angles.append(round(random.uniform(p_chi_min, p_chi_max), self.float_precision))
		return angles
	
	def use_histogram(self, maxmin_angles, prob_list, prob2_list, name):
		if prob2_list == []:
			luck = random.uniform(0.0, 1.0)
			edge = 0.0
			for probs in prob_list:
				if(luck <= probs[2] + edge):
					# Adjust the phi and psi range borders, can't be greater than 180 or smaller than -180
					p_phi_min = probs[0] - self.prob_radius
					p_phi_min = -180.0 if p_phi_min < -180.0 else 180.0 if p_phi_min > 180.0 else p_phi_min
					p_phi_max = probs[0] + self.prob_radius
					p_phi_max = -180.0 if p_phi_max < -180.0 else 180.0 if p_phi_max > 180.0 else p_phi_max
					p_psi_min = probs[1] - self.prob_radius
					p_psi_min = -180.0 if p_psi_min < -180.0 else 180.0 if p_psi_min > 180.0 else p_psi_min
					p_psi_max = probs[1] + self.prob_radius
					p_psi_max = -180.0 if p_psi_max < -180.0 else 180.0 if p_psi_max > 180.0 else p_psi_max
					
					angles = self.get_angle_chis(probs)
					aa_angles = [round(random.uniform(p_phi_min, p_phi_max), self.float_precision), round(random.uniform(p_psi_min, p_psi_max), self.float_precision)] + angles
					break
				else:
					edge = edge + probs[2]
					p_backup = probs
			else: # for
				p_phi_min = p_backup[0] - self.prob_radius
				p_phi_min = -180.0 if p_phi_min < -180.0 else 180.0 if p_phi_min > 180.0 else p_phi_min
				p_phi_max = p_backup[0] + self.prob_radius
				p_phi_max = -180.0 if p_phi_max < -180.0 else 180.0 if p_phi_max > 180.0 else p_phi_max
				p_psi_min = p_backup[1] - self.prob_radius
				p_psi_min = -180.0 if p_psi_min < -180.0 else 180.0 if p_psi_min > 180.0 else p_psi_min
				p_psi_max = p_backup[1] + self.prob_radius
				p_psi_max = -180.0 if p_psi_max < -180.0 else 180.0 if p_psi_max > 180.0 else p_psi_max
				
				angles = self.get_angle_chis(p_backup)
				aa_angles = [round(random.uniform(p_phi_min, p_phi_max), self.float_precision), round(random.uniform(p_psi_min, p_psi_max), self.float_precision)] + angles
			return aa_angles
		
		else:
			luck = random.uniform(0.0, 1.0)
			edge = 0.0
			for probs in prob_list:
				if(luck <= probs[2] + edge):
					p_phi_min = probs[0] - self.prob_radius
					p_phi_min = -180.0 if p_phi_min < -180.0 else 180.0 if p_phi_min > 180.0 else p_phi_min
					p_phi_max = probs[0] + self.prob_radius
					p_phi_max = -180.0 if p_phi_max < -180.0 else 180.0 if p_phi_max > 180.0 else p_phi_max
					p_psi_min = probs[1] - self.prob_radius
					p_psi_min = -180.0 if p_psi_min < -180.0 else 180.0 if p_psi_min > 180.0 else p_psi_min
					p_psi_max = probs[1] + self.prob_radius
					p_psi_max = -180.0 if p_psi_max < -180.0 else 180.0 if p_psi_max > 180.0 else p_psi_max
					testboo = False
					angles = []
					for probs2 in prob2_list:
						if probs[0] == probs2[0]:
							if probs[1] == probs2[1]:
								angles = self.get_angle_chis(probs2)
								testboo = True
								aa_angles = [round(random.uniform(p_phi_min, p_phi_max),self.float_precision), round(random.uniform(p_psi_min, p_psi_max),self.float_precision)] + angles
								break
					if not testboo:
						luck = random.uniform(0.0, 1.0)
						edge = 0.0
						for probs in prob2_list:
							if(luck <= probs[2] + edge):
								# Adjust the phi and psi range borders, can't be greater than 180 or smaller than -180
								p_phi_min = probs[0] - self.prob_radius
								p_phi_min = -180.0 if p_phi_min < -180.0 else 180.0 if p_phi_min > 180.0 else p_phi_min
								p_phi_max = probs[0] + self.prob_radius
								p_phi_max = -180.0 if p_phi_max < -180.0 else 180.0 if p_phi_max > 180.0 else p_phi_max
								p_psi_min = probs[1] - self.prob_radius
								p_psi_min = -180.0 if p_psi_min < -180.0 else 180.0 if p_psi_min > 180.0 else p_psi_min
								p_psi_max = probs[1] + self.prob_radius
								p_psi_max = -180.0 if p_psi_max < -180.0 else 180.0 if p_psi_max > 180.0 else p_psi_max
								
								angles = self.get_angle_chis(probs)
								aa_angles = [round(random.uniform(p_phi_min, p_phi_max), self.float_precision), round(random.uniform(p_psi_min, p_psi_max), self.float_precision)] + angles
								break
							else:
								edge = edge + probs[2]
								p_backup = probs
						else:
							p_phi_min = p_backup[0] - self.prob_radius
							p_phi_min = -180.0 if p_phi_min < -180.0 else 180.0 if p_phi_min > 180.0 else p_phi_min
							p_phi_max = p_backup[0] + self.prob_radius
							p_phi_max = -180.0 if p_phi_max < -180.0 else 180.0 if p_phi_max > 180.0 else p_phi_max
							p_psi_min = p_backup[1] - self.prob_radius
							p_psi_min = -180.0 if p_psi_min < -180.0 else 180.0 if p_psi_min > 180.0 else p_psi_min
							p_psi_max = p_backup[1] + self.prob_radius
							p_psi_max = -180.0 if p_psi_max < -180.0 else 180.0 if p_psi_max > 180.0 else p_psi_max
							
							angles = self.get_angle_chis(p_backup)
							aa_angles = [round(random.uniform(p_phi_min, p_phi_max),self.float_precision), round(random.uniform   (p_psi_min, p_psi_max),self.float_precision)] + angles
						
						return aa_angles
					break
				else:
					edge = edge + probs[2]
					p_backup = probs
			
			else: # for prob_list
				p_phi_min = p_backup[0] - self.prob_radius
				p_phi_min = -180.0 if p_phi_min < -180.0 else 180.0 if p_phi_min > 180.0 else p_phi_min
				p_phi_max = p_backup[0] + self.prob_radius
				p_phi_max = -180.0 if p_phi_max < -180.0 else 180.0 if p_phi_max > 180.0 else p_phi_max
				p_psi_min = p_backup[1] - self.prob_radius
				p_psi_min = -180.0 if p_psi_min < -180.0 else 180.0 if p_psi_min > 180.0 else p_psi_min
				p_psi_max = p_backup[1] + self.prob_radius
				p_psi_max = -180.0 if p_psi_max < -180.0 else 180.0 if p_psi_max > 180.0 else p_psi_max
				testboo = False
				angles = []
				for probs2 in prob2_list:
					if p_backup[0] == probs2[0]:
						if p_backup[1] == probs2[1]:
							angles = self.get_angle_chis(probs2)
							testboo = True
							aa_angles = [round(random.uniform(p_phi_min, p_phi_max), self.float_precision), round(random.uniform(p_psi_min, p_psi_max), self.float_precision)] + angles
							break
					
				if not testboo:
					luck = random.uniform(0.0, 1.0)
					edge = 0.0
					for probs in prob2_list:
						if(luck <= probs[2] + edge):
							# Adjust the phi and psi range borders, can't be greater than 180 or smaller than -180
							p_phi_min = probs[0] - self.prob_radius
							p_phi_min = -180.0 if p_phi_min < -180.0 else 180.0 if p_phi_min > 180.0 else p_phi_min
							p_phi_max = probs[0] + self.prob_radius
							p_phi_max = -180.0 if p_phi_max < -180.0 else 180.0 if p_phi_max > 180.0 else p_phi_max
							p_psi_min = probs[1] - self.prob_radius
							p_psi_min = -180.0 if p_psi_min < -180.0 else 180.0 if p_psi_min > 180.0 else p_psi_min
							p_psi_max = probs[1] + self.prob_radius
							p_psi_max = -180.0 if p_psi_max < -180.0 else 180.0 if p_psi_max > 180.0 else p_psi_max
							
							angles = self.get_angle_chis(probs)
							aa_angles = [round(random.uniform(p_phi_min, p_phi_max), self.float_precision), round(random.uniform(p_psi_min, p_psi_max), self.float_precision)] + angles
							break
						else:
							edge = edge + probs[2]
							p_backup = probs
					else:
						p_phi_min = p_backup[0] - self.prob_radius
						p_phi_min = -180.0 if p_phi_min < -180.0 else 180.0 if p_phi_min > 180.0 else p_phi_min
						p_phi_max = p_backup[0] + self.prob_radius
						p_phi_max = -180.0 if p_phi_max < -180.0 else 180.0 if p_phi_max > 180.0 else p_phi_max
						p_psi_min = p_backup[1] - self.prob_radius
						p_psi_min = -180.0 if p_psi_min < -180.0 else 180.0 if p_psi_min > 180.0 else p_psi_min
						p_psi_max = p_backup[1] + self.prob_radius
						p_psi_max = -180.0 if p_psi_max < -180.0 else 180.0 if p_psi_max > 180.0 else p_psi_max
						
						angles = self.get_angle_chis(p_backup)
						aa_angles = [round(random.uniform(p_phi_min, p_phi_max), self.float_precision), round(random.uniform   (p_psi_min, p_psi_max), self.float_precision)] + angles
			
			return aa_angles
