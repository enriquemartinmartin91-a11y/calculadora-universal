from flask import Flask, request, render_template_string
import sympy as sp
import numpy as np
import re

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Calculadora Universal con IA</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>body{background:#0f0f0f;color:#fff;font-family:Arial;display:flex;justify-content:center;padding:20px}
.card{background:#1e1e1e;padding:20px;border-radius:20px;width:100%;max-width:550px}
input{width:100%;padding:16px;border-radius:12px;border:none;font-size:17px;margin-bottom:8px;box-sizing:border-box}
button{width:100%;padding:14px;border-radius:12px;border:none;font-size:17px;font-weight:bold;cursor:pointer;margin:5px 0}
.calc{background:#00ff88;color:#000}.hablar{background:#fff;color:#000}.mini{background:#333;color:#00ff88;width:32%;font-size:13px}
.result{background:#000;padding:15px;border-radius:12px;margin-top:10px;min-height:90px;white-space:pre-wrap;line-height:1.4}
.hist{color:#00ff88;font-size:12px;margin-top:10px}canvas{background:white;border-radius:12px;margin-top:12px}</style>
</head><body><div class="card">
<h2>🛠️ Calculadora Universal IA</h2>
<input id="expr" placeholder="Escribe lo que quieras: x^2, techo, sal para 100 litros, si tengo 100 y vale 55...">
<div style="display:flex;justify-content:space-between"><button class="mini" onclick="setText('techo 17x6')">🧱 Techo</button><button class="mini" onclick="setText('pecera 80x40x50')">🐠 Pecera</button><button class="mini" onclick="setText('sal para 100 litros')">🧂 Sal</button></div>
<button class="calc" onclick="calcular()">Calcular con IA</button><button class="hablar" onclick="hablar()">🎤 Hablar</button>
<div id="res" class="result">Modo IA activado 🤖
Prueba:
→ si el kilo de jitomate vale 55 y tengo 100 cuanto me sobra?
→ sal para 100 litros
→ pecera 80x40x50 cuanta sal necesita?
→ techo 17x6
→ x^2
→ integral(x^2)</div><canvas id="graf" width="400" height="280" style="display:none"></canvas><div id="historial" class="hist"></div>
</div>
<script>
let historial = JSON.parse(localStorage.getItem('hist')||'[]'); let chart;
function setText(t){document.getElementById('expr').value=t; calcular();}
function mostrarHist(){document.getElementById('historial').innerHTML=historial.map(h=>'→ '+h).join('<br>');} mostrarHist();
async function calcular(){
 let e=document.getElementById('expr').value; if(!e) return;
 document.getElementById('res').innerText='Pensando con IA...';
 let r=await fetch('/api/calc?expr='+encodeURIComponent(e)); let data=await r.json();
 document.getElementById('res').innerText=data.texto;
 historial.unshift(e+' = '+data.texto.split('\\n')[0]); historial=historial.slice(0,8);
 localStorage.setItem('hist', JSON.stringify(historial)); mostrarHist();
 if(data.grafica){let ctx=document.getElementById('graf').getContext('2d'); document.getElementById('graf').style.display='block'; if(chart) chart.destroy();
 chart=new Chart(ctx,{type:'line',data:{labels:data.grafica.x,datasets:[{data:data.grafica.y,borderColor:'#00ff88',tension:0.1,pointRadius:0}]},options:{plugins:{legend:{display:false}},scales:{x:{display:false}}}});
 } else {document.getElementById('graf').style.display='none';}
}
function hablar(){let rec=new (window.webkitSpeechRecognition||window.SpeechRecognition)(); rec.lang='es-MX'; rec.start(); rec.onresult=(e)=>{document.getElementById('expr').value=e.results[0][0].transcript; calcular();}}
</script></body></html>
"""

x=sp.Symbol('x')

def modo_ia_flexible(texto_original):
    t = texto_original.lower()
    numeros = list(map(float, re.findall(r'\d+\.?\d*', t.replace(',', '.'))))
    
    # 1. PECERA / SAL
    if any(p in t for p in ['pecera','sal','acuario','marino','litro']):
        litros = 0
        # busca patron 80x40x50 o 80*40*50
        m = re.search(r'(\d+)\s*[x\*]\s*(\d+)\s*[x\*]\s*(\d+)', t)
        if m:
            a,b,c = map(float, m.groups())
            # asume cm -> litros = a*b*c/1000
            litros = a*b*c/1000
            detalle_dim = f"Medidas {a}x{b}x{c} cm"
        elif numeros:
            # si dice "100 litros" usa ese numero
            litros = numeros[0]
            detalle_dim = f"{litros} litros"
            # si hay 3 numeros, el primero es litros, ignora resto
            if len(numeros) >=3 and not m:
                # si escribió 80 40 50 sin x, lo interpretamos como dimensiones
                if all(n < 500 for n in numeros[:3]):
                    litros = numeros[0]*numeros[1]*numeros[2]/1000
                    detalle_dim = f"Medidas {numeros[0]}x{numeros[1]}x{numeros[2]} cm"
        
        if litros <=0 and numeros: litros = numeros[0]
        if litros <=0: litros = 100

        kg_sal = litros * 0.035  # 35g por litro estandar marino
        hierro = litros * 0.2  # 0.2 ml por litro aprox semanal
        acond = litros * 0.1

        return f"""🐠 CÁLCULO PECERA MARINA (IA)
{detalle_dim} → {litros:.1f} Litros totales

🧂 Sal marina: {kg_sal:.2f} kg ({kg_sal*1000:.0f} gramos)
   Fórmula: 35g x litro

💧 Acondicionador: {acond:.1f} ml
🧪 Hierro (plantado/marino): {hierro:.1f} ml/semana
♻️ Cambio de agua 20%: {litros*0.2:.1f} litros

Tu amigo solo pone litros o medidas y yo calculo todo.""", litros

    # 2. TECHO
    if 'techo' in t:
        if numeros and len(numeros)>=2:
            largo, ancho = numeros[0], numeros[1]
        else:
            largo, ancho = 17, 6 # tu ejemplo original
        m2 = largo*ancho
        laminas = m2 / 2.5  # ejemplo lamina 2.5m2
        return f"""🧱 CÁLCULO TECHO (IA)
Techo {largo}x{ancho} = {m2} m2

📐 Área total: {m2} m2
📦 Láminas (2.5m2 c/u): {laminas:.1f} → {int(laminas)+1} láminas
🔩 Pijas: {int(m2*3)} pzas aprox
Polines: {int(largo/2)+1} aprox

Escribe: techo 10x5 y lo recalculo.""", 0

    # 3. DINERO / SOBRA / JITOMATE
    if any(p in t for p in ['sobra','cambio','queda','jitomate','kilo','vale','tengo']):
        if len(numeros)>=2:
            # logica: tengo 100, vale 55 -> sobra 45
            # agarra el mayor menos el menor
            mayor = max(numeros)
            menor = min(numeros)
            sobra = mayor - menor
            return f"""💰 CÁLCULO DINERO (IA)
Entendí: Tienes ${mayor} y cuesta ${menor}

Te sobran: ${sobra:.2f}
Cálculo: {mayor} - {menor} = {sobra}

Ya no necesitas escribir solo números, puedes hablarme normal.""", 0

    return None, 0

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/calc')
def calc_api():
    expr_raw = request.args.get('expr','')
    # Intenta primero modo IA flexible
    texto_ia, litros_ia = modo_ia_flexible(expr_raw)
    if texto_ia:
        return {"texto": texto_ia, "grafica": None}

    # Si no es oficio, intenta matemáticas
    e = expr_raw.lower().replace('^','**').strip()
    try:
        graf_x=None; graf_y=None; texto=""
        if 'integral' in e:
            inner=e.replace('integral','').replace('(','').replace(')','').strip()
            f=sp.sympify(inner); res=sp.integrate(f,x)
            texto=f"∫ {inner} dx = {res} + C"; f_lamb=sp.lambdify(x,f,'numpy')
        elif 'derivada' in e or 'derivar' in e:
            inner=e.replace('derivada','').replace('derivar','').replace('(','').replace(')','').strip()
            f=sp.sympify(inner); res=sp.diff(f,x)
            texto=f"d/dx({inner}) = {res}"; f_lamb=sp.lambdify(x,f,'numpy')
        else:
            f=sp.sympify(e)
            if x in f.free_symbols:
                texto=f"f(x) = {f} (graficando...)"; f_lamb=sp.lambdify(x,f,'numpy')
            else:
                res=float(f.evalf()); 
                if res==int(res): res=int(res)
                texto=f"Resultado: {res}"; f_lamb=None

        if 'f_lamb' in locals() and f_lamb is not None:
            try:
                xs=np.linspace(-10,10,200); ys=f_lamb(xs)
                ys=np.where(np.abs(ys)>1000, np.nan, ys)
                graf_x=xs.tolist(); graf_y=ys.tolist()
            except: pass

        return {"texto": texto, "grafica": {"x": graf_x, "y": graf_y} if graf_x else None}
    except Exception as ex:
        return {"texto": f"🤖 IA: No pude entenderlo como matemáticas, pero intenta escribirme como hablas.\nEj: 'sal para 100 litros' o 'tengo 100 y vale 55'\nError tecnico: {ex}", "grafica": None}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
