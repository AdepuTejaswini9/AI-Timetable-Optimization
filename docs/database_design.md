# Database design
Schema: `database/schema.sql` (generated from the SQLAlchemy models by `database/generate_sql.py`). 20 required tables + `system_settings`.
Key points: `timetable` rows belong to a `timetable_versions` row (history/versioning, `parent_version_id`); unique constraints on (subject, section) assignments, (version, department) approvals, (day, period) slots; FK + indexes on all lookup columns; passwords are bcrypt hashes.
Faculty unavailability is stored as rows in `faculty_availability` (is_available=false); soft "avoid" slots in `faculty_preferences`.
HOD ↔ department is `users.department_id`; student ↔ section is `student_profiles.section_id`.
