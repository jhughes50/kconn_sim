#!/usr/bin/env python3

import rclpy
import random
import numpy as np
from rclpy.node import Node
from kconn_sim.barrier_certificates import BarrierCertificates
from kconn_sim.agent import Agent
from kconn_sim.cluster import Cluster
from kconn_sim.network import K1Network
from kconn_sim.plotting import *
from time import sleep
from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist

class Simulation(Node):

    def __init__(self):

        super().__init__('MultiAgentSim')

        self.num_agents =  20
        self.type0 = 15
        self.type1 = 5

        assert self.num_agents == (self.type0 + self.type1)

        self.k0 = 2
        self.k1 = 3

        self.n_clust = int(self.type0/self.type1)
        
        self.env = {0:np.array((-100,100,0)),
                         1: np.array((100,100,0)),
                         2: np.array((-100,-100,0))}

        self.locations = np.array((1,1,1)) 
        
        self.swarm = list()
        self.clusters = list()

        self.__init_swarm__()
        self.cycle()
        
        
    def __init_swarm__(self):

        for i in range(self.type0):
            
            self.swarm.append( Agent(i,
                                     np.append(np.random.randint(-5,5,size=2), np.array((0))),
                                     random.randint(0,2),
                                     0) )
            
        for i in range(self.type1):
            self.swarm.append( Agent(i+self.type0,
                                     np.append(np.random.randint(-5,5,size=2),np.array((1))),
                                     random.randint(0,2),
                                     1) )
            
        for i in range(self.n_clust):
            self.clusters.append( Cluster(i) ) 
            
        self.get_logger().info('Swarm Initialized')


    def locs_to_numpy(self):
        locs = list()
        for ag in self.swarm:
            locs.append(ag.location)

        self.locations =  np.array(locs)
        
    def cluster(self):

        locs = list()

        for ag in self.swarm:
            locs.append(ag.location)
        X = np.array( locs[0:self.type0] )

        km = KMeans(n_clusters = self.n_clust, random_state = 0).fit(X)

        return km.labels_, km.cluster_centers_

    def matching(self, centroids):
        W = cdist(self.locations[self.type0:],centroids, 'euclidean')
        for iter, ag in enumerate(self.swarm[self.type0:]):
            ag.cluster = np.argmin(W[iter])
        for cluster in self.clusters:
            cluster.add_members( self.swarm[self.type0:] )

    def cycle(self):

        while rclpy.ok():

            labels, centroids = self.cluster()

            for iter, ag in enumerate( self.swarm[:self.type0] ):
                ag.cluster = labels[iter]

            for cluster in self.clusters:
                cluster.set_members( self.swarm )
                cluster.set_centroid( centroids[cluster.cluster_id] )
            self.locs_to_numpy()

            self.matching(centroids)
            
            k1net = K1Network(self.clusters, self.k0)

            for ag in self.swarm:
                ag.set_connections(k1net.connections)
                print(ag)
            print(len(k1net.connections))
            break
            #sleep(1)

            
            

if __name__ == "__main__":
    rclpy.init()

    Simulation()