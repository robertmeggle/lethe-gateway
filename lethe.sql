CREATE DATABASE  IF NOT EXISTS `lethe_privacy` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `lethe_privacy`;
-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: lethe_privacy
-- ------------------------------------------------------
-- Server version	8.0.46-0ubuntu0.24.04.3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `admin_auth`
--

DROP TABLE IF EXISTS `admin_auth`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin_auth` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ist_admin` tinyint(1) NOT NULL DEFAULT '0',
  `login_attempts` int NOT NULL DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `locked_at` timestamp NULL DEFAULT NULL,
  `reset_token` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `reset_expires` datetime DEFAULT NULL,
  `client_id` varchar(4) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` enum('active','locked') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active',
  `unlock_code` varchar(8) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_client` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-31 14:48:05
CREATE DATABASE  IF NOT EXISTS `lethe_privacy` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `lethe_privacy`;
-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: lethe_privacy
-- ------------------------------------------------------
-- Server version	8.0.46-0ubuntu0.24.04.3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `api_logs`
--

DROP TABLE IF EXISTS `api_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `api_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_id` varchar(4) COLLATE utf8mb4_unicode_ci NOT NULL,
  `endpoint` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `word_count` int NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=705 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-31 14:48:04
CREATE DATABASE  IF NOT EXISTS `lethe_privacy` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `lethe_privacy`;
-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: lethe_privacy
-- ------------------------------------------------------
-- Server version	8.0.46-0ubuntu0.24.04.3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `client_auth`
--

DROP TABLE IF EXISTS `client_auth`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client_auth` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_id` varchar(4) COLLATE utf8mb4_unicode_ci NOT NULL,
  `client_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `valid_until` datetime NOT NULL,
  `status` enum('active','locked') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active',
  `max_file_size_mb` int NOT NULL DEFAULT '20',
  `max_text_length` int NOT NULL DEFAULT '100000',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_client` (`client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-31 14:48:04
CREATE DATABASE  IF NOT EXISTS `lethe_privacy` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `lethe_privacy`;
-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: lethe_privacy
-- ------------------------------------------------------
-- Server version	8.0.46-0ubuntu0.24.04.3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `error_logs`
--

DROP TABLE IF EXISTS `error_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `error_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `error_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `message` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `details` text COLLATE utf8mb4_unicode_ci,
  `client_id` varchar(4) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_error_type` (`error_type`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_client_id` (`client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-31 14:48:05
CREATE DATABASE  IF NOT EXISTS `lethe_privacy` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `lethe_privacy`;
-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: lethe_privacy
-- ------------------------------------------------------
-- Server version	8.0.46-0ubuntu0.24.04.3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `lethe_dictionary`
--

DROP TABLE IF EXISTS `lethe_dictionary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lethe_dictionary` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_id` varchar(4) COLLATE utf8mb4_unicode_ci NOT NULL,
  `term` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `blind_index` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `category` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `match_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'exact',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_client_blind_cat` (`client_id`,`blind_index`,`category`),
  KEY `idx_term` (`term`),
  KEY `idx_blind_index` (`blind_index`)
) ENGINE=InnoDB AUTO_INCREMENT=59 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-31 14:48:04
CREATE DATABASE  IF NOT EXISTS `lethe_privacy` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `lethe_privacy`;
-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: lethe_privacy
-- ------------------------------------------------------
-- Server version	8.0.46-0ubuntu0.24.04.3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `lethe_system_dictionary`
--

DROP TABLE IF EXISTS `lethe_system_dictionary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lethe_system_dictionary` (
  `id` int NOT NULL AUTO_INCREMENT,
  `term` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` enum('LOC','SUFFIX_TECH','SUFFIX_MED','SUFFIX_CUSTOM') COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `comment` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_term_category` (`term`,`category`),
  KEY `idx_category_active` (`category`,`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=223 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lethe_system_dictionary`
--

LOCK TABLES `lethe_system_dictionary` WRITE;
/*!40000 ALTER TABLE `lethe_system_dictionary` DISABLE KEYS */;
INSERT INTO `lethe_system_dictionary` VALUES (1,'München','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(2,'Berlin','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(3,'Hamburg','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(4,'Köln','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(5,'Frankfurt','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(6,'Stuttgart','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(7,'Düsseldorf','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(8,'Leipzig','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(9,'Dortmund','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(10,'Essen','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(11,'Bremen','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(12,'Dresden','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(13,'Hannover','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(14,'Nürnberg','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(15,'Duisburg','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(16,'Bochum','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(17,'Wuppertal','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(18,'Bielefeld','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(19,'Bonn','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(20,'Münster','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(21,'Karlsruhe','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(22,'Mannheim','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(23,'Augsburg','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(24,'Wiesbaden','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(25,'Gelsenkirchen','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(26,'Mönchengladbach','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(27,'Aachen','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(28,'Braunschweig','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(29,'Chemnitz','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(30,'Kiel','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(31,'Halle','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(32,'Magdeburg','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(33,'Freiburg','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(34,'Krefeld','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(35,'Lübeck','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(36,'Oberhausen','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(37,'Erfurt','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(38,'Mainz','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(39,'Rostock','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(40,'Kassel','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(41,'Hagen','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(42,'Potsdam','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(43,'Saarbrücken','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(44,'Hamm','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(45,'Mülheim','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(46,'Ludwigshafen','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(47,'Leverkusen','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(48,'Oldenburg','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(49,'Osnabrück','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(50,'Solingen','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(51,'Heidelberg','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(52,'Darmstadt','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(53,'Paderborn','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(54,'Regensburg','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(55,'Ingolstadt','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(56,'Würzburg','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(57,'Fürth','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(58,'Ulm','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(59,'Heilbronn','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(60,'Pforzheim','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(61,'Wolfsburg','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(62,'Göttingen','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(63,'Offenbach','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(64,'Bottrop','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(65,'Recklinghausen','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(66,'Bremerhaven','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(67,'Remscheid','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(68,'Reutlingen','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(69,'Koblenz','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(70,'Jena','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(71,'Erlangen','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(72,'Moers','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(73,'Siegen','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(74,'Hildesheim','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(75,'Salzgitter','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(76,'Wien','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(77,'Graz','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(78,'Linz','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(79,'Salzburg','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(80,'Innsbruck','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(81,'Klagenfurt','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(82,'Villach','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(83,'Wels','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(84,'Dornbirn','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(85,'Steyr','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(86,'Feldkirch','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(87,'Zürich','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(88,'Genf','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(89,'Basel','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(90,'Bern','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(91,'Lausanne','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(92,'Winterthur','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(93,'Luzern','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(94,'Lugano','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(95,'Biel','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(96,'Thun','LOC',1,'Initial import: Known cities','2026-07-27 18:03:50','2026-07-27 18:03:50'),(97,'daten','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(98,'container','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(99,'applikation','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(100,'applikationen','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(101,'environment','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(102,'environments','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(103,'instanz','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(104,'instanzen','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(105,'ordner','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(106,'verzeichnis','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(107,'verzeichnisse','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(108,'tabelle','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(109,'tabellen','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(110,'router','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(111,'routers','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(112,'endpunkt','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(113,'endpunkte','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(114,'daemon','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(115,'daemons','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(116,'proxy','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(117,'proxies','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(118,'repository','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(119,'repositories','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(120,'traffic','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(121,'modus','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(122,'modi','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(123,'netzwerkmodus','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(124,'server','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(125,'servers','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(126,'client','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(127,'clients','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(128,'app','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(129,'apps','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(130,'dienst','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(131,'dienste','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(132,'process','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(133,'processes','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(134,'prozess','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(135,'prozesse','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(136,'bibliothek','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(137,'bibliotheken','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(138,'library','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(139,'libraries','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(140,'schnittstelle','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(141,'schnittstellen','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(142,'treiber','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(143,'drivers','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(144,'driver','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(145,'system','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(146,'systeme','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(147,'zertifikat','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(148,'zertifikate','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(149,'schlüssel','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(150,'key','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(151,'keys','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(152,'token','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(153,'tokens','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(154,'session','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(155,'sessionen','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(156,'verbindung','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(157,'verbindungen','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(158,'connection','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(159,'connections','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(160,'port','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(161,'ports','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(162,'host','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(163,'hosts','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(164,'ip','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(165,'adresse','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(166,'adressen','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(167,'netzwerk','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(168,'netzwerke','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(169,'network','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(170,'networks','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(171,'speicher','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(172,'datenbank','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(173,'datenbanken','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(174,'database','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(175,'databases','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(176,'datei','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(177,'dateien','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(178,'file','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(179,'files','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(180,'pfad','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(181,'pfade','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(182,'path','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(183,'paths','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(184,'bereich','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(185,'bereiche','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(186,'zone','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(187,'zonen','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(188,'umgebung','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(189,'umgebungen','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(190,'socket','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(191,'sockets','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(192,'skript','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(193,'skripte','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(194,'script','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(195,'scripts','SUFFIX_TECH',1,'Initial import: Technical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(196,'wert','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(197,'werte','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(198,'spiegel','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(199,'profil','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(200,'status','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(201,'test','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(202,'parameter','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(203,'fraktion','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(204,'enzym','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(205,'nachweis','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(206,'clearance','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(207,'protein','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(208,'quotient','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(209,'funktion','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(210,'toleranz','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(211,'index','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(212,'faktor','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(213,'antikörper','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(214,'antigen','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(215,'rezeptor','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(216,'marker','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(217,'cholesterin','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(218,'blutbild','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(219,'serum','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(220,'plasma','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(221,'diagnostik','SUFFIX_MED',1,'Initial import: Medical suffixes','2026-07-27 18:03:50','2026-07-27 18:03:50'),(222,'Wald','LOC',1,'Added for testing','2026-07-27 18:09:16','2026-07-27 18:09:16');
/*!40000 ALTER TABLE `lethe_system_dictionary` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-31 14:49:31
