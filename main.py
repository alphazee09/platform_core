from app import app

# Import and register blueprints
from routes import main_bp
from auth import auth_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
