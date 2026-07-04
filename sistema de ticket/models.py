from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    contrasena = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), default='Cliente')  # Cliente, Soporte, Admin

    # Relaciones para conectar con los tickets
    tickets_creados = db.relationship('Ticket', backref='creador', foreign_keys='Ticket.id_creador')
    tickets_asignados = db.relationship('Ticket', backref='tecnico', foreign_keys='Ticket.id_asignado')

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    prioridad = db.Column(db.String(20), default='Media')  # Baja, Media, Alta, Critica
    estado = db.Column(db.String(20), default='Abierto')   # Abierto, En Progreso, Resuelto, Cerrado
    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Claves foráneas (Alineación corregida)
    id_creador = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_asignado = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)