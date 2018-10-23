CREATE TABLE `tracks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(100) DEFAULT NULL,
  `artist` varchar(100) DEFAULT NULL,
  `popularity` int(11) DEFAULT NULL,
  `uri` varchar(100) DEFAULT NULL,
  `spoffy_title` varchar(300) DEFAULT NULL,
  `spoffy_artist` varchar(300) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1521 DEFAULT CHARSET=utf8;

CREATE TABLE `albums` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(100) DEFAULT NULL,
  `artist` varchar(100) DEFAULT NULL,
  `popularity` int(11) DEFAULT NULL,
  `uri` varchar(100) DEFAULT NULL,
  `spoffy_title` varchar(300) DEFAULT NULL,
  `spoffy_artist` varchar(300) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1521 DEFAULT CHARSET=utf8;

CREATE TABLE `hot-100` (
  `week` date NOT NULL,
  `idx` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  PRIMARY KEY (`week`,`idx`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `billboard-200` (
  `week` date NOT NULL,
  `idx` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  PRIMARY KEY (`week`,`idx`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

