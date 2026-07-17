from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()

# TABLA 1: Usuarios del sistema
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    contrasena = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), default='Cliente')  # Puede ser: Cliente, Soporte o Admin

    # Relaciones: Permiten acceder a los datos vinculados sin hacer consultas manuales
    tickets_creados = db.relationship('Ticket', backref='creador', foreign_keys='Ticket.id_creador')
    tickets_asignados = db.relationship('Ticket', backref='tecnico', foreign_keys='Ticket.id_asignado')


# TABLA 2: Registro de Tickets
class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    prioridad = db.Column(db.String(20), default='Media')  # Baja, Media, Alta, Critica
    estado = db.Column(db.String(20), default='Abierto')   # Abierto, En Progreso, Resuelto, Cerrado
    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Claves foráneas: Conectan el ticket con la ID de un usuario real
    id_creador = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_asignado = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    # Relación: Trae todos los comentarios de este ticket ordenados por fecha
    comentarios = db.relationship('Comentario', backref='ticket', lazy=True, order_by="Comentario.fecha_creacion")


# NUEVA TABLA 3: Mensajes y Respuestas dentro de los tickets
class Comentario(db.Model):
    __tablename__ = 'comentarios'
    
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Vinculación: A qué ticket pertenece el comentario y quién lo escribió
    id_ticket = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Relación: Permite saber los datos del autor del comentario usando "comentario.autor"
    autor = db.relationship('Usuario', backref='comentarios_creados', lazy=True)