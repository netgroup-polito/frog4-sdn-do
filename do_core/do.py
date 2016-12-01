"""
@author: fabiomignini
@author: vida
@author: giacomoratta
@author: gabrielecastellano
"""

from __future__ import division
import logging
import copy

from do_core.domain_info import DomainInfo
from do_core.vnf_repository.rest import VNF_Repository_Rest
from nffg_library.nffg import FlowRule as NffgFlowrule, Action as NffgAction, VNF

from do_core.config import Configuration
from do_core.sql.graph_session import GraphSession, VnfModel
from do_core.resource_description import ResourceDescription
from do_core.netmanager import NetManager
from do_core.netmanager import OvsdbManager
from do_core.domain_information_manager import Messaging, DomainInformationManager

from do_core.exception import sessionNotFound, GraphError, NffgUselessInformations, MessagingError, VNFNotFound

from requests.exceptions import HTTPError


class DO(object):
    def __init__(self, user_data):

        self.__session_id = None
        self.__print_enabled = Configuration().OO_CONSOLE_PRINT

        self.nffg = None
        self.user_data = user_data
        '''
        Fields:
         - user_data.username
         - user_data.password
         - user_data.tenant
        '''

        # NetManager
        self.NetManager = NetManager()
        self.ovsdb = OvsdbManager()

    def __print(self, msg):
        if self.__print_enabled:
            print(msg)

    def NFFG_Put(self, nffg):
        """
        Manage the request of NF-FG instantiation.
        """
        logging.debug("Put NF-FG: put from user " + self.user_data.username + " on tenant " + self.user_data.tenant)

        # Check if the NF-FG is already instantiated, update it and exit
        if self.NFFG_Update(nffg) is not None:
            return self.__session_id

        # Instantiate a new NF-FG
        try:
            logging.debug("Put NF-FG: instantiating a new nffg: " + nffg.getJSON(True))
            self.__session_id = GraphSession().addNFFG(nffg, self.user_data.user_id)

            # Build the Profile Graph
            self.NetManager.ProfileGraph_BuildFromNFFG(nffg)

            # Set up GRE tunnels if any
            self.__NC_TunnelSetUp(nffg)

            # Send flow rules to Network Controller
            self.__NC_FlowsInstantiation(nffg)
            logging.debug("Flow rules instantiated!")

            # activate needed applications
            self.__NC_ApplicationsInstantiation(nffg)
            logging.debug("Applications activated!")

            logging.debug("Put NF-FG: session " + self.__session_id + " correctly instantiated!")

            GraphSession().updateStatus(self.__session_id, 'complete')

            # Update the resource description .json
            ResourceDescription().updateAll()
            ResourceDescription().saveFile()
            Messaging().publish_domain_description()

            return self.__session_id

        except MessagingError as err:
            logging.error(err.message)
            logging.error(err)
        except Exception as ex:
            logging.error(ex)
            self.__NFFG_NC_deleteGraph()
            GraphSession().updateError(self.__session_id)
            raise ex



    def NFFG_Update(self, new_nffg):

        # Check and get the session id for this user-graph couple
        logging.debug(
            "Update NF-FG: check if the user " + self.user_data.user_id + " has already instantiated the graph " + new_nffg.id + ".")
        session = GraphSession().getActiveUserGraphSession(self.user_data.user_id, new_nffg.id, error_aware=True)
        if session is None:
            return None
        self.__session_id = session.session_id
        logging.debug("Update NF-FG: already instantiated, trying to update it")

        try:
            logging.debug(
                "Update NF-FG: updating session " + self.__session_id + " from user " + self.user_data.username + " on tenant " + self.user_data.tenant)
            GraphSession().updateStatus(self.__session_id, 'updating')

            # Build the Profile Graph
            self.NetManager.ProfileGraph_BuildFromNFFG(new_nffg)

            # Get the old NFFG
            old_nffg = GraphSession().getNFFG(self.__session_id)
            logging.debug("Update NF-FG: the old session: " + old_nffg.getJSON())

            # Get the updated NFFG
            updated_nffg = old_nffg.diff(new_nffg)
            logging.debug("Update NF-FG: coming updates: " + updated_nffg.getJSON(True))

            # Delete useless endpoints and flowrules, from DB and Network Controller 
            self.__NFFG_NC_DeleteAndUpdate(updated_nffg)

            # Update database
            GraphSession().updateNFFG(updated_nffg, self.__session_id)

            # Set up GRE tunnels if any
            self.__NC_TunnelSetUp(new_nffg)

            # Send flowrules to Network Controller
            self.__NC_FlowsInstantiation(updated_nffg)
            logging.debug("Update NF-FG: session " + self.__session_id + " correctly updated!")

            # activate needed applications
            self.__NC_ApplicationsInstantiation(new_nffg)
            logging.debug("Applications activated!")

            GraphSession().updateStatus(self.__session_id, 'complete')

            # Update the resource description .json
            ResourceDescription().updateAll()
            ResourceDescription().saveFile()

            Messaging().publish_domain_description()

        except MessagingError as err:
            logging.error(err.message)
            logging.error(err)
        except Exception as ex:
            logging.error("Update NF-FG: ", ex)
            self.__NFFG_NC_deleteGraph()
            GraphSession().updateError(self.__session_id)
            raise ex
        return self.__session_id

    def NFFG_Delete(self, nffg_id):

        session = GraphSession().getActiveUserGraphSession(self.user_data.user_id, nffg_id, error_aware=False)
        if session is None:
            raise sessionNotFound("Delete NF-FG: session not found for graph " + str(nffg_id))
        self.__session_id = session.session_id

        try:
            instantiated_nffg = GraphSession().getNFFG(self.__session_id)
            logging.debug("Delete NF-FG: [session=" + str(
                self.__session_id) + "] we are going to delete: " + instantiated_nffg.getJSON())
            self.__NFFG_NC_deleteGraph()
            logging.debug("Delete NF-FG: session " + self.__session_id + " correctly deleted!")

            # Update the resource description .json
            ResourceDescription().updateAll()
            ResourceDescription().saveFile()

            Messaging().publish_domain_description()

        except MessagingError as err:
            logging.error(err.message)
            logging.error(err)
        except Exception as ex:
            logging.error("Delete NF-FG: ", ex)
            raise ex

    def NFFG_Get(self, nffg_id):
        session = GraphSession().getActiveUserGraphSession(self.user_data.user_id, nffg_id, error_aware=True)
        if session is None:
            raise sessionNotFound("Get NF-FG: session not found, for graph " + str(nffg_id))

        self.__session_id = session.session_id
        logging.debug("Getting session: " + str(self.__session_id))
        return GraphSession().getNFFG(self.__session_id)

    def NFFG_Get_All(self):

        logging.debug("Getting all graphs")
        nffgs = {'NF-FG': []}
        for nffg in GraphSession().getAllNFFG():
            nffgs['NF-FG'].append(nffg.getDict())
        return nffgs

    def NFFG_Status(self, nffg_id):
        session = GraphSession().getActiveUserGraphSession(self.user_data.user_id, nffg_id, error_aware=False)
        if session is None:
            raise sessionNotFound("Status NF-FG: session not found, for graph " + str(nffg_id))

        self.__session_id = session.session_id
        percentage = 0

        if session.status != 'error':
            percentage = GraphSession().getFlowruleProgressionPercentage(self.__session_id, nffg_id)

        logging.debug("Status NF-FG: graph status: " + str(session.status) + " " + str(percentage) + "%")
        return session.status, percentage

    def NFFG_Validate(self, nffg):
        """
        A validator for this specific domain orchestrator.
        The original json, as specified in the extern NFFG library,
        could contain useless objects and fields for this DO.
        If this happens, we have to raise exceptions to stop the request processing.
        """

        def raise_useless_info(msg):
            logging.debug("NFFG Validation: " + msg + ". This DO does not process this kind of data.")
            raise NffgUselessInformations("NFFG Validation: " + msg + ". This DO does not process this kind of data.")

        def raise_invalid_actions(msg):
            logging.debug("NFFG Validation: " + msg + ". This DO does not process this kind of flowrules.")
            raise NffgUselessInformations("NFFG Validation: " + msg +
                                          ". This DO does not process this kind of flowrules.")

        # EP Array
        EPs = {}

        '''
        The below domain could offer some network function capabilities that could be used to implement
        the VNFs of this graph. Here we check if this is possible (all VNFs of the graph could be implemented on the
        domain), else raise an error.
        '''
        # VNFs inspections
        # TODO this check is implemented comparing vnf name with fc type, in the future nffg should have vnf type
        domain_info = DomainInfo.get_from_file(Configuration().DOMAIN_DESCRIPTION_FILE)
        available_functions = []
        for functional_capability in domain_info.capabilities.functional_capabilities:
            available_functions.append(functional_capability.type)
        for vnf in nffg.vnfs:
            if vnf.name not in available_functions:
                response = self.get_VNF(vnf.name)  # check again if the vnf repository has the VNF
                #TODO: logica che sceglie tra i template ritornati, scarica l'immagine e installa l'app
                if response is False:
                    logging.debug("Passato di qui. do.py risposta falsa. lancio errore")
                    raise_useless_info("The VNF '" + vnf.name + "' cannot be implemented on this domain. VNF not found in the VNF Repository!")
                if response is True:
                    logging.debug("Passato di qui. do.py risposta true. installo app.")
                    try:
                        app_name = self.get_vnf_image_from_uri("http://127.0.0.1:8080/v2/nf_image/nat-1.0-SNAPSHOT.oar")
                    except:
                        raise NffgUselessInformations("Error! Cannot download vnf image from uri")
                    self.NetManager.install_app(app_name)
                    DomainInformationManager().fetch_functional_capabilities(vnf.name)


        '''
        Busy VLAN ID: the control on the required vlan id(s) must wait for
        the graph instantiation into the database in order to clarify the situation.
        Finally, the the control on the required vlan id(s) is always made before
        processing a flowrule (see the first rows of "__NC_ProcessFlowrule").
        '''

        # END POINTs inspections
        for ep in nffg.end_points:
            if ep.type is not None and ep.type != "interface" and ep.type != "vlan" and ep.type != "gre-tunnel":
                raise_useless_info("'end-points.type' must be 'interface', 'vlan' or 'gre-tunnel'" +
                                   " (not '" + ep.type + "')")
            '''
            if ep.remote_endpoint_id is not None:
                raise_useless_info("presence of 'end-points.remote_endpoint_id'")
            if ep.remote_ip is not None:
                raise_useless_info("presence of 'end-points.remote-ip'")
            if ep.local_ip is not None:
                raise_useless_info("presence of 'end-points.local-ip'")
            if ep.gre_key is not None:
                raise_useless_info("presence of 'gre-key'")
            '''
            if ep.ttl is not None:
                raise_useless_info("presence of 'ttl'")
            if ep.prepare_connection_to_remote_endpoint_id is not None:
                raise_useless_info("presence of connection to remote endpoint")
            if ep.prepare_connection_to_remote_endpoint_ids is not None and len(
                    ep.prepare_connection_to_remote_endpoint_ids) > 0:
                raise_useless_info("presence of connection to remote endpoints")
            """
            # Check endpoints in ResourceDescription.json (switch/port)
            if ResourceDescription().checkEndpoint(ep.node_id, ep.interface)==False:
                raise GraphError("Endpoint "+str(ep.id)+" not found")
            """
            # Check vlan availability
            # if ep.type == "vlan" and ep.vlan_id is not None:
            #    if ResourceDescription().VlanID_isAvailable(int(ep.vlan_id), ep.node_id, ep.interface)==False:
            #        vids_list = ResourceDescription().VlanID_getAvailables_asString(ep.node_id, ep.interface)
            #        raise GraphError("Vlan ID "+str(ep.vlan_id)+" not allowed on the endpoint "+str(ep.id)+"! Valid vlan ids: "+vids_list)

            # Add the endpoint
            EPs['endpoint:' + ep.id] = {"sid": ep.node_id, "pid": ep.interface}

        # FLOW RULEs inspection
        for flowrule in nffg.flow_rules:

            if flowrule.match is None:
                GraphError("Flowrule " + flowrule.id + " has not match section")
            if flowrule.match.port_in is None:
                GraphError("Flowrule " + flowrule.id + " has not an ingress endpoint ('port_in')")
            if self.__getEndpointIdFromString(flowrule.match.port_in) is None:
                GraphError("Flowrule " + flowrule.id + " has not an ingress endpoint ('port_in')")

            # Check vlan availability
            # if flowrule.match.vlan_id is not None and ResourceDescription().VlanID_isAvailable(int(flowrule.match.vlan_id), EPs[flowrule.match.port_in]['sid'], EPs[flowrule.match.port_in]['pid'])==False:
            #    vids_list = ResourceDescription().VlanID_getAvailables_asString(ep.node_id, ep.interface)
            #    raise GraphError("Vlan ID "+str(ep.vlan_id)+" not allowed! Valid vlan ids: "+vids_list)

            # Detect multiple output actions (they are not allowed).
            # If multiple output are needed, multiple flow rules should be written
            # in the nffg.json, with a different priorities!
            output_action_counter = 0
            output_ep = None
            for a in flowrule.actions:
                if a.controller is not None and a.controller == True:
                    raise_useless_info("presence of 'output_to_controller'")
                if a.output_to_queue is not None:
                    raise_useless_info("presence of 'output_to_queue'")
                if a.output is not None:
                    if output_action_counter > 0:
                        raise_invalid_actions(
                            "Multiple 'output_to_port' not allowed (flow rule " + str(flowrule.id) + ")")
                    output_action_counter = output_action_counter + 1
                    if self.__getEndpointIdFromString(a.output) is None:
                        GraphError("Flowrule " + str(
                            flowrule.id) + " has not an egress endpoint ('output_to_port' in 'action')")
                    output_ep = a.output

            # Check vlan availability
            for a in flowrule.actions:
                if a.push_vlan is not None and ResourceDescription().VlanID_isAvailable(int(a.push_vlan),
                                                                                        EPs[output_ep]['sid'],
                                                                                        EPs[output_ep]['pid']) == False:
                    vids_list = str(Configuration().VLAN_AVAILABLE_IDS)
                    raise GraphError("Vlan ID " + str(a.push_vlan) + " not allowed! Valid vlan ids: " + vids_list)
                if a.set_vlan_id is not None and ResourceDescription().VlanID_isAvailable(int(a.set_vlan_id),
                                                                                          EPs[output_ep]['sid'],
                                                                                          EPs[output_ep][
                                                                                              'pid']) == False:
                    vids_list = str(Configuration().VLAN_AVAILABLE_IDS)
                    raise GraphError("Vlan ID " + str(a.set_vlan_id) + " not allowed! Valid vlan ids: " + vids_list)

    '''
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
        NETWORK CONTROLLER INTERACTIONS
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
    '''

    def __NFFG_NC_deleteGraph(self):
        """
        Delete a whole graph, and set it as "ended".
        Delete all endpoints, and related resources.
        Delete all flowrules from database and from the network controller.
        Deactivate all applications implementing graph vnf
        """

        # TODO the graph is deleted only from the DB, not from the NC

        # Endpoints
        endpoints = GraphSession().getEndpointsBySessionID(self.__session_id)
        if endpoints is not None:
            for ep in endpoints:
                self.__deleteEndpointByID(ep.id)

        # Flowrules (maybe will never enter)
        flowrules = GraphSession().getFlowrules(self.__session_id)
        if flowrules is not None:
            for fr in flowrules:
                self.__deleteFlowRule(fr)

        # vnfs
        vnfs = GraphSession().getVnfsBySessionID(self.__session_id)
        if vnfs is not None:
            for vnf in vnfs:
                self.__deleteVnf(vnf)
                self.__NC_DeactivateApplication(vnf.application_name)

        # End field
        GraphSession().updateEnded(self.__session_id)

    def __NFFG_NC_DeleteAndUpdate(self, updated_nffg):
        """
        Remove all endpoints, flowrules and nf which are marked as 'to_be_deleted'.
        For each flowrule and vnf marked as 'already_deployed' this function checks if the
        releated endpoints are been updated: in this case the flowrule or vnf is deleted
        and it is set as 'new' in order that be installed again.
        """
        # Get domain informations from file
        domain_info = DomainInfo.get_from_file(Configuration().DOMAIN_DESCRIPTION_FILE)

        # List of updated endpoints
        updated_endpoints = []

        # Delete the endpoints 'to_be_deleted'
        for endpoint in updated_nffg.end_points[:]:  # "[:]" keep in memory deleted items during the loop.
            if endpoint.status == 'to_be_deleted':
                self.__deleteEndpointByID(endpoint.db_id)
                updated_nffg.end_points.remove(endpoint)
            elif endpoint.status == 'new' or endpoint.status is None:
                updated_endpoints.append(endpoint.id)

        # Delete the flowrules 'to_be_deleted'
        for flowrule in updated_nffg.flow_rules[:]:  # "[:]" keep in memory deleted items during the loop.

            # Delete flowrule
            if flowrule.status == 'to_be_deleted':  # and flowrule.type != 'external':
                self.__deleteFlowRuleByGraphID(flowrule.id)
                updated_nffg.flow_rules.remove(flowrule)

            # Set flowrule as "new" when associated endpoint has been updated
            elif flowrule.status == 'already_deployed':
                ep_in = self.__getEndpointIdFromString(flowrule.match.port_in)
                if ep_in is not None and ep_in in updated_endpoints:
                    flowrule.status = 'new'
                else:
                    for a in flowrule.actions:
                        ep_out = self.__getEndpointIdFromString(a.output)
                        if ep_out is not None and ep_out in updated_endpoints:
                            flowrule.status = 'new'

        # Delete the vnfs 'to_be_deleted'
        for vnf in updated_nffg.vnfs[:]:  # "[:]" keep in memory deleted items during the loop.
            if vnf.status == 'to_be_deleted':
                vnf_model = GraphSession().getVnfByID(vnf.id)
                self.__NC_DeactivateApplication(vnf_model.application_name)
                self.__deleteVnf(vnf)
                updated_nffg.vnfs.remove(vnf)
            elif vnf.status == 'already_deployed':
                # check if there are ports to update
                for port in vnf.ports[:]:
                    if port.status == 'new':
                        vnf.status = 'new'
                    elif port.status == 'to_be_deleted':
                        vnf.ports.remove(port)
                        vnf.status = 'new'
                # check if there are updated endpoints attached to the vnf
                flows = self.NetManager.ProfileGraph.get_flows_from_vnf(vnf)
                vnf_port_map = {}
                # get endpoints attached to vnf ports
                for flow in flows:
                    for action in flow.actions:
                        if action.output is not None:
                            vnf_port_map[flow.match.port_in.split(':', 2)[2]] = action.output
                # get interface names for endpoints
                for vnf_port in vnf_port_map:
                    endpoint = self.NetManager.ProfileGraph.getEndpoint(vnf_port_map[vnf_port].split(':')[1])
                    if endpoint in updated_endpoints:
                        vnf_model = GraphSession().getVnfByID(vnf.id)
                        self.__NC_DeactivateApplication(vnf_model.application_name)
                        self.__deleteVnf(vnf)
                        vnf.status = 'new'

    def __getEndpointIdFromString(self, endpoint_string):
        if endpoint_string is None:
            return None
        endpoint_string = str(endpoint_string)
        tmp2 = endpoint_string.split(':')
        port2_type = tmp2[0]
        port2_id = tmp2[1]
        if port2_type == 'endpoint':
            return port2_id
        return None

    def __NC_TunnelSetUp(self, nffg):

        # check for tunnel end points
        for ep in nffg.end_points:
            if ep.type == 'gre-tunnel':
                # set up tunnel through controller library
                port = GraphSession().getPort(ep.id)

                print("[New Gre] device:'"+Configuration().GRE_BRIDGE+"' port:'"+port.graph_port_id+"'")
                logging.info("[New Gre] device:'"+port.switch_id+"' port:'"+port.graph_port_id+"'")
                self.ovsdb.add_gre_tunnel(Configuration().GRE_BRIDGE, port.graph_port_id,
                                          ep.local_ip, ep.remote_ip, ep.gre_key)
                # change endpoint to an interface endpoint on the new gre interface
                ep.type = 'interface'
                ep.interface = port.graph_port_id
                ep.node_id = port.switch_id

    def __NC_FlowsInstantiation(self, nffg):

        # [ FLOW RULEs ]
        for flowrule in self.NetManager.ProfileGraph.get_ep_flowrules():

            # Check if this flowrule has to be installed
            if flowrule.status != 'new':
                continue

            # Get ingress endpoint
            logging.debug("port_in: " + flowrule.match.port_in)
            port_in_id = self.__getEndpointIdFromString(flowrule.match.port_in)
            logging.debug("port_in_id: " + port_in_id)
            in_endpoint = self.NetManager.ProfileGraph.getEndpoint(port_in_id)

            # Process flow rule with VLAN
            self.__NC_ProcessFlowrule(in_endpoint, flowrule)
            logging.debug("instantiated flow rule: " + str(flowrule.getDict()))

    def __NC_ApplicationsInstantiation(self, nffg):
        """
        Instantiate applications on the controller implementing VNFs of the NF_FG.
        The vnf are categorized in three groups:
        DETACHED: vnfs that have flows just to/from endpoints
        ATTACHED: vnfs that have flows to/from an other vnf
        :param nffg:
        :return:
        """

        def raise_useless_info(msg):
            logging.debug("NFFG vnf emulation: " + msg + ". This DO does not process this kind of data.")
            raise NffgUselessInformations("NFFG vnf emulation: " + msg + ". This DO does not process this kind of data.")

        domain_info = DomainInfo.get_from_file(Configuration().DOMAIN_DESCRIPTION_FILE)

        # [ DETACHED VNFs ]
        for vnf in self.NetManager.ProfileGraph.get_detached_vnfs():
            # get the name of the application
            application_name = ""
            for capability in domain_info.capabilities.functional_capabilities:
                if capability.type == vnf.name:
                    application_name = capability.name
            # we just need to activate the application and to pass as configuration the interfaces
            self.__NC_ProcessDetachedVnf(application_name, vnf)
            logging.debug("Activated application: " + application_name)

        # [ ATTACHED VNFs ]
        if len(self.NetManager.ProfileGraph.get_attached_vnfs()) != 0:
            # TODO add support to implement a vnf sending/receiving traffic to/from an other vnf
            raise_useless_info("Attached vnf not supported yet")

    def __NC_ProcessDetachedVnf(self, application_name, vnf):
        """
        Activate the application and push the port configuration in order to match the vnf setup
        :param application_name: application implementing the vnf
        :param vnf: vnf to emulate
        :type application_name: str
        :type vnf: VNF
        """
        self.__NC_ActivateApplication(application_name)
        self.__NC_ConfigureVnfPorts(application_name, vnf)

    def __NC_ActivateApplication(self, application_name):
        """
        Activate the given application on the Network Controller
        :param application_name:
        :return:
        """
        self.NetManager.activate_app(application_name)
        print("[Activated App] app-name:'"+application_name+"'")
        logging.info("[Activated App] app-name:'"+application_name+"'")

    def __NC_ConfigureVnfPorts(self, application_name, vnf):
        """
        push the port configuration to an application in order to match the vnf setup
        :param application_name: application implementing the vnf
        :param vnf: vnf to emulate
        :type application_name: str
        :type vnf: VNF
        :return:
        """
        # TODO I am assuming that flows are all bidirectional
        flows = self.NetManager.ProfileGraph.get_flows_from_vnf(vnf)
        vnf_port_map = {}   # key=graph port id, value=attached device/interface

        # get endpoints attached to vnf ports
        for flow in flows:
            for action in flow.actions:
                if action.output is not None:
                    vnf_port_map[flow.match.port_in.split(':', 2)[2]] = action.output

        # get interface names for endpoints
        for vnf_port in vnf_port_map:
            endpoint = self.NetManager.ProfileGraph.getEndpoint(vnf_port_map[vnf_port].split(':')[1])
            vnf_port_map[vnf_port] = {'device': endpoint.node_id, 'interface': endpoint.interface}

        # push configuration to set application ports
        ports_configuration = {'ports': {}}
        for port in vnf_port_map:
            ports_configuration['ports'][port] = {
                'device-id': vnf_port_map[port]['device'],
                'port-number': self.NetManager.getPortByInterface(
                    vnf_port_map[port]['device'],
                    vnf_port_map[port]['interface']
                )
            }
        self.NetManager.push_app_configuration(application_name, ports_configuration)
        print("[Configured App] app-name:'"+application_name+"' ports:'"+str(ports_configuration)+"'")
        logging.info("[Configured App] app-name:'"+application_name+"' ports:'"+str(ports_configuration)+"'")

    def __NC_DeactivateApplication(self, application_name):
        """
        Deactivate the application implementing the specified vnf
        :param application_name: the application to deactivate
        :type application_name: str
        :return:
        """
        self.NetManager.deactivate_app(application_name)
        print("[Deactivated App] app-name:'"+application_name+"'")
        logging.info("[Deactivated App] app-name:'"+application_name+"'")

    def __NC_ProcessFlowrule(self, in_endpoint, flowrule):
        '''
        in_endpoint = nffg.EndPoint
        flowrule = nffg.FlowRule
        
        Process a flow rule written in the section "big switch" of a nffg json.
        Add a vlan match/mod/strip to every flowrule in order to distinguish it.
        After the verification that output is an endpoint, this function manages
        three main cases:
            1) endpoints are on the same switch;
            2) endpoints are on different switches, so search for a path.
        '''

        # Endpoint.type = VLAN ...overwrites the match on vlan_id
        if in_endpoint.type == "vlan":
            flowrule.match.vlan_id = in_endpoint.vlan_id

        self.__NC_CheckFlowruleOnEndpoint(in_endpoint, flowrule)

        out_endpoint = None

        # Search for a "drop" action.
        # Install immediately the flow rule, and return.
        # If a flow rule has a drop action, we don't care of other actions!
        for a in flowrule.actions:
            if a.drop is True:
                single_efr = self.NetManager.externalFlowrule(nffg_match=flowrule.match, priority=flowrule.priority,
                                                              flow_id=flowrule.id, nffg_flowrule=flowrule)
                single_efr.setInOut(in_endpoint.node_id, a, in_endpoint.interface, None, "1")
                self.__Push_externalFlowrule(single_efr)
                return

        # Search for the output endpoint
        for a in flowrule.actions:
            if a.output is not None:
                port2_id = self.__getEndpointIdFromString(a.output)  # Is the 'output' destination an endpoint?
                if port2_id is not None:
                    out_endpoint = self.NetManager.ProfileGraph.getEndpoint(
                        port2_id)  # Endpoint object (declared in resources.py)
                    break

        # Out Endpoint not valid
        if out_endpoint is None:
            raise GraphError("Flowrule " + flowrule.id + " has an invalid egress endpoint")

        # [ 1 ] Endpoints are on the same switch
        if in_endpoint.node_id == out_endpoint.node_id:
            logging.debug("Endpoint are on the same switch.")
            # Error: endpoints are equal!
            if in_endpoint.interface == out_endpoint.interface:
                raise GraphError("Flowrule " + flowrule.id + " is wrong: endpoints are overlapping")

            # 'Single-switch' path
            self.__NC_LinkEndpointsByVlanID([in_endpoint.node_id], in_endpoint, out_endpoint, flowrule)
            return

        # [ 2 ] Endpoints are on different switches...search for a path!
        logging.debug("Endpoint are on different switches, finding a path...")
        nodes_path = self.NetManager.getShortestPath(in_endpoint.node_id, out_endpoint.node_id)
        if (nodes_path is not None):

            logging.info(
                "Found a path between " + in_endpoint.node_id + " and " + out_endpoint.node_id + ". " + "Path Length = " + str(
                    len(nodes_path)))
            if self.__NC_checkEndpointsOnPath(nodes_path, in_endpoint, out_endpoint) == False:
                logging.debug("Invalid link between the endpoints")
                return
            self.__NC_LinkEndpointsByVlanID(nodes_path, in_endpoint, out_endpoint, flowrule)
            return

        # [ 3 ] No paths between the endpoints 
        logging.debug("Cannot find a link between " + in_endpoint.node_id + " and " + out_endpoint.node_id)
        return

    def __NC_CheckFlowruleOnEndpoint(self, in_endpoint, flowrule):
        '''
        Check if the flowrule can be installed on the ingress endpoint.
        '''

        # Is the endpoint enabled?
        if GraphSession().isDirectEndpoint(in_endpoint.interface, in_endpoint.node_id):
            raise GraphError("The ingress endpoint " + in_endpoint.id + " is a busy direct endpoint")

        # Flowrule collision
        qref = GraphSession().getFlowruleOnTheSwitch(in_endpoint.node_id, in_endpoint.interface, flowrule)
        if qref is not None:
            raise GraphError(
                "Flowrule " + flowrule.id + " collides with an another flowrule on the ingress port (ingress endpoint " + in_endpoint.id + ").")

    def __NC_checkEndpointsOnPath(self, path, ep1, ep2):
        if len(path) < 2:
            return None
        # check if ep1 stays on the link
        if ep1.interface == self.NetManager.switchPortIn(path[0], path[1]):
            logging.debug(
                "...path not valid: endpoint " + ep1.node_id + " port:" + ep1.interface + " stay on the link!")
            return False
        # check if ep2 stays on the link
        path_last = len(path) - 1
        if ep2.interface == self.NetManager.switchPortIn(path[path_last], path[path_last - 1]):
            logging.debug(
                "...path not valid: endpoint " + ep2.node_id + " port:" + ep2.interface + " stay on the link!")
            return False
        return True

    def __NC_LinkEndpointsByVlanID(self, path, epIN, epOUT, flowrule):
        ''' 
        This function links two endpoints with a set of flow rules pushed in
        all the intermediate switches (and in first and last switches, of course).
        
        The link between this endpoints is based on vlan id.
        If no ingress (or egress) vlan id is specified, a suitable vlan id will be chosen.
        In any case, all the vlan ids will be checked in order to avoid possible 
        conflicts in the traversed switches.
        '''

        efr = self.NetManager.externalFlowrule(flow_id=flowrule.id, priority=flowrule.priority, nffg_flowrule=flowrule)

        base_actions = []
        vlan_out = None
        original_vlan_out = None
        vlan_in = None
        pop_vlan_flag = False

        # Initialize vlan_id and save it
        if flowrule.match.vlan_id is not None:
            vlan_in = flowrule.match.vlan_id
            original_vlan_out = vlan_in

        # Clean actions, search for an egress vlan id and pop vlan action
        for a in flowrule.actions:

            # [PUSH VLAN (ID)] Store the VLAN ID and remove the action
            if a.push_vlan is not None:
                vlan_out = a.push_vlan
                original_vlan_out = a.push_vlan
                continue

            # [SET VLAN ID] Store the VLAN ID and remove the action
            if a.set_vlan_id is not None:
                vlan_out = a.set_vlan_id
                original_vlan_out = a.set_vlan_id
                continue

            # [POP VLAN] Set the flag and remove the action
            if a.pop_vlan is not None and a.pop_vlan == True:
                pop_vlan_flag = True
                continue

            # Filter non OUTPUT actions
            if a.output is None:
                base_actions.append(copy.copy(a))

        ''' Remember to pop vlan header by the last switch.
            If vlan out is not None, a pushvlan/setvlan action is present, and popvlan action is incompatible.
            Otherwise, if vlan in is None, a vlan header will be pushed by the first switch,
            so it will have to be removed by the last switch.
            This flag is also set to True when a "pop-vlan" action and a vlan match are present. 
        '''
        pop_vlan_flag = (vlan_out is None) and (pop_vlan_flag or vlan_in is None)

        # [PATH] Traverse the path and create the flow for each switch
        logging.debug("Creating the flow for each switch")
        logging.debug("Path: " + str(path))
        for i in range(0, len(path)):
            logging.debug("index in path: " + str(i))
            hop = path[i]
            efr.set_flow_name(i)
            efr.set_actions(None)  # efr.set_actions(list(base_actions))

            # Switch position
            pos = 0  # (-2: 'single-switch' path, -1:first, 0:middle, 1:last)

            # Next switch and next ingress port
            next_switch_ID = None
            next_switch_portIn = None
            if i < (len(path) - 1):
                next_switch_ID = path[i + 1]
                next_switch_portIn = self.NetManager.switchPortIn(next_switch_ID, hop)

            # First switch
            if i == 0:
                pos = -1
                logging.debug("setting switch_id: " + epIN.node_id)
                efr.set_switch_id(epIN.node_id)
                port_in = self.NetManager.getPortByInterface(epIN.node_id, epIN.interface)
                port_out = self.NetManager.switchPortOut(hop, next_switch_ID)
                if port_out is None and len(path) == 1:  # 'single-switch' path
                    pos = -2
                    port_out = self.NetManager.getPortByInterface(epOUT.node_id, epOUT.interface)

            # Last switch
            elif i == len(path) - 1:
                pos = 1
                logging.debug("setting switch_id: " + epOUT.node_id)
                efr.set_switch_id(epOUT.node_id)
                port_in = self.NetManager.switchPortIn(hop, path[i - 1])
                port_out = self.NetManager.getPortByInterface(epOUT.node_id, epOUT.interface)
                # Add actions
                efr.set_actions(list(base_actions))

                # Force the vlan out to be equal to the original
                if pop_vlan_flag is False and original_vlan_out is not None:
                    vlan_out = original_vlan_out

            # Middle way switch
            else:
                efr.set_switch_id(hop)
                port_in = self.NetManager.switchPortIn(hop, path[i - 1])
                port_out = self.NetManager.switchPortOut(hop, next_switch_ID)

            # Vlan egress endpoint ...set the vlan_id
            if epOUT.type == 'vlan' and (pos == 1 or pos == -2):
                pop_vlan_flag = False
                vlan_out = epOUT.vlan_id

            # Check, generate and set vlan ids
            vlan_out, set_vlan_out = self.__checkAndSetVlanIDs(next_switch_ID, next_switch_portIn, flowrule.match,
                                                               vlan_out)

            # MATCH           
            base_nffg_match = copy.copy(flowrule.match)

            # VLAN In
            if vlan_in is not None:
                base_nffg_match.vlan_id = vlan_in

            # ACTIONS

            # Remove VLAN header
            if pop_vlan_flag and (pos == 1 or pos == -2):  # 1=last switch; -2='single-switch' path
                efr.append_action(NffgAction(pop_vlan=True))

            # Add/mod VLAN header
            if set_vlan_out is not None:

                # If there is a match rule on vlan id, it means a vlan header 
                # it is already present and we do not need to push a vlan.
                if vlan_in is None:
                    efr.append_action(NffgAction(push_vlan=True))
                    efr.append_action(NffgAction(set_vlan_id=set_vlan_out))

            # Set next ingress vlan
            vlan_in = vlan_out

            # Push the flow rule
            base_nffg_match.port_in = port_in
            efr.set_match(base_nffg_match)
            efr.append_action(NffgAction(output=port_out))
            self.__Push_externalFlowrule(efr)
        # end-for
        '''
        Note#1 - Where are the original vlan id?
            vlan in = flowrule.match.vlan_id
            vlan out = original_vlan_out
        '''
        return

    def __checkAndSetVlanIDs(self, switch_id, port_in, nffg_match, vlan_in=None):
        '''
        Receives the main parameters for a "vlan based" flow rule.
        Check all vlan ids on the specified ports of current switch and the next switch.
        If a similar "vlan based" flow rule exists, new vlan in/out will be chosen.
        This function make other some checks to verify the correctness of all parameters.
        
        '''
        # New Egress VLAN ID
        free_vlan_id = None
        if switch_id is not None:
            free_vlan_id = self.__getFreeVlanOnSwitch(switch_id, port_in, nffg_match, vlan_in)
            if free_vlan_id is None:
                raise GraphError("No free vlan ids on the switch " + switch_id)
            if free_vlan_id == vlan_in:
                free_vlan_id = None
        else:
            free_vlan_id = vlan_in

        previous_vlan_out = vlan_in
        set_previous_vlan_out = free_vlan_id
        if set_previous_vlan_out is not None:
            previous_vlan_out = set_previous_vlan_out

        return previous_vlan_out, set_previous_vlan_out

    def __getFreeVlanOnSwitch(self, switch_id, port_in, nffg_match, vlan_in=None):
        busy_vlan_ids = GraphSession().getBusyVlanInOnTheSwitch(switch_id, port_in, nffg_match)

        if vlan_in is not None and vlan_in not in busy_vlan_ids:
            return vlan_in

        # Select first valid VLAN ID
        for vid_range in Configuration().ALLOWED_VLANS:
            vid = vid_range[0]
            while vid < vid_range[1]:
                if vid not in busy_vlan_ids:
                    return vid
                vid = vid + 1
        return None

    '''
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
        DATABASE INTERACTIONS
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
    '''

    def __deleteFlowRuleByGraphID(self, graph_flow_rule_id):
        flowrules = GraphSession().getFlowrules(self.__session_id, graph_flow_rule_id)
        if flowrules is not None:
            for fr in flowrules:
                self.__deleteFlowRule(fr)

    def __deleteFlowRuleByID(self, flow_rule_id):
        fr = GraphSession().getFlowruleByID(flow_rule_id)
        if fr is None:
            return
        # if fr.internal_id is not None and fr.type is not None:
        #     self.__deleteFlowRule(fr)
        self.__deleteFlowRule(fr)

    # Database + Controller
    def __deleteFlowRule(self, flow_rule_ref):
        # flow_rule_ref is a FlowRuleModel object
        if flow_rule_ref.type == 'external':  # and flow.status == "complete"
            try:
                # PRINT
                self.__print(
                    "[Remove Flow] id:'" + flow_rule_ref.internal_id + "' device:'" + flow_rule_ref.switch_id + "'")
                logging.info(
                    "[Remove Flow] id:'" + flow_rule_ref.internal_id + "' device:'" + flow_rule_ref.switch_id + "'")
                # RESOURCE DESCRIPTION
                ResourceDescription().delete_flowrule(flow_rule_ref.id)

                # CONTROLLER
                self.NetManager.deleteFlow(flow_rule_ref.switch_id, flow_rule_ref.internal_id)
            except Exception as ex:
                if type(ex) is HTTPError and ex.response.status_code == 404:
                    logging.debug(
                        "External flow " + flow_rule_ref.internal_id + " does not exist in the switch " + flow_rule_ref.switch_id + ".")
                else:
                    logging.debug(
                        "Exception while deleting external flow " + flow_rule_ref.internal_id + " in the switch " + flow_rule_ref.switch_id + ". ")
                    raise ex
        GraphSession().deleteFlowruleByID(flow_rule_ref.id)

    def __deletePortByID(self, port_id):
        GraphSession().deletePort(port_id, self.__session_id)

    def __deleteEndpointByGraphID(self, graph_endpoint_id):
        ep = GraphSession().getEndpointByGraphID(graph_endpoint_id, self.__session_id)
        if ep is not None:
            self.__deleteEndpointByID(ep.id)

    def __deleteEndpointByID(self, endpoint_id):

        endpoint = GraphSession().getEndpointByID(endpoint_id)
        if endpoint.type == 'gre-tunnel':
                self.__deleteGreTunnel(endpoint_id)
        ep_resources = GraphSession().getEndpointResourcesByEndpointID(endpoint_id)
        if ep_resources is None:
            return
        for eprs in ep_resources:
            if eprs.resource_type == 'flow-rule':
                self.__deleteFlowRuleByID(eprs.resource_id)
            elif eprs.resource_type == 'port':
                self.__deletePortByID(eprs.resource_id)
        GraphSession().deleteEndpointByID(endpoint_id)

    def __deleteGreTunnel(self, endpoint_id):
        ep_resources = GraphSession().getEndpointResourcesPortByEndpointID(endpoint_id)
        if ep_resources is not None:  # <- non ci entra (?)
            port = GraphSession().getPortById(ep_resources.resource_id)
            # delete from controller
            print("[Remove Gre] device:'"+Configuration().GRE_BRIDGE+"' port:'"+port.graph_port_id+"'")
            logging.info("[Remove Gre] device:'"+Configuration().GRE_BRIDGE+"' port:'"+port.graph_port_id+"'")
            self.ovsdb.delete_gre_tunnel(Configuration().GRE_BRIDGE, port.graph_port_id)

    def __deleteVnf(self, vnf):
        vnf_ports = GraphSession().getVnfPortsByVnfID(vnf.id)
        for vnf_port in vnf_ports:
            self.__deleteVnfPortByID(vnf_port.id)
        GraphSession().deleteVnfByID(vnf.id)

    def __deleteVnfPortByID(self, port_id):
        GraphSession().deleteVnfPortByID(port_id)

    '''
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
        EXTERNAL FLOWRULE
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
    '''

    def __Push_externalFlowrule(self, efr):
        # efr = NetManager.externalFlowrule
        '''
        This is the only function that should be used to push an external flow
        (a "custom flow", in other words) in the database and in the network controller.
        GraphSession().addFlowrule(...) is also used in GraphSession().updateNFFG 
        and in GraphSession().addNFFG to store the flow rules written in nffg.json.
        '''

        nffg_match = efr.getNffgMatch()
        nffg_actions = efr.getNffgAction()
        nffg_flowrule = NffgFlowrule(match=nffg_match, actions=nffg_actions)

        '''
        Check if exists a flowrule with the same match criteria in the same switch (very rare event);
        If it exists, raise an exception!
        Similar flow rules are replaced by ovs switch, so one of them disappear!
        '''
        qref = GraphSession().getFlowruleOnTheSwitch(efr.get_switch_id(), nffg_match.port_in, nffg_flowrule)
        if qref is not None:
            raise GraphError(
                "Cannot install the flowrule " + efr.get_flow_name() + ". Collision on switch " + efr.get_switch_id() + " .")

        # If the flow name already exists, get new one
        self.__checkFlowname_externalFlowrule(efr)

        # NC/Switch: Add flow rule
        # sw_flow_name = self.NetManager.createFlow(efr)  # efr.get_flow_name()
        sw_flow_name = self.NetManager.createFlow(efr)  # efr.get_flow_name()

        # DATABASE: Add flow rule
        flow_rule = NffgFlowrule(_id=efr.get_flow_id(), node_id=efr.get_switch_id(), _type='external',
                                 status='complete', priority=efr.get_priority(), internal_id=sw_flow_name)
        flow_rule_db_id = GraphSession().addFlowrule(self.__session_id, efr.get_switch_id(), flow_rule)
        GraphSession().dbStoreMatch(nffg_match, flow_rule_db_id, flow_rule_db_id)
        GraphSession().dbStoreAction(nffg_actions, flow_rule_db_id)

        # RESOURCE DESCRIPTION
        #ResourceDescription().new_flowrule(flow_rule_db_id)

        # PRINT
        self.__print("[New Flow] id:'" + efr.get_flow_name() + "' device:'" + efr.get_switch_id() + "'")
        logging.info("[New Flow] id:'" + efr.get_flow_name() + "' device:'" + efr.get_switch_id() + "'")

    def __checkFlowname_externalFlowrule(self, efr):
        '''
        Check if the flow name already exists on the same switch,
        in order to avoid subscribing the existing flowrule in one switch.
        '''
        if GraphSession().externalFlowruleExists(efr.get_switch_id(), efr.get_flow_name()) == False:
            return

        efr.set_flow_name(0)
        this_efr = self.NetManager.externalFlowrule()

        flow_rules_ref = GraphSession().getExternalFlowrulesByGraphFlowruleID(efr.get_switch_id(), efr.get_flow_id())
        for fr in flow_rules_ref:
            if fr.type != 'external' or fr.internal_id is None:
                continue

            this_efr.set_complete_flow_name(fr.internal_id)

            if this_efr.compare_flow_name(
                    efr.get_flow_name()) < 2:  # [ ( this_efr.flow_name - prev_efr.flow_name ) < 2 ]
                efr.set_complete_flow_name(fr.internal_id)
                continue
            break
        efr.inc_flow_name()

    '''
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
    VNF_REPOSITORY
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
    '''
    def get_VNF(self, vnf_name):
            vnf_repository_endpoint=Configuration().VNF_REPOSITORY_ENDPOINT
            return VNF_Repository_Rest().get_vnf(vnf_repository_endpoint, vnf_name)

    def get_vnf_image_from_uri(self, vnf_image_uri):
        return VNF_Repository_Rest().get_vnf_image_from_uri(vnf_image_uri)
