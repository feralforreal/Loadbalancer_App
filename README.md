# Loadbalancer_App
A round-robin load balancer application deployed on RYU Software-Defined Network controller to perform distributed load-balancing across multi-vendor servers using Python, mininet 
iles: lbalan.py and statefullb.py


Note: lbalan.py and statefullb.py are applications present in '~/.local/lib/python2.7/site-packages/ryu/ryu/app' 

Basic Topology Design :




![image](https://github.com/feralforreal/Loadbalancer_App/assets/132085748/3d2ebb20-47d0-4e39-a15c-b25e5654889d)




<<<<<<<<<<<<<<<< Stateless load balancer >>>>>>>>>>>>>>>>
1) In Mininet, execute the command 'sudo mn --topo single,7 --mac --controller=remote,ip=10.224.78.5 --switch ovs,protocols=OpenFlow13'
2) Initialize the RYU controller with the llb.py application using the command 'ryu run llb.py'
3) Using Xming, open terminals for all 7 hosts with the command 'xterm h1 h2 h3 h4 h5 h6 h7'
4) Execute 'python -m SimpleHTTPserver 80' on terminals of h1, h2 and h3
5) From h4, h5, h6 and h7, if you execute 'curl 10.0.0.100' or 'wget -O - 10.0.0.100', every new request will be redirected to a different server by the load balancer. Sequence: h4/h5/h6/h7 -> load balancer -> server.
6) The server then gets back to the host h4/h5/h6/h7 via the load balancer only. Sequence: h1/h2/h3 -> load balancer -> h4/h5/h6/h7
7) Since, on every new reuqest from one of the four hosts (clients), a new server is selected by the load balancer, like h1, then h2, then h3 and again back to h1 and so on, this is called as a round-robin load balancer.


Results : 

![image](https://github.com/feralforreal/Loadbalancer_App/assets/132085748/1cb8d387-5b56-40a9-b798-368a7496ccf5)

![image](https://github.com/feralforreal/Loadbalancer_App/assets/132085748/d722d0e5-43b7-4bcf-9eb7-9f5c399d4ef6)

![image](https://github.com/feralforreal/Loadbalancer_App/assets/132085748/7701b730-94c6-4f53-89e9-54ac0df1b19f)



<<<<<<<<<<<<<<<< Stateful load balancer >>>>>>>>>>>>>>>>

8) Execute the command 'sudo mn --topo single,7 --mac --controller=remote,ip=10.224.78.5 --switch ovs,protocols=OpenFlow13' in Mininet
9) Initialize the RYU controller with the pranit13extra.py application using the command 'ryu run pranit13extra.py'
10) In this case, any request made by curl or wget command from h4 or h5 would be redirected by the load balancer to h1 web server, requests from h6 would be redirected to h2 web server and requests from h7 would be redirected to h3 web server.
11) This re-direction to specific seervers by the load balancer is done on basis of source IP of the clients h4, h5, h6 and h7 that it learns
12) All communications to and fro the web servers are via the load balancer

Results:
![image](https://github.com/feralforreal/Loadbalancer_App/assets/132085748/0aa71bfb-cd6a-4973-9175-ec1243a7dabe)


![image](https://github.com/feralforreal/Loadbalancer_App/assets/132085748/4c41bf86-526b-4242-8a3d-5cb380b69d46)



<<<<<<<<<<<<<<<<<<<< Testing >>>>>>>>>>>>>>>>>>>>>>>>>>>>

We can test this using two applications. a basic web server and an echo server. Below are the Python scripts for both applications along with instructions on how to start and test them.

![image](https://github.com/feralforreal/Loadbalancer_App/assets/132085748/da6f580c-ad03-48ed-b0ae-c0b989056089)
OR 
![image](https://github.com/feralforreal/Loadbalancer_App/assets/132085748/9e5287ca-3699-4810-aa16-de47f01bd3fc)


How to Test:
Save the script as simple_web_server.py and run it using the following command:
python simple_web_server.py


2. Echo Server (using Python's socket module)
Python Script (echo_server.py):
![image](https://github.com/feralforreal/Loadbalancer_App/assets/132085748/853440b2-2f2f-438f-bc90-941359e69eca)

How to Start:
Save the script as echo_server.py.

Open a terminal.
Navigate to the directory containing your script.
Run the following command:
python echo_server.py
This will start an echo server on port 8888.

How to Test:
Open another terminal and use a tool like telnet or netcat to connect to the server:
telnet localhost 8888
Once connected, type any text, and the server should echo it back.

