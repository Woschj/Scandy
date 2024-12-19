from run import create_app

application = create_app()
app = application  # Für Gunicorn

if __name__ == '__main__':
    application.run()
