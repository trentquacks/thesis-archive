-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS author;
DROP TABLE IF EXISTS department;
DROP TABLE IF EXISTS branch;
DROP TABLE IF EXISTS format;
DROP TABLE IF EXISTS thesis;
DROP TABLE IF EXISTS thesis_author;
DROP TABLE IF EXISTS bookmark; -- Added drop for bookmark

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  role TEXT CHECK( role IN ('student', 'admin', 'librarian') ) DEFAULT 'student'
);

CREATE TABLE author (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  middle_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  student_no TEXT NOT NULL
);

CREATE TABLE department (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL, -- cs department, it department
  description TEXT UNIQUE NOT NULL,
  icon TEXT DEFAULT 'fa-building'
);

CREATE TABLE branch (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL -- imus, main, australia
);

CREATE TABLE format (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  format TEXT UNIQUE NOT NULL -- hard copy, digital pdf
);


CREATE TABLE thesis (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date_published TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- kailan na add sa system
  title TEXT NOT NULL,
  abstract TEXT NOT NULL, -- preview text
  file_path TEXT NOT NULL, -- digital pdf sa db

  -- APPROVAL WORKFLOW
  status TEXT CHECK( status IN ('pending', 'approved', 'rejected') ) DEFAULT 'pending',

  -- specifics
  keywords TEXT,
  isbn TEXT,
  barcode TEXT,
  call_number TEXT, -- used for finding in shelves easily

  -- foreigns
  department_id INTEGER NOT NULL, 
  branch_id INTEGER NOT NULL,
  format_id INTEGER NOT NULL,
  uploader_id INTEGER NOT NULL,
  FOREIGN KEY (department_id) REFERENCES department (id),
  FOREIGN KEY (branch_id) REFERENCES branch (id),
  FOREIGN KEY (format_id) REFERENCES format (id),
  FOREIGN KEY (uploader_id) REFERENCES user (id)
);

CREATE TABLE thesis_author (
  thesis_id INTEGER NOT NULL,
  author_id INTEGER NOT NULL,
  PRIMARY KEY (thesis_id, author_id), -- prevents same pair
  FOREIGN KEY (thesis_id) REFERENCES thesis (id),
  FOREIGN KEY (author_id) REFERENCES author (id)
);

-- =========================================
-- NEW BOOKMARK TABLE
-- =========================================
CREATE TABLE bookmark (
  user_id INTEGER NOT NULL,
  thesis_id INTEGER NOT NULL,
  date_bookmarked TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, thesis_id), -- Prevents a user from bookmarking the same thesis twice
  FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
  FOREIGN KEY (thesis_id) REFERENCES thesis (id) ON DELETE CASCADE
);

-- Information required according to SRS
-- searchable by keyword, title, author, date year
-- filterable by title, author, year and category
-- thesis ISBD and MARC view format
-- history of submissions, user actions, log in activity, modification of theses and approval of submissions
-- total thesis records
--
-- bookmark table (ADDED ABOVE)
-- preview: digital preview, digital scan, abstract

-- discontinued??
-- availability.. :C


INSERT INTO user (email, password, role) VALUES 
('testing@gmail.com', 'scrypt:32768:8:1$CnOYZglEnYCUPpVx$3bf12468ee0826fbf6b59c8422670a3e2429b56ed9f6dc0f60ffd354fab2ac41bee12647d5d2fcb01524dd627c9a13e519a71f93379dca9490161e300547a1dc', 'admin');

INSERT INTO author (first_name, middle_name, last_name, student_no) VALUES 
('David', '', 'Wilson', '2024-0023'),
('Sarah', '', 'Gomez', '2023-1100'),
('Kevin', '', 'Lee', '2022-0912'),
('Maria', '', 'Santos', '2021-0452'),
('Juan', 'Dela', 'Cruz', '2020-0001');

INSERT INTO department (name, description, icon) VALUES 
('Office Administration', 'Management of clerical and administrative systems.', 'fa-user-tie'),
('Psychology', 'Study of human behavior and mental processes.', 'fa-brain'),
('Journalism', 'Media production and investigative reporting.', 'fa-pen-nib'),
('Information Technology', 'Applied technology solutions and networking.', 'fa-desktop'),
('Hospitality Management', 'Service industry management and tourism.', 'fa-hotel'),
('Education', 'Pedagogy and teacher training for modern classrooms.', 'fa-book-open'),
('Entrepreneurship', 'Study of innovation and small business management.', 'fa-lightbulb'),
('Computer Science', 'Theory and practice of computation and software development.', 'fa-robot'),
('Business Administration', 'Focuses on corporate management, marketing, and finance.', 'fa-briefcase-clock');

INSERT INTO branch (name) VALUES 
('Imus'), 
('Main'), 
('Australia');

INSERT INTO format (format) VALUES 
('Digital PDF'), 
('Hard Copy');

INSERT INTO thesis (title, abstract, file_path, status, keywords, isbn, barcode, call_number, department_id, branch_id, format_id, uploader_id) VALUES 
('AI-driven Scheduling Systems', 'Optimizing executive calendars with machine learning.', '/static/uploads/2026/oa_schedule.pdf', 'approved', 'AI, Scheduling, Machine Learning', '978-0-009-00005-0', 'BC905', 'OA-2026-05', 1, 1, 1, 1),
('Automated Workflow Efficiency', 'Using RPA (Robotic Process Automation) for data entry.', '/static/uploads/2024/oa_rpa.pdf', 'approved', 'RPA, Workflow, Automation', '978-0-009-00004-0', 'BC904', 'OA-2024-04', 1, 2, 1, 1),
('VR in History Classes', 'Immersive learning experiences in historical education.', '/static/uploads/2025/edu_vr.pdf', 'approved', 'VR, History, Education', '978-0-004-00005-0', 'BC405', 'EDU-2025-05', 6, 3, 1, 1),
('Blended Learning Retention', 'Comparing student outcomes in hybrid vs traditional setups.', '/static/uploads/2024/edu_blended.pdf', 'pending', 'Blended Learning, Hybrid', '978-0-004-00004-0', 'BC404', 'EDU-2024-04', 6, 1, 1, 1),
('Quantum Cryptography Protocols', 'Securing data transmission against quantum decryption.', '/static/uploads/2024/cs_crypto.pdf', 'approved', 'Quantum, Cryptography, Security', '978-0-002-00004-0', 'BC204', 'CS-2024-04', 8, 2, 1, 1);

INSERT INTO thesis_author (thesis_id, author_id) VALUES 
(1, 1),
(2, 2),
(3, 3),
(4, 4),
(5, 5);

-- Sample Bookmarks
INSERT INTO bookmark (user_id, thesis_id) VALUES 
(1, 1),
(1, 5);
