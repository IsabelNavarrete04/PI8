from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app
from conexion import get_connection
from werkzeug.utils import secure_filename
import os
import re

perfil_bp = Blueprint('perfil', __name__)

@perfil_bp.route('/perfil')
def perfil():
    if 'id_usuario' not in session:
        flash("Debes iniciar sesión para ver tu perfil.", "error")
        return redirect(url_for('auth.login'))

    id_usuario = session['id_usuario']
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT nombre, apellidoPaterno, apellidoMaternousuarios, correo, profile_image
        FROM Usuarios
        WHERE id = %s
    """, (id_usuario,))

    usuario = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('perfil.html', usuario=usuario)


@perfil_bp.route('/actualizar-perfil', methods=['POST'])
def actualizar_perfil():
    if 'id_usuario' not in session:
        return redirect(url_for('auth.login'))

    id_usuario = session['id_usuario']

    # Recoger datos del formulario
    nombre = request.form.get('nombre', '').strip()
    apellido_paterno = request.form.get('apellido_paterno', '').strip()
    apellido_materno = request.form.get('apellido_materno', '').strip()
    correo = request.form.get('correo', '').strip()
    contrasena = request.form.get('contrasena', '').strip()
    
    # CUMPLE RUBRICA: Validación estricta lado servidor
    # (Necesaria al quitar 'required' del HTML)
    errores = []
    
    # Regex para validaciones
    texto_regex = re.compile(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$')
    email_regex = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    
    # Validar nombre
    if not nombre:
        errores.append("El nombre es obligatorio.")
    elif not texto_regex.match(nombre):
        errores.append("El nombre solo debe contener letras.")
    elif len(nombre) > 20:
        errores.append("El nombre no puede exceder 20 caracteres.")
    
    # Validar apellido paterno
    if not apellido_paterno:
        errores.append("El apellido paterno es obligatorio.")
    elif not texto_regex.match(apellido_paterno):
        errores.append("El apellido paterno solo debe contener letras.")
    elif len(apellido_paterno) > 20:
        errores.append("El apellido paterno no puede exceder 20 caracteres.")
    
    # Validar apellido materno (opcional, pero si existe debe ser válido)
    if apellido_materno:
        if not texto_regex.match(apellido_materno):
            errores.append("El apellido materno solo debe contener letras.")
        elif len(apellido_materno) > 20:
            errores.append("El apellido materno no puede exceder 20 caracteres.")
    
    # Validar correo
    if not correo:
        errores.append("El correo es obligatorio.")
    elif not email_regex.match(correo):
        errores.append("El formato del correo no es válido.")
    elif len(correo) > 40:
        errores.append("El correo no puede exceder 40 caracteres.")
    
    # Validación de contraseña SOLO si se intenta cambiar
    actualizar_pass = False
    if contrasena:
        if len(contrasena) < 8:
            errores.append("La contraseña nueva debe tener al menos 8 caracteres.")
        else:
            actualizar_pass = True

    if errores:
        flash("validation_error|" + "|".join(errores), "error")
        return redirect(url_for('perfil.perfil'))

    # --- MANEJO DE IMAGEN ---
    upload_folder = os.path.join(current_app.root_path, "static/imgperfil")
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    foto = request.files.get('foto_perfil')
    nombre_foto = None

    if foto and foto.filename != "":
        # Validar extensión de imagen
        extensiones_permitidas = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        extension = foto.filename.rsplit('.', 1)[1].lower() if '.' in foto.filename else ''
        
        if extension not in extensiones_permitidas:
            flash("El archivo debe ser una imagen válida (png, jpg, jpeg, gif, webp).", "error")
            return redirect(url_for('perfil.perfil'))
        
        nombre_foto = secure_filename(f"user_{id_usuario}_{foto.filename}")
        try:
            foto.save(os.path.join(upload_folder, nombre_foto))
        except Exception as e:
            flash("Error al subir la imagen.", "error")
            return redirect(url_for('perfil.perfil'))

    # --- ACTUALIZACIÓN EN BD ---
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Query base: campos obligatorios
        sql = """
            UPDATE Usuarios 
            SET nombre=%s, apellidoPaterno=%s, apellidoMaternousuarios=%s, correo=%s
        """
        valores = [nombre, apellido_paterno, apellido_materno, correo]

        # Agregar contraseña si aplica
        if actualizar_pass:
            sql += ", contrasena=%s"
            valores.append(contrasena)

        # Agregar foto si aplica
        if nombre_foto:
            sql += ", profile_image=%s"
            valores.append(nombre_foto)

        # Cerrar el WHERE
        sql += " WHERE id=%s"
        valores.append(id_usuario)

        cursor.execute(sql, tuple(valores))
        conn.commit()
        
        # Actualizar sesión para reflejar cambios inmediatos
        session['usuario'] = correo
        
        flash("Tu perfil ha sido actualizado exitosamente.", "success")
        
    except Exception as e:
        conn.rollback()
        print("Error Update:", e)
        flash("Hubo un error interno al actualizar los datos.", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('perfil.perfil'))