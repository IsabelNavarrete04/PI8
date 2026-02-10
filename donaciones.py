from flask import Flask, render_template

app = Flask(__name__)

# Datos de donadores
donadores = [
    {"nombre": "Ana López", "lugar": "Querétaro"},
    {"nombre": "Carlos Rivera", "lugar": "Corregidora"},
    {"nombre": "Fernanda T.", "lugar": "El Marqués"}
]

@app.route('/')
def donaciones():
    return render_template("donaciones.html", donadores=donadores)

if __name__ == "__main__":
    app.run(debug=True)

