from .main_routes import main_bp
from .admin_routes import admin_bp
from .student_routes import student_bp

def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)