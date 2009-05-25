CREATE TABLE assertions (
	id INTEGER NOT NULL, 
	text TEXT, 
	test_id INTEGER, 
	PRIMARY KEY (id), 
	 FOREIGN KEY(test_id) REFERENCES tests (id), 
	 UNIQUE (text, test_id)
);
CREATE TABLE brokentests (
	id INTEGER NOT NULL, 
	testfile_id INTEGER, 
	revision_id INTEGER, 
	PRIMARY KEY (id), 
	 FOREIGN KEY(testfile_id) REFERENCES testfiles (id), 
	 FOREIGN KEY(revision_id) REFERENCES revisions (id), 
	 UNIQUE (testfile_id, revision_id)
);
CREATE TABLE results (
	id INTEGER NOT NULL, 
	"fail" BOOLEAN, 
	assertion_id INTEGER, 
	revision_id INTEGER, 
	PRIMARY KEY (id), 
	 FOREIGN KEY(assertion_id) REFERENCES assertions (id), 
	 FOREIGN KEY(revision_id) REFERENCES revisions (id)
);
CREATE TABLE revisions (
	id INTEGER NOT NULL, 
	svn_id INTEGER, 
	git_id VARCHAR(40), 
	message TEXT, 
	author VARCHAR(100), 
	date TIMESTAMP, 
	PRIMARY KEY (id), 
	 UNIQUE (git_id)
);
CREATE TABLE testfiles (
	id INTEGER NOT NULL, 
	name VARCHAR(100), 
	PRIMARY KEY (id), 
	 UNIQUE (name)
);
CREATE TABLE tests (
	id INTEGER NOT NULL, 
	name VARCHAR(50), 
	testfile_id INTEGER, 
	PRIMARY KEY (id), 
	 FOREIGN KEY(testfile_id) REFERENCES testfiles (id), 
	 UNIQUE (name, testfile_id)
);
