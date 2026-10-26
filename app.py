from flask import Flask, render_template_string
import sympy as sp
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, base64

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Calculadora Universal de Oficio</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{background:#111;color:white;font-family:Arial;display:flex;justify-content:center;padding:20px}
.card{background:#1e1e1e;padding:20px;border-radius:20px;width:100%;max-width:500px;box-shadow:0 0 20px #000}
input{width:100%;padding:15px;border-radius:12px;border:none;font-size:18px;margin-bottom:10px}
button{width:100%;padding:14px;border-radius:12px;border:none;font-size:18px;font-weight:bold;cursor:pointer;margin-bottom:10px}
.calc{background:#00ff88;color:#000}
.hablar{background:#fff;color:#000}
.result{background:#000;padding:15px;border-radius:12px;margin-top:10px;min-height:80px;white-space:pre-wrap}
.hist{color:#00ff88;font-size:13px;margin-top:10px}
canvas{background:white;border-radius:12px;margin-top:15px}
</style>
</head>
<body>
<div class="card">
<h2>🛠️ Calculadora Universal</h2>
<input id="expr" placeholder="Ej: x^2, 2+2, integral(x^2), derivada(x^3)">
<button class="calc" onclick="calcular()">Calcular</button>
<button class="hablar" onclick="hablar()">🎤 Hablar</button>
<div id="res" class="result">Escribe algo y dale Calcular.
Guardado en memoria local.
Ejemplos:
→ x^2
→ 5*8+20
→ integral(x^2)
→ derivada(sin(x))
→ techo es 17x6</div>
<canvas id="graf" width="400" height="300" style="display:none"></canvas>
<div id="historial" class="hist"></div>
</div>

<script>
let historial = JSON.parse(localStorage.getItem('hist')||'[]');
let chart;
function mostrarHist(){
 document.getElementById('historial').innerHTML = historial.map(h=>'→ '+h).join('<br>');
}
mostrarHist();

async function calcular(){
 let e = document.getElementById('expr').value;
 if(!e) return;
 document.getElementById('res').innerText='Calculando...';
 let r = await fetch('/api/calc?expr='+encodeURIComponent(e));
 let data = await r.json();
 document.getElementById('res').innerText = data.texto;
 
 historial.unshift(e + ' = ' + data.texto.split('\\n')[0]);
 historial = historial.slice(0,10);
 localStorage.setItem('hist', JSON.stringify(historial));
 mostrarHist();

 if(data.grafica){
  let ctx = document.getElementById('graf').getContext('2d');
  document.getElementById('graf').style.display='block';
  if(chart) chart.destroy();
  chart = new Chart(ctx, {
   type:'line',
   data:{labels:data.grafica.x, datasets:[{data:data.grafica.y, borderColor:'#00ff88', tension:0.1, pointRadius:0}]},
   options:{plugins:{legend:{display:false}}, scales:{x:{display:false}}}
  });
 } else {
  document.getElementById('graf').style.display='none';
 }
}

function hablar(){
 let rec = new (window.webkitSpeechRecognition||window.SpeechRecognition)();
 rec.lang='es-MX'; rec.start();
 rec.onresult=(e)=>{document.getElementById('expr').value=e.results[0][0].transcript; calcular();}
}
</script>
</body>
</html>
"""

x = sp.Symbol('x')

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/calc')
def calc_api():
    from flask import request
    expr_raw = request.args.get('expr','')
    e = expr_raw.lower().replace('^','**').replace('techo es','').strip()
    try:
        texto = ""
        graf_x = None
        graf_y = None

        if 'integral' in e:
            inner = e.replace('integral','').replace('(','').replace(')','').strip()
            f = sp.sympify(inner)
            res = sp.integrate(f, x)
            texto = f"∫ {inner} dx = {res} + C\n\nEvaluado: {res}"
            f_lamb = sp.lambdify(x, f, 'numpy')
        elif 'derivada' in e or 'derivar' in e:
            inner = e.replace('derivada','').replace('derivar','').replace('(','').replace(')','').strip()
            f = sp.sympify(inner)
            res = sp.diff(f, x)
            texto = f"d/dx({inner}) = {res}"
            f_lamb = sp.lambdify(x, f, 'numpy')
        else:
            f = sp.sympify(e)
            if x in f.free_symbols:
                res = f
                texto = f"f(x) = {f}\nTipo: función graficable"
                f_lamb = sp.lambdify(x, f, 'numpy')
            else:
                res = float(f.evalf())
                if res == int(res): res = int(res)
                texto = f"Resultado: {res}"
                f_lamb = None

        if f_lamb is not None:
            try:
                xs = np.linspace(-10,10,200)
                ys = f_lamb(xs)
                ys = np.where(np.abs(ys)>1000, np.nan, ys)
                graf_x = xs.tolist()
                graf_y = ys.tolist()
            except:
                graf_x = None

        return {"texto": texto, "grafica": {"x": graf_x, "y": graf_y} if graf_x else None}
    except Exception as ex:
        return {"texto": f"Error: {ex}\nPrueba con: x^2 o 5*8", "grafica": None}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
