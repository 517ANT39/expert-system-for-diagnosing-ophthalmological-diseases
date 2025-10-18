import os
import subprocess
import sys

def run_migrations():
    try:
        # Запускаем Alembic напрямую
        result = subprocess.run(['alembic', 'upgrade', 'head'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("Migrations completed successfully")
        else:
            print(f"Migration error: {result.stderr}")
            # Не падаем, продолжаем работу
    except Exception as e:
        print(f"Migration skipped: {e}")

if __name__ == "__main__":
    run_migrations()