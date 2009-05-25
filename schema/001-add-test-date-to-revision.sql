ALTER TABLE revisions
  ADD COLUMN test_date TIMESTAMP;

UPDATE revisions SET test_date = CURRENT_TIMESTAMP;
