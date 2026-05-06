SET search_path TO public, provsql;
DO $$
DECLARE
    rec RECORD;
    step TEXT;  -- Track current step for debugging
BEGIN
    CREATE TABLE provenance_mapping (value TEXT, provenance UUID);
    
    FOR rec IN 
        SELECT schemaname, tablename 
        FROM pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema', 'provsql') AND tablename NOT IN ('provenance_mapping')
    LOOP
        BEGIN
            step := 'add_provenance';
            EXECUTE format('SELECT add_provenance(%L)', rec.tablename);
            
            step := 'add_tuple_id';
            EXECUTE format('ALTER TABLE %I ADD COLUMN tuple_id SERIAL', rec.tablename);
            
            step := 'cleanup_tmp';
            EXECUTE 'DROP TABLE IF EXISTS tmp_provsql';
            
            step := 'create_mapping_table';
            EXECUTE format('SELECT create_provenance_mapping(%L,%L,%L)', 
                          'tuple_ids_for_' || rec.tablename, 
                          rec.tablename, 
                          'tuple_id');
            
            step := 'insert_into_mapping';
            EXECUTE format('INSERT INTO provenance_mapping (value, provenance) SELECT concat(%L, value::TEXT), provenance FROM %I', 
                          rec.tablename || '-', 
                          'tuple_ids_for_' || rec.tablename);
            
            RAISE NOTICE 'Successfully processed %.%', rec.schemaname, rec.tablename;
            
        EXCEPTION
            WHEN OTHERS THEN
                RAISE WARNING 'Failed at step "%": %.% (%) (%) ', 
                    step, rec.schemaname, rec.tablename, SQLERRM, SQLSTATE;
        END;
    END LOOP;
    
    CREATE INDEX map_idx ON provenance_mapping (provenance);
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Critical error in main block: %', SQLERRM;
END $$;