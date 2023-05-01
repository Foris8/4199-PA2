import socket
import threading
import sys
import json
import time
import random
import pickle
import time

class DVNode:
    def __init__(self, local_port, neighbors):
        self.port = local_port
        self.neighbors = neighbors
        self.neighbor_nodes = [] #contains the neighbor nodes
        self.routing_table = {}
        self.lock = threading.Lock()
        self.running = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('localhost', int(self.port)))
        self_last_check = False
        self.nodes_in_table =[]

    def initial_routing_table(self):
        #Have to check if the node is the last or not
        last_node = self.neighbors[-1]
        init_routing_table = {}
        if last_node =="last":
            #Have to start send the message
            for i in range(0,len(self.neighbors)-1,2):
                neighbor_port = self.neighbors[i]
                neighbor_weights = float(self.neighbors[i+1])
                init_routing_table[neighbor_port] = (neighbor_weights,None)
                self.neighbor_nodes.append(neighbor_port)
                self.nodes_in_table.append(neighbor_port)
                
            self.routing_table[self.port] = init_routing_table
            self.send_routing_table()
            
        # if it is not the last node just initiate the routing table    
        else:
            for i in range(0,len(self.neighbors)-1,2):
                neighbor_port = self.neighbors[i]
                neighbor_weights = float(self.neighbors[i+1])
                init_routing_table[neighbor_port] = (neighbor_weights,None)
                self.neighbor_nodes.append(neighbor_port)
                self.nodes_in_table.append(neighbor_port)

            self.routing_table[self.port] = init_routing_table
        
           
    
    #send the routing table to the neighbors
    def send_routing_table(self):
        for port in self.neighbor_nodes:
            packet = pickle.dumps((self.port,self.routing_table[self.port])) #send only its port
            self.sock.sendto(packet,('localhost', int(port)))
            
            seconds = time.time() # timestamp
            print(f"[{seconds}] Message sent from Node {self.port} to Node {port}")
            
    
        
        
    
    def start_routing(self):
        #initiate the routing table 
        self.initial_routing_table()
        print(self.routing_table)
    
    
    #Update the routing table when receive new info from other nodes,send the updated table    
    def update_routing_table(self,rcv_table):
        port_num, value = rcv_table
        seconds = time.time() # timestamp
        print(f"[{seconds}] Message received at Node {self.port} from Node {port_num}")
        old_routing_table = self.routing_table.copy()
        # key = next(iter(rcv_table))
        # value = rcv_table[key]
        # print(key)
        # print(value)
        self.routing_table[port_num] = value
        
        #after adding the new entry to the routing table, update the nodes in table
        for key in self.routing_table:
            
            # if key != self.port:
                new_nodes_arr = list(self.routing_table[key].keys())
                for node in new_nodes_arr:
                    if node not in self.routing_table[self.port] :
                        self.routing_table[self.port][node] = (1000,None)
                    elif node == self.port:
                        self.routing_table[self.port][node] = (0,None)
        
        #next need to conduct the bellman ford algorithm to update the internal distance
        # print("Bellman Ford")
        self.bellman_ford()
        # seconds = time.time() # timestamp
        # print(seconds)
        # print(self.routing_table)
        
        #check if the routing table is updated or not
        if old_routing_table != self.routing_table:
            self.send_routing_table()
        
        
    
    #Now I have to make bellman ford algorithm to update the table
    def bellman_ford(self):
        current_node_routing_table = self.routing_table[self.port]
        next_hop = None #define a none hop
        
        #key is the destination     
        for key in current_node_routing_table:
            # if key not in self.neighbor_nodes: #check if it is in neighbor nodes, if it is in, just skip dont need to update
            (weight,hop) = current_node_routing_table[key]
            best_weight = weight #assign the weight to the best
            best_hop = hop
            
            
            #check the neighbors nodes cost to destination
            for nei_node in self.neighbor_nodes:
                
                #
                if nei_node in self.routing_table:
                    (neighbor_cost,neighbor_hop) = self.routing_table[nei_node][self.port]
                    if key in self.routing_table[nei_node]:
                        (next_weight,next_hop) = self.routing_table[nei_node][key]
                        
                        next_weight += neighbor_cost
                        if next_weight < best_weight:
                            best_weight = next_weight
                            best_hop = nei_node

            self.routing_table[self.port][key] = (best_weight,best_hop)
            
            
                        
                    
               
    def report_routing_table(self):
        seconds = time.time() # timestamp
        print(f"[{seconds}] Node {self.port} Routing Table: ")
        routing_table = self.routing_table[self.port]
        # print(routing_table)
        
        for key in routing_table:
            (cost,next_hop) =routing_table[key]
            print(f"{cost} -> Node {key} ; Next hop -> Node {next_hop}")
        
        
            
    def receive_packet(self):
        while True:
            pck = self.sock.recv(1024)
            pck = pickle.loads(pck)
            self.update_routing_table(pck)
            seconds = time.time() # timestamp
    
            
            # print("after update")
            
            # print(self.routing_table)
            self.report_routing_table()
            
            
            #update the routing table
            #have to check it there any new nodes not recorded!

            #1. Find the key and value
                 
    def activate_routing(self):
        listen = threading.Thread(target=self.receive_packet, args=()) #keep receiveing the message
        listen.start()
        
        self.start_routing()

    #add time step and will be all right


if __name__ =="__main__":
        
        a = sys.argv
        local_port = a[1]
        last_input_checker = a[-1]
        
        neighbors = a[2:]
        # #check the last input is "last" or not 
        # if last_input_checker == "last":
        #     neighbor_ports = a[2:-1]
        # else:
        #     neighbor_ports = a[2:]
        
        # #Now I have the values for neighbor nodes    
        # neighbors = {}    
        # for i in range(0,len(neighbor_ports),2):
        #     neighbors[neighbor_ports[i]] = neighbor_ports[i+1]
        try:
            dvnode = DVNode(local_port,neighbors)
            dvnode.activate_routing()
        except KeyboardInterrupt:
            print("Program terminated by user.")