-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS author;
DROP TABLE IF EXISTS department;
DROP TABLE IF EXISTS branch;
DROP TABLE IF EXISTS format;
DROP TABLE IF EXISTS thesis;
DROP TABLE IF EXISTS thesis_author;
DROP TABLE IF EXISTS advisor;
DROP TABLE IF EXISTS thesis_advisor; 
DROP TABLE IF EXISTS bookmark; 
DROP TABLE IF EXISTS user_history; 
DROP TABLE IF EXISTS active_borrow; 

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  student_no TEXT NOT NULL,
  course TEXT NOT NULL,
  profile_pic TEXT DEFAULT 'default.png',
  role TEXT CHECK( role IN ('student', 'admin', 'librarian') ) DEFAULT 'student',
  failed_attempts INTEGER DEFAULT 0,
  lockout_until DATETIME
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

CREATE TABLE advisor (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  middle_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  faculty_no TEXT NOT NULL UNIQUE
);
CREATE TABLE thesis_advisor (
  thesis_id INTEGER NOT NULL,
  advisor_id INTEGER NOT NULL,
  PRIMARY KEY (thesis_id, advisor_id),
  FOREIGN KEY (thesis_id) REFERENCES thesis (id),
  FOREIGN KEY (advisor_id) REFERENCES advisor (id)
);

CREATE TABLE bookmark (
  user_id INTEGER NOT NULL,
  thesis_id INTEGER NOT NULL,
  date_bookmarked TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, thesis_id), -- Prevents a user from bookmarking the same thesis twice
  FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
  FOREIGN KEY (thesis_id) REFERENCES thesis (id) ON DELETE CASCADE
);

CREATE TABLE user_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  action TEXT NOT NULL, -- e.g., 'Bookmarked', 'Unbookmarked', 'Submitted', 'Borrowed'
  thesis_id INTEGER,
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
  FOREIGN KEY (thesis_id) REFERENCES thesis (id) ON DELETE CASCADE
);

CREATE TABLE active_borrow (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  thesis_id INTEGER NOT NULL,
  
  time_left INTEGER DEFAULT 7200, -- 2 hours
  last_tick TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_paused INTEGER DEFAULT 0, 
  
  FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
  FOREIGN KEY (thesis_id) REFERENCES thesis (id) ON DELETE CASCADE,
  UNIQUE(user_id, thesis_id) -- user can only have one active session per thesis at a time
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


INSERT INTO user (first_name, last_name, email, password, student_no, course, role) VALUES 
('System', 'Admin', 'testing@gmail.com', 'scrypt:32768:8:1$CnOYZglEnYCUPpVx$3bf12468ee0826fbf6b59c8422670a3e2429b56ed9f6dc0f60ffd354fab2ac41bee12647d5d2fcb01524dd627c9a13e519a71f93379dca9490161e300547a1dc', '202600000', 'BS Computer Science', 'admin');

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
('Hard Copy'),
('Both'); 

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


INSERT INTO author (first_name, middle_name, last_name, student_no) VALUES 
('Emily', 'R.', 'Chen', '2023-0101'),
('Michael', 'T.', 'Rodriguez', '2022-0555'),
('Jessica', '', 'Kim', '2024-0888'),
('David', 'L.', 'Smith', '2021-0222'),
('Ashley', 'Marie', 'Garcia', '2025-0333');

-- 20 Fake Theses across different departments
INSERT INTO thesis (title, abstract, file_path, status, keywords, isbn, barcode, call_number, department_id, branch_id, format_id, uploader_id) VALUES 
-- Computer Science (8)
('Decentralized Ledger Technology in E-Voting', 'A framework for secure and verifiable digital elections using blockchain.', '/static/uploads/2026/dummy.pdf', 'approved', 'Blockchain, Voting, Security', '978-0-111-00001-0', 'BC1001', 'CS-2026-06', 8, 1, 1, 1),
('Machine Learning for Crop Disease Detection', 'Utilizing convolutional neural networks to identify rice leaf diseases.', '/static/uploads/2025/dummy.pdf', 'pending', 'Machine Learning, Agriculture, CNN', '978-0-111-00002-0', 'BC1002', 'CS-2025-07', 8, 2, 1, 1),
('Natural Language Processing for Indigenous Dialects', 'Creating a translation model for underrepresented Philippine languages.', '/static/uploads/2026/dummy.pdf', 'approved', 'NLP, Linguistics, Translation', '978-0-111-00003-0', 'BC1003', 'CS-2026-08', 8, 1, 1, 1),

-- Information Technology (4)
('IoT Smart Home Security Frameworks', 'Analyzing vulnerabilities in consumer-grade smart home devices.', '/static/uploads/2024/dummy.pdf', 'approved', 'IoT, Security, Smart Home', '978-0-111-00004-0', 'BC1004', 'IT-2024-01', 4, 3, 1, 1),
('Cloud-Native App Deployment Strategies', 'Comparing cost and performance of AWS vs Azure for local startups.', '/static/uploads/2025/dummy.pdf', 'rejected', 'Cloud Computing, Deployment, AWS', '978-0-111-00005-0', 'BC1005', 'IT-2025-02', 4, 2, 2, 1),
('Blockchain in Healthcare Data Management', 'Proposing a tamper-proof patient record system for rural clinics.', '/static/uploads/2026/dummy.pdf', 'pending', 'Blockchain, Healthcare, Database', '978-0-111-00006-0', 'BC1006', 'IT-2026-03', 4, 1, 1, 1),

-- Psychology (2)
('Impact of Remote Work on Cognitive Load', 'A quantitative study on burnout rates among work-from-home employees.', '/static/uploads/2025/dummy.pdf', 'approved', 'Cognitive Load, Remote Work, Burnout', '978-0-111-00007-0', 'BC1007', 'PSY-2025-01', 2, 1, 1, 1),
('Social Media and Adolescent Anxiety', 'Correlating screen time with social anxiety disorders in teens.', '/static/uploads/2024/dummy.pdf', 'approved', 'Social Media, Anxiety, Adolescents', '978-0-111-00008-0', 'BC1008', 'PSY-2024-02', 2, 2, 2, 1),

-- Business Administration (9)
('Corporate Sustainability Practices post-2020', 'How ESG metrics affect investor relations in Southeast Asia.', '/static/uploads/2026/dummy.pdf', 'approved', 'Sustainability, ESG, Corporate', '978-0-111-00009-0', 'BC1009', 'BA-2026-01', 9, 3, 1, 1),
('Microfinance Impact on Rural Enterprises', 'Evaluating the success rate of SME loans in the Calabarzon region.', '/static/uploads/2025/dummy.pdf', 'pending', 'Microfinance, SME, Economics', '978-0-111-00010-0', 'BC1010', 'BA-2025-02', 9, 1, 1, 1),
('Gig Economy Effects on Traditional HR', 'Adapting human resource policies for freelance and contractual workers.', '/static/uploads/2026/dummy.pdf', 'approved', 'HR, Gig Economy, Management', '978-0-111-00011-0', 'BC1011', 'BA-2026-03', 9, 2, 1, 1),

-- Hospitality Management (5)
('Contactless Service in Boutique Hotels', 'Guest satisfaction metrics regarding automated check-in kiosks.', '/static/uploads/2024/dummy.pdf', 'approved', 'Hospitality, Automation, Service', '978-0-111-00012-0', 'BC1012', 'HM-2024-01', 5, 1, 1, 1),
('Culinary Tourism in Calabarzon', 'Marketing local delicacies to boost regional tourism revenues.', '/static/uploads/2025/dummy.pdf', 'approved', 'Tourism, Culinary, Marketing', '978-0-111-00013-0', 'BC1013', 'HM-2025-02', 5, 2, 2, 1),

-- Education (6)
('Gamification in High School STEM', 'Using interactive digital platforms to improve math test scores.', '/static/uploads/2026/dummy.pdf', 'pending', 'Gamification, STEM, Pedagogy', '978-0-111-00014-0', 'BC1014', 'EDU-2026-06', 6, 3, 1, 1),
('Inclusive Practices for Neurodivergent Students', 'Adapting classroom environments for students with autism spectrum disorder.', '/static/uploads/2025/dummy.pdf', 'approved', 'Special Education, Neurodivergent', '978-0-111-00015-0', 'BC1015', 'EDU-2025-07', 6, 1, 1, 1),

-- Journalism (3)
('Fact-Checking Algorithms in Newsrooms', 'The integration of AI tools by journalists to verify sources.', '/static/uploads/2026/dummy.pdf', 'approved', 'Journalism, AI, Fact-Checking', '978-0-111-00016-0', 'BC1016', 'JOU-2026-01', 3, 2, 1, 1),
('Evolution of Citizen Journalism', 'How smartphones have shifted the paradigm of breaking news coverage.', '/static/uploads/2024/dummy.pdf', 'approved', 'Media, Breaking News, Citizen Journalism', '978-0-111-00017-0', 'BC1017', 'JOU-2024-02', 3, 1, 2, 1),

-- Entrepreneurship (7)
('Bootstrapping Tech Startups', 'Financial strategies for early-stage software companies in the Philippines.', '/static/uploads/2025/dummy.pdf', 'rejected', 'Startups, Finance, Bootstrapping', '978-0-111-00018-0', 'BC1018', 'ENT-2025-01', 7, 3, 1, 1),
('Social Enterprises and Profitability', 'Balancing social missions with financial sustainability.', '/static/uploads/2026/dummy.pdf', 'approved', 'Social Enterprise, Business Model', '978-0-111-00019-0', 'BC1019', 'ENT-2026-02', 7, 1, 1, 1),

-- Office Administration (1)
('Digital Archiving Protocols for Legal Firms', 'Transitioning from physical to encrypted cloud storage solutions.', '/static/uploads/2026/dummy.pdf', 'pending', 'Archiving, Cloud Storage, Admin', '978-0-111-00020-0', 'BC1020', 'OA-2026-06', 1, 2, 1, 1);
INSERT INTO thesis_author (thesis_id, author_id) VALUES 
(6, 6),
(7, 7),
(8, 8), (8, 2), -- Co-authored
(9, 9),
(10, 10),
(11, 1),
(12, 2),
(13, 3), (13, 4), -- Co-authored
(14, 5),
(15, 6),
(16, 7),
(17, 8),
(18, 9), (18, 10), -- Co-authored
(19, 1),
(20, 2),
(21, 3),
(22, 4),
(23, 5), (23, 6), -- Co-authored
(24, 7),
(25, 8);

INSERT INTO user_history (user_id, action, thesis_id, timestamp) VALUES 
(1, 'Bookmarked', 5, '2026-05-04 12:24:00'),
(1, 'Unbookmarked', 5, '2026-05-04 12:25:00'),
(1, 'Submitted', 1, '2026-04-10 00:24:00');
