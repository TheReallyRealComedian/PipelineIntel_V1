-- UsecaseExplorer/db/init.sql
-- This script runs automatically when the PostgreSQL container initializes its data volume.
-- It should primarily ensure the database exists and is clean for the application.

-- Drop tables only if they exist, to avoid errors on a truly fresh initialization
-- This is a safety measure to ensure clean state from a previous partial run or migration attempt.
-- The order is important due to foreign key constraints.
DROP TABLE IF EXISTS process_step_process_step_relevance CASCADE;
DROP TABLE IF EXISTS usecase_usecase_relevance CASCADE;
DROP TABLE IF EXISTS usecase_step_relevance CASCADE;
DROP TABLE IF EXISTS usecase_area_relevance CASCADE;
DROP TABLE IF EXISTS use_cases CASCADE;
DROP TABLE IF EXISTS process_steps CASCADE;
DROP TABLE IF EXISTS areas CASCADE;
DROP TABLE IF EXISTS llm_settings CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS flask_sessions CASCADE;

-- IMPORTANT: REMOVE ALL 'CREATE TABLE' STATEMENTS FROM HERE.
-- These will now be handled by SQLAlchemy's Base.metadata.create_all(db.engine) in backend/db.py
-- This ensures that your Python models are the single source of truth for the schema.

-- Add initial user if not exists (for development)
-- Note: Passwords should ideally be handled securely and not hardcoded in production.
-- This is a placeholder for development convenience.
DO 
 BEGIN
IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin') THEN
-- This INSERT will only happen if the 'users' table exists.
-- If Base.metadata.create_all() hasn't run yet, this will effectively do nothing
-- or error if the table structure doesn't match, which is fine as the app will create it.
-- For a truly fresh DB, the app will create the table, then on a subsequent startup,
-- this check might run. A more robust solution for initial data seeding is via application logic.
-- However, for simplicity in this context, we keep it, understanding its limitations.
-- A common pattern is to let the application handle seeding after migrations/table creation.
-- INSERT INTO users (username, password) VALUES ('admin', '
𝑝
𝑏
𝑘
𝑑
𝑓
2
−
𝑠
ℎ
𝑎
256
pbkdf2−sha256
29000
8
𝑎
927
𝑎
445
𝑒
𝑒
1023
𝑑
8
𝑐
11
𝑒
03
𝑎
95
𝑑
43
𝑎
6
𝑑
2
𝑓
342
𝑓
0
𝑎
8274618
𝑒
7
𝑒
1451
𝑓
2249
𝑐
118
𝑏
8a927a445ee1023d8c11e03a95d43a6d2f342f0a8274618e7e1451f2249c118b
c97ee2e7428f57277862086e330554289895318d18d4512e2c2f70624a080826'); -- password is 'admin'
-- The above INSERT is commented out as the 'users' table might not exist when this script runs.
-- Initial user creation should be handled by the application after tables are created by SQLAlchemy.
END IF;
END 
;

-- Indexes might be created here, but it's generally better to define them in SQLAlchemy models
-- or use Alembic migrations for schema management, so they are in sync with the application's view of the DB.
-- If kept here, ensure they match the SQLAlchemy model definitions.
-- CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
-- CREATE INDEX IF NOT EXISTS idx_areas_name ON areas (name);
-- CREATE INDEX IF NOT EXISTS idx_process_steps_area_id ON process_steps (area_id);
-- CREATE INDEX IF NOT EXISTS idx_process_steps_bi_id ON process_steps (bi_id);
-- CREATE INDEX IF NOT EXISTS idx_use_cases_process_step_id ON use_cases (process_step_id);
-- CREATE INDEX IF NOT EXISTS idx_use_cases_bi_id ON use_cases (bi_id);
-- CREATE INDEX IF NOT EXISTS idx_uc_area_rev_source_uc_id ON usecase_area_relevance (source_usecase_id);
-- CREATE INDEX IF NOT EXISTS idx_uc_area_rev_target_area_id ON usecase_area_relevance (target_area_id);
-- CREATE INDEX IF NOT EXISTS idx_uc_step_rev_source_uc_id ON usecase_step_relevance (source_usecase_id);
-- CREATE INDEX IF NOT EXISTS idx_uc_step_rev_target_step_id ON usecase_step_relevance (target_process_step_id);
-- CREATE INDEX IF NOT EXISTS idx_uc_uc_rev_source_uc_id ON usecase_usecase_relevance (source_usecase_id);
-- CREATE INDEX IF NOT EXISTS idx_uc_uc_rev_target_uc_id ON usecase_usecase_relevance (target_usecase_id);
-- CREATE INDEX IF NOT EXISTS idx_ps_ps_rev_source_ps_id ON process_step_process_step_relevance (source_process_step_id);
-- CREATE INDEX IF NOT EXISTS idx_ps_ps_rev_target_ps_id ON process_step_process_step_relevance (target_process_step_id);
-- CREATE INDEX IF NOT EXISTS idx_llm_settings_user_id ON llm_settings (user_id);

-- The index creation statements are commented out above as they should ideally be managed by SQLAlchemy/Alembic.
-- If you choose to manage indexes via this script, uncomment them, but be aware that
-- they might fail if the tables don't exist when this script runs (before SQLAlchemy creates them).

/*
-- Optional: Trigger for automatically updating updated_at on row modification
-- This is also better handled by SQLAlchemy's event system or default values in models.
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS 

BEGIN
NEW.updated_at = CURRENT_TIMESTAMP;
RETURN NEW;
END;

 LANGUAGE plpgsql;

-- Example for one table (if it were created here):
-- CREATE TRIGGER set_process_steps_updated_at_timestamp
-- BEFORE UPDATE ON process_steps
-- FOR EACH ROW
-- EXECUTE FUNCTION trigger_set_timestamp();
-- Similar triggers can be created for other tables if desired.
*/