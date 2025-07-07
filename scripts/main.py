# Define path and content for main.py
script_path = "/mnt/data/dunkin_sales_dashboard/scripts/main.py"

script_content = '''import subprocess

def run_pipeline():
    print("📥 Downloading sales reports from Gmail...")
    subprocess.run(["python", "scripts/download_from_gmail.py"], check=True)

    print("🧹 Compiling and transforming Excel reports...")
    subprocess.run(["python", "scripts/compile_reports.py"], check=True)

    print("🗄️ Loading compiled data into SQLite database...")
    subprocess.run(["python", "scripts/load_to_sqlite.py"], check=True)

    print("✅ All steps completed successfully!")

if __name__ == "__main__":
    run_pipeline()
'''

# Write main.py to disk
with open(script_path, "w") as f:
    f.write(script_content)

script_path
