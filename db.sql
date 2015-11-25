SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `orchestrator`
--
CREATE DATABASE IF NOT EXISTS `frog4_odl_ca` DEFAULT CHARACTER SET latin1 COLLATE latin1_swedish_ci;
USE `frog4_odl_ca`;

-- --------------------------------------------------------

--
-- Struttura della tabella `action`
--

DROP TABLE IF EXISTS `action`;
CREATE TABLE IF NOT EXISTS `action` (
  `id` int(64) NOT NULL,
  `flow_rule_id` varchar(64) NOT NULL,
  `output` varchar(64) DEFAULT NULL,
  `controller` tinyint(1) DEFAULT NULL,
  `set_vlan_id` varchar(64) DEFAULT NULL,
  `set_vlan_priority` varchar(64) DEFAULT NULL,
  `pop_vlan` tinyint(1) DEFAULT NULL,
  `set_ethernet_src_address` varchar(64) DEFAULT NULL,
  `set_ethernet_dst_address` varchar(64) DEFAULT NULL,
  `set_ip_src_address` varchar(64) DEFAULT NULL,
  `set_ip_dst_address` varchar(64) DEFAULT NULL,
  `set_ip_tos` varchar(64) DEFAULT NULL,
  `set_l4_src_port` varchar(64) DEFAULT NULL,
  `set_l4_dst_port` varchar(64) DEFAULT NULL,
  `output_to_queue` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `endpoint`
--

DROP TABLE IF EXISTS `endpoint`;
CREATE TABLE IF NOT EXISTS `endpoint` (
  `id` int(64) NOT NULL,
  `internal_id` varchar(64) DEFAULT NULL,
  `graph_endpoint_id` varchar(64) NOT NULL,
  `graph_id` varchar(64) NOT NULL,
  `name` varchar(64) DEFAULT NULL,
  `type` varchar(64) DEFAULT NULL,
  `location` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `endpoint_resource`
--

DROP TABLE IF EXISTS `endpoint_resource`;
CREATE TABLE IF NOT EXISTS `endpoint_resource` (
  `endpoint_id` int(64) NOT NULL,
  `resource_type` varchar(64) NOT NULL,
  `resource_id` int(64) NOT NULL,
  PRIMARY KEY (`endpoint_id`,`resource_type`,`resource_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `flowrule`
--

DROP TABLE IF EXISTS `flowrule`;
CREATE TABLE IF NOT EXISTS `flowrule` (
  `id` int(64) NOT NULL,
  `internal_id` varchar(255) DEFAULT NULL,
  `graph_flow_rule_id` varchar(64) NOT NULL,
  `graph_id` varchar(64) NOT NULL,
  `priority` varchar(64) DEFAULT NULL,
  `status` varchar(64) DEFAULT NULL,
  `creation_date` datetime NOT NULL,
  `last_update` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `graph`
--

DROP TABLE IF EXISTS `graph`;
CREATE TABLE IF NOT EXISTS `graph` (
  `id` int(64) NOT NULL,
  `session_id` varchar(64) NOT NULL,
  `node_id` varchar(64) DEFAULT NULL,
  `partial` tinyint(4) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `service_graph_id` (`session_id`,`node_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Struttura della tabella `graph_connection`
--

DROP TABLE IF EXISTS `graph_connection`;
CREATE TABLE IF NOT EXISTS `graph_connection` (
  `endpoint_id_1` varchar(64) NOT NULL,
  `endpoint_id_2` varchar(64) NOT NULL,
  PRIMARY KEY (`endpoint_id_1`,`endpoint_id_2`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `match`
--

DROP TABLE IF EXISTS `match`;
CREATE TABLE IF NOT EXISTS `match` (
  `id` int(64) NOT NULL,
  `flow_rule_id` varchar(64) NOT NULL,
  `port_in` varchar(64) DEFAULT NULL,
  `ether_type` varchar(64) DEFAULT NULL,
  `vlan_id` varchar(64) DEFAULT NULL,
  `vlan_priority` varchar(64) DEFAULT NULL,
  `source_mac` varchar(64) DEFAULT NULL,
  `dest_mac` varchar(64) DEFAULT NULL,
  `source_ip` varchar(64) DEFAULT NULL,
  `dest_ip` varchar(64) DEFAULT NULL,
  `tos_bits` varchar(64) DEFAULT NULL,
  `source_port` varchar(64) DEFAULT NULL,
  `dest_port` varchar(64) DEFAULT NULL,
  `protocol` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Struttura della tabella `node`
--

DROP TABLE IF EXISTS `node`;
CREATE TABLE IF NOT EXISTS `node` (
  `id` varchar(64) NOT NULL,
  `name` varchar(64) NOT NULL,
  `type` varchar(64) NOT NULL,
  `domain_id` varchar(64) NOT NULL,
  `availability_zone` varchar(64) NOT NULL,
  `openstack_controller` varchar(64) NOT NULL,
  `openflow_controller` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Struttura della tabella `openflow_controller`
--

DROP TABLE IF EXISTS `openflow_controller`;
CREATE TABLE IF NOT EXISTS `openflow_controller` (
  `id` varchar(64) CHARACTER SET utf8 NOT NULL,
  `endpoint` varchar(64) CHARACTER SET utf8 NOT NULL,
  `version` varchar(64) CHARACTER SET utf8 NOT NULL,
  `username` varchar(64) CHARACTER SET utf8 NOT NULL,
  `password` varchar(64) CHARACTER SET utf8 NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------


--
-- Struttura della tabella `port`
--

DROP TABLE IF EXISTS `port`;
CREATE TABLE IF NOT EXISTS `port` (
  `id` int(64) NOT NULL,
  `internal_id` varchar(64) DEFAULT NULL,
  `graph_port_id` varchar(64) NOT NULL,
  `graph_id` int(64) NOT NULL,
  `name` varchar(64) NOT NULL,
  `vnf_id` varchar(64) DEFAULT NULL,
  `location` varchar(64) DEFAULT NULL,
  `type` varchar(64) DEFAULT NULL,
  `virtual_switch` varchar(64) DEFAULT NULL,
  `status` varchar(64) DEFAULT NULL,
  `creation_date` datetime NOT NULL,
  `last_update` datetime DEFAULT NULL,
  `os_network_id` varchar(64) DEFAULT NULL,
  `mac_address` varchar(64) DEFAULT NULL,
  `ipv4_address` varchar(64) DEFAULT NULL,
  `vlan_id` varchar(64) DEFAULT NULL,
  `gre_key` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `graph_port_id` (`graph_port_id`,`vnf_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `session`
--

DROP TABLE IF EXISTS `session`;
CREATE TABLE IF NOT EXISTS `session` (
  `id` varchar(64) NOT NULL,
  `user_id` varchar(64) DEFAULT NULL,
  `service_graph_id` varchar(63) NOT NULL,
  `service_graph_name` varchar(64) NOT NULL,
  `ingress_node` varchar(64) DEFAULT NULL,
  `egress_node` varchar(64) DEFAULT NULL,
  `status` varchar(64) NOT NULL,
  `started_at` datetime DEFAULT NULL,
  `last_update` datetime DEFAULT NULL,
  `error` datetime DEFAULT NULL,
  `ended` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Struttura della tabella `tenant`
--

DROP TABLE IF EXISTS `tenant`;
CREATE TABLE IF NOT EXISTS `tenant` (
  `id` varchar(64) CHARACTER SET utf8 NOT NULL,
  `name` varchar(64) CHARACTER SET utf8 NOT NULL,
  `description` varchar(128) CHARACTER SET utf8 NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `user`
--

DROP TABLE IF EXISTS `user`;
CREATE TABLE IF NOT EXISTS `user` (
  `id` varchar(64) CHARACTER SET utf8 NOT NULL,
  `name` varchar(64) CHARACTER SET utf8 NOT NULL,
  `password` varchar(64) CHARACTER SET utf8 NOT NULL,
  `tenant` varchar(64) CHARACTER SET utf8 NOT NULL,
  `mail` varchar(64) CHARACTER SET utf8 DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------


/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
