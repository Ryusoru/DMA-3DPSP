#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import copy
import random
import datetime
import cPickle as pickle
from multiprocessing import Process, Manager, Condition, Lock, Event, Queue

from agent import *


class WorkerProcess(Process):
	def __init__(self, id, leader_send, leader_recv, root_div_send, leader_div_send, leader_reset_send, leader_reset_recv, config, sequence, hist_obj, energy_list, stop_event, results_path):
		Process.__init__(self)
		self.id = id
		self.config = config
		self.sequence = sequence
		self.hist_obj = hist_obj
		self.agent = Agent(self.id, config, sequence)
		self.leader_send = leader_send
		self.leader_recv = leader_recv
		self.support_send = [Queue(1) for i in range(1, self.config.num_sup+1)] if id * self.config.num_sup + 1 < self.config.num_agents else None
		self.support_recv = Queue() if id * self.config.num_sup + 1 < self.config.num_agents else None
		self.root_div_send = root_div_send
		self.leader_div_send = leader_div_send
		self.agent_div_recv = [Queue(1) for i in range(1, self.config.num_agents)] if self.agent.id_leader == None else None
		self.support_div_recv = [Queue(1) for i in range(1, self.config.num_sup+1)] if self.agent.id_supporters else None
		self.leader_reset_send = leader_reset_send
		self.leader_reset_recv = leader_reset_recv
		self.support_reset_send = [Queue(1) for i in range(1, self.config.num_sup+1)] if id * self.config.num_sup + 1 < self.config.num_agents else None
		self.support_reset_recv = [Queue(1) for i in range(1, self.config.num_sup+1)] if id * self.config.num_sup + 1 < self.config.num_agents else None
		self.event_restart = Event()
		self.energy_list = energy_list
		self.stop_event = stop_event
		self.results_path = results_path
	
	def select_rand_solution(self, solutions):
		index = 0
		counter_sol = 0
		for sol in solutions:
			if sol != None:
				counter_sol += 1
		counter_sol -= 1 
		index = random.randint(0, counter_sol)
		return index
	
	def fitness_roulette_selection(self, solutions):
		fitness_last = 0
		fitness_total = 0
		fitness_acum = 0
		index = 0
		selection = random.uniform(0, 1)
		for sol in solutions:
			if sol != None:
				fitness_last = sol.energy_value
		for sol in solutions:
			if sol != None:
				fitness_total += fitness_last - sol.energy_value
		if fitness_total != 0:
			for sol in solutions:
				if sol != None:
					fitness_acum += fitness_last - sol.energy_value
					prob = fitness_acum / fitness_total
					if selection <= prob:
						break
					index += 1
		return index
	
	def send_solution(self, solution, queue):
		time_send_start = datetime.datetime.now()
		queue.put(copy.deepcopy(solution))
		self.agent.trx_send += 1
		self.agent.time_send += datetime.datetime.now() - time_send_start
	
	def receive_solution(self, queue, is_leader):
		time_receive_start = datetime.datetime.now()
		solution = queue.get()
		if is_leader:
			self.agent.update(solution)
		else:
			index = 0
			for sol in solution:
				if sol != None:
					self.agent.leader_pockets[index] = copy.deepcopy(sol)
				else:
					break
				index += 1
		self.agent.trx_receive += 1
		self.agent.time_receive += datetime.datetime.now() - time_receive_start
	
	# Para los pickles no olvidar agregar pickle.loads en agente 0 durante el reset
	def send_solution_pickle(self, solution, queue):
		time_send_start = datetime.datetime.now()
		buff = pickle.dumps(solution, 2)
		queue.put(buff)
		self.agent.trx_send += 1
		self.agent.time_send += datetime.datetime.now() - time_send_start
	
	def receive_solution_pickle(self, queue, is_leader):
		time_receive_start = datetime.datetime.now()
		buff = queue.get()
		solution = pickle.loads(buff)
		self.agent.trx_receive += 1
		self.agent.time_receive += datetime.datetime.now() - time_receive_start
		if is_leader:
			self.agent.update(solution)
		else:
			index = 0
			for sol in solution:
				if sol != None:
					self.agent.leader_pockets[index] = copy.deepcopy(sol)
				else:
					break
				index += 1
	
	def save_results(self):
		if not os.path.exists(self.results_path):
			try:
				os.makedirs(self.results_path)
			except:
				pass
		
		if self.agent.id_leader == None:
			fout = open('%s/run-summary.txt' % (self.results_path), 'w')
			
			print 'Parameters'
			fout.write('Parameters\n')
			print '--- pockets: %d' % (self.config.num_pockets)
			fout.write('--- pockets: %d\n' % (self.config.num_pockets))
			print '--- agents: %d' % (self.config.num_agents)
			fout.write('--- agents: %d\n' % (self.config.num_agents))
			print '--- supporters per leader: %d' % (self.config.num_sup)
			fout.write('--- supporters per leader: %d\n' % (self.config.num_sup))
			print '--- do reset: %s' % (str(self.config.if_reset))
			fout.write('--- do reset: %s\n' % (str(self.config.if_reset)))
			print '--- prob radius: %f' % (self.hist_obj.prob_radius)
			fout.write('--- prob radius: %f\n' % (self.hist_obj.prob_radius))
			print '--- prob of ls: %f' % (self.config.test_ls_prob)
			fout.write('--- prob of ls: %f\n' % (self.config.test_ls_prob))
			print '--- simulated annealing decrease factor: %f' % (self.config.test_ls_fact)
			fout.write('--- simulated annealing decrease factor: %f\n' % (self.config.test_ls_fact))
			print '--- prob of jump before ls: %f' % (self.config.test_jump_prob)
			fout.write('--- prob of jump before ls: %f\n' % (self.config.test_jump_prob))
			print '--- jump decrease factor: %f' % (self.config.test_jump_fact)
			fout.write('--- jump decrease factor: %f\n' % (self.config.test_jump_fact))
			print '--- initial temperature for simulated annealing: %d' % (self.config.test_temp_init)
			fout.write('--- initial temperature for simulated annealing: %d\n' % (self.config.test_temp_init))
			print '--- initial max jump distance: %f' % (self.config.test_jump_dist)
			fout.write('--- initial max jump distance: %f\n' % (self.config.test_jump_dist))
			print '--- generations without improvements: %d' % (self.config.test_noimprove)
			fout.write('--- generations without improvements: %d\n' % (self.config.test_noimprove))
			print '--- prob of crossover: %f' % (self.config.crossover_prob)
			fout.write('--- prob of crossover: %f\n' % (self.config.crossover_prob))
			
			fout.close()
			
			for i in range(0, self.config.num_pockets):
				if self.agent.pockets[i] != None:
					self.agent.pockets[i].pose.dump_pdb('%s/pocket-%02d.pdb' % (self.results_path, i))
		
		fout = open('%s/log-agent-%02d.txt' % (self.results_path, self.id), 'w')

		print '\n%s' % (self.agent)
		fout.write('%s\n' % (self.agent))
		print 'Total generation of agent_%02d: %d' % (self.id, self.agent.generation)
		fout.write('Total generation of agent_%02d: %d\n' % (self.id, self.agent.generation))
		print 'Total restarts of agent_%02d: %d' % (self.id, self.agent.restarts)
		fout.write('Total restarts of agent_%02d: %d\n' % (self.id, self.agent.restarts))
		print 'Total time LocalSearch of agent_%02d: %s' % (self.id, str(self.agent.time_ls))
		fout.write( 'Total time LocalSearch of agent_%02d: %s\n' % (self.id, str(self.agent.time_ls)))
		print 'Total time Diversity calculations of agent_%02d: %s' % (self.id, str(self.agent.time_div))
		fout.write( 'Total time Diversity calculations of agent_%02d: %s\n' % (self.id, str(self.agent.time_div)))
		print 'Total time SEND of agent_%02d: %s' % (self.id, str(self.agent.time_send))
		fout.write( 'Total time SEND of agent_%02d: %s\n' % (self.id, str(self.agent.time_send)))
		print 'Total transactions SEND of agent_%02d: %s' % (self.id, str(self.agent.trx_send))
		fout.write( 'Total transactions SEND of agent_%02d: %s\n' % (self.id, str(self.agent.trx_send)))
		print 'Total time RECEIVE of agent_%02d: %s' % (self.id, str(self.agent.time_receive))
		fout.write( 'Total time RECEIVE of agent_%02d: %s\n' % (self.id, str(self.agent.time_receive)))
		print 'Total transactions RECEIVE of agent_%02d: %s\n' % (self.id, str(self.agent.trx_receive))
		fout.write( 'Total transactions RECEIVE of agent_%02d: %s\n\n' % (self.id, str(self.agent.trx_receive)))
		
		fout.close()
		self.agent.status_write('%s/log-agent-%02d.txt' % (self.results_path, self.id))
		
	
	def run(self):
		workers = []
		
		if self.agent.id_supporters:
			manager = Manager()
			if self.agent.id_leader == None:
				self.energy_list = manager.list(range(self.config.num_agents))
				for i in range(0, self.config.num_agents):
					self.energy_list[i] = 0
				self.stop_event = manager.Event()
			stop_event = manager.Event()
			
			for i in range(0, self.config.num_sup):
				if self.agent.id_leader == None:
					workers.append(WorkerProcess(self.agent.id_supporters[i], self.support_recv, self.support_send[i], self.agent_div_recv, self.support_div_recv[i], self.support_reset_recv[i], self.support_reset_send[i],
												 self.config, self.sequence, self.hist_obj, self.energy_list, stop_event, self.results_path))
				else:
					workers.append(WorkerProcess(self.agent.id_supporters[i], self.support_recv, self.support_send[i], self.root_div_send, self.support_div_recv[i], self.support_reset_recv[i], self.support_reset_send[i],
												 self.config, self.sequence, self.hist_obj, self.energy_list, stop_event, self.results_path))
			
			for worker in workers:
				worker.start()
		
		else:
			if self.agent.id_leader == None:
				self.energy_list = [0]
				self.stop_event = Event()
			
		
		jump_radius_aux = self.config.test_jump_dist
		self.agent.current.init_solution(self.hist_obj)
		self.agent.update()
		
		print 'WorkerProcess %d: \n%s' % (self.id, self.agent)
		
		start_process_time = datetime.datetime.now()
		self.agent.generation = 1
		
		best_energy = self.agent.pockets[0].energy_value
		gens_without_improve = 0
		gens_convergence = self.config.test_noimprove
		gens_start = 0
		restart_successed = True
		restarts_failed = 0
		energy_calls = sum(self.energy_list)
		self.agent.status_log_append(datetime.datetime.now() - start_process_time, energy_calls)
		
		
		while(self.stop_event.is_set() == False):
			
			# Crossover it isn't allowed to execute on agent 0
			if self.agent.id_leader != None:
				if self.agent.leader_pockets[0] != None:
					index_pocket_leader_agent = self.fitness_roulette_selection(self.agent.leader_pockets)
					index_pocket_self_agent = self.select_rand_solution(self.agent.pockets)
					self.agent.crossover(self.agent.leader_pockets[index_pocket_leader_agent], self.agent.pockets[index_pocket_self_agent], self.config.crossover_prob)
			else:
				index_pocket_self_agent = self.select_rand_solution(self.agent.pockets)
				self.agent.current = copy.deepcopy(self.agent.pockets[index_pocket_self_agent])
			
			# Local search
			time_ls_start = datetime.datetime.now()
			self.agent.simulated_annealing(self.config.ls_prob_ss, self.config.test_ls_fact, self.config.test_jump_prob, jump_radius_aux, self.config.test_temp_init, self.hist_obj)
			self.agent.time_ls += datetime.datetime.now() - time_ls_start
			jump_radius_aux = jump_radius_aux * self.config.test_jump_fact
			
			updated = self.agent.update()
			
			# Update pockets with supporter data
			if self.agent.id_supporters:
				while not self.support_recv.empty():
					self.receive_solution_pickle(self.support_recv, True)
					print '>> WorkerProcess %d receive a pocket from supporters, pocket list: %s' % (self.id, self.agent.pockets)
			
			# Update pocket_leader with leader data
			if self.agent.id_leader != None:
				if not self.leader_recv.empty():
					self.receive_solution_pickle(self.leader_recv, False)
					print '>> WorkerProcess %d receive a list of pockets from leader %d' % (self.id, self.agent.id_leader)
			
			if updated or self.agent.update():
				# Send pocket_leader with leader data
				if self.agent.id_supporters:
					for i in range(0, self.config.num_sup):
						if not self.support_send[i].full():
							print '> WorkerProcess %d send a list of pockets to supporter %d' % (self.id, self.agent.id_supporters[i])
							self.send_solution_pickle(self.agent.pockets, self.support_send[i])

				# Send pockets with supporter data
				if self.agent.id_leader != None:
					if self.agent.pockets[0].energy_value < best_energy:
						if not self.leader_send.full():
							print '> WorkerProcess %d send a pocket to leader %d with energy: %d' % (self.id, self.agent.id_leader, self.agent.pockets[0].energy_value)
							self.send_solution_pickle(self.agent.pockets[0], self.leader_send)
			
			if self.config.calculate_div_density:
				# Diversity density calculations
				time_div_start = datetime.datetime.now()

				if self.agent.id_leader == None:
					for i in range(0, self.config.num_agents-1):
						if not self.agent_div_recv[i].empty():
							buff = self.agent_div_recv[i].get()
							agent_pockets = pickle.loads(buff)
							j = 0
							for p in agent_pockets:
								if p != None:
									self.agent.population_pockets[i][j] = copy.deepcopy(p)
								else:
									break
								j += 1

					if self.agent.id_supporters:
						for i in range(0, self.config.num_sup):
							if not self.support_div_recv[i].empty():
								buff = self.support_div_recv[i].get()
								supporter_pockets = pickle.loads(buff)
								j = 0
								for p in supporter_pockets:
									if p != None:
										self.agent.supporter_pockets[i][j] = copy.deepcopy(p)
									else:
										break
									j += 1
				else:
					if not self.root_div_send[self.id-1].full():
						buff = pickle.dumps(self.agent.pockets, 2)
						self.root_div_send[self.id-1].put(buff)

					if not self.leader_div_send.full():
						buff = pickle.dumps(self.agent.pockets, 2)
						self.leader_div_send.put(buff)

					if self.agent.id_supporters:
						for i in range(0, self.config.num_sup):
							if not self.support_div_recv[i].empty():
								buff = self.support_div_recv[i].get()
								supporter_pockets = pickle.loads(buff)
								j = 0
								for p in supporter_pockets:
									if p != None:
										self.agent.supporter_pockets[i][j] = copy.deepcopy(p)
									else:
										break
									j += 1

				self.agent.calculate_densities()
				self.agent.time_div += datetime.datetime.now() - time_div_start

			self.agent.generation += 1
			
			# Reset control
			if self.config.if_reset:
				if self.agent.id_leader == None:
					if self.agent.pockets[0].energy_value == best_energy:
						gens_without_improve += 1
					else:
						gens_without_improve = 0

					if gens_without_improve == gens_convergence:
						if self.agent.id_supporters:
							for i in range(0, self.config.num_sup):
								self.support_reset_send[i].put(0)
							for i in range(0, self.config.num_sup):
								last_solution = pickle.loads(self.support_reset_recv[i].get())
								if last_solution.energy_value < best_energy:
									restarts_failed += 1
									restart_successed = False
									self.agent.update(last_solution)
									best_energy = self.agent.pockets[0].energy_value
									gens_without_improve = 0
						if restart_successed:
							print '\n***Restart successed***\n'
							self.event_restart.set()
							if self.agent.id_supporters:
								for i in range(0, self.config.num_sup):
									self.support_reset_send[i].put(True)
						else:
							print '\n***Restart failed: %d***\n' % restarts_failed
							if self.agent.id_supporters:
								for i in range(0, self.config.num_sup):
									self.support_reset_send[i].put(False)
						restart_successed = True
				else:
					if not self.leader_reset_recv.empty():
						self.leader_reset_recv.get()
						if self.agent.id_supporters:
							for i in range(0, self.config.num_sup):
								self.support_reset_send[i].put(0)
							for i in range(0, self.config.num_sup):
								self.receive_solution_pickle(self.support_reset_recv[i], True)
						self.send_solution_pickle(self.agent.pockets[0], self.leader_reset_send)
						restart_successed = self.leader_reset_recv.get()
						if restart_successed:
							self.event_restart.set()
							if self.agent.id_supporters:
								for i in range(0, self.config.num_sup):
									self.support_reset_send[i].put(True)
						else:
							if self.agent.id_supporters:
								for i in range(0, self.config.num_sup):
									self.support_reset_send[i].put(False)
						restart_successed = True
				
				# Is event restart set?
				if self.event_restart.is_set():
					if self.agent.id_leader == None:
						# Only the root leader can keep the best solution
						self.agent.pockets = [self.agent.pockets[0]] + [None for i in range(1, self.config.num_pockets)]
						self.agent.population_pockets = [[None for i in range(0, self.config.num_pockets)] for i in range(1, self.config.num_agents)]
						for i in range(0, self.config.num_agents-1):
							if not self.agent_div_recv[i].empty():
								self.agent_div_recv[i].get()
					else:
						self.agent.pockets = [None for i in range(0, self.config.num_pockets)]
						self.agent.leader_pockets = [None for i in range(0, self.config.num_pockets)]
						if not self.leader_recv.empty():
							self.leader_recv.get()
					
					if self.agent.id_supporters:
						while not self.support_recv.empty():
							self.support_recv.get()
						
						self.agent.supporter_pockets = [[None for i in range(0, config.num_pockets)] for i in range(1, config.num_sup+1)]
						for i in range(0, self.config.num_sup):
							if not self.support_div_recv[i].empty():
								self.support_div_recv[i].get()
						
					self.agent.restarts += 1

					print 'RESTARTING %3d - WorkerProcess %2d - %s' % (self.agent.restarts, self.id, self.agent)
					self.agent.current.init_solution(self.hist_obj)
					self.agent.update()
					jump_radius_aux = self.config.test_jump_dist
					gens_convergence = self.config.test_noimprove + self.agent.generation - gens_convergence - gens_start
					gens_start = self.agent.generation
					gens_without_improve = 0
					self.event_restart.clear()
					print 'RESTARTED %3d - WorkerProcess %2d - %s' % (self.agent.restarts, self.id, self.agent)
			
			self.energy_list[self.id] = self.agent.current.energy_calls
			energy_calls = sum(self.energy_list)
			self.agent.status_log_append(datetime.datetime.now() - start_process_time, energy_calls)
			
			if self.agent.id_leader == None:
				if energy_calls > self.config.energy_limit:
					self.stop_event.set()
			
			best_energy = self.agent.pockets[0].energy_value
		
		if self.agent.id_supporters:
			stop_event.set()
		if self.agent.id_leader != None:
			self.leader_send.cancel_join_thread()
			self.root_div_send[self.id-1].cancel_join_thread()
			self.leader_div_send.cancel_join_thread()
		
		self.save_results()
		
		if self.agent.id_supporters:
			for worker in workers:
				worker.join()
		
		print '\n************ WorkerProcess %d done ************\n' % (self.id)
