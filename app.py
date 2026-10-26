from flask import Flask, request, render_template_string
import sympy as sp, numpy as np, re
app = Flask(__name__)

HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Calculadora Universal</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{background:#0f0f0f;color:#fff;font-family:Arial;display:flex;justify-content:center;padding:20px}
.card{background:#1e1e1e;padding:22px;border-radius:22px;width:100%;max-width:560px;box-shadow:0 0 25px #000}
h2{text-align:center}
.modes{display:flex;gap:10px;margin-bottom:12px}
.mode{flex:1;padding:14px;border-radius:14px;border:2px solid #333;background:#2a2a2a;color:#aaa;font-weight:bold;cursor:pointer}
.mode.active{background:#00ff88;color:#000;border-color:#00ff88}
input{width:100%;padding:16px;border-radius:12px;border:none;font-size:17px;margin-bottom:10px;box-sizing:border-box}
button.calc{width:100%;padding:15px;border-radius:12px;border:none;background:#00ff88;color:#000;font-size:18px;font-weight:bold;cursor:pointer}
button.hablar{width:100%;padding:12px;border-radius:12px;border:none;background:#fff;color:#000;margin-top:8px;cursor:pointer}
.result{background:#000;padding:16px;border-radius:12px;margin-top:12px;min-height:90px;white-space:pre-wrap;line-height:1.45}
canvas{background:white;border-radius:12px;margin-top:12px}.hist{color:#00ff88;font-size:12px;margin-top:10px}
</style></head><body><div class="card">
<h2>🛠️ Calculadora Universal</h2>
<div class="modes">
<button id="btnMate" class="mode active" onclick="setMode('mate')">🧮 Normal + Gráfica</button>
<button id="btnDia" class="mode" onclick="setMode('dia')">🛒 Día a día</button>
</div>
<input id="expr" placeholder="Modo Normal: escribe x^2">
<button class="calc" onclick="calcular()">Calcular con IA</button>
<button class="hablar" onclick="hablar()">🎤 Hablar</button>
<div id="res" class="result">Estás en Modo Normal 🧮
Prueba: x^2, integral(x^2), 100-55

Cambia a Día a día para: sal para 100 litros, pecera 80x40x50, tengo 100 y vale 55, techo 17x6, kilo de tortillas vale 25...</div>
<canvas id="graf" width="400" height="280" style="display:none"></canvas><div id="historial" class="hist"></div>
</div>
<script>
let modo='mate'; let historial=JSON.parse(localStorage.getItem('hist')||'[]'); let chart;
function setMode(m){modo=m; document.getElementById('btnMate').classList.toggle('active', m=='mate'); document.getElementById('btnDia').classList.toggle('active', m=='dia');
 if(m=='mate'){document.getElementById('expr').placeholder='Ej: x^2 , integral(x^2) , 5*8+20'; document.getElementById('res').innerText='Modo Normal 🧮 Activo - Ahora grafica';}
 else{document.getElementById('expr').placeholder='Ej: sal para 100 litros, tengo 100 y el jitomate vale 55, pecera 80x40x50'; document.getElementById('res').innerText='Modo Día a día 🛒 Activo - Escribe como hablas, yo entiendo';}
 document.getElementById('graf').style.display='none';}
function mostrarHist(){document.getElementById('historial').innerHTML=historial.map(h=>'→ '+h).join('<br>');} mostrarHist();
async function calcular(){
 let e=document.getElementById('expr').value; if(!e) return;
 document.getElementById('res').innerText='Calculando...';
 let r=await fetch('/api/calc?expr='+encodeURIComponent(e)+'&modo='+modo); let data=await r.json();
 document.getElementById('res').innerText=data.texto;
 historial.unshift(e+' = '+data.texto.split('\\n')[0]); historial=historial.slice(0,8);
 localStorage.setItem('hist', JSON.stringify(historial)); mostrarHist();
 if(data.grafica){let ctx=document.getElementById('graf').getContext('2d'); document.getElementById('graf').style.display='block'; if(chart) chart.destroy();
 chart=new Chart(ctx,{type:'line',data:{labels:data.grafica.x,datasets:[{data:data.grafica.y,borderColor:'#00ff88',tension:0.1,pointRadius:0}]},options:{plugins:{legend:{display:false}},scales:{x:{display:false}}}});}
 else{document.getElementById('graf').style.display='none';}
}
function hablar(){let rec=new (window.webkitSpeechRecognition||window.SpeechRecognition)(); rec.lang='es-MX'; rec.start(); rec.onresult=(e)=>{document.getElementById('expr').value=e.results[0][0].transcript; calcular();}}
</script></body></html>
"""
x=sp.Symbol('x')
def ia_dia_a_dia(t):
    tl=t.lower(); nums=list(map(float, re.findall(r'\d+\.?\d*', tl.replace(',', '.'))))
    if any(k in tl for k in ['pecera','sal','acuario','marino','litro']):
        m=re.search(r'(\d+)\s*[x\*]\s*(\d+)\s*[x\*]\s*(\d+)', tl)
        if m: a,b,c=map(float,m.groups()); litros=a*b*c/1000; det=f"{a}x{b}x{c} cm"
        else: litros=nums[0] if nums else 100; det=f"{litros} L"
        kg=litros*0.035; return f"🛒 DÍA A DÍA - PECERA MARINA\n{det} → {litros:.1f} Litros\n\n🧂 Sal: {kg:.2f} kg ({kg*1000:.0f} g) = 35g x L\n💧 Acondicionador: {litros*0.1:.1f} ml\n🧪 Hierro: {litros*0.2:.1f} ml/semana\n♻️ Cambio 20%: {litros*0.2:.1f} L"
    if 'techo' in tl:
        largo,ancho=(nums[0],nums[1]) if len(nums)>=2 else (17,6); m2=largo*ancho
        return f"🛒 DÍA A DÍA - TECHO\nTecho {largo}x{ancho} = {m2} m2\n📦 Láminas: {int(m2/2.5)+1} pzas\n🔩 Pijas: {int(m2*3)} pzas"
    if any(k in tl for k in ['sobra','cambio','queda','vale','tengo','kilo','jitomate','tortilla']):
        if len(nums)>=2:
            mayor,menor=max(nums),min(nums); sobra=mayor-menor
            return f"🛒 DÍA A DÍA - DINERO\nTienes ${mayor} y cuesta ${menor}\nTe sobran: ${sobra:.2f}\nCálculo: {mayor} - {menor} = {sobra}"
        else:
            return "🛒 Dime cuánto tienes y cuánto vale. Ej: tengo 100 y el kilo de tortillas vale 25"
    return None

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/calc')
def calc_api():
    expr_raw=request.args.get('expr',''); modo=request.args.get('modo','mate')
    if modo=='dia':
        res=ia_dia_a_dia(expr_raw)
        if res: return {"texto":res,"grafica":None}
        # si no entendió, intenta dinero igual
        res=ia_dia_a_dia(expr_raw)
        if res: return {"texto":res,"grafica":None}

    e=expr_raw.lower().replace('^','**').strip()
    try:
        graf_x=graf_y=None; texto=""; 
        if 'integral' in e:
            inner=e.replace('integral','').replace('(','').replace(')','').strip(); f=sp.sympify(inner); res=sp.integrate(f,x); texto=f"∫ {inner} dx = {res} + C"; f_lamb=sp.lambdify(x,f,'numpy')
        elif 'derivada' in e or 'derivar' in e:
            inner=e.replace('derivada','').replace('derivar','').replace('(','').replace(')','').strip(); f=sp.sympify(inner); res=sp.diff(f,x); texto=f"d/dx = {res}"; f_lamb=sp.lambdify(x,f,'numpy')
        else:
            f=sp.sympify(e)
            if x in f.free_symbols: texto=f"f(x) = {f}"; f_lamb=sp.lambdify(x,f,'numpy')
            else: res=float(f.evalf()); res=int(res) if res==int(res) else res; texto=f"Resultado: {res}"; f_lamb=None
        if 'f_lamb' in locals() and f_lamb is not None:
            xs=np.linspace(-10,10,200); ys=f_lamb(xs); ys=np.where(np.abs(ys)>1000, np.nan, ys); graf_x=xs.tolist(); graf_y=ys.tolist()
        return {"texto":texto,"grafica":{"x":graf_x,"y":graf_y} if graf_x else None}
    except Exception as ex:
        if modo=='dia':
            return {"texto":"🛒 No entendí, escribe como hablas. Ej: sal para 100 litros, tengo 100 y vale 55, techo 17x6","grafica":None}
        return {"texto":f"Error: {ex}","grafica":None}

if __name__ == '__main__': app.run(host='0.0.0.0', port=10000)
