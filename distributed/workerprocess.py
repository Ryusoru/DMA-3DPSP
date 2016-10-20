#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import copy
import random
import datetime
import subprocess
import cPickle as pickle
from multiprocessing import Process, Manager, Condition, Lock, Event, Queue, Value
from multiprocessing.managers import SyncManager

from agent import *



class WorkerProcess(Process):
	def __init__(self, id, config, sequence, hist_obj, results_path, log_id):
		Process.__init__(self)
		self.id = id
		self.config = config
		self.sequence = sequence
		self.hist_obj = hist_obj
		self.agent = Agent(self.id, config, sequence)
		self.results_path = results_path
		self.log_id = log_id
		self.leader_send = None
		self.leader_recv = None
		self.support_send = [None for i in range(0, self.config.num_sup)] if id * self.config.num_sup + 1 < self.config.num_agents else None
		self.support_recv = [None for i in range(0, self.config.num_sup)] if id * self.config.num_sup + 1 < self.config.num_agents else None
		self.leader_reset_send = None
		self.leader_reset_recv = None
		self.support_reset_send = [None for i in range(0, self.config.num_sup)] if id * self.config.num_sup + 1 < self.config.num_agents else None
		self.support_reset_recv = [None for i in range(0, self.config.num_sup)] if id * self.config.num_sup + 1 < self.config.num_agents else None
		self.event_restart = Event()
		self.stop_event = Event()
		self.support_stop_event = [None for i in range(0, self.config.num_sup)] if id * self.config.num_sup + 1 < self.config.num_agents else None
		self.energy_number = Queue(1)
		self.support_energy_number = [None for i in range(0, self.config.num_sup)] if id * self.config.num_sup + 1 < self.config.num_agents else None
	
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
		
		self.agent.pockets[0].pose.dump_pdb('%s/agent-%02d.pdb' % (self.results_path, self.id))
		fout = open('%s/log-agent-%02d.txt' % (self.results_path, self.id), 'w')

		print '\n%s' % (self.agent)
		fout.write('%s\n' % (self.agent))
		print 'Total generation of agent_%02d: %d' % (self.id, self.agent.generation)
		fout.write('Total generation of agent_%02d: %d\n' % (self.id, self.agent.generation))
		print 'Total restarts of agent_%02d: %d' % (self.id, self.agent.restarts)
		fout.write('Total restarts of agent_%02d: %d\n' % (self.id, self.agent.restarts))
		print 'Total time LocalSearch of agent_%02d: %s' % (self.id, str(self.agent.time_ls))
		fout.write( 'Total time LocalSearch of agent_%02d: %s\n' % (self.id, str(self.agent.time_ls)))
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
	
	
	def make_server_manager(self, port, authkey):
		queue_send = Queue(1)
		queue_recv = Queue()
		queue_reset_send = Queue(1)
		queue_reset_recv = Queue(1)
		stop_event = Event()
		energy_number = Queue(1)
		
		class ServerManager(SyncManager):
			pass

		ServerManager.register('get_queue_send', callable=lambda: queue_send)
		ServerManager.register('get_queue_recv', callable=lambda: queue_recv)
		ServerManager.register('get_queue_reset_send', callable=lambda: queue_reset_send)
		ServerManager.register('get_queue_reset_recv', callable=lambda: queue_reset_recv)
		ServerManager.register('get_stop_event', callable=lambda: stop_event)
		ServerManager.register('get_energy_number', callable=lambda: energy_number)

		manager = ServerManager(address=('', port), authkey=authkey)
		manager.start()
		print 'Agent %d server started at port %d' % (self.id, port)
		return manager
	
	
	def make_client_manager(self, host, port, authkey):
		class ClientManager(SyncManager):
			pass

		ClientManager.register('get_queue_send')
		ClientManager.register('get_queue_recv')
		ClientManager.register('get_queue_reset_send')
		ClientManager.register('get_queue_reset_recv')
		ClientManager.register('get_stop_event')
		ClientManager.register('get_energy_number')

		manager = ClientManager(address=(host, port), authkey=authkey)
		manager.connect()
		print 'Agent %d client connected to %s at port %d ' % (self.id, host, port)
		return manager
	
	def run_servers(self):
		servers = [None for i in range(0, self.config.num_sup)]
		for i in range(0, self.config.num_sup):
			host = self.config.hosts[self.agent.id_supporters[i]][0]
			port = self.config.hosts[self.agent.id_supporters[i]][1]
			path = self.config.hosts[self.agent.id_supporters[i]][2]
			servers[i] = self.make_server_manager(port, '')
			self.support_send[i] = servers[i].get_queue_send()
			self.support_recv[i] = servers[i].get_queue_recv()
			self.support_reset_send[i] = servers[i].get_queue_reset_send()
			self.support_reset_recv[i] = servers[i].get_queue_reset_recv()
			self.support_stop_event[i] = servers[i].get_stop_event()
			self.support_energy_number[i] = servers[i].get_energy_number()
			
			if not os.path.exists(self.config.logs_path):
				os.makedirs(self.config.logs_path)
			
			argv = (str(self.config.protein) + ' ' + str(self.config.num_levels) + ' ' + str(self.config.num_sup) + ' ' + str(self.config.max_agents) + ' ' +
					str(self.config.num_pockets) + ' ' + str(self.config.if_reset) + ' ' + str(self.config.test_noimprove) + ' ' + str(self.config.score_weight) + ' ' +
					str(self.config.sasa_weight) + ' ' + str(self.config.energy_limit) + ' ' + str(self.agent.id_supporters[i]))
			cmd = 'python memetic_parallel.py %s %d > %s/memetic_parallel_%03d_agent-%02d.log 2>&1' % (argv, self.log_id, self.config.logs_path, self.log_id, self.agent.id_supporters[i])
			subprocess.Popen(['ssh', host, 'cd ' + path + ' && ' + cmd], stdin = None, stdout = None, stderr = None)
		return servers
	
	def run_client(self):
		host = self.config.hosts[self.agent.id_leader][0]
		port = self.config.hosts[self.id][1]
		client = self.make_client_manager(host, port, '')
		self.leader_send = client.get_queue_recv()
		self.leader_recv = client.get_queue_send()
		self.leader_reset_send = client.get_queue_reset_recv()
		self.leader_reset_recv = client.get_queue_reset_send()
		self.stop_event = client.get_stop_event()
		self.energy_number = client.get_energy_number()
	
	def run(self):
		if self.agent.id_leader != None:
			self.run_client()
		
		if self.agent.id_supporters:
			servers = self.run_servers()
		
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
		energy_calls = self.agent.current.energy_calls
		support_energy_calls = [0 for i in range(0, self.config.num_sup)]
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
				for i in range(0, self.config.num_sup):
					while not self.support_recv[i].empty():
						self.receive_solution_pickle(self.support_recv[i], True)
						print '>> WorkerProcess %d receive a pocket from supporter %d, pocket list: %s' % (self.id, self.agent.id_supporters[i], self.agent.pockets)
			
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
					else:
						self.agent.pockets = [None for i in range(0, self.config.num_pockets)]
						self.agent.leader_pockets = [None for i in range(0, self.config.num_pockets)]
						if not self.leader_recv.empty():
							self.leader_recv.get()
					
					if self.agent.id_supporters:
						for i in range(0, self.config.num_sup):
							while not self.support_recv[i].empty():
								self.support_recv[i].get()
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
			
			
			energy_calls = self.agent.current.energy_calls
			
			if self.agent.id_supporters:
				for i in range(0, self.config.num_sup):
					if not self.support_energy_number[i].empty():
						support_energy_calls[i] = self.support_energy_number[i].get()
					energy_calls += support_energy_calls[i]
			
			if not self.energy_number.full():
				self.energy_number.put_nowait(energy_calls)
			
			self.agent.status_log_append(datetime.datetime.now() - start_process_time, energy_calls)
			
			if self.agent.id_leader == None:
				if energy_calls > self.config.energy_limit:
					self.stop_event.set()
			
			best_energy = self.agent.pockets[0].energy_value
		
		if self.agent.id_supporters:
			for i in range(0, self.config.num_sup):
				self.support_stop_event[i].set()
		
		if self.agent.id_leader != None:
			self.leader_reset_send.put(0)
		
		self.save_results()
		
		if self.agent.id_supporters:
			for i in range(0, self.config.num_sup):
				self.support_reset_recv[i].get()
				servers[i].shutdown()
		
		print '\n************ WorkerProcess %d done ************\n' % (self.id)
