SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

CREATE TABLE `bans` (
  `id` mediumint(5) unsigned NOT NULL auto_increment,
  `ip` varchar(15) NOT NULL,
  `boards` text NOT NULL,
  `added` int(20) unsigned NOT NULL,
  `until` int(20) unsigned NOT NULL,
  `staff` varchar(75) NOT NULL,
  `reason` text NOT NULL,
  `note` text NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `ip` (`ip`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

CREATE TABLE `boards` (
  `id` smallint(5) unsigned NOT NULL auto_increment,
  `dir` varchar(75) NOT NULL,
  `name` varchar(75) NOT NULL,
  `configuration` text NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `dir` (`dir`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

CREATE TABLE `logs` (
  `timestamp` int(20) unsigned NOT NULL,
  `staff` varchar(75) NOT NULL,
  `action` text NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `posts` (
  `id` int(10) unsigned NOT NULL auto_increment,
  `boardid` smallint(5) unsigned NOT NULL,
  `parentid` int(10) unsigned NOT NULL,
  `name` varchar(255) NOT NULL,
  `tripcode` varchar(30) NOT NULL,
  `email` varchar(255) NOT NULL,
  `nameblock` varchar(255) NOT NULL,
  `subject` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `password` varchar(255) NOT NULL,
  `file` varchar(75) NOT NULL,
  `file_hex` varchar(75) NOT NULL,
  `file_mime` varchar(75) NOT NULL,
  `file_original` varchar(255) NOT NULL,
  `file_size` int(20) NOT NULL,
  `file_size_formatted` varchar(75) NOT NULL,
  `image_width` smallint(5) unsigned NOT NULL,
  `image_height` smallint(5) unsigned NOT NULL,
  `thumb` varchar(255) NOT NULL,
  `thumb_width` smallint(5) unsigned NOT NULL,
  `thumb_height` smallint(5) unsigned NOT NULL,
  `thumb_catalog_width` smallint(5) unsigned NOT NULL,
  `thumb_catalog_height` smallint(5) unsigned NOT NULL,
  `ip` varchar(15) NOT NULL,
  `timestamp_formatted` varchar(50) NOT NULL,
  `timestamp` int(20) unsigned NOT NULL,
  `bumped` int(20) unsigned NOT NULL,
  PRIMARY KEY  (`boardid`,`id`),
  KEY `parentid` (`parentid`),
  KEY `bumped` (`bumped`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `staff` (
  `id` smallint(5) unsigned NOT NULL auto_increment,
  `username` varchar(75) NOT NULL,
  `password` varchar(255) NOT NULL,
  `added` int(20) unsigned NOT NULL,
  `lastactive` int(20) unsigned NOT NULL,
  `rights` tinyint(1) unsigned NOT NULL default '0',
  `boards` text NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `username` (`username`,`password`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

INSERT INTO `staff` (`username`, `password`, `added`, `lastactive`, `rights`, `boards`) VALUES ('admin', '21232f297a57a5a743894a0e4a801fc3', UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 0, '');
