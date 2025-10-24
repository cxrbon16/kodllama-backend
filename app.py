#============================================
# 5. app.py - Ana Flask Uygulaması
# ============================================
# Register blueprints (route'ları ekleyeceğiz)


from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from database import db
# ...existing code...
# Create Flask app
load_dotenv()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
CORS(app)
# ...existing code...

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    """
    Health check
    ---
    get:
      summary: Check API health
      responses:
        200:
          description: service is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                  message:
                    type: string
    """
    return jsonify({
        "status": "healthy",
        "message": "PlanLLaMA API is running",
        "database": "connected"
    }), 200


from routes import projects_bp, employees_bp, tasks_bp, jira_sync_bp

app.register_blueprint(projects_bp, url_prefix='/api/projects')
app.register_blueprint(employees_bp, url_prefix='/api/employees')
app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
app.register_blueprint(jira_sync_bp, url_prefix='/api/jira')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_DEBUG', 'True') == 'True'
    )