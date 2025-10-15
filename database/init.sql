-- Создаем ENUM типы если они не существуют
DO $$ BEGIN
    CREATE TYPE sex_enum AS ENUM ('M', 'F');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE status_enum AS ENUM ('draft', 'active', 'completed', 'canceled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;