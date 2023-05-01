
import socket
import threading
import sys
import json
import time
import random
import pickle
import time
#start the network 

BUFFER_SIZE = 1024
TIMEOUT = 0.5

class Packet:
    def __init__(self, seq_num, data):
        self.seq_num = seq_num
        self.data = data
        
class Gbnnode:
    def __init__(self,self_port, peer_port, drop_num):
        
        self.self_port = int(self_port)
        self.peer_port = int(peer_port)
        self.window_size = int(5)
        self.drop_mode = "-p"
        self.drop_prob = float(drop_num)
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        # self.socket.bind(('localhost',self.self_port))
        self.seq_num = 0
        self.base = 0
        self.next_seq_num = 0
        self.buffer = [0]*1024
        self.timer = None
        self.lock = threading.Lock()
        self.rcv_seq_num = 0
        self.drop_pck = 0
        self.total_pck = 0
    
    def send_buffer(self,msg):
        #Put data into buffer
        pass
        
    
    # def msg_input(self):
    #     pck = input("<node> ")
    #     pck = pck.split(" ") 
    #     return pck[1]
    
    def start_timer(self):
        if self.timer is not None:
            self.timer.cancel()
        self.timer = threading.Timer(TIMEOUT, self.on_timeout)
        self.timer.start()
        
    def on_timeout(self):
        # Resend all packets in the window
        with self.lock:
            self.next_seq_num = self.base
            if self.base != len(self.buffer):
                for i in range(self.base, self.base + self.window_size):
                    if i < len(self.buffer):
                            packet = self.make_packet(i)
                            self.socket.sendto(packet, ("localhost", self.peer_port))
                            self.total_pck +=1
                self.start_timer()
                # print("resend")
    
    def make_packet(self, seq_num):
        if seq_num >= len(self.buffer):
            return None
        data = self.buffer[seq_num]
        header = seq_num
        packet = (header,data)
        encoded_turple = pickle.dumps(packet)
        return encoded_turple
    
    def make_ack(self,seq_num):
        header = "ack"
        msg = seq_num
        packet = (header,msg)
        encoded_turple = pickle.dumps(packet)
        return encoded_turple
        
        
    def send_packet(self):
        # send_msg = self.msg_input()
        # self.send_buffer(send_msg)
        self.start_timer()
        while self.base != len(self.buffer):
            while self.next_seq_num < (self.base + self.window_size) and self.next_seq_num < len(self.buffer):
                if self.drop_mode == "-p":
                    if random.random() > self.drop_prob:
                        packet = self.make_packet(self.next_seq_num)
                        self.socket.sendto(packet, ('localhost', self.peer_port))
                        self.total_pck +=1
                        print("total pck:")
                        print(self.total_pck)
                        
                    else:
                        self.drop_pck += 1
                        seconds = time.time()
                        # print(f"[{seconds}] ACK{self.next_seq_num} discarded")
                        print("drop pck")
                        print(self.drop_pck)
                        self.loss_rate = self.drop_pck/(self.total_pck+1)
                        self.loss_rate =round(self.loss_rate,2)
                        print(self.loss_rate)
                    self.next_seq_num += 1
                else:                
                    if self.next_seq_num % self.drop_prob != 0.0:
                        packet = self.make_packet(self.next_seq_num)
                        self.socket.sendto(packet, ('localhost', self.peer_port))
                        self.total_pck +=1
                    else:
                        # print(self.next_seq_num%self.drop_prob)
                        self.drop_pck += 1
                        seconds = time.time()
                        # print(f"[{seconds}] ACK{self.next_seq_num} discarded")
                    # if self.base == self.next_seq_num:
                    #     # Starst the timer if the first packet in the window is sent out
                    #     self.start_timer()
                    self.next_seq_num += 1
        # print(self.buffer)
        
        # self.loss_rate = loss_rate
        print(f"[Summary] loss rate = {self.loss_rate}")       


    
    def receive_ack(self):
        while True:
            pck = self.socket.recv(1024)
            pck =pickle.loads(pck)
            header = pck[0] #get the seq_num   
        
            #there two things I have to do
            #first if the header is ack, we have to update our current window
            #if the header is a seq number, which means we are the receiver side, we have to send the ack back to the sender
            if header == "ack":
                #msg is the seq_number of the packet
                seq_num = pck[1]
                
                #if the base is the same as ack seq num, we move the window to next one 
                if self.base == seq_num:
                    # self.timer.cancel()
                    self.base += 1
                
                seconds = time.time()
                print(f"[{seconds}] ACK{seq_num} received, window moves to {self.base}")
                
           
            # else means the header is the sequnce 
            else:
                msg = pck[1]
                #header is the sequnce number
                seconds = time.time()
                if self.rcv_seq_num == header: #if the pck seq num match the rcv_seq_num
                    if self.drop_mode =="-p":
                        if random.random() > self.drop_prob:
                            print(f"[{seconds}] packet{header} {msg} received")
                            pck = self.make_ack(self.rcv_seq_num)
                            self.socket.sendto(pck, ('localhost', self.peer_port))
                            next_pack_num = self.rcv_seq_num + 1
                            print(f"[{seconds}] ACK{self.rcv_seq_num} sent, expecting packet{next_pack_num}")
                            self.rcv_seq_num += 1
                        else:
                            print(f"[{seconds}] pck{header}{msg} discarded")
                    else:
                            print(f"packet{header} {msg} received")
                            pck = self.make_ack(self.rcv_seq_num)
                            self.socket.sendto(pck, ('localhost', self.peer_port))
                            next_pack_num = self.rcv_seq_num + 1
                            print(f"[{seconds}] ACK{self.rcv_seq_num} sent, expecting packet{next_pack_num}")
                            self.rcv_seq_num += 1
                # print("ACK {}sent, expecting pack{}")
                
            
                
    
    

    def activate_data(self):
        listen = threading.Thread(target=self.receive_ack, args=()) #keep receiveing the message
        listen.start()
        
        self.send_packet()


class DVNode:
    def __init__(self, local_port, neighbors,reiceive_node,send_node):
        self.receive_node = reiceive_node #this node contains an array of its sending nodes and prob
        self.send_node = send_node
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
        self.start_prob = False
        
    
    def activate_gbn(self,self_port,peer_port,prob):
        gbnode = Gbnnode(self_port,peer_port,prob)
        gbnode.activate_data()
        time.sleep(1)
        loss_rate = gbnode.loss_rate
        
        return loss_rate
    
    def initiate_gbn_table(self):
        self.receive_table = {}
        self.send_table = {}
        
        #inital the send_table
        
        for port in send_node:
            if port != "last":
                self.send_table[port] = {
                    "send_pck" :0,
                    "ack" :0
                }
        
        #initial the rcv_table
        for i in range(0,len(receive_node),2):
            port = receive_node[i]
            p = receive_node[i+1]
            self.receive_table[port] = p
        
        print(self.receive_table)
        print(self.send_table)
    
    def gbn_prob(self,port_num,prob):
        total_count =0
        total_drop = 0
        port = port_num
        prob = float(prob)
        
        while True:
            if self.start_prob:
                start_time = time.time()
                while time.time() - start_time < 0.0005:
                    if random.random() <= prob:
                        total_drop +=1
                    
                    total_count+=1
                
                loss_rate = round(total_drop/total_count,2)
                (cost,next_hop)=self.routing_table[self.port][port]
                if loss_rate < cost:
                    (new_cost,new_hop) = (loss_rate,next_hop)
                    self.routing_table[self.port][port] =  (new_cost,new_hop)
                print(f"Link to {port_num}: {total_count} packets sent, {total_drop} packets lost, lost rate: {loss_rate}")
                time.sleep(5) 
            
        
        

    def make_send_pck(self,header,port,msg):
        header = header
        msg = msg
        pck = [header,port,msg]
        pck = pickle.dumps(pck)
        
        return pck  
    
    def send_pck(self):
        #if send the pck, the header should be send_pck and msg should be the port num
        # while True:
        # print("msg sendt")
        # while True:
        #     for port in self.send_table:
        #         pck = self.make_send_pck("pck",port,"")
        #         self.sock.sendto(pck,('localhost', int(port)))
        #         self.send_table[port]["send_pck"] +=1
        
            # if self.start_prob:
        for port in self.receive_table:
            prob = self.receive_table[port]
            # prob_mode = self.gbn_prob(port,prob)
            prob_mode = threading.Thread(target=self.gbn_prob,args=(port,prob))
            prob_mode.start()
                
                    # loss_rate = self.activate_gbn(self.port,port,prob)
                    # print("loss_rate")
                    # print(loss_rate)
            
                
        
        
    

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
        
        self.start_prob =True
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
        # if old_routing_table != self.routing_table:
        time.sleep(2.5)
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
        
            
            # print(header)
            
            
            # if header == "pck":
            #     port_num = pck[1]
            #     prob = self.receive_table[port_num]
            #     if random.random() > prob :
            #         pck = self.make_send_pck("ack",self.port,)
                    
                
            # elif header =="ack":
            #     port_num = pck[1]
            
            # #if not update the routing table
            # else:
            self.start_prob =True
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
        
        
        gbn = threading.Thread(target=self.send_pck,args=())
        gbn.start()
        
        
        
        
        

    #add time step and will be all right     

if __name__ == "__main__":

    
    #first thing it initiate the network 
    self_port = sys.argv[1]
    for idx, arg in enumerate(sys.argv):
        if arg == "send":
            send_idx = idx
        
        elif arg == "receive":
            receive_idx = idx
    
    receive_node = sys.argv[receive_idx+1:send_idx]
    send_node = sys.argv[send_idx+1:]
    
    #Have to initiate the GBN and DV algorithm
    neighbors = receive_node.copy()
    for ele in send_node:
        if ele !="last":
            neighbors.append(ele)
            neighbors.append("10")
        else:
            neighbors.append(ele)
        
    # #add the gbn_node
    # gbnnode = Gbnnode(self_port)    
    try:
        dvnode = DVNode(self_port,neighbors,receive_node,send_node)
        dvnode.initiate_gbn_table()
        dvnode.activate_routing()

    except KeyboardInterrupt:
        print("Program terminated by user.")
    
            
    
        