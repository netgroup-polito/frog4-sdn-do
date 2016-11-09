CREATE TABLE "action" (
  "id" int(64) NOT NULL,
  "flow_rule_id" varchar(64) NOT NULL,
  "output_type" varchar(64) DEFAULT NULL,
  "output_to_port" varchar(64) DEFAULT NULL,
  "output_to_controller" tinyint(1) DEFAULT NULL,
  "_drop" tinyint(1) DEFAULT NULL,
  "set_vlan_id" varchar(64) DEFAULT NULL,
  "set_vlan_priority" varchar(64) DEFAULT NULL,
  "push_vlan" varchar(64) DEFAULT NULL,
  "pop_vlan" tinyint(1) DEFAULT NULL,
  "set_ethernet_src_address" varchar(64) DEFAULT NULL,
  "set_ethernet_dst_address" varchar(64) DEFAULT NULL,
  "set_ip_src_address" varchar(64) DEFAULT NULL,
  "set_ip_dst_address" varchar(64) DEFAULT NULL,
  "set_ip_tos" varchar(64) DEFAULT NULL,
  "set_l4_src_port" varchar(64) DEFAULT NULL,
  "set_l4_dst_port" varchar(64) DEFAULT NULL,
  "output_to_queue" varchar(64) DEFAULT NULL,
  PRIMARY KEY ("id")
);
CREATE TABLE "endpoint" (
  "id" int(64) NOT NULL,
  "graph_endpoint_id" varchar(64) NOT NULL,
  "name" varchar(64) DEFAULT NULL,
  "type" varchar(64) DEFAULT NULL,
  "session_id" varchar(64) NOT NULL,
  PRIMARY KEY ("id")
);
CREATE TABLE "endpoint_resource" (
  "endpoint_id" int(64) NOT NULL,
  "resource_type" varchar(64) NOT NULL,
  "resource_id" int(64) NOT NULL,
  PRIMARY KEY ("endpoint_id","resource_type","resource_id")
);
CREATE TABLE "match" (
  "id" int(64) NOT NULL,
  "flow_rule_id" varchar(64) NOT NULL,
  "port_in_type" varchar(64) DEFAULT NULL,
  "port_in" varchar(64) DEFAULT NULL,
  "ether_type" varchar(64) DEFAULT NULL,
  "vlan_id" varchar(64) DEFAULT NULL,
  "vlan_priority" varchar(64) DEFAULT NULL,
  "source_mac" varchar(64) DEFAULT NULL,
  "dest_mac" varchar(64) DEFAULT NULL,
  "source_ip" varchar(64) DEFAULT NULL,
  "dest_ip" varchar(64) DEFAULT NULL,
  "tos_bits" varchar(64) DEFAULT NULL,
  "source_port" varchar(64) DEFAULT NULL,
  "dest_port" varchar(64) DEFAULT NULL,
  "protocol" varchar(64) DEFAULT NULL,
  PRIMARY KEY ("id")
);
CREATE TABLE "port" (
  "id" int(64) NOT NULL,
  "graph_port_id" varchar(64) NOT NULL,
  "status" varchar(64) DEFAULT NULL,
  "switch_id" varchar(64) DEFAULT NULL,
  "session_id" varchar(64) NOT NULL,
  "mac_address" varchar(64) DEFAULT NULL,
  "ipv4_address" varchar(64) DEFAULT NULL,
  "tunnel_remote_ip" varchar(64) DEFAULT NULL,
  "vlan_id" varchar(64) DEFAULT NULL,
  "gre_key" varchar(64) DEFAULT NULL,
  "creation_date" datetime NOT NULL,
  "last_update" datetime DEFAULT NULL,
  PRIMARY KEY ("id")
);
CREATE TABLE "tenant" (
  "id" varchar(64) NOT NULL,
  "name" varchar(64) NOT NULL,
  "description" varchar(128) NOT NULL,
  PRIMARY KEY ("id")
);
INSERT INTO "tenant" ("id","name","description") VALUES ('1','admin_tenant','Admin Tenant');
CREATE TABLE 'user' (
  "id" varchar(64) NOT NULL,
  "tenant_id" varchar(64) NOT NULL,'username' varchar(64) NOT NULL,
  "pwdhash" varchar(64) NOT NULL,
  "mail" varchar(64) DEFAULT NULL,
  "token"  varchar(64) DEFAULT NULL ,
  "token_timestamp"  int(64) DEFAULT NULL ,
  PRIMARY KEY ("id")
);
INSERT INTO "user" ("id","tenant_id","username","pwdhash","mail","token","token_timestamp") VALUES ('1','1','admin','8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918','admin@admin',NULL,NULL);
CREATE TABLE 'graph_session' (
  "session_id" varchar(64) NOT NULL,
  "user_id" varchar(64) DEFAULT NULL,
  "graph_id" varchar(64) NOT NULL,
  "graph_name" varchar(64) NOT NULL,
  "status" varchar(64) NOT NULL,
  "started_at" datetime NOT NULL,
  "last_update" datetime DEFAULT NULL,
  "error" datetime DEFAULT NULL,
  "ended" datetime DEFAULT NULL, 'description'  varchar(256) DEFAULT NULL ,
  PRIMARY KEY ("session_id")
);
CREATE TABLE 'flow_rule' (
  "id" int(64) NOT NULL,
  "graph_flow_rule_id" varchar(64) NOT NULL,
  "internal_id" varchar(64) DEFAULT NULL,
  "session_id" varchar(64) NOT NULL,
  "switch_id" varchar(64) DEFAULT NULL,
  "type" varchar(64) DEFAULT NULL,
  "priority" varchar(64) DEFAULT NULL,
  "status" varchar(64) DEFAULT NULL,
  "creation_date" datetime NOT NULL,
  "last_update" datetime DEFAULT NULL, 'description'  varchar(128) DEFAULT NULL ,
  PRIMARY KEY ("id")
);
CREATE TABLE 'vlan' ( 
  "id" int(64) NOT NULL, 
  "switch_id" varchar(64) NOT NULL, 
  "port_in" int(64) NOT NULL, 
  "vlan_in" int(64), 
  "port_out" int(64) NOT NULL, 
  "vlan_out" int(64), 
  "flow_rule_id" int(64), 
  PRIMARY KEY ("id") 
);
CREATE TABLE 'vnf' (
  "id" int(64) NOT NULL,
  "graph_vnf_id" varchar(64) NOT NULL,
  "session_id" varchar(64) NOT NULL,
  "name" varchar(64) NOT NULL,
  "template" varchar(64) NOT NULL,
  "application_name" varchar(64),
  PRIMARY KEY ("id")
);
CREATE TABLE 'vnf_port' (
  "id" int(64) NOT NULL,
  "graph_port_id" varchar(64) NOT NULL,
  "vnf_id" int(64) NOT NULL,
  "name" varchar(64),
  PRIMARY KEY ("id")
);
