from flask import Flask
from app.models.database import Database
from app import create_app
import os

app = create_app()

with app.app_context():
    Database.init_db()
    print("Datenbank erfolgreich initialisiert!") 