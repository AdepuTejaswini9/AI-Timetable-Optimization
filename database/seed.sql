-- DEVELOPMENT-ONLY seed data. Passwords are bcrypt hashes of the demo credentials in README.md.

USE timetable_db;

SET FOREIGN_KEY_CHECKS = 0;

INSERT INTO `departments` (`id`, `code`, `name`) VALUES
  (1, 'CSE', 'Computer Science & Engineering'),
  (2, 'ECE', 'Electronics & Communication Engineering');

INSERT INTO `rooms` (`id`, `name`, `capacity`, `is_lab`, `is_available`, `building`) VALUES
  (1, 'R101', 60, 0, 1, 'Main Block'),
  (2, 'R102', 60, 0, 1, 'Main Block'),
  (3, 'R103', 70, 0, 1, 'Main Block'),
  (4, 'R104', 50, 0, 1, 'Main Block'),
  (5, 'R105', 45, 0, 1, 'Main Block'),
  (6, 'LAB-1', 60, 1, 1, 'Main Block'),
  (7, 'LAB-2', 60, 1, 1, 'Main Block');

INSERT INTO `system_settings` (`key`, `value`) VALUES
  ('break_after_period', '2'),
  ('weight_student_free_periods', '1.0'),
  ('weight_faculty_preference_violations', '1.0'),
  ('weight_excess_consecutive_teaching', '1.0'),
  ('weight_room_underutilization', '1.0'),
  ('weight_subject_distribution', '1.0');

INSERT INTO `time_slots` (`id`, `day`, `period`, `start_time`, `end_time`) VALUES
  (1, 0, 0, '09:00', '09:50'),
  (2, 0, 1, '10:00', '10:50'),
  (3, 0, 2, '11:00', '11:50'),
  (4, 0, 3, '13:00', '13:50'),
  (5, 0, 4, '14:00', '14:50'),
  (6, 0, 5, '15:00', '15:50'),
  (7, 1, 0, '09:00', '09:50'),
  (8, 1, 1, '10:00', '10:50'),
  (9, 1, 2, '11:00', '11:50'),
  (10, 1, 3, '13:00', '13:50'),
  (11, 1, 4, '14:00', '14:50'),
  (12, 1, 5, '15:00', '15:50'),
  (13, 2, 0, '09:00', '09:50'),
  (14, 2, 1, '10:00', '10:50'),
  (15, 2, 2, '11:00', '11:50'),
  (16, 2, 3, '13:00', '13:50'),
  (17, 2, 4, '14:00', '14:50'),
  (18, 2, 5, '15:00', '15:50'),
  (19, 3, 0, '09:00', '09:50'),
  (20, 3, 1, '10:00', '10:50'),
  (21, 3, 2, '11:00', '11:50'),
  (22, 3, 3, '13:00', '13:50'),
  (23, 3, 4, '14:00', '14:50'),
  (24, 3, 5, '15:00', '15:50'),
  (25, 4, 0, '09:00', '09:50'),
  (26, 4, 1, '10:00', '10:50'),
  (27, 4, 2, '11:00', '11:50'),
  (28, 4, 3, '13:00', '13:50'),
  (29, 4, 4, '14:00', '14:50'),
  (30, 4, 5, '15:00', '15:50');

INSERT INTO `sections` (`id`, `name`, `department_id`, `semester`, `strength`) VALUES
  (1, 'A', 1, 3, 55),
  (2, 'B', 1, 3, 50),
  (3, 'A', 2, 3, 45);

INSERT INTO `subjects` (`id`, `code`, `name`, `department_id`, `semester`, `weekly_hours`, `is_lab`, `lab_block`) VALUES
  (1, 'CS301', 'Data Structures', 1, 3, 4, 0, 2),
  (2, 'CS302', 'Database Management Systems', 1, 3, 4, 0, 2),
  (3, 'CS303', 'Operating Systems', 1, 3, 3, 0, 2),
  (4, 'CS304', 'Computer Networks', 1, 3, 3, 0, 2),
  (5, 'CS305L', 'Data Structures Lab', 1, 3, 4, 1, 2),
  (6, 'EC301', 'Signals & Systems', 2, 3, 4, 0, 2),
  (7, 'EC302', 'Digital Electronics', 2, 3, 4, 0, 2),
  (8, 'EC303', 'Electromagnetic Theory', 2, 3, 3, 0, 2),
  (9, 'EC304', 'Analog Circuits', 2, 3, 3, 0, 2),
  (10, 'EC305L', 'Electronics Lab', 2, 3, 4, 1, 2);

INSERT INTO `users` (`id`, `email`, `password_hash`, `full_name`, `role`, `department_id`, `is_active`, `created_at`) VALUES
  (1, 'admin@college.edu', '$2b$12$Sa6TSv/92ZDTewsXdEKFAe6li1hyb6CFRJGm.Q3YE7QPR4uqK5pOW', 'System Admin', 'admin', NULL, 1, '2026-11-05 08:36:24'),
  (2, 'hod.cse@college.edu', '$2b$12$tSIhiopOAmr620qpBYwLmOWjGADpBfEJutJk2H7x0xomFexGU7Icm', 'Dr. Ravi Kumar (HOD CSE)', 'hod', 1, 1, '2026-11-05 08:36:25'),
  (3, 'hod.ece@college.edu', '$2b$12$GVOfQAJXxlt2c6pDUkL.QuzWIb.LthM8h0InMjSD40zr/1MMqw8FC', 'Dr. Sunita Rao (HOD ECE)', 'hod', 2, 1, '2026-11-05 08:36:25'),
  (4, 'faculty1@college.edu', '$2b$12$9qIBhSqDAl6PoTrEYzxR6e3up4cciLVv1zHihfolqN6oxLOq8EJJi', 'Dr. Anil Sharma', 'faculty', NULL, 1, '2026-11-05 08:36:25'),
  (5, 'faculty2@college.edu', '$2b$12$jljvzUBTSmBGcvI2MgGd3emw8T0YS80Q8cnOzzFr2aHTdNcwM3My.', 'Prof. Meera Iyer', 'faculty', NULL, 1, '2026-11-05 08:36:25'),
  (6, 'faculty3@college.edu', '$2b$12$bHB1.Zirln9Y8zGsvlfpk.UmvsDM/YuuJ40kV0oQuJAhx6m3JbIGK', 'Dr. Kiran Reddy', 'faculty', NULL, 1, '2026-11-05 08:36:26'),
  (7, 'faculty4@college.edu', '$2b$12$P0hMDg.M8wz30tGsJfwtc.8aRCRuGCnlG7YlDpyEB5xTjaF8nRtZC', 'Prof. Lakshmi Devi', 'faculty', NULL, 1, '2026-11-05 08:36:26'),
  (8, 'faculty5@college.edu', '$2b$12$Ts2q52VKGu.eKXKf75UskOEwSWQTfWB9908xCD1wpWUAFLRJZiCOy', 'Dr. Suresh Babu', 'faculty', NULL, 1, '2026-11-05 08:36:26'),
  (9, 'faculty6@college.edu', '$2b$12$tye149AOktkp099N/Ia.Q.BuTyL7xnSaZL8lbVU9bujbOCOoeAUvC', 'Dr. Priya Nair', 'faculty', NULL, 1, '2026-11-05 08:36:27'),
  (10, 'faculty7@college.edu', '$2b$12$rc1LyyfDIC4.dXOBjXXPWeik4d/BwFg/mqEFU0O/3Okm348M5JRRW', 'Prof. Rahul Verma', 'faculty', NULL, 1, '2026-11-05 08:36:27'),
  (11, 'faculty8@college.edu', '$2b$12$wdnxQ8bdcx8..Qzj0Fs9EOKjdH7ZvvtmlOoM9KkDcWLAmuoDfrg4S', 'Dr. Anita Das', 'faculty', NULL, 1, '2026-11-05 08:36:27'),
  (12, 'faculty9@college.edu', '$2b$12$fpy1PgR8.ceq7ddh5QBKtOSwhpccuQdtVp4YJsjaoSdNYSOptaI8a', 'Prof. Vikram Singh', 'faculty', NULL, 1, '2026-11-05 08:36:27'),
  (13, 'faculty10@college.edu', '$2b$12$YNTExApMWK/V0G9U1KSgW.Oe1SoSw12/e/ZCQZ2JFpz9DWhr3.6ia', 'Dr. Neha Gupta', 'faculty', NULL, 1, '2026-11-05 08:36:28'),
  (14, 'student1@college.edu', '$2b$12$v3ErZ2yPOOFiZdM8P46kc.BKnZgtkgrnZBheaPBEkXNGGp8.pFAv6', 'Asha Student', 'student', NULL, 1, '2026-11-05 08:36:28'),
  (15, 'student2@college.edu', '$2b$12$AxKm9MoxGldO1aDJBdKjNeQxBU9bRONoRUVrNEyVIMjBlxKyg.H1q', 'Bharat Student', 'student', NULL, 1, '2026-11-05 08:36:28'),
  (16, 'student3@college.edu', '$2b$12$LanIQtxVO4n1iapnbl/RCuMCJCUHmwDb7yNADV1j5lq6mtwLlGdzm', 'Chitra Student', 'student', NULL, 1, '2026-11-05 08:36:29'),
  (17, 'student4@college.edu', '$2b$12$bdTkRSDTqw6nG8cD2BTbqukMvfbmOsbxiIQNRr5wlDwVPL/iKcqgm', 'Dev Student', 'student', NULL, 1, '2026-11-05 08:36:29'),
  (18, 'student5@college.edu', '$2b$12$OVMUewXjeDuSFWq1vb007.EUgEN1YjGer9/cRshaCjMJiQNoJdi1W', 'Esha Student', 'student', NULL, 1, '2026-11-05 08:36:29'),
  (19, 'student6@college.edu', '$2b$12$kRz0/UyUAny618z2WKGQcOr5avsRERuyuAhX8mDzBi17OR9RZpYn6', 'Farhan Student', 'student', NULL, 1, '2026-11-05 08:36:29');

INSERT INTO `faculty_profiles` (`id`, `user_id`, `department_id`, `designation`, `max_daily_hours`, `max_weekly_hours`) VALUES
  (1, 4, 1, 'Assistant Professor', 5, 18),
  (2, 5, 1, 'Assistant Professor', 5, 18),
  (3, 6, 1, 'Assistant Professor', 5, 18),
  (4, 7, 1, 'Assistant Professor', 5, 18),
  (5, 8, 1, 'Assistant Professor', 5, 18),
  (6, 9, 2, 'Assistant Professor', 5, 18),
  (7, 10, 2, 'Assistant Professor', 5, 18),
  (8, 11, 2, 'Assistant Professor', 5, 18),
  (9, 12, 2, 'Assistant Professor', 5, 18),
  (10, 13, 2, 'Assistant Professor', 5, 18);

INSERT INTO `student_profiles` (`id`, `user_id`, `section_id`, `roll_no`) VALUES
  (1, 14, 1, '2211001'),
  (2, 15, 1, '2211002'),
  (3, 16, 2, '2212003'),
  (4, 17, 2, '2212004'),
  (5, 18, 3, '2223005'),
  (6, 19, 3, '2223006');

INSERT INTO `faculty_availability` (`id`, `faculty_id`, `day`, `period`, `is_available`) VALUES
  (1, 1, 4, 3, 0),
  (2, 1, 4, 4, 0),
  (3, 1, 4, 5, 0),
  (4, 6, 0, 0, 0);

INSERT INTO `faculty_preferences` (`id`, `faculty_id`, `day`, `period`, `preference`) VALUES
  (1, 2, 0, 5, 'avoid'),
  (2, 2, 1, 5, 'avoid'),
  (3, 2, 2, 5, 'avoid'),
  (4, 2, 3, 5, 'avoid'),
  (5, 2, 4, 5, 'avoid'),
  (6, 3, 0, 0, 'avoid'),
  (7, 3, 1, 0, 'avoid'),
  (8, 3, 2, 0, 'avoid'),
  (9, 3, 3, 0, 'avoid'),
  (10, 3, 4, 0, 'avoid');

INSERT INTO `subject_assignments` (`id`, `subject_id`, `section_id`, `faculty_id`) VALUES
  (1, 1, 1, 1),
  (2, 1, 2, 1),
  (3, 2, 1, 2),
  (4, 2, 2, 2),
  (5, 3, 1, 3),
  (6, 3, 2, 3),
  (7, 4, 1, 4),
  (8, 4, 2, 4),
  (9, 5, 1, 5),
  (10, 5, 2, 5),
  (11, 6, 3, 6),
  (12, 7, 3, 7),
  (13, 8, 3, 8),
  (14, 9, 3, 9),
  (15, 10, 3, 10);

SET FOREIGN_KEY_CHECKS = 1;
