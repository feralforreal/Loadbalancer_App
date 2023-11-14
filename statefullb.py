import random
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types, arp, tcp, ipv4
from ryu.ofproto import ether, inet
from ryu.ofproto import ofproto_v1_3
#from ryu.app.sdnhub_apps import learning_switch

    
class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.serverlist=[]                                                              #Creating a list of servers
        self.virtual_lb_ip = "10.0.0.100"                                               #Virtual Load Balancer IP
        self.virtual_lb_mac = "AB:BC:CD:EF:AB:BC"                                          #Virtual Load Balancer MAC Address
        self.counter = 0                                                                #Used to calculate mod in server selection below
        
        self.serverlist.append({'ip':"10.0.0.1", 'mac':"00:00:00:00:00:01", "outport":"1"})            #Appending all given IP's, assumed MAC's and ports of switch to which servers are connected to the list created 
        self.serverlist.append({'ip':"10.0.0.2", 'mac':"00:00:00:00:00:02", "outport":"2"})
        self.serverlist.append({'ip':"10.0.0.3", 'mac':"00:00:00:00:00:03", "outport":"3"})
        print("Done with initial setup related to server list creation.")
        

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def function_for_arp_reply(self, dst_ip, dst_mac):                                      #Function placed here, source MAC and IP passed from below now become the destination for the reply ppacket 
        print("Entered the ARP Reply function to build a packet and reply back appropriately.")
        arp_target_ip = dst_ip
        arp_target_mac = dst_mac
        src_ip = self.virtual_lb_ip                                                         #Making the load balancers IP and MAC as source IP and MAC
        src_mac = self.virtual_lb_mac

        arp_opcode = 2                          #ARP opcode is 2 for ARP reply
        hardware_type = 1                       #1 indicates Ethernet ie 10Mb
        arp_protocol = 2048                       #2048 means IPv4 packet
        ether_protocol = 2054                   #2054 indicates ARP protocol
        len_of_mac = 6                  #Indicates length of MAC in bytes
        len_of_ip = 4                   #Indicates length of IP in bytes

        pkt = packet.Packet()
        ether_frame = ethernet.ethernet(dst_mac, src_mac, ether_protocol)               #Dealing with only layer 2
        arp_reply_pkt = arp.arp(hardware_type, arp_protocol, len_of_mac, len_of_ip, arp_opcode, src_mac, src_ip, arp_target_mac, dst_ip)   #Building the ARP reply packet, dealing with layer 3
        pkt.add_protocol(ether_frame)
        pkt.add_protocol(arp_reply_pkt)
        pkt.serialize()
        print("Exiting the ARP Reply Function as done with processing for ARP reply packet.")
        return pkt
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)                
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        dpid = datapath.id
        #print("Debugging purpose dpid", dpid)
        
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        if eth.ethertype == ether.ETH_TYPE_ARP:                                   #If the ethernet frame has eth type as 2054 indicating as ARP packet..  
            arp_header = pkt.get_protocols(arp.arp)[0]
            
            if arp_header.dst_ip == self.virtual_lb_ip and arp_header.opcode == arp.ARP_REQUEST:                 #..and if the destination is the virtual IP of the load balancer and Opcode = 1 indicating ARP Request

                reply_packet=self.function_for_arp_reply(arp_header.src_ip, arp_header.src_mac)    #Call the function that would build a packet for ARP reply passing source MAC and source IP
                actions = [parser.OFPActionOutput(in_port)]
                packet_out = parser.OFPPacketOut(datapath=datapath, in_port=ofproto.OFPP_ANY, data=reply_packet.data, actions=actions, buffer_id=0xffffffff)    
                datapath.send_msg(packet_out)
                print("Debug: Sent the packet_out.")
            return

        
        ip_header = pkt.get_protocols(ipv4.ipv4)[0]
        tcp_header = pkt.get_protocols(tcp.tcp)[0]
      
        match = parser.OFPMatch(in_port=in_port, eth_type=eth.ethertype, eth_src=eth.src, eth_dst=eth.dst, ip_proto=ip_header.proto, ipv4_src=ip_header.src, ipv4_dst=ip_header.dst, tcp_src=tcp_header.src_port, tcp_dst=tcp_header.dst_port)

        if ip_header.src == "10.0.0.4" or ip_header.src == "10.0.0.5":
            server_mac_selected = self.serverlist[0]['mac']
            server_ip_selected = self.serverlist[0]['ip']
            server_outport_selected = int(self.serverlist [0]['outport'])
        elif ip_header.src == "10.0.0.6":
            server_mac_selected = self.serverlist[1]['mac']
            server_ip_selected = self.serverlist[1]['ip']
            server_outport_selected = int(self.serverlist [1]['outport'])
        else:
            server_mac_selected = self.serverlist[2]['mac']
            server_ip_selected = self.serverlist[2]['ip']
            server_outport_selected = int(self.serverlist [2]['outport'])

        actions = [parser.OFPActionSetField(ipv4_src=self.virtual_lb_ip), parser.OFPActionSetField(eth_src=self.virtual_lb_mac), parser.OFPActionSetField(eth_dst=server_mac_selected), parser.OFPActionSetField(ipv4_dst=server_ip_selected), parser.OFPActionOutput(server_outport_selected)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        cookie = random.randint(0, 0xffffffffffffffff)
        flow_mod = parser.OFPFlowMod(datapath=datapath, match=match, idle_timeout=7, instructions=inst, buffer_id = msg.buffer_id, cookie=cookie)
        datapath.send_msg(flow_mod)
        print("<========Packet sent from Client :"+str(ip_header.src)+" to Server: "+str(server_ip_selected)+", MAC: "+str(server_mac_selected)+" and on switch port: "+str(server_outport_selected)+"========>")  


        match = parser.OFPMatch(in_port=server_outport_selected, eth_type=eth.ethertype, eth_src=server_mac_selected, eth_dst=self.virtual_lb_mac, ip_proto=ip_header.proto, ipv4_src=server_ip_selected, ipv4_dst=self.virtual_lb_ip, tcp_src=tcp_header.dst_port, tcp_dst=tcp_header.src_port)
        actions = [parser.OFPActionSetField(eth_src=self.virtual_lb_mac), parser.OFPActionSetField(ipv4_src=self.virtual_lb_ip), parser.OFPActionSetField(ipv4_dst=ip_header.src), parser.OFPActionSetField(eth_dst=eth.src), parser.OFPActionOutput(in_port)]
        inst2 = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        cookie = random.randint(0, 0xffffffffffffffff)
        flow_mod2 = parser.OFPFlowMod(datapath=datapath, match=match, idle_timeout=7, instructions=inst2, cookie=cookie)
        datapath.send_msg(flow_mod2)
        print("<++++++++Reply sent from server having IP: "+str(server_ip_selected)+", MAC: "+str(server_mac_selected)+" to client:"+str(ip_header.src)+" via load balancer :"+str(self.virtual_lb_ip)+"++++++++>")
