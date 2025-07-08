import subprocess

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



