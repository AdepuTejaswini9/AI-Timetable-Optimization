-- MySQL 8 schema generated from backend/app/models/models.py (python database/generate_sql.py)

CREATE DATABASE IF NOT EXISTS timetable_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE timetable_db;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `departments`;

DROP TABLE IF EXISTS `rooms`;

DROP TABLE IF EXISTS `system_settings`;

DROP TABLE IF EXISTS `time_slots`;

DROP TABLE IF EXISTS `sections`;

DROP TABLE IF EXISTS `subjects`;

DROP TABLE IF EXISTS `users`;

DROP TABLE IF EXISTS `faculty_profiles`;

DROP TABLE IF EXISTS `notifications`;

DROP TABLE IF EXISTS `optimization_runs`;

DROP TABLE IF EXISTS `student_profiles`;

DROP TABLE IF EXISTS `faculty_availability`;

DROP TABLE IF EXISTS `faculty_preferences`;

DROP TABLE IF EXISTS `leave_requests`;

DROP TABLE IF EXISTS `subject_assignments`;

DROP TABLE IF EXISTS `timetable_versions`;

DROP TABLE IF EXISTS `approval_records`;

DROP TABLE IF EXISTS `constraint_violations`;

DROP TABLE IF EXISTS `optimization_solutions`;

DROP TABLE IF EXISTS `timetable`;

DROP TABLE IF EXISTS `timetable_change_requests`;

CREATE TABLE departments (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	code VARCHAR(20) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code), 
	UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE rooms (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(40) NOT NULL, 
	capacity INTEGER NOT NULL, 
	is_lab BOOL NOT NULL, 
	is_available BOOL NOT NULL, 
	building VARCHAR(60), 
	PRIMARY KEY (id), 
	UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE system_settings (
	`key` VARCHAR(60) NOT NULL, 
	value VARCHAR(255) NOT NULL, 
	PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE time_slots (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	day INTEGER NOT NULL, 
	period INTEGER NOT NULL, 
	start_time VARCHAR(5) NOT NULL, 
	end_time VARCHAR(5) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_slot UNIQUE (day, period)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE sections (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(40) NOT NULL, 
	department_id INTEGER NOT NULL, 
	semester INTEGER NOT NULL, 
	strength INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_section UNIQUE (name, department_id, semester), 
	FOREIGN KEY(department_id) REFERENCES departments (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX ix_sections_department_id ON sections (department_id);

CREATE TABLE subjects (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	code VARCHAR(20) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	department_id INTEGER NOT NULL, 
	semester INTEGER NOT NULL, 
	weekly_hours INTEGER NOT NULL, 
	is_lab BOOL NOT NULL, 
	lab_block INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_hours CHECK (weekly_hours > 0), 
	UNIQUE (code), 
	FOREIGN KEY(department_id) REFERENCES departments (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX ix_subjects_department_id ON subjects (department_id);

CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	full_name VARCHAR(120) NOT NULL, 
	`role` VARCHAR(10) NOT NULL, 
	department_id INTEGER, 
	is_active BOOL NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_user_role CHECK (role in ('admin','hod','faculty','student')), 
	FOREIGN KEY(department_id) REFERENCES departments (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE faculty_profiles (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	department_id INTEGER NOT NULL, 
	designation VARCHAR(60), 
	max_daily_hours INTEGER NOT NULL, 
	max_weekly_hours INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(department_id) REFERENCES departments (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX ix_faculty_profiles_department_id ON faculty_profiles (department_id);

CREATE TABLE notifications (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	title VARCHAR(120) NOT NULL, 
	message TEXT, 
	is_read BOOL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX ix_notifications_user_id ON notifications (user_id);

CREATE TABLE optimization_runs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	algorithm VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	outcome VARCHAR(30), 
	params JSON, 
	progress JSON, 
	history JSON, 
	message TEXT, 
	created_by INTEGER, 
	created_at DATETIME, 
	finished_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE student_profiles (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	section_id INTEGER NOT NULL, 
	roll_no VARCHAR(30) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(section_id) REFERENCES sections (id), 
	UNIQUE (roll_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX ix_student_profiles_section_id ON student_profiles (section_id);

CREATE TABLE faculty_availability (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	faculty_id INTEGER NOT NULL, 
	day INTEGER NOT NULL, 
	period INTEGER NOT NULL, 
	is_available BOOL NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_avail UNIQUE (faculty_id, day, period), 
	FOREIGN KEY(faculty_id) REFERENCES faculty_profiles (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE faculty_preferences (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	faculty_id INTEGER NOT NULL, 
	day INTEGER NOT NULL, 
	period INTEGER NOT NULL, 
	preference VARCHAR(10) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_pref UNIQUE (faculty_id, day, period), 
	FOREIGN KEY(faculty_id) REFERENCES faculty_profiles (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE leave_requests (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	faculty_id INTEGER NOT NULL, 
	day INTEGER NOT NULL, 
	period_from INTEGER, 
	period_to INTEGER, 
	reason VARCHAR(255), 
	status VARCHAR(10), 
	reviewed_by INTEGER, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(faculty_id) REFERENCES faculty_profiles (id), 
	FOREIGN KEY(reviewed_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE subject_assignments (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	subject_id INTEGER NOT NULL, 
	section_id INTEGER NOT NULL, 
	faculty_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_assign UNIQUE (subject_id, section_id), 
	FOREIGN KEY(subject_id) REFERENCES subjects (id), 
	FOREIGN KEY(section_id) REFERENCES sections (id), 
	FOREIGN KEY(faculty_id) REFERENCES faculty_profiles (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE timetable_versions (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(120) NOT NULL, 
	version_number INTEGER, 
	status VARCHAR(15) NOT NULL, 
	run_id INTEGER, 
	parent_version_id INTEGER, 
	created_by INTEGER, 
	created_at DATETIME, 
	hard_violations INTEGER, 
	objectives JSON, 
	notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(run_id) REFERENCES optimization_runs (id), 
	FOREIGN KEY(parent_version_id) REFERENCES timetable_versions (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE approval_records (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	version_id INTEGER NOT NULL, 
	department_id INTEGER NOT NULL, 
	status VARCHAR(10) NOT NULL, 
	decided_by INTEGER, 
	comment TEXT, 
	decided_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_approval UNIQUE (version_id, department_id), 
	FOREIGN KEY(version_id) REFERENCES timetable_versions (id) ON DELETE CASCADE, 
	FOREIGN KEY(department_id) REFERENCES departments (id), 
	FOREIGN KEY(decided_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE constraint_violations (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	version_id INTEGER, 
	run_id INTEGER, 
	type VARCHAR(40) NOT NULL, 
	severity VARCHAR(10), 
	faculty_id INTEGER, 
	subject_id INTEGER, 
	section_id INTEGER, 
	room_id INTEGER, 
	day INTEGER, 
	period INTEGER, 
	explanation TEXT, 
	suggestion TEXT, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(version_id) REFERENCES timetable_versions (id) ON DELETE CASCADE, 
	FOREIGN KEY(run_id) REFERENCES optimization_runs (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE optimization_solutions (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	run_id INTEGER NOT NULL, 
	`rank` INTEGER, 
	genes JSON NOT NULL, 
	objectives JSON NOT NULL, 
	hard_violations INTEGER, 
	is_selected BOOL, 
	version_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(run_id) REFERENCES optimization_runs (id) ON DELETE CASCADE, 
	FOREIGN KEY(version_id) REFERENCES timetable_versions (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX ix_optimization_solutions_run_id ON optimization_solutions (run_id);

CREATE TABLE timetable (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	version_id INTEGER NOT NULL, 
	section_id INTEGER NOT NULL, 
	subject_id INTEGER NOT NULL, 
	faculty_id INTEGER NOT NULL, 
	room_id INTEGER NOT NULL, 
	day INTEGER NOT NULL, 
	period INTEGER NOT NULL, 
	duration INTEGER NOT NULL, 
	is_lab BOOL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(version_id) REFERENCES timetable_versions (id) ON DELETE CASCADE, 
	FOREIGN KEY(section_id) REFERENCES sections (id), 
	FOREIGN KEY(subject_id) REFERENCES subjects (id), 
	FOREIGN KEY(faculty_id) REFERENCES faculty_profiles (id), 
	FOREIGN KEY(room_id) REFERENCES rooms (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX ix_timetable_faculty_id ON timetable (faculty_id);

CREATE INDEX ix_timetable_section_id ON timetable (section_id);

CREATE INDEX ix_timetable_version_id ON timetable (version_id);

CREATE INDEX ix_tt_slot ON timetable (version_id, day, period);

CREATE TABLE timetable_change_requests (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	requested_by INTEGER NOT NULL, 
	version_id INTEGER, 
	request_type VARCHAR(20), 
	description TEXT NOT NULL, 
	payload JSON, 
	status VARCHAR(10), 
	response_note TEXT, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(requested_by) REFERENCES users (id), 
	FOREIGN KEY(version_id) REFERENCES timetable_versions (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
