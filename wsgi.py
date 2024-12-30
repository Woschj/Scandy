from app import create_app
import os

print(f"Current working directory: {os.getcwd()}")
print("Initializing Flask app...")

app = create_app()

if __name__ == '__main__':
    print("Starting Flask development server...")
    app.run()
