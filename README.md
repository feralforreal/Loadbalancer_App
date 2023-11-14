# Loadbalancer_App
A round-robin load balancer application deployed on RYU Software-Defined Network controller to perform load-balancing across servers using Python
iles: lbalan.py and statefullb.py


Note: lbalan.py and statefullb.py are applications present in '~/.local/lib/python2.7/site-packages/ryu/app' 

<<<<<<<<<<<<<<<< Stateless load balancer >>>>>>>>>>>>>>>>
1) In Mininet, execute the command 'sudo mn --topo single,7 --mac --controller=remote,ip=192.168.94.52 --switch ovs,protocols=OpenFlow13'
2) Initialize the RYU controller with the llb.py application using the command 'ryu run llb.py'
3) Using Xming, open terminals for all 7 hosts with the command 'xterm h1 h2 h3 h4 h5 h6 h7'
4) Execute 'python -m SimpleHTTPserver 80' on terminals of h1, h2 and h3
5) From h4, h5, h6 and h7, if you execute 'curl 10.0.0.100' or 'wget -O - 10.0.0.100', every new request will be redirected to a different server by the load balancer. Sequence: h4/h5/h6/h7 -> load balancer -> server.
6) The server then gets back to the host h4/h5/h6/h7 via the load balancer only. Sequence: h1/h2/h3 -> load balancer -> h4/h5/h6/h7
7) Since, on every new reuqest from one of the four hosts (clients), a new server is selected by the load balancer, like h1, then h2, then h3 and again back to h1 and so on, this is called as a round-robin load balancer.

<<<<<<<<<<<<<<<< Stateful load balancer >>>>>>>>>>>>>>>>
8) Execute the command 'sudo mn --topo single,7 --mac --controller=remote,ip=192.168.94.52 --switch ovs,protocols=OpenFlow13' in Mininet
9) Initialize the RYU controller with the pranit13extra.py application using the command 'ryu run pranit13extra.py'
10) In this case, any request made by curl or wget command from h4 or h5 would be redirected by the load balancer to h1 web server, requests from h6 would be redirected to h2 web server and requests from h7 would be redirected to h3 web server.
11) This re-direction to specific seervers by the load balancer is done on basis of source IP of the clients h4, h5, h6 and h7 that it learns
12) All communications to and fro the web servers are via the load balancer


<<<<<<<<<<<<<<<<<<<< Testing >>>>>>>>>>>>>>>>>>>>>>>>>>>>

We can test this using two applications. a basic web server and an echo server. Below are the Python scripts for both applications along with instructions on how to start and test them.

1. Basic Web Server
Python Script (simple_web_server.py):
from http.server import SimpleHTTPRequestHandler, HTTPServer

class SimpleServer(SimpleHTTPRequestHandler):
    pass

def run(server_class=HTTPServer, handler_class=SimpleServer, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting the web server on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run()

How to Test:
Save the script as simple_web_server.py and run it using the following command:
python simple_web_server.py


2. Echo Server (using Python's socket module)
Python Script (echo_server.py):
import socket

def run_server(host='127.0.0.1', port=8888):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"Echo server listening on {host}:{port}...")
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                conn.sendall(data)

if __name__ == "__main__":
    run_server()

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

