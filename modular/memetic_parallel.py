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
			
			else:
				print 'Bad format in the configuration file'
				sys.exit()
			
			line = f.readline()

		f.close()


def main():
	log_path = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + 'pid-' + str(os.getpid())
	
	rosetta.init()
	
	config = Config(sys.argv)
	config.load_config()
	error = Error()
	
	results_path = config.results_path + '/' + config.protein + '/' + log_path
	
	sequence = Sequence(config.protein, error, config.sequences_path)
	sequence.read_sequence()
	
	hist_obj = HistogramFiles(sequence, error, config.use_angle_range, config.prob_radius, config.histograms_path)
	hist_obj.read_histograms()
	
	worker = WorkerProcess(0, None, None, None, None, config, sequence, hist_obj, None, None, results_path)
	
	start_time = datetime.datetime.now()
	worker.start()
	worker.join()
	t_final = datetime.datetime.now() - start_time
	
	print 'Total time: ' + str(t_final)
	print '**** end MainProcess ****'	

if __name__ == '__main__':
	main()
