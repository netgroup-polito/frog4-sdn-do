-- phpMyAdmin SQL Dump
-- version 4.0.10deb1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Dec 09, 2015 at 06:09 PM
-- Server version: 5.5.46-0ubuntu0.14.04.2
-- PHP Version: 5.5.9-1ubuntu4.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `frog4_odl_ca`
--

-- --------------------------------------------------------

--
-- Table structure for table `action`
--

DROP TABLE IF EXISTS `action`;
CREATE TABLE IF NOT EXISTS `action` (
  `id` int(64) NOT NULL,
  `flow_rule_id` varchar(64) NOT NULL,
  `output_type` varchar(64) DEFAULT NULL,
  `output` varchar(64) DEFAULT NULL,
  `controller` tinyint(1) DEFAULT NULL,
  `_drop` tinyint(1) DEFAULT NULL,
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `endpoint`
--

DROP TABLE IF EXISTS `endpoint`;
CREATE TABLE IF NOT EXISTS `endpoint` (
  `id` int(64) NOT NULL,
  `graph_endpoint_id` varchar(64) NOT NULL,
  `name` varchar(64) DEFAULT NULL,
  `type` varchar(64) DEFAULT NULL,
  `session_id` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `endpoint_resource`
--

DROP TABLE IF EXISTS `endpoint_resource`;
CREATE TABLE IF NOT EXISTS `endpoint_resource` (
  `endpoint_id` int(64) NOT NULL,
  `resource_type` varchar(64) NOT NULL,
  `resource_id` int(64) NOT NULL,
  PRIMARY KEY (`endpoint_id`,`resource_type`,`resource_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `flow_rule`
--

DROP TABLE IF EXISTS `flow_rule`;
CREATE TABLE IF NOT EXISTS `flow_rule` (
  `id` int(64) NOT NULL,
  `graph_flow_rule_id` varchar(64) NOT NULL,
  `internal_id` varchar(255) DEFAULT NULL,
  `session_id` varchar(64) NOT NULL,
  `switch_id` varchar(64) DEFAULT NULL,
  `type` varchar(64) DEFAULT NULL,
  `priority` varchar(64) DEFAULT NULL,
  `status` varchar(64) DEFAULT NULL,
  `creation_date` datetime NOT NULL,
  `last_update` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `graph_session`
--

DROP TABLE IF EXISTS `graph_session`;
CREATE TABLE IF NOT EXISTS `graph_session` (
  `session_id` varchar(64) NOT NULL,
  `user_id` varchar(64) DEFAULT NULL,
  `graph_id` varchar(64) NOT NULL,
  `graph_name` varchar(64) NOT NULL,
  `status` varchar(64) NOT NULL,
  `started_at` datetime NOT NULL,
  `last_update` datetime DEFAULT NULL,
  `error` datetime DEFAULT NULL,
  `ended` datetime DEFAULT NULL,
  PRIMARY KEY (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `match`
--

DROP TABLE IF EXISTS `match`;
CREATE TABLE IF NOT EXISTS `match` (
  `id` int(64) NOT NULL,
  `flow_rule_id` varchar(64) NOT NULL,
  `port_in_type` varchar(64) DEFAULT NULL,
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
-- Table structure for table `port`
--

DROP TABLE IF EXISTS `port`;
CREATE TABLE IF NOT EXISTS `port` (
  `id` int(64) NOT NULL,
  `graph_port_id` varchar(64) NOT NULL,
  `status` varchar(64) DEFAULT NULL,
  `switch_id` varchar(64) DEFAULT NULL,
  `session_id` varchar(64) NOT NULL,
  `mac_address` varchar(64) DEFAULT NULL,
  `ipv4_address` varchar(64) DEFAULT NULL,
  `tunnel_remote_ip` varchar(64) DEFAULT NULL,
  `vlan_id` varchar(64) DEFAULT NULL,
  `gre_key` varchar(64) DEFAULT NULL,
  `creation_date` datetime NOT NULL,
  `last_update` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tenant`
--

DROP TABLE IF EXISTS `tenant`;
CREATE TABLE IF NOT EXISTS `tenant` (
  `id` varchar(64) NOT NULL,
  `name` varchar(64) NOT NULL,
  `description` varchar(128) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dumping data for table `tenant`
--

INSERT INTO `tenant` (`id`, `name`, `description`) VALUES
('3', 'admin_tenant', 'Admin Tenant');

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
CREATE TABLE IF NOT EXISTS `user` (
  `id` varchar(64) NOT NULL,
  `tenant_id` varchar(64) NOT NULL,
  `name` varchar(64) NOT NULL,
  `password` varchar(64) NOT NULL,
  `mail` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`id`, `tenant_id`, `name`, `password`, `mail`) VALUES
('3', '3', 'admin', 'admin', 'admin@admin');

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
