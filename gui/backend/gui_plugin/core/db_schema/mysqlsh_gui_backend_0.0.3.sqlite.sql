/*
 * Copyright (c) 2020, 2021, Oracle and/or its affiliates.
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
-- Mon Mar  2 16:42:22 2020
-- Model: New Model    Version: 1.0
-- MySQL Workbench Forward Engineering


PRAGMA foreign_keys = OFF;


-- -----------------------------------------------------
-- Schema gui_backend
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Table `db_connection`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `db_connection` ;

CREATE TABLE IF NOT EXISTS `db_connection` (
  `id` INTEGER NOT NULL,
  `db_type_id` INTEGER NOT NULL,
  `caption` VARCHAR(256) NULL,
  `description` VARCHAR(200) NULL,
  `connection_info` TEXT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_db_connection_db_type1`
    FOREIGN KEY (`db_type_id`)
    REFERENCES `db_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE INDEX `fk_db_connection_db_type1_idx` ON `db_connection` (`db_type_id` ASC);


-- -----------------------------------------------------
-- Table `db_connection_group`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `db_connection_group` ;

CREATE TABLE IF NOT EXISTS `db_connection_group` (
  `id` INTEGER NOT NULL,
  `caption` VARCHAR(80) NULL,
  `description` VARCHAR(200) NULL,
  PRIMARY KEY (`id`));


-- -----------------------------------------------------
-- Table `db_type`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `db_type` ;

CREATE TABLE IF NOT EXISTS `db_type` (
  `id` INTEGER NOT NULL,
  `name` VARCHAR(45) NULL,
  PRIMARY KEY (`id`));


-- -----------------------------------------------------
-- Table `log`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `log` ;

CREATE TABLE IF NOT EXISTS `log` (
  `id` INTEGER NOT NULL,
  `session_id` INTEGER NULL,
  `user_id` INTEGER NULL,
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
    ON UPDATE NO ACTION);

CREATE INDEX `fk_log_user1_idx` ON `log` (`user_id` ASC);

CREATE INDEX `fk_log_session1_idx` ON `log` (`session_id` ASC);


-- -----------------------------------------------------
-- Table `message`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `message` ;

CREATE TABLE IF NOT EXISTS `message` (
  `id` INTEGER NOT NULL,
  `session_id` INTEGER NOT NULL,
  `request_id` BLOB(16) NULL,
  `is_response` TINYINT NULL,
  `message` TEXT NULL,
  `sent` DATETIME NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_message_session1`
    FOREIGN KEY (`session_id`)
    REFERENCES `session` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE INDEX `fk_message_session1_idx` ON `message` (`session_id` ASC);


-- -----------------------------------------------------
-- Table `module`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `module` ;

CREATE TABLE IF NOT EXISTS `module` (
  `id` VARCHAR(256) NOT NULL,
  PRIMARY KEY (`id`));


-- -----------------------------------------------------
-- Table `module_data`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `module_data` ;

CREATE TABLE IF NOT EXISTS `module_data` (
  `id` INTEGER NOT NULL,
  `module_id` VARCHAR(256) NOT NULL,
  `module_data_type_id` INTEGER NOT NULL,
  `user_group_id` INTEGER NULL,
  `group_data_privilege_id` INTEGER NULL,
  `caption` VARCHAR(256) NULL,
  `folder_path` VARCHAR(1024) NULL,
  `content` TEXT NULL,
  `created` DATETIME NULL,
  `last_update` DATETIME NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_module_data_module1`
    FOREIGN KEY (`module_id`)
    REFERENCES `module` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_module_data_module_data_type1`
    FOREIGN KEY (`module_data_type_id`)
    REFERENCES `module_data_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_module_data_user_group1`
    FOREIGN KEY (`user_group_id`)
    REFERENCES `user_group` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_module_data_module_data_privilege1`
    FOREIGN KEY (`group_data_privilege_id`)
    REFERENCES `module_data_privilege` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE INDEX `fk_module_data_module1_idx` ON `module_data` (`module_id` ASC);

CREATE INDEX `fk_module_data_module_data_type1_idx` ON `module_data` (`module_data_type_id` ASC);

CREATE INDEX `fk_module_data_user_group1_idx` ON `module_data` (`user_group_id` ASC);

CREATE INDEX `fk_module_data_module_data_privilege1_idx` ON `module_data` (`group_data_privilege_id` ASC);

CREATE INDEX `module_data_caption_idx` ON `module_data` (`caption` ASC);

CREATE INDEX `module_data_folder_path_idx` ON `module_data` (`folder_path` ASC);


-- -----------------------------------------------------
-- Table `module_data_privilege`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `module_data_privilege` ;

CREATE TABLE IF NOT EXISTS `module_data_privilege` (
  `id` INTEGER NOT NULL,
  `caption` VARCHAR(45) NULL,
  `description` VARCHAR(200) NULL,
  PRIMARY KEY (`id`));


-- -----------------------------------------------------
-- Table `module_data_type`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `module_data_type` ;

CREATE TABLE IF NOT EXISTS `module_data_type` (
  `id` INTEGER NOT NULL,
  `caption` VARCHAR(80) NULL,
  PRIMARY KEY (`id`));


-- -----------------------------------------------------
-- Table `privilege`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `privilege` ;

CREATE TABLE IF NOT EXISTS `privilege` (
  `id` INTEGER NOT NULL,
  `privilege_type_id` INTEGER NOT NULL,
  `name` VARCHAR(100) NULL,
  `access_pattern` VARCHAR(250) NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_privilege_privilege_type1`
    FOREIGN KEY (`privilege_type_id`)
    REFERENCES `privilege_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE INDEX `fk_privilege_privilege_type1_idx` ON `privilege` (`privilege_type_id` ASC);


-- -----------------------------------------------------
-- Table `privilege_type`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `privilege_type` ;

CREATE TABLE IF NOT EXISTS `privilege_type` (
  `id` INTEGER NOT NULL,
  `name` VARCHAR(45) NULL,
  PRIMARY KEY (`id`));


-- -----------------------------------------------------
-- Table `profile`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `profile` ;

CREATE TABLE IF NOT EXISTS `profile` (
  `id` INTEGER NOT NULL,
  `user_id` INTEGER NOT NULL,
  `name` VARCHAR(80) NULL,
  `description` VARCHAR(200) NULL,
  `options` TEXT NULL,
  `active` TINYINT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_profile_user1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE INDEX `fk_profile_user1_idx` ON `profile` (`user_id` ASC);


-- -----------------------------------------------------
-- Table `profile_has_db_connection`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `profile_has_db_connection` ;

CREATE TABLE IF NOT EXISTS `profile_has_db_connection` (
  `profile_id` INTEGER NOT NULL,
  `db_connection_id` INTEGER NOT NULL,
  `db_connection_group_id` INTEGER NOT NULL,
  `active` TINYINT NULL DEFAULT 1,
  PRIMARY KEY (`profile_id`, `db_connection_id`),
  CONSTRAINT `fk_profile_has_db_connection_profile1`
    FOREIGN KEY (`profile_id`)
    REFERENCES `profile` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_profile_has_db_connection_db_connection1`
    FOREIGN KEY (`db_connection_id`)
    REFERENCES `db_connection` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_profile_has_db_connection_db_connection_group1`
    FOREIGN KEY (`db_connection_group_id`)
    REFERENCES `db_connection_group` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE INDEX `fk_profile_has_db_connection_db_connection1_idx` ON `profile_has_db_connection` (`db_connection_id` ASC);

CREATE INDEX `fk_profile_has_db_connection_user_profile1_idx` ON `profile_has_db_connection` (`profile_id` ASC);

CREATE INDEX `fk_profile_has_db_connection_db_connection_group1_idx` ON `profile_has_db_connection` (`db_connection_group_id` ASC);


-- -----------------------------------------------------
-- Table `profile_has_module_data`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `profile_has_module_data` ;

CREATE TABLE IF NOT EXISTS `profile_has_module_data` (
  `profile_id` INTEGER NOT NULL,
  `module_data_id` INTEGER NOT NULL,
  `module_data_privilege_id` INTEGER NOT NULL,
  `active` TINYINT NULL DEFAULT 1,
  PRIMARY KEY (`profile_id`, `module_data_id`),
  CONSTRAINT `fk_profile_has_module_data_profile1`
    FOREIGN KEY (`profile_id`)
    REFERENCES `profile` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_profile_has_module_data_module_data1`
    FOREIGN KEY (`module_data_id`)
    REFERENCES `module_data` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_profile_has_module_data_module_data_privi1`
    FOREIGN KEY (`module_data_privilege_id`)
    REFERENCES `module_data_privilege` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE INDEX `fk_profile_has_module_data_module_data1_idx` ON `profile_has_module_data` (`module_data_id` ASC);

CREATE INDEX `fk_rofile_has_module_data_profile1_idx` ON `profile_has_module_data` (`profile_id` ASC);

CREATE INDEX `fk_profile_has_module_data_module_data_pri_idx` ON `profile_has_module_data` (`module_data_privilege_id` ASC);


-- -----------------------------------------------------
-- Table `profile_has_module_options`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `profile_has_module_options` ;

CREATE TABLE IF NOT EXISTS `profile_has_module_options` (
  `module_id` VARCHAR(256) NOT NULL,
  `profile_id` INTEGER NOT NULL,
  `options` TEXT NULL,
  PRIMARY KEY (`module_id`, `profile_id`),
  CONSTRAINT `fk_module_options_profile1`
    FOREIGN KEY (`profile_id`)
    REFERENCES `profile` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_module_options_module1`
    FOREIGN KEY (`module_id`)
    REFERENCES `module` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE INDEX `fk_profile_has_module_options_profile1_idx` ON `profile_has_module_options` (`profile_id` ASC);

CREATE INDEX `fk_profile_has_module_options_module1_idx` ON `profile_has_module_options` (`module_id` ASC);


-- -----------------------------------------------------
-- Table `role`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `role` ;

CREATE TABLE IF NOT EXISTS `role` (
  `id` INTEGER NOT NULL,
  `name` VARCHAR(45) NULL,
  `description` VARCHAR(200) NULL,
  PRIMARY KEY (`id`));


-- -----------------------------------------------------
-- Table `role_has_privilege`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `role_has_privilege` ;

CREATE TABLE IF NOT EXISTS `role_has_privilege` (
  `role_id` INTEGER NOT NULL,
  `privilege_id` INTEGER NOT NULL,
  PRIMARY KEY (`role_id`, `privilege_id`),
  CONSTRAINT `fk_role_has_privilege_role`
    FOREIGN KEY (`role_id`)
    REFERENCES `role` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_role_has_privilege_privilege1`
    FOREIGN KEY (`privilege_id`)
    REFERENCES `privilege` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE INDEX `fk_role_has_privilege_privilege1_idx` ON `role_has_privilege` (`privilege_id` ASC);

CREATE INDEX `fk_role_has_privilege_role_idx` ON `role_has_privilege` (`role_id` ASC);


-- -----------------------------------------------------
-- Table `session`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `session` ;

CREATE TABLE IF NOT EXISTS `session` (
  `id` INTEGER NOT NULL,
  `continued_session_id` INTEGER NULL,
  `user_id` INTEGER NULL,
  `uuid` BLOB(16) NULL,
  `started` DATETIME NULL,
  `ended` DATETIME NULL,
  `source_ip` VARCHAR(256) NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_session_users1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_session_session1`
    FOREIGN KEY (`continued_session_id`)
    REFERENCES `session` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE INDEX `fk_session_users1_idx` ON `session` (`user_id` ASC);

CREATE INDEX `fk_session_session1_idx` ON `session` (`continued_session_id` ASC);


-- -----------------------------------------------------
-- Table `user`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `user` ;

CREATE TABLE IF NOT EXISTS `user` (
  `id` INTEGER NOT NULL,
  `default_profile_id` INTEGER NULL,
  `name` VARCHAR(45) NULL,
  `password_hash` VARCHAR(256) NULL,
  `allowed_hosts` VARCHAR(512) NULL,
  `active` TINYINT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_user_profile1`
    FOREIGN KEY (`default_profile_id`)
    REFERENCES `profile` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE UNIQUE INDEX `name_UNIQUE` ON `user` (`name` ASC);

CREATE INDEX `fk_user_profile1_idx` ON `user` (`default_profile_id` ASC);


-- -----------------------------------------------------
-- Table `user_group`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `user_group` ;

CREATE TABLE IF NOT EXISTS `user_group` (
  `id` INTEGER NOT NULL,
  `name` VARCHAR(45) NULL,
  `description` VARCHAR(200) NULL,
  `active` TINYINT NULL,
  PRIMARY KEY (`id`));


-- -----------------------------------------------------
-- Table `user_group_has_user`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `user_group_has_user` ;

CREATE TABLE IF NOT EXISTS `user_group_has_user` (
  `user_group_id` INTEGER NOT NULL,
  `user_id` INTEGER NOT NULL,
  `owner` TINYINT NULL,
  PRIMARY KEY (`user_group_id`, `user_id`),
  CONSTRAINT `fk_user_group_has_user_user_group1`
    FOREIGN KEY (`user_group_id`)
    REFERENCES `user_group` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_user_group_has_user_user1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE INDEX `fk_user_group_has_user_user1_idx` ON `user_group_has_user` (`user_id` ASC);

CREATE INDEX `fk_user_group_has_user_user_group1_idx` ON `user_group_has_user` (`user_group_id` ASC);


-- -----------------------------------------------------
-- Table `user_has_role`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `user_has_role` ;

CREATE TABLE IF NOT EXISTS `user_has_role` (
  `user_id` INTEGER NOT NULL,
  `role_id` INTEGER NOT NULL,
  PRIMARY KEY (`user_id`, `role_id`),
  CONSTRAINT `fk_users_has_role_users1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_users_has_role_role1`
    FOREIGN KEY (`role_id`)
    REFERENCES `role` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE INDEX `fk_users_has_role_role1_idx` ON `user_has_role` (`role_id` ASC);

CREATE INDEX `fk_users_has_role_users1_idx` ON `user_has_role` (`user_id` ASC);


-- -----------------------------------------------------
-- Data for table `db_type`
-- -----------------------------------------------------
BEGIN TRANSACTION;
INSERT INTO `db_type` (`id`, `name`) VALUES (1, 'MySQL');
INSERT INTO `db_type` (`id`, `name`) VALUES (2, 'Sqlite');

COMMIT;


-- -----------------------------------------------------
-- Data for table `module_data_privilege`
-- -----------------------------------------------------
BEGIN TRANSACTION;
INSERT INTO `module_data_privilege` (`id`, `caption`, `description`) VALUES (1, 'Owner', 'Owner of the data');
INSERT INTO `module_data_privilege` (`id`, `caption`, `description`) VALUES (2, 'User', 'User of the data with read/write permissions');
INSERT INTO `module_data_privilege` (`id`, `caption`, `description`) VALUES (3, 'Viewer', 'User of the data with read permissions only');

COMMIT;


-- -----------------------------------------------------
-- Data for table `module_data_type`
-- -----------------------------------------------------
BEGIN TRANSACTION;
INSERT INTO `module_data_type` (`id`, `caption`) VALUES (1, 'File');
INSERT INTO `module_data_type` (`id`, `caption`) VALUES (2, 'Script');
INSERT INTO `module_data_type` (`id`, `caption`) VALUES (3, 'JSON');
INSERT INTO `module_data_type` (`id`, `caption`) VALUES (4, 'File Link');

COMMIT;


-- -----------------------------------------------------
-- Data for table `privilege`
-- -----------------------------------------------------
BEGIN TRANSACTION;
INSERT INTO `privilege` (`id`, `privilege_type_id`, `name`, `access_pattern`) VALUES (1, 1, 'Full access to all python globals', '.*');
INSERT INTO `privilege` (`id`, `privilege_type_id`, `name`, `access_pattern`) VALUES (2, 2, 'Full access to all web gui modules', '.*');
INSERT INTO `privilege` (`id`, `privilege_type_id`, `name`, `access_pattern`) VALUES (3, 1, 'Access to common gui extension objects', 'gui\\.(modules|sqleditor)\\.\\w*');
INSERT INTO `privilege` (`id`, `privilege_type_id`, `name`, `access_pattern`) VALUES (4, 2, 'Access to all web gui modules except shell', '\\b(?!shell\\b)\\w+');
INSERT INTO `privilege` (`id`, `privilege_type_id`, `name`, `access_pattern`) VALUES (5, 1, 'Access to selected gui.users functions', 'gui\\.users\\.(get_gui_module_list|get_profiles|add_profile|get_default_profile|set_default_profile|set_web_session_profile)');

COMMIT;


-- -----------------------------------------------------
-- Data for table `privilege_type`
-- -----------------------------------------------------
BEGIN TRANSACTION;
INSERT INTO `privilege_type` (`id`, `name`) VALUES (1, 'Python Environment Access');
INSERT INTO `privilege_type` (`id`, `name`) VALUES (2, 'GUI Module Access');

COMMIT;


-- -----------------------------------------------------
-- Data for table `role`
-- -----------------------------------------------------
BEGIN TRANSACTION;
INSERT INTO `role` (`id`, `name`, `description`) VALUES (1, 'Administrator', 'Administrator with full access');
INSERT INTO `role` (`id`, `name`, `description`) VALUES (2, 'Poweruser', 'Web user with full access');
INSERT INTO `role` (`id`, `name`, `description`) VALUES (3, 'User', 'Web user with full access expect to the shell module');

COMMIT;


-- -----------------------------------------------------
-- Data for table `role_has_privilege`
-- -----------------------------------------------------
BEGIN TRANSACTION;
INSERT INTO `role_has_privilege` (`role_id`, `privilege_id`) VALUES (1, 1);
INSERT INTO `role_has_privilege` (`role_id`, `privilege_id`) VALUES (1, 2);
INSERT INTO `role_has_privilege` (`role_id`, `privilege_id`) VALUES (2, 2);
INSERT INTO `role_has_privilege` (`role_id`, `privilege_id`) VALUES (2, 3);
INSERT INTO `role_has_privilege` (`role_id`, `privilege_id`) VALUES (3, 3);
INSERT INTO `role_has_privilege` (`role_id`, `privilege_id`) VALUES (3, 4);

COMMIT;



PRAGMA foreign_keys = ON;

