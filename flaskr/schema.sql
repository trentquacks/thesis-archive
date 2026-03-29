-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS author;
DROP TABLE IF EXISTS department;
DROP TABLE IF EXISTS branch;
DROP TABLE IF EXISTS format;
DROP TABLE IF EXISTS thesis;
DROP TABLE IF EXISTS thesis_author;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE author (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  student_no TEXT NOT NULL
);

CREATE TABLE department (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL -- cs department, it department
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

  -- specifics
  isbn TEXT,
  barcode TEXT NOT NULL,
  call_number TEXT NOT NULL, -- used for finding in shelves easily

  -- foreigns
  department_id INTEGER NOT NULL, 
  branch_id INTEGER NOT NULL,
  format_id INTEGER NOT NULL,
  FOREIGN KEY (department_id) REFERENCES department (id),
  FOREIGN KEY (branch_id) REFERENCES branch (id),
  FOREIGN KEY (format_id) REFERENCES format (id)
);

CREATE TABLE thesis_author (
  thesis_id INTEGER NOT NULL,
  author_id INTEGER NOT NULL,
  PRIMARY KEY (thesis_id, author_id), -- prevents same pair
  FOREIGN KEY (thesis_id) REFERENCES thesis (id),
  FOREIGN KEY (author_id) REFERENCES author (id)
);

-- Information required according to SRS
-- searchable by keyword, title, author, date year
-- filterable by title, author, year and category
-- thesis ISBD and MARC view format
-- history of submissions, user actions, log in activity, modification of theses and approval of submissions
-- total thesis records
--
-- bookmark table
-- preview: digital preview, digital scan, abstract

-- discontinued??
-- availability.. :C
