#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import urllib2
import traceback
import subprocess


class LaunchTests:
	def __init__(self):
		self.proteins = []
		self.configs = []
		self.tests = []
		self.if_download = True
		self.tests_by_protein = 1
		self.tests_concurrent = 1
		
	def set_config(self):
		try:
			f = open('launch_tests.config', 'r')
		except:
			traceback.print_exc()
			sys.exit('ERROR: failed to open config file')
		
		status = 0
		line = f.readline()

		while (line):
			if (line.startswith('#') or line.strip() == ''):
				pass
			
			elif line.startswith('proteins:'):
				proteins = line[10:].split()
				for protein in proteins:
					self.proteins.append(protein)
			
			elif line.startswith('if_download:'):
				if line[13:].rstrip() == 'True':
					self.if_download = True
				if line[13:].rstrip() == 'False':
					self.if_download = False
			
			elif line.startswith('tests_by_protein:'):
				self.tests_by_protein = int(line[18:])
			elif line.startswith('tests_concurrent:'):
				self.tests_concurrent = int(line[18:])
			
			elif line.startswith('start config:'):
				line = f.readline()
				tree_nodes = '1'
				tree_levels = '1'
				max_agents = '1'
				num_pockets = '10'
				if_reset = 'True'
				test_noimprove = '10'
				energy_limit = '100000'
				
				while ((line) and (line.startswith('end config') == False)):
					if line.startswith('tree_nodes:'):
						tree_nodes = line[12:].rstrip()
					elif line.startswith('tree_levels:'):
						tree_levels = line[13:].rstrip()
					elif line.startswith('max_agents:'):
						max_agents = line[12:].rstrip()
					elif line.startswith('num_pockets:'):
						num_pockets = line[13:].rstrip()
					elif line.startswith('if_reset:'):
						if_reset = line[10:].rstrip()
					elif line.startswith('test_noimprove:'):
						test_noimprove = line[16:].rstrip()
					elif line.startswith('energy_limit:'):
						energy_limit = line[14:].rstrip()
					else:
						print 'Bad format in the configuration file'
						sys.exit()
					line = f.readline()
				
				self.configs.append(tree_levels + ' ' + tree_nodes + ' ' + max_agents + ' ' + num_pockets + ' ' + if_reset + ' ' + test_noimprove + ' ' + energy_limit)
			else:
				print 'Bad format in the configuration file'
				sys.exit()
			
			line = f.readline()

		f.close()

		for conf in self.configs:
			for protein in self.proteins:
				for i in range(0, self.tests_by_protein):
					self.tests.append(protein + ' ' + conf)


	def download_pdbs(self):
		INFO_SEQ = '\033[32m'
		WARNING_SEQ = '\033[33m'
		RESET_SEQ = '\033[0m'

		rcsb_restful_url = 'http://www.rcsb.org/pdb/files/'
		download_path = 'protein_pdbs/'

		logging.info('%sDownloading proteins: %s%s' % (INFO_SEQ, self.proteins, RESET_SEQ))

		if not os.path.exists(download_path):
			os.makedirs(download_path)

		for protein_id in self.proteins:
			if(os.path.isfile(os.path.join(download_path, protein_id + '.pdb'))):
				logging.info('%sProtein %s already exists in %s%s' % (WARNING_SEQ, protein_id, download_path, RESET_SEQ))
			else:
				req = rcsb_restful_url+protein_id + '.pdb'
				response = urllib2.urlopen(req)
				pdb = response.read()
				f = open(os.path.join(download_path, protein_id + '.pdb'), 'w')
				f.write(pdb)
				f.close()
				logging.info('%sProtein %s has been downloaded from %s to %s%s' % (WARNING_SEQ, protein_id, req, os.path.abspath(download_path), RESET_SEQ))


	def parallel_run(self):
		INFO_SEQ = '\033[32m'
		WARNING_SEQ = '\033[33m'
		RESET_SEQ = '\033[0m'

		test_run = 0
		log_id = 1

		while not (len(self.tests) == 0):
			if test_run < self.tests_concurrent:
				test_protein = self.tests.pop()
				cmd = 'python memetic_parallel.py %s > memetic_parallel_%d.log 2>&1' % (test_protein, log_id)
				logging.info(INFO_SEQ + cmd + RESET_SEQ)
				subprocess.Popen(cmd, shell = True)
				test_run += 1
				log_id += 1
				continue
			if(test_run > 0):
				os.wait()
				test_protein = self.tests.pop()
				cmd = 'python memetic_parallel.py %s > memetic_parallel_%d.log 2>&1' % (test_protein, log_id)
				logging.info(INFO_SEQ + cmd + RESET_SEQ)
				subprocess.Popen(cmd, shell = True)
				log_id += 1


def main():
	logging.basicConfig(format = '%(message)s', level = logging.INFO)
	
	run = LaunchTests()
	
	run.set_config()
	
	if run.if_download:
		run.download_pdbs()
	
	run.parallel_run()

if __name__ == '__main__':
	main()
