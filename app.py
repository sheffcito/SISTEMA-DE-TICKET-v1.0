import os
from flask import Flask, render_template, redirect, url_for, request, flash
from models import db, Usuario, Ticket, Comentario
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Configuración para leer los HTML sueltos en la carpeta "SISTEMA DE TICKET"
ruta_actual = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=ruta_actual)
app.config['SECRET_KEY'] = 'mi_clave_secreta_v2'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.db' # Base de datos SQLite local
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar Base de Datos y Gestor de Sesiones
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# ==========================================
# 🔐 RUTAS DE AUTENTICACIÓN (LOGIN Y REGISTRO)
# ==========================================

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        # Recibe los datos del formulario de registro
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        contrasena = request.form.get('contrasena')
        rol = request.form.get('rol', 'Cliente')

        if Usuario.query.filter_by(email=email).first():
            flash('El correo ya está registrado.', 'danger')
            return redirect(url_for('registro'))

        # Encripta la contraseña antes de guardarla por seguridad
        password_encriptada = generate_password_hash(contrasena, method='scrypt')
        nuevo_usuario = Usuario(nombre=nombre, email=email, contrasena=password_encriptada, rol=rol)
        
        db.session.add(nuevo_usuario)
        db.session.commit() # Guarda el usuario en la BD
        flash('Registro exitoso. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        contrasena = request.form.get('contrasena')
        usuario = Usuario.query.filter_by(email=email).first()
        
        # Compara la contraseña ingresada con el hash guardado en la BD
        if usuario and check_password_hash(usuario.contrasena, contrasena):
            login_user(usuario)
            return redirect(url_for('dashboard'))
        
        flash('Credenciales incorrectas.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user() # Cierra la sesión activa del usuario
    return redirect(url_for('login'))


# ==========================================
# 🎫 RUTAS DE GESTIÓN DE TICKETS
# ==========================================

@app.route('/')
@login_required
def dashboard():
    # FILTRO: Soporte ve todo; los clientes solo ven lo que ellos crearon
    if current_user.rol in ['Soporte', 'Admin']:
        mis_tickets = Ticket.query.all()
    else:
        mis_tickets = Ticket.query.filter_by(id_creador=current_user.id).all()
    return render_template('dashboard.html', tickets=mis_tickets)

@app.route('/ticket/nuevo', methods=['GET', 'POST'])
@login_required
def crear_ticket():
    if request.method == 'POST':
        # Inserta un nuevo ticket en la base de datos vinculado al usuario actual
        nuevo_ticket = Ticket(
            titulo=request.form.get('titulo'),
            descripcion=request.form.get('descripcion'),
            prioridad=request.form.get('prioridad'),
            id_creador=current_user.id
        )
        db.session.add(nuevo_ticket)
        db.session.commit()
        flash('Ticket creado con éxito.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('crear_ticket.html')

@app.route('/ticket/<int:id_ticket>')
@login_required
def ver_ticket(id_ticket):
    # Busca el ticket por su ID único. Si no existe, muestra error 404.
    ticket = Ticket.query.get_or_404(id_ticket)
    
    # SEGURIDAD: Evita que un cliente husmee tickets de otros usuarios
    if current_user.rol == 'Cliente' and ticket.id_creador != current_user.id:
        flash('No tienes permiso para ver este ticket.', 'danger')
        return redirect(url_for('dashboard'))
        
    return render_template('ver_ticket.html', ticket=ticket)

@app.route('/ticket/<int:id_ticket>/comentar', methods=['POST'])
@login_required
def agregar_comentario(id_ticket):
    ticket = Ticket.query.get_or_404(id_ticket)
    texto = request.form.get('texto')
    
    if texto:
        # Crea un nuevo registro en la tabla "comentarios" ligado a este ticket
        nuevo_comentario = Comentario(texto=texto, id_ticket=ticket.id, id_usuario=current_user.id)
        db.session.add(nuevo_comentario)
        db.session.commit()
        flash('Respuesta enviada.', 'success')
        
    return redirect(url_for('ver_ticket', id_ticket=ticket.id))

@app.route('/ticket/<int:id_ticket>/gestionar', methods=['POST'])
@login_required
def gestionar_ticket(id_ticket):
    ticket = Ticket.query.get_or_404(id_ticket)
    
    # SEGURIDAD: Solo soporte y admin pueden usar esta ruta
    if current_user.rol not in ['Soporte', 'Admin']:
        flash('Acción denegada.', 'danger')
        return redirect(url_for('dashboard'))
        
    accion = request.form.get('accion')
    nuevo_estado = request.form.get('estado')
    
    # CAMBIO EN LA BD: Asigna el ID del técnico actual al ticket y cambia su estado
    if accion == 'asignar_me':
        ticket.id_asignado = current_user.id
        ticket.estado = 'En Progreso'
        flash('Te has asignado el ticket.', 'success')
    # CAMBIO EN LA BD: Modifica directamente el string del estado del ticket
    elif nuevo_estado:
        ticket.estado = nuevo_estado
        flash('Estado del ticket actualizado.', 'success')
        
    db.session.commit() # Aplica las modificaciones en el archivo SQLite
    return redirect(url_for('ver_ticket', id_ticket=ticket.id))


# Creación automática del archivo tickets.db con sus tablas limpias al arrancar
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)