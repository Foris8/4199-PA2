# 4199-PA2


2. Go-Back-N Protocol

python3 gbnnode.py <self-port> <peer-port> <window-size> [ -d <value-of-n> | -p <value-of-p>]

The user can choose which mode to be used. If user input "-d", it means the GBN node will drop the packets in a  deterministic way. If user choose "-p", the GBN node will drop the packets with a probability of p.

The sample input to the terminal is :
python3 gbnnode.py 1111 2222 5 -p 0.1

open another terminal:
python3 gbnnode.py 2222 1111 5 -p 0.1

The GBN node will compute the loss rate and conduct GBN algorithm. The sample test is in test.txt.

3. Distance- Vector Routing Algorithm
The algorithm will start to compute when the input from users contains "last". The routing table of each node will start to update when there is an change in routing table. The timestamp is used to record the information exchange. The routing table will stop to change when the routing table converges.

To start the algorithm, the user has to open four terminals and input the following command.
$ ./dvnode 1111 2222 .1 3333 .5
$ ./dvnode 2222 1111 .1 3333 .2 4444 .8
$ ./dvnode 3333 1111 .5 2222 .2 4444 .5
$ ./dvnode 4444 2222 .8 3333 .5 last

4. Combination
In this problem, I have to combine GBN node and DV node together to update the routing table while sending prob packets to the other router. The DV table will update for every 5 seconds or if there is any change in the routing table. And the link cost will be updated in a fixed interval.

To start the algorithm, the user has to open four terminals and input the following command:

$ ./cnnode 1111 receive send 2222 3333
$ ./cnnode 2222 receive 1111 .1 send 3333 4444
$ ./cnnode 3333 receive 1111 .5 2222 .2 send 4444
$ ./cnnode 4444 receive 2222 .8 3333 .5 send last 

The DV node and GBN node will start to run when the last command input
