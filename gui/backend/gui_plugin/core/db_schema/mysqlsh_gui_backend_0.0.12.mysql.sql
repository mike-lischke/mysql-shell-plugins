/*
 * Copyright (c) 2021, Oracle and/or its affiliates.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License, version 2.0,
 * as published by the Free Software Foundation.
 *
 * This program is also distributed with certain software (including
 * but not limited to OpenSSL) that is licensed under separate terms, as
 * designated in a particular file or component or in included license
 * documentation.  The authors of MySQL hereby grant you an additional
 * permission to link the program and your derivative works with the
 * separately licensed software that they have included with MySQL.
 * This program is distributed in the hope that it will be useful,  but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
 * the GNU General Public License, version 2.0, for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 */

-- MySQL Script generated by MySQL Workbench
-- Fri Oct  8 13:20:37 2021
-- Model: MSG Model    Version: 1.0
-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema gui_backend
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Table `db_connection`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `db_connection` ;

CREATE TABLE IF NOT EXISTS `db_connection` (
  `id` INT NOT NULL,
  `db_type` VARCHAR(45) NOT NULL,
  `caption` VARCHAR(256) NULL,
  `description` VARCHAR(200) NULL,
  `options` TEXT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `db_connection_group`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `db_connection_group` ;

CREATE TABLE IF NOT EXISTS `db_connection_group` (
  `id` INT NOT NULL,
  `caption` VARCHAR(80) NULL,
  `description` VARCHAR(200) NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `db_connection_has_tag`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `db_connection_has_tag` ;

CREATE TABLE IF NOT EXISTS `db_connection_has_tag` (
  `profile_id` INT NOT NULL,
  `db_connection_id` INT NOT NULL,
  `tag_id` INT NOT NULL,
  PRIMARY KEY (`profile_id`, `db_connection_id`, `tag_id`),
  INDEX `fk_db_connection_has_tag_tag1_idx` (`tag_id` ASC) VISIBLE,
  INDEX `fk_db_connection_has_tag_db_connection_idx` (`profile_id` ASC, `db_connection_id` ASC) VISIBLE,
  CONSTRAINT `fk_db_connection_has_tag_db_connection1`
    FOREIGN KEY (`profile_id` , `db_connection_id`)
    REFERENCES `profile_has_db_connection` (`profile_id` , `db_connection_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_db_connection_has_tag_tag1`
    FOREIGN KEY (`tag_id`)
    REFERENCES `tag` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `data`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `data` ;

CREATE TABLE IF NOT EXISTS `data` (
  `id` INT NOT NULL,
  `data_category_id` INT NOT NULL,
  `caption` VARCHAR(256) NULL,
  `content` TEXT NULL,
  `created` DATETIME NULL,
  `last_update` DATETIME NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_data_data_category1`
    FOREIGN KEY (`data_category_id`)
    REFERENCES `data_category` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

CREATE INDEX `module_data_caption_idx` ON `data` (`caption` ASC) VISIBLE;
CREATE INDEX `fk_data_data_category1_idx` ON `data` (`data_category_id` ASC) VISIBLE;


-- -----------------------------------------------------
-- Table `data_category`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `data_category` ;

CREATE TABLE IF NOT EXISTS `data_category` (
  `id` INT NOT NULL,
  `parent_category_id` INT NULL,
  `name` VARCHAR(80) NULL,
  `module_id` VARCHAR(256) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_module_data_category_module_data_category1_idx` (`parent_category_id` ASC) VISIBLE,
  UNIQUE INDEX `unique_caption_per_module_id` (`name` ASC, `module_id` ASC) VISIBLE,
  CONSTRAINT `fk_module_data_category_module_data_category1`
    FOREIGN KEY (`parent_category_id`)
    REFERENCES `data_category` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `data_folder`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `data_folder` ;

CREATE TABLE IF NOT EXISTS `data_folder` (
  `id` INT NOT NULL,
  `caption` VARCHAR(80) NULL,
  `parent_folder_id` INT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_module_data_folder_module_data_folder1_idx` (`parent_folder_id` ASC) VISIBLE,
  CONSTRAINT `fk_module_data_folder_module_data_folder1`
    FOREIGN KEY (`parent_folder_id`)
    REFERENCES `data_folder` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `data_folder_has_data`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `data_folder_has_data` ;

CREATE TABLE IF NOT EXISTS `data_folder_has_data` (
  `data_id` INT NOT NULL,
  `data_folder_id` INT NOT NULL,
  `read_only` TINYINT NOT NULL DEFAULT 0,
  PRIMARY KEY (`data_id`, `data_folder_id`),
  INDEX `fk_data_has_data_folder_data_folder1_idx` (`data_folder_id` ASC) VISIBLE,
  INDEX `fk_data_has_data_folder_data1_idx` (`data_id` ASC) VISIBLE,
  CONSTRAINT `fk_data_has_data_folder_data1`
    FOREIGN KEY (`data_id`)
    REFERENCES `data` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_data_has_data_folder_data_folder1`
    FOREIGN KEY (`data_folder_id`)
    REFERENCES `data_folder` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `module_data_has_tag`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `module_data_has_tag` ;

CREATE TABLE IF NOT EXISTS `module_data_has_tag` (
  `profile_id` INT NOT NULL,
  `data_id` INT NOT NULL,
  `tag_id` INT NOT NULL,
  PRIMARY KEY (`profile_id`, `data_id`, `tag_id`),
  INDEX `fk_data_has_tag_tag1_idx` (`tag_id` ASC) VISIBLE,
  CONSTRAINT `fk_data_has_tag_tag1`
    FOREIGN KEY (`tag_id`)
    REFERENCES `tag` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `privilege`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `privilege` ;

CREATE TABLE IF NOT EXISTS `privilege` (
  `id` INT NOT NULL,
  `privilege_type_id` INT NOT NULL,
  `name` VARCHAR(100) NULL,
  `access_pattern` VARCHAR(250) NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_privilege_privilege_type1_idx` (`privilege_type_id` ASC) VISIBLE,
  CONSTRAINT `fk_privilege_privilege_type1`
    FOREIGN KEY (`privilege_type_id`)
    REFERENCES `privilege_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `privilege_type`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `privilege_type` ;

CREATE TABLE IF NOT EXISTS `privilege_type` (
  `id` INT NOT NULL,
  `name` VARCHAR(45) NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `profile`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `profile` ;

CREATE TABLE IF NOT EXISTS `profile` (
  `id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `name` VARCHAR(80) NULL,
  `description` VARCHAR(200) NULL,
  `options` TEXT NULL,
  `active` TINYINT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  INDEX `fk_profile_user1_idx` (`user_id` ASC) VISIBLE,
  CONSTRAINT `fk_profile_user1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `profile_has_db_connection`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `profile_has_db_connection` ;

CREATE TABLE IF NOT EXISTS `profile_has_db_connection` (
  `profile_id` INT NOT NULL,
  `db_connection_id` INT NOT NULL,
  `folder_path` VARCHAR(1024) NULL,
  `active` TINYINT NULL DEFAULT 1,
  PRIMARY KEY (`profile_id`, `db_connection_id`),
  INDEX `fk_profile_has_db_connection_db_connection1_idx` (`db_connection_id` ASC) VISIBLE,
  INDEX `fk_profile_has_db_connection_user_profile1_idx` (`profile_id` ASC) VISIBLE,
  CONSTRAINT `fk_profile_has_db_connection_profile1`
    FOREIGN KEY (`profile_id`)
    REFERENCES `profile` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_profile_has_db_connection_db_connection1`
    FOREIGN KEY (`db_connection_id`)
    REFERENCES `db_connection` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `data_profile_tree`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `data_profile_tree` ;

CREATE TABLE IF NOT EXISTS `data_profile_tree` (
  `profile_id` INT NOT NULL,
  `root_folder_id` INT NOT NULL,
  `tree_identifier` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`profile_id`, `root_folder_id`),
  INDEX `fk_profile_has_module_data_folder_profile1_idx` (`profile_id` ASC) VISIBLE,
  INDEX `fk_profile_has_module_data_folder_module_data_folder1_idx` (`root_folder_id` ASC) VISIBLE,
  CONSTRAINT `fk_profile_has_module_data_folder_profile1`
    FOREIGN KEY (`profile_id`)
    REFERENCES `profile` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_profile_has_module_data_folder_module_data_folder1`
    FOREIGN KEY (`root_folder_id`)
    REFERENCES `data_folder` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `role`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `role` ;

CREATE TABLE IF NOT EXISTS `role` (
  `id` INT NOT NULL,
  `name` VARCHAR(45) NULL,
  `description` VARCHAR(200) NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `role_has_privilege`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `role_has_privilege` ;

CREATE TABLE IF NOT EXISTS `role_has_privilege` (
  `role_id` INT NOT NULL,
  `privilege_id` INT NOT NULL,
  PRIMARY KEY (`role_id`, `privilege_id`),
  INDEX `fk_role_has_privilege_privilege1_idx` (`privilege_id` ASC) VISIBLE,
  INDEX `fk_role_has_privilege_role_idx` (`role_id` ASC) VISIBLE,
  CONSTRAINT `fk_role_has_privilege_role`
    FOREIGN KEY (`role_id`)
    REFERENCES `role` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_role_has_privilege_privilege1`
    FOREIGN KEY (`privilege_id`)
    REFERENCES `privilege` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `session`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `session` ;

CREATE TABLE IF NOT EXISTS `session` (
  `id` INT NOT NULL,
  `continued_session_id` INT NULL,
  `user_id` INT NULL,
  `uuid` BLOB(16) NULL,
  `started` DATETIME NULL,
  `ended` DATETIME NULL,
  `source_ip` VARCHAR(256) NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_session_users1_idx` (`user_id` ASC) VISIBLE,
  INDEX `fk_session_session1_idx` (`continued_session_id` ASC) VISIBLE,
  CONSTRAINT `fk_session_users1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_session_session1`
    FOREIGN KEY (`continued_session_id`)
    REFERENCES `session` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `tag`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tag` ;

CREATE TABLE IF NOT EXISTS `tag` (
  `id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `caption` VARCHAR(80) NULL,
  `color` VARCHAR(45) NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_tag_user1_idx` (`user_id` ASC) VISIBLE,
  CONSTRAINT `fk_tag_user1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `user`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `user` ;

CREATE TABLE IF NOT EXISTS `user` (
  `id` INT NOT NULL,
  `default_profile_id` INT NULL,
  `name` VARCHAR(45) NULL,
  `password_hash` VARCHAR(256) NULL,
  `allowed_hosts` VARCHAR(512) NULL,
  `active` TINYINT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  INDEX `fk_user_profile1_idx` (`default_profile_id` ASC) VISIBLE,
  UNIQUE INDEX `name_UNIQUE` (`name` ASC) VISIBLE,
  CONSTRAINT `fk_user_profile1`
    FOREIGN KEY (`default_profile_id`)
    REFERENCES `profile` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `user_group`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `user_group` ;

CREATE TABLE IF NOT EXISTS `user_group` (
  `id` INT NOT NULL,
  `name` VARCHAR(45) NULL,
  `description` VARCHAR(200) NULL,
  `active` TINYINT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `data_user_group_tree`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `data_user_group_tree` ;

CREATE TABLE IF NOT EXISTS `data_user_group_tree` (
  `user_group_id` INT NOT NULL,
  `root_folder_id` INT NOT NULL,
  `tree_identifier` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`user_group_id`, `root_folder_id`),
  INDEX `fk_user_group_has_module_data_folder_user_group1_idx` (`user_group_id` ASC) VISIBLE,
  INDEX `fk_user_group_has_module_data_folder_module_data_folder1_idx` (`root_folder_id` ASC) VISIBLE,
  CONSTRAINT `fk_user_group_has_module_data_folder_user_group1`
    FOREIGN KEY (`user_group_id`)
    REFERENCES `user_group` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_user_group_has_module_data_folder_module_data_folder1`
    FOREIGN KEY (`root_folder_id`)
    REFERENCES `data_folder` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `user_group_has_user`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `user_group_has_user` ;

CREATE TABLE IF NOT EXISTS `user_group_has_user` (
  `user_group_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `owner` TINYINT NULL,
  `active` TINYINT NULL,
  PRIMARY KEY (`user_group_id`, `user_id`),
  INDEX `fk_user_group_has_user_user1_idx` (`user_id` ASC) VISIBLE,
  INDEX `fk_user_group_has_user_user_group1_idx` (`user_group_id` ASC) VISIBLE,
  CONSTRAINT `fk_user_group_has_user_user_group1`
    FOREIGN KEY (`user_group_id`)
    REFERENCES `user_group` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_user_group_has_user_user1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `user_has_role`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `user_has_role` ;

CREATE TABLE IF NOT EXISTS `user_has_role` (
  `user_id` INT NOT NULL,
  `role_id` INT NOT NULL,
  PRIMARY KEY (`user_id`, `role_id`),
  INDEX `fk_users_has_role_role1_idx` (`role_id` ASC) VISIBLE,
  INDEX `fk_users_has_role_users1_idx` (`user_id` ASC) VISIBLE,
  CONSTRAINT `fk_users_has_role_users1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_users_has_role_role1`
    FOREIGN KEY (`role_id`)
    REFERENCES `role` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Schema gui_backend_log
-- -----------------------------------------------------
-- ATTACH DATABASE 'mysqlsh_gui_backend_log_0.0.12.sqlite3' as logs;

-- -----------------------------------------------------
-- Table `log`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `logs`.`log` ;

CREATE TABLE IF NOT EXISTS `logs`.`log` (
  `id` INT NOT NULL,
  `session_id` INT NULL,
  `user_id` INT NULL,
  `event_time` DATETIME NULL,
  `event_type` VARCHAR(45) NULL,
  `message` TEXT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_log_user1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_log_session1`
    FOREIGN KEY (`session_id`)
    REFERENCES `session` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `message`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `logs`.`message` ;

CREATE TABLE IF NOT EXISTS `logs`.`message` (
  `id` INT NOT NULL,
  `session_id` INT NOT NULL,
  `request_id` BLOB(16) NULL,
  `is_response` TINYINT NULL,
  `message` TEXT NULL,
  `sent` DATETIME NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_message_session1`
    FOREIGN KEY (`session_id`)
    REFERENCES `session` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- View `schema_version`
-- -----------------------------------------------------
DROP VIEW IF EXISTS `schema_version` ;
CREATE VIEW schema_version (major, minor, patch) AS SELECT 0, 0, 12;

-- -----------------------------------------------------
-- Data for table `privilege`
-- -----------------------------------------------------
START TRANSACTION;
INSERT INTO `privilege` (`id`, `privilege_type_id`, `name`, `access_pattern`) VALUES (1, 1, 'Full access to all python globals', '.*');
INSERT INTO `privilege` (`id`, `privilege_type_id`, `name`, `access_pattern`) VALUES (2, 2, 'Full access to all web gui modules', '.*');
INSERT INTO `privilege` (`id`, `privilege_type_id`, `name`, `access_pattern`) VALUES (3, 1, 'Access to common gui extension objects', 'gui\\.(modules|sqleditor)\\.\\w*');
INSERT INTO `privilege` (`id`, `privilege_type_id`, `name`, `access_pattern`) VALUES (4, 2, 'Access to all web gui modules except shell', '\\b(?!shell\\b)\\w+');
INSERT INTO `privilege` (`id`, `privilege_type_id`, `name`, `access_pattern`) VALUES (5, 1, 'Access to selected gui.users functions', 'gui\\.users\\.(get_gui_module_list|list_profiles|get_profile|add_profile|get_default_profile|set_default_profile|set_web_session_profile)');

COMMIT;


-- -----------------------------------------------------
-- Data for table `privilege_type`
-- -----------------------------------------------------
START TRANSACTION;
INSERT INTO `privilege_type` (`id`, `name`) VALUES (1, 'Python Environment Access');
INSERT INTO `privilege_type` (`id`, `name`) VALUES (2, 'GUI Module Access');

COMMIT;


-- -----------------------------------------------------
-- Data for table `role`
-- -----------------------------------------------------
START TRANSACTION;
INSERT INTO `role` (`id`, `name`, `description`) VALUES (1, 'Administrator', 'Administrator with full access');
INSERT INTO `role` (`id`, `name`, `description`) VALUES (2, 'Poweruser', 'Web user with full access');
INSERT INTO `role` (`id`, `name`, `description`) VALUES (3, 'User', 'Web user with full access expect to the shell module');

COMMIT;


-- -----------------------------------------------------
-- Data for table `role_has_privilege`
-- -----------------------------------------------------
START TRANSACTION;
INSERT INTO `role_has_privilege` (`role_id`, `privilege_id`) VALUES (1, 1);
INSERT INTO `role_has_privilege` (`role_id`, `privilege_id`) VALUES (1, 2);
INSERT INTO `role_has_privilege` (`role_id`, `privilege_id`) VALUES (2, 2);
INSERT INTO `role_has_privilege` (`role_id`, `privilege_id`) VALUES (2, 3);
INSERT INTO `role_has_privilege` (`role_id`, `privilege_id`) VALUES (3, 3);
INSERT INTO `role_has_privilege` (`role_id`, `privilege_id`) VALUES (3, 4);

COMMIT;


-- -----------------------------------------------------
-- Data for table `user_group`
-- -----------------------------------------------------
START TRANSACTION;
INSERT INTO `user_group` (`id`, `name`, `description`, `active`) VALUES (1, 'all', 'All Users', 1);

COMMIT;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
