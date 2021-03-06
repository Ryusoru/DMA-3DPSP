#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import datetime
import traceback
from rosetta import *

from sequence import *
from histogram import *
from workerprocess import *


class Error:
	def __init__(self):
		self.ERROR_CODE_fileopening = 'Error while opening '
		self.ERROR_CODE_filewriting = 'Error while writing '
		self.ERROR_CODE_PDBwriting = 'Error while writing PDB file '
		self.ERROR_CODE_emptyfile = 'Error: empty file'
		self.ERROR_CODE_lessangles = 'Error: file has less angles than expected'
		self.ERROR_CODE_incompletefile = 'Error: file is incomplete'
		self.ERROR_CODE_mysteriousresidue = 'Error: mysterious amino acid residue found'


class Config:
	def __init__(self, argv):
		self.protein = str(argv[1]).strip().upper()
		self.num_levels = int(argv[2])
		self.num_sup = int(argv[3])
		self.num_agents = 1
		for n in range(1, self.num_levels):
			self.num_agents += self.num_sup**n
		self.max_agents = int(argv[4])
		if self.num_agents > self.max_agents:
			self.num_agents = self.max_agents
		self.num_pockets = int(argv[5])
		self.if_reset = (str(argv[6]) == 'True')
		self.test_noimprove = int(argv[7])
		self.score_weight = int(argv[8])
		self.sasa_weight = int(argv[9])
		self.energy_limit = int(argv[10])
		
		self.sequences_path = 'Sequences'
		self.histograms_path = 'Histograms'
		self.logs_path = 'Logs'
		self.results_path = 'Results'
		self.use_angle_range = False
		self.prob_radius = 0.5
		self.crossover_prob = 0.4
		
		# Constants for simulated_annealing()
		self.test_ls_prob = 0.9
		self.test_ls_fact = 0.9
		self.test_jump_prob = 0.3
		self.test_jump_fact = 0.85
		self.test_temp_init = 2000
		self.test_jump_dist = 180
		self.ls_prob_ss = [0.9 for i in range (0,7)]
		self.calculate_ls_probs = False
		
		self.calculate_div_density = False
		self.hosts = [['127.0.0.1', 20000, ''] for i in range(0, self.num_agents)]
		self.root_hosts = [['127.0.0.1', 20000, ''] for i in range(0, self.num_agents)]
	
	def set_ls_probs(self, sequence):
		count_ss_B = 0
		count_ss_C = 0
		count_ss_E = 0
		count_ss_G = 0
		count_ss_H = 0
		count_ss_I = 0
		count_ss_T = 0
		
		for ss in sequence.secondary_amino_sequence:
			if ss == 'B':
				count_ss_B += 1
			if ss == 'C':
				count_ss_C += 1
			if ss == 'E':
				count_ss_E += 1
			if ss == 'G':
				count_ss_G += 1
			if ss == 'H':
				count_ss_H += 1
			if ss == 'I':
				count_ss_I += 1
			if ss == 'T':
				count_ss_T += 1
		
		for i in range(len(self.ls_prob_ss)):
			if i == 6:
				self.ls_prob_ss[i] = 0.9
			else:
				self.ls_prob_ss[i] = 0.9 * (1 - (float(count_ss_T) / len(sequence.secondary_amino_sequence)))
	
	def load_config(self):
		try:
			f = open('memetic_parallel.config', 'r')
		except:
			traceback.print_exc()
			sys.exit('ERROR: failed to open config file')
		
		line = f.readline()

		while (line):
			if (line.startswith('#') or line.strip() == ''):
				pass
			
			elif line.startswith('sequences_path:'):
				self.sequences_path = str(line[16:].rstrip())
			elif line.startswith('histograms_path:'):
				self.histograms_path = str(line[17:].rstrip())
			elif line.startswith('logs_path:'):
				self.logs_path = str(line[11:].rstrip())
			elif line.startswith('results_path:'):
				self.results_path = str(line[14:].rstrip())
			
			elif line.startswith('use_angle_range:'):
				if line[17:].rstrip() == 'True':
					self.use_angle_range = True
				if line[17:].rstrip() == 'False':
					self.use_angle_range = False
			
			elif line.startswith('prob_radius:'):
				self.prob_radius = float(line[13:])
			elif line.startswith('crossover_prob:'):
				self.crossover_prob = float(line[16:])
			
			elif line.startswith('test_ls_prob:'):
				self.test_ls_prob = float(line[14:])
			elif line.startswith('test_ls_fact:'):
				self.test_ls_fact = float(line[14:])
			elif line.startswith('test_jump_prob:'):
				self.test_jump_prob = float(line[16:])
			elif line.startswith('test_jump_fact:'):
				self.test_jump_fact = float(line[16:])
			elif line.startswith('test_temp_init:'):
				self.test_temp_init = float(line[16:])
			elif line.startswith('test_jump_dist:'):
				self.test_jump_dist = float(line[16:])
			
			elif line.startswith('ls_prob_B:'):
				self.ls_prob_ss[0] = float(line[11:])
			elif line.startswith('ls_prob_C:'):
				self.ls_prob_ss[1] = float(line[11:])
			elif line.startswith('ls_prob_E:'):
				self.ls_prob_ss[2] = float(line[11:])
			elif line.startswith('ls_prob_G:'):
				self.ls_prob_ss[3] = float(line[11:])
			elif line.startswith('ls_prob_H:'):
				self.ls_prob_ss[4] = float(line[11:])
			elif line.startswith('ls_prob_I:'):
				self.ls_prob_ss[5] = float(line[11:])
			elif line.startswith('ls_prob_T:'):
				self.ls_prob_ss[6] = float(line[11:])
			
			elif line.startswith('calculate_ls_probs:'):
				if line[20:].rstrip() == 'True':
					self.calculate_ls_probs = True
				if line[20:].rstrip() == 'False':
					self.calculate_ls_probs = False
			
			elif line.startswith('calculate_div_density:'):
				if line[23:].rstrip() == 'True':
					self.calculate_div_density = True
				if line[23:].rstrip() == 'False':
					self.calculate_div_density = False
			
			else:
				print 'Bad format in the configuration file'
				sys.exit()
			
			line = f.readline()

		f.close()
	
	def load_hosts(self, log_id):
		try:
			f = open('hosts.config', 'r')
		except:
			traceback.print_exc()
			sys.exit('ERROR: failed to open hosts file')
		
		line = f.readline()

		while (line):
			if (line.startswith('#') or line.strip() == ''):
				pass
			
			elif line.startswith('start agent:'):
				line = f.readline()
				agents = []
				host = '127.0.0.1'
				# ports = []
				path = ''
				
				while ((line) and (line.startswith('end agent') == False)):
					if line.startswith('agents:'):
						agents = line[8:].split(",")
					elif line.startswith('host:'):
						host = line[6:].rstrip()
				#	elif line.startswith('ports:'):
				#		ports = line[7:].split(",")
					elif line.startswith('path:'):
						path = line[6:].rstrip()
					else:
						print 'Bad format in the configuration file'
						sys.exit()
					line = f.readline()
				
				for agent in agents:
				#	i = 0
					if int(agent) < self.num_agents:
						self.hosts[int(agent)][0] = host
				#		self.hosts[int(agent)][1] = int(ports[i])
						self.hosts[int(agent)][1] = 20000 + ((log_id - 1) * self.num_agents) + int(agent)
						self.hosts[int(agent)][1] = 20000 + ((log_id - 1) * self.num_agents) + int(agent)
						self.hosts[int(agent)][2] = path
						
						self.root_hosts[int(agent)][0] = host
				#		self.root_hosts[int(agent)][1] = int(ports[i])
						self.root_hosts[int(agent)][1] = 20000 - ((log_id - 1) * self.num_agents) - int(agent)
						self.root_hosts[int(agent)][1] = 20000 - ((log_id - 1) * self.num_agents) - int(agent)
						self.root_hosts[int(agent)][2] = path
				#	i += 1
			
			else:
				print 'Bad format in the configuration file'
				sys.exit()
			
			line = f.readline()

		f.close()


def main():
	log_path = 'Test-%03d' % int(sys.argv[12])
	
	rosetta.init()
	
	config = Config(sys.argv)
	config.load_config()
	config.load_hosts(int(sys.argv[12]))
	error = Error()
	
	results_path = config.results_path + '/' + config.protein + '/' + log_path
	
	sequence = Sequence(config.protein, error, config.sequences_path)
	sequence.read_sequence()
	
	if config.calculate_ls_probs:
		config.set_ls_probs(sequence)
	
	hist_obj = HistogramFiles(sequence, error, config.use_angle_range, config.prob_radius, config.histograms_path)
	hist_obj.read_histograms()
	
	worker = WorkerProcess(int(sys.argv[11]), config, sequence, hist_obj, results_path, int(sys.argv[12]))
	
	start_time = datetime.datetime.now()
	worker.start()
	worker.join()
	t_final = datetime.datetime.now() - start_time
	
	print 'Total time: ' + str(t_final)
	print '**** end MainProcess ****'	

if __name__ == '__main__':
	main()
