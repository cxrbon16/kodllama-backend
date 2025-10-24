from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def init_db(app):
    """Database'i başlat"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("✅ Database tabloları oluşturuldu")
