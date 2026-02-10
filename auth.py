from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from conexion import get_connection

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo')
        contrasena = request.form.get('contraseña')
        if not correo or not contrasena:
            flash("Debes llenar todos los campos.", "error")
            return redirect(url_for('auth.login'))

        conexion = get_connection()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Usuarios WHERE correo = %s AND contrasena = %s", (correo, contrasena))
        usuario = cursor.fetchone()
        cursor.close()
        conexion.close()

        if usuario:
            session['id_usuario'] = usuario['id']
            session['usuario'] = usuario['correo']
            rol = usuario['rol'].strip().lower()
            session['rol'] = rol

            flash(f"Bienvenido al sistema, {usuario['nombre']}", "success")

            if rol == 'admin':
                return redirect(url_for('admin.panel_admin'))
            else:
                return redirect(url_for('auth.inicio_usuario'))
        else:
            flash("Credenciales incorrectas. Verifica tu correo o contraseña.", "error")
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth.route('/inicio_usuario')
def inicio_usuario():
    if 'usuario' not in session or session.get('rol') != 'usuario':
        flash("Acceso denegado. Inicia sesión.", "error")
        return redirect(url_for('auth.login'))

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            COUNT(*) AS total_especies,
            COUNT(CASE WHEN tipo = 1 THEN 1 END) AS flora,
            COUNT(CASE WHEN tipo = 2 THEN 1 END) AS fauna,
            COUNT(CASE WHEN id_estado_conservacion IN (3,4,5) THEN 1 END) AS vulnerables
        FROM especies
    """)
    stats = cursor.fetchone()
    cursor.execute("SELECT COUNT(DISTINCT id_especie) AS fotografiadas FROM fotografia")
    fotos = cursor.fetchone()
    cursor.close()
    conexion.close()

    imagenes_zonas = [
        {'nombre': 'Jalpan de Serra', 'ruta': 'imagenes_zonas/jalpan.jpg'},
        {'nombre': 'Landa de Matamoros', 'ruta': 'imagenes_zonas/landa.jpg'},
        {'nombre': 'Pinal de Amoles', 'ruta': 'imagenes_zonas/pinal.jpg'},
        {'nombre': 'San Joaquín', 'ruta': 'imagenes_zonas/sanjoaquin.jpg'},
        {'nombre': 'Peñamiller', 'ruta': 'imagenes_zonas/penamiller.jpg'},
        {'nombre': 'Cadereyta de Montes', 'ruta': 'imagenes_zonas/cadereyta.png'},
        {'nombre': 'Amealco de Bonfil', 'ruta': 'imagenes_zonas/amealco.jpg'}
    ]

    return render_template('inicio_usuario.html', stats=stats, fotos=fotos, zonas=imagenes_zonas)

@auth.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        ap_paterno = request.form.get('ap_paterno')
        ap_materno = request.form.get('ap_materno')
        correo = request.form.get('correo')
        contrasena = request.form.get('contraseña')

        errores = []
        if not nombre: errores.append("Falta el nombre.")
        if not ap_paterno: errores.append("Falta el apellido paterno.")
        if not correo: errores.append("Falta el correo.")
        if not contrasena or len(contrasena) < 8: errores.append("Contraseña inválida (mín. 8 caracteres).")

        if errores:
            flash("Error de validación: " + " ".join(errores), "error")
            return redirect(url_for('auth.registro'))

        conexion = get_connection()
        cursor = conexion.cursor()
        
        try:
            query = """
                INSERT INTO Usuarios (nombre, apellidoPaterno, apellidoMaternousuarios, correo, contrasena, rol) 
                VALUES (%s, %s, %s, %s, %s, 'usuario')
            """
            cursor.execute(query, (nombre, ap_paterno, ap_materno, correo, contrasena))
            conexion.commit()
            flash("Registro exitoso. ¡Bienvenido! Por favor inicia sesión.", "success")
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            conexion.rollback()
            flash(f"Error al registrar usuario: Posiblemente el correo ya existe.", "error")
            print("Error BD:", e)
            return redirect(url_for('auth.registro'))
            
        finally:
            cursor.close()
            conexion.close()

    return render_template('registro.html')

@auth.route('/actualizar_perfil', methods=['POST'])
def actualizar_perfil():
    if 'id_usuario' not in session:
        return redirect(url_for('auth.login'))
    
    nuevo_nombre = request.form.get('nombre')
    id_usuario = session['id_usuario']

    if not nuevo_nombre:
        flash("El nombre no puede estar vacío.", "error")
        return redirect(url_for('auth.inicio_usuario'))

    conexion = get_connection()
    cursor = conexion.cursor()
    try:
        cursor.execute("UPDATE Usuarios SET nombre = %s WHERE id = %s", (nuevo_nombre, id_usuario))
        conexion.commit()
        flash("Tu nombre ha sido actualizado.", "success")
    except Exception as e:
        conexion.rollback()
        flash("Error al actualizar perfil.", "error")
    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for('auth.inicio_usuario'))

@auth.route('/eliminar_cuenta', methods=['POST'])
def eliminar_cuenta():
    if 'id_usuario' not in session:
        return redirect(url_for('auth.login'))
    
    id_usuario = session['id_usuario']
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        cursor.execute("DELETE FROM Likes WHERE id_usuario = %s", (id_usuario,))
        cursor.execute("DELETE FROM Comentario WHERE ID_usuario = %s", (id_usuario,))
        cursor.execute("DELETE FROM Usuarios WHERE id = %s", (id_usuario,))
        conexion.commit()
        
        session.clear()
        flash("Lamentamos que te vayas. Tu cuenta ha sido eliminada.", "success")
        return redirect(url_for('auth.login'))
    except Exception as e:
        conexion.rollback()
        flash("Error crítico al eliminar la cuenta.", "error")
        return redirect(url_for('auth.inicio_usuario'))
    finally:
        cursor.close()
        conexion.close()

@auth.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión.", "success")
    return redirect(url_for('auth.login'))