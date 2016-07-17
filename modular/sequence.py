#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import copy
import string
import traceback


class Sequence:
	def __init__(self, protein, error, sequences_path):
		self.protein = protein
		self.primary_amino_sequence = None
		self.secondary_amino_sequence = ''
		self.secondary_sequence_list = []
		self.secondary_section_index = []
		self.maxmin_angles = []
		self.customize_chi_range = False
		self.use_chi_angles = False
		self.error = error
		self.sequences_path = sequences_path
		
		self.sigla = {'A' : 'ALA',
					  'R' : 'ARG',
				 	  'N' : 'ASN',
				 	  'D' : 'ASP',
				 	  'R' : 'ARG',
				 	  'B' : 'ASX',
				 	  'C' : 'CYS',
					  'E' : 'GLU',
					  'Q' : 'GLN',
					  'Z' : 'GLX',
					  'G' : 'GLY',
					  'H' : 'HIS',
					  'I' : 'ILE',
					  'L' : 'LEU',
					  'K' : 'LYS',
					  'M' : 'MET',
					  'F' : 'PHE',
					  'P' : 'PRO',
					  'S' : 'SER',
					  'T' : 'THR',
					  'W' : 'TRP',
					  'Y' : 'TYR',
					  'V' : 'VAL'}
		self.siglaSS = {'0' : 'B',
					    '1' : 'C',
					    '2' : 'E',
					    '3' : 'G',
					    '4' : 'H',
					    '5' : 'I',
					    '6' : 'T'}
		
	def min_rot_chi(self, amino, chi):
		if (amino == 'SER'):
			if (chi == 1):
				return -39.0974526602
			else:
				return 0.0
	 	
		if (amino == 'CYS')or(amino == 'CYX'):
			if (chi == 1): 
				return -157.751341619 
			else:
				return 0.0
		
		if (amino == 'THR'): #only chi1
			if (chi == 1):
				return -153.24819924
			else:
				return 0.0
		
		if (amino == 'VAL'):
			if (chi == 1): 
				return -37.1805850827 
			else:
				return 0.0
		
		if (amino == 'ILE'): 
			if (chi == 1): 
				return -150.62880823
			if (chi == 2): 
				return -41.9536560708
			else:
				return 0.0
		
		if (amino == 'LEU'):
			if (chi == 1): 
				return -158.45718524
			if (chi == 2): 
				return -41.1651784582 
			else:
				return 0.0
		
		if (amino == 'ASP'):
			if (chi == 1):
				return -154.759146052
			if (chi == 2):
				return -46.0141277967
			else:
				return 0.0
		
		if (amino == 'ASN'):
			if (chi == 1): 
				return -154.999658218
			if (chi == 2): 
				return -78.6804677964
			else:
				return 0.0
		
		if (amino == 'HIS') or (amino == 'HID'):
			if (chi == 1): 
				return -156.435615538 
			if (chi == 2):
				return -96.5817995178 
			else:
				return 0.0
		
		if (amino == 'PHE'):
			if (chi == 1): 
				return -158.224844705
			if (chi == 2): 
				return -1.89539086499
			else:
				return 0.0
		
		if (amino == 'TYR'):
			if (chi == 1): 
				return -158.518614718
			if (chi == 2): 
				return -3.56448935905
			else:
				return 0.0
		
		if (amino == 'TRP'):
			if (chi == 1): 
				return -159.333604703
			if (chi == 2): 
				return -77.5000361533
			else:
				return 0.0
		
		if (amino == 'MET'):
			if (chi == 1): 
				return -159.535936996
			if (chi == 2):
				return -95.9804879414
			if (chi == 3):
				return -113.617738242
			else:
				return 0.0
		
		if (amino == 'GLU'):
			if (chi == 1): 
				return -154.3304485
			if (chi == 2): 
				return -114.381414072
			if (chi == 3): 
				return -46.2622279015
			else:
				return 0.0
		
		if (amino == 'GLN'):
			if (chi == 1): 
				return -156.107286967
			if (chi == 2): 
				return -130.31218703
			if (chi == 3): 
				return -107.208042715
			else:
				return 0.0
		
		if (amino == 'LYS'):
			if (chi == 1): 
				return -155.042685651
			if (chi == 2):
				return -131.521384644
			if (chi == 3):
				return -131.389541682
			if (chi == 4):
				return -131.389541682
		
		if (amino == 'ARG'):
			if (chi == 1):
				return -151.830993739
			if (chi == 2): 
				return -105.206308323
			if (chi == 3): 
				return -136.745709869
			if (chi == 4): 
				return -136.745709869
		
		if (amino == 'PRO') or (amino == 'ALA') or (amino == 'GLY'):
			if (chi == 1):
				return 0.0
			if (chi == 2): 
				return 0.0
			if (chi == 3): 
				return 0.0
			if (chi == 4): 
				return 0.0
	
	def max_rot_chi(self, amino, chi):
		if (amino == 'SER'):
			if (chi == 1):
				return 159.364119327
			else:
				return 0.0
	 	
		if (amino == 'CYS')or(amino == 'CYX'):
			if (chi == 1): 
				return 39.1513416194
			else:
				return 0.0
		
		if (amino == 'THR'): #only chi1
			if (chi == 1):
				return 38.1815325735
			else:
				return 0.0
		
		if (amino == 'VAL'):
			if (chi == 1): 
				return 156.980585083
			else:
				return 0.0
		
		if (amino == 'ILE'): 
			if (chi == 1): 
				return 36.9621415634
			if (chi == 2): 
				return 158.553656071
			else:
				return 0.0
		
		if (amino == 'LEU'):
			if (chi == 1): 
				return 34.5682963508
			if (chi == 2): 
				return 153.698511792
			else:
				return 0.0
		
		if (amino == 'ASP'):
			if (chi == 1):
				return 35.1147016071
			if (chi == 2):
				return 46.9696833523
			else:
				return 0.0
		
		if (amino == 'ASN'):
			if (chi == 1): 
				return 36.4441026627
			if (chi == 2): 
				return 102.880467796
			else:
				return 0.0
		
		if (amino == 'HIS') or (amino == 'HID'):
			if (chi == 1): 
				return 39.0133933155
			if (chi == 2):
				return 134.60402174
			else:
				return 0.0
		
		if (amino == 'PHE'):
			if (chi == 1): 
				return 37.1915113716
			if (chi == 2): 
				return 90.4287241983
			else:
				return 0.0
		
		if (amino == 'TYR'):
			if (chi == 1): 
				return 40.6852813843
			if (chi == 2): 
				return 90.3311560257
			else:
				return 0.0
		
		if (amino == 'TRP'):
			if (chi == 1): 
				return 37.20027137
			if (chi == 2): 
				return 76.1667028199
			else:
				return 0.0
		
		if (amino == 'MET'):
			if (chi == 1): 
				return 38.6100110704
			if (chi == 2):
				return 136.936043497
			if (chi == 3):
				return 127.810330834
			else:
				return 0.0
		
		if (amino == 'GLU'):
			if (chi == 1): 
				return 36.0193373885
			if (chi == 2): 
				return 127.166599257
			if (chi == 3): 
				return 45.906672346
			else:
				return 0.0
		
		if (amino == 'GLN'):
			if (chi == 1): 
				return 38.251731411
			if (chi == 2): 
				return 110.023298141
			if (chi == 3): 
				return 78.3524871589
			else:
				return 0.0
		
		if (amino == 'LYS'):
			if (chi == 1): 
				return 45.9834263916
			if (chi == 2):
				return 107.881878471
			if (chi == 3):
				return 109.224109583
			if (chi == 4):
				return 109.224109583
		
		if (amino == 'ARG'):
			if (chi == 1):
				return 55.4581542333
			if (chi == 2): 
				return 135.482851533
			if (chi == 3): 
				return 95.5111419674
			if (chi == 4): 
				return 95.5111419674
		
		if (amino == 'PRO') or (amino == 'ALA') or (amino == 'GLY'):
			if (chi == 1):
				return 0.0
			if (chi == 2): 
				return 0.0
			if (chi == 3): 
				return 0.0
			if (chi == 4): 
				return 0.0
		
	def read_sequence(self):
		input_file_name  = '%s/%s.txt' % (self.sequences_path, self.protein)
		try:
			input_file = open(input_file_name)
		except:
			print('ERROR')
			traceback.print_exc()
			sys.exit(self.error.ERROR_CODE_fileopening + input_file_name)
		
		line = input_file.readline()
		self.primary_amino_sequence = line.strip()
		line = input_file.readline()
		self.secondary_amino_sequence = line.strip()

		try:
			input_file.close()
		except:
			print('ERROR')
			traceback.print_exc()
			sys.exit(self.error.ERROR_CODE_fileclosing + input_file_name)

		ss_sec = 'NA'
		i_sec = 0
		
		# Secondary structure constants
		SS_B = 0
		SS_C = 1
		SS_E = 2
		SS_G = 3
		SS_H = 4
		SS_I = 5
		SS_T = 6

		for ss in self.secondary_amino_sequence:
			if   ss == 'B':
				ssi = SS_B
			elif ss == 'C':
				ssi = SS_C
			elif ss == 'E':
				ssi = SS_E
			elif ss == 'G':
				ssi = SS_G
			elif ss == 'H':
				ssi = SS_H
			elif ss == 'I':
				ssi = SS_I
			elif ss == 'T':
				ssi = SS_T
			else:
				sys.exit('Line ' + ': ' + 'Secondary structure unknown: ' + ss + ' ' + str(ssi))
			self.secondary_sequence_list.append(ssi)

			if	ss_sec == 'NA':
				ss_sec = ss
				self.secondary_section_index.append(i_sec)
			else:
				if ss_sec != ss:
					self.secondary_section_index.append(i_sec - 1)
					self.secondary_section_index.append(i_sec)
					ss_sec = ss
			i_sec += 1
		self.secondary_section_index.append(i_sec - 1)
	
		for aminoacid in self.primary_amino_sequence:
			Phi_min  = -180
			Phi_max  = 180
			Psi_min  = -180
			Psi_max  = 180
			if self.customize_chi_range:
				Chi1_min = -180
				Chi1_max = 180
				Chi2_min = -180
				Chi2_max = 180
				Chi3_min = -180
				Chi3_max = 180
				Chi4_min = -180
				Chi4_max = 180
			else:
				if self.use_chi_angles:
					Chi1_min = self.min_rot_chi(self.sigla[aminoacid], 1)
					Chi1_max = self.max_rot_chi(self.sigla[aminoacid], 1)
					Chi2_min = self.min_rot_chi(self.sigla[aminoacid], 2)
					Chi2_max = self.max_rot_chi(self.sigla[aminoacid], 2)
					Chi3_min = self.min_rot_chi(self.sigla[aminoacid], 3)
					Chi3_max = self.max_rot_chi(self.sigla[aminoacid], 3)
					Chi4_min = self.min_rot_chi(self.sigla[aminoacid], 4)
					Chi4_max = self.max_rot_chi(self.sigla[aminoacid], 4)
				else:
					Chi1_min = 0.0
					Chi1_max = 0.0
					Chi2_min = 0.0
					Chi2_max = 0.0
					Chi3_min = 0.0
					Chi3_max = 0.0
					Chi4_min = 0.0
					Chi4_max = 0.0

			maxmin = [Phi_min, Phi_max, Psi_min, Psi_max,
					  Chi1_min, Chi1_max, Chi2_min, Chi2_max,
					  Chi3_min, Chi3_max, Chi4_min, Chi4_max]
			
			self.maxmin_angles.append(copy.deepcopy(maxmin))
