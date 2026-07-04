import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from models import db, Usuario, Ticket
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# CONFIGURACIÓN DE CARPETA RAÍZ
# Esto obliga a Flask a buscar los HTML en tu carpeta "SISTEMA DE TICKET" sin usar subcarpetas
ruta_actual = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=ruta_actual)
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la base de datos con la app
db.init_app(app)

# Configurar el manejo de sesiones de usuario
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --- RUTAS DE AUTENTICACIÓN ---

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        contrasena = request.form.get('contrasena')
        rol = request.form.get('rol', 'Cliente') # Por defecto es Cliente

        # Verificar si el correo ya existe
        user_existente = Usuario.query.filter_by(email=email).first()
        if user_existente:
            flash('El correo ya está registrado.', 'danger')
            return redirect(url_for('registro'))

        # Encriptar contraseña y guardar usuario
        password_encriptada = generate_password_hash(contrasena, method='scrypt')
        nuevo_usuario = Usuario(nombre=nombre, email=email, contrasena=password_encriptada, rol=rol)
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('Usuario registrado con éxito. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        contrasena = request.form.get('contrasena')
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        # Validar usuario y verificar contraseña encriptada
        if usuario and check_password_hash(usuario.contrasena, contrasena):
            login_user(usuario)
            flash('¡Bienvenido de vuelta!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Correo o contraseña incorrectos.', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('login'))


# --- RUTAS DE LOS TICKETS ---

@app.route('/')
@login_required # Ahora que tenemos login, podemos proteger el dashboard de forma segura
def dashboard():
    # Si es Soporte o Admin ve todo, si es Cliente solo ve lo que él creó
    if current_user.rol in ['Soporte', 'Admin']:
        mis_tickets = Ticket.query.all()
    else:
        mis_tickets = Ticket.query.filter_by(id_creador=current_user.id).all()
    return render_template('dashboard.html', tickets=mis_tickets)

@app.route('/ticket/nuevo', methods=['GET', 'POST'])
@login_required
def crear_ticket():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        prioridad = request.form.get('prioridad')
        
        nuevo_ticket = Ticket(
            titulo=titulo,
            descripcion=descripcion,
            prioridad=prioridad,
            id_creador=current_user.id
        )
        db.session.add(nuevo_ticket)
        db.session.commit()
        flash('Ticket creado con éxito', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('crear_ticket.html')

# Crear las tablas automáticamente si no existen al arrancar
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)