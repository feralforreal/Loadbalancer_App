import random
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types, arp, tcp, ipv4

class LoadBalancerApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(LoadBalancerApp, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.serverlist = []  
        self.virtual_lb_ip = "10.0.0.100"  
        self.virtual_lb_mac = "AB:BC:CD:EF:AB:BC"  
        self.counter = 0 

        self.serverlist.append({'ip': "10.0.0.1", 'mac': "00:00:00:00:00:01", "outport": "1"}) 
        self.serverlist.append({'ip': "10.0.0.2", 'mac': "00:00:00:00:00:02", "outport": "2"})
        self.serverlist.append({'ip': "10.0.0.3", 'mac': "00:00:00:00:00:03", "outport": "3"})
        print("Done with initial setup related to server list creation.")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        dp = ev.msg.dp
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        mch = parser.OFPmch()
        actn = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 0, mch, actn)

    def add_flow(self, dp, priority, mch, actn, buffer_id=None):
        ofproto = dp.ofproto
        parser = dp.ofproto_parser

        inst = [parser.OFPInstructionactn(ofproto.OFPIT_APPLY_actn,
                                             actn)]
        if buffer_id:
            mod = parser.OFPFlowMod(dp=dp, buffer_id=buffer_id,
                                    priority=priority, mch=mch,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(dp=dp, priority=priority,
                                    mch=mch, instructions=inst)
        dp.send_msg(mod)

    def function_for_arp_reply(self, dst_ip, dst_mac):
        print("(((Entered the ARP Reply function to build a packet and reply back appropriately)))")
        arp_target_ip = dst_ip
        arp_target_mac = dst_mac
        src_ip = self.virtual_lb_ip  
        src_mac = self.virtual_lb_mac

        arp_opcode = 2  
        hardware_type = 1  
        arp_protocol = 2048  
        ether_protocol = 2054  
        len_of_mac = 6  
        len_of_ip = 4  

        pkt = packet.Packet()
        ether_frame = ethernet.ethernet(dst_mac, src_mac, ether_protocol)  
        arp_reply_pkt = arp.arp(hardware_type, arp_protocol, len_of_mac, len_of_ip, arp_opcode, src_mac, src_ip,
                                arp_target_mac, dst_ip)  
        pkt.add_protocol(ether_frame)
        pkt.add_protocol(arp_reply_pkt)
        pkt.serialize()
        print("{{{Exiting the ARP Reply Function as done with processing for ARP reply packet}}}")
        return pkt

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        dp = msg.dp
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        in_port = msg.mch['in_port']
        dpid = dp.id

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        if eth.ethertype == ether_types.ETH_TYPE_ARP:  
            arph = pkt.get_protocols(arp.arp)[0]

            if arph.dst_ip == self.virtual_lb_ip and arph.opcode == arp.ARP_REQUEST:
               
                reply_packet = self.function_for_arp_reply(arph.src_ip, arph.src_mac)
                actn = [parser.OFPActionOutput(in_port)]
                packet_out = parser.OFPPacketOut(dp=dp, in_port=ofproto.OFPP_ANY, data=reply_packet.data,
                                                  actn=actn, buffer_id=0xffffffff)
                dp.send_msg(packet_out)
                print("::::Sent the packet_out::::")
            return

        iph = pkt.get_protocols(ipv4.ipv4)[0]
        tch = pkt.get_protocols(tcp.tcp)[0]

        count = self.counter % 3  
        s_ip = self.serverlist[count]['ip']
        s_mac = self.serverlist[count]['mac']
        s_otput = self.serverlist[count]['outport']
        s_otput = int(s_otput)
        self.counter = self.counter + 1
        print("The selected server is ===> ", s_ip)

        
        mch = parser.OFPmch(in_port=in_port, eth_type=eth.ethertype, eth_src=eth.src, eth_dst=eth.dst,
                                ip_proto=iph.proto, ipv4_src=iph.src, ipv4_dst=iph.dst,
                                tcp_src=tch.src_port, tcp_dst=tch.dst_port)
        actn = [parser.OFPactnetField(ipv4_src=self.virtual_lb_ip),
                   parser.OFPactnetField(eth_src=self.virtual_lb_mac),
                   parser.OFPactnetField(eth_dst=s_mac),
                   parser.OFPactnetField(ipv4_dst=s_ip),
                   parser.OFPActionOutput(s_otput)]
        inst = [parser.OFPInstructionactn(ofproto.OFPIT_APPLY_actn, actn)]
        cookie = random.randint(0, 0xffffffffffffffff)
        flow_mod = parser.OFPFlowMod(dp=dp, mch=mch, idle_timeout=7, instructions=inst,
                                     buffer_id=msg.buffer_id, cookie=cookie)
        dp.send_msg(flow_mod)
        print("<========Packet from client: " + str(iph.src) + ". Sent to server: " + str(
            s_ip) + ", MAC: " + str(s_mac) + " and on switch port: " + str(
            s_otput) + "========>")

   
        mch = parser.OFPmch(in_port=s_otput, eth_type=eth.ethertype,
                                eth_src=s_mac, eth_dst=self.virtual_lb_mac, ip_proto=iph.proto,
                                ipv4_src=s_ip, ipv4_dst=self.virtual_lb_ip,
                                tcp_src=tch.dst_port, tcp_dst=tch.src_port)
        actn = [parser.OFPactnetField(eth_src=self.virtual_lb_mac),
                   parser.OFPactnetField(ipv4_src=self.virtual_lb_ip),
                   parser.OFPactnetField(ipv4_dst=iph.src),
                   parser.OFPactnetField(eth_dst=eth.src),
                   parser.OFPActionOutput(in_port)]
        inst2 = [parser.OFPInstructionactn(ofproto.OFPIT_APPLY_actn, actn)]
        cookie = random.randint(0, 0xffffffffffffffff)
        flow_mod2 = parser.OFPFlowMod(dp=dp, mch=mch, idle_timeout=7, instructions=inst2, cookie=cookie)
        dp.send_msg(flow_mod2)
        print("<++++++++Reply sent from server: " + str(s_ip) + ", MAC: " + str(
            s_mac) + ". Via load balancer: " + str(
            self.virtual_lb_ip) + ". To client: " + str(iph.src) + "++++++++>")

if __name__ == "__main__":
    from ryu.cmd import manager

    manager.main()

