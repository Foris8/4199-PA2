import socket
import threading
import sys
import json
import time
import random
import pickle


BUFFER_SIZE = 1024
TIMEOUT = 0.5

class Packet:
    def __init__(self, seq_num, data):
        self.seq_num = seq_num
        self.data = data
        
class Gbnnode:
    def __init__(self,self_port, peer_port, window_size, drop_mode, drop_num):
        self.self_port = int(self_port)
        self.peer_port = int(peer_port)
        self.window_size = int(window_size)
        self.drop_mode = drop_mode
        self.drop_prob = float(drop_num)
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.bind(('localhost',self.self_port))
        self.seq_num = 0
        self.base = 0
        self.next_seq_num = 0
        self.buffer = []
        self.timer = None
        self.lock = threading.Lock()
        self.rcv_seq_num = 0
        self.drop_pck = 0
        self.total_pck = 0
    
    def send_buffer(self,msg):
        #Put data into buffer
        for i in msg:
            self.buffer.append(i)
        print(self.buffer)
    
    def msg_input(self):
        pck = input("<node> ")
        pck = pck.split(" ") 
        return pck[1]
    
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
        send_msg = self.msg_input()
        self.send_buffer(send_msg)
        self.start_timer()
        while self.base != len(self.buffer):
            while self.next_seq_num < (self.base + self.window_size) and self.next_seq_num < len(self.buffer):
                if self.drop_mode == "-p":
                    if random.random() > self.drop_prob:
                        packet = self.make_packet(self.next_seq_num)
                        self.socket.sendto(packet, ('localhost', self.peer_port))
                        self.total_pck +=1
                    else:
                        self.drop_pck += 1
                        seconds = time.time()
                        print(f"[{seconds}] ACK{self.next_seq_num} discarded")
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
                        print(f"[{seconds}] ACK{self.next_seq_num} discarded")
                    # if self.base == self.next_seq_num:
                    #     # Starst the timer if the first packet in the window is sent out
                    #     self.start_timer()
                    self.next_seq_num += 1
        
        loss_rate = self.drop_pck/self.total_pck
        print(f"[Summary] loss rate = {loss_rate}")       


    
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
        


    
if __name__ == "__main__":
    
    self_port = sys.argv[1] #self port
    peer_port = sys.argv[2] 
    window_size = sys.argv[3]
    drop_mode = sys.argv[4]
    drop_num = sys.argv[5] 
    print(self_port)
    print(peer_port)
    
    try:
        gnbnode=  Gbnnode(self_port,peer_port,window_size,drop_mode,drop_num)
        gnbnode.activate_data()
    except KeyboardInterrupt:
        print("Program terminated by user.")

