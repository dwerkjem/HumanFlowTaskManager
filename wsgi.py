from modules.main import server as application

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=8000, debug=True)
    