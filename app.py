from flask import Flask, request, render_template_string
import sympy as sp, numpy as np, re, math
app = Flask(__name__)

HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Calculadora Universal IA</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{background:#0f0f0f;color:#fff;font-family:Arial;display:flex;justify-content:center;padding:15px}
.card{background:#1e1e1e;padding:20px;border-radius:22px;width:100%;max-width:560px}
.modes{display:flex;gap:10px;margin-bottom:12px}
.mode{flex:1;padding:14px;border-radius:14px;border:2px solid #333;background:#2a2a2a;color:#aaa;font-weight:bold;cursor:pointer}
.mode.active{background:#00ff88;color:#000;border-color:#00ff88}
input{width:100%;padding:16px;border-radius:12px;border:none;font-size:16px;margin-bottom:10px;box-sizing:border-box}
button.calc{width:100%;padding:15px;border-radius:12px;border:none;background:#00ff88;color:#000;font-size:18px;font-weight:bold;cursor:pointer}
button.hablar{width:100%;padding:12px;border-radius:12px;border:none;background:#fff;color:#000;margin-top:8px;cursor:pointer}
.result{background:#000;padding:16px;border-radius:12px;margin-top:12px;min-height:100px;white-space:pre-wrap}
canvas{background:white;border-radius:12px;margin-top:12px}
</style></head><body><div class="card">
<h2>🛠️ Calculadora Universal IA</h2>
<div class="modes">
<button id="btnMate" class="mode active" onclick="setMode('mate')">🧮 Normal + Gráfica</button>
<button id="btnDia" class="mode" onclick="setMode('dia')">🛒 Día a día + IA</button>
</div>
<input id="expr" placeholder="Ej: x^2, sqrt(81), 55*2.22">
<button class="calc" onclick="calcular()">Calcular con IA</button>
<button class="hablar" onclick="hablar()">🎤 Hablar</button>
<div id="res" class="result">Modo Normal activo. Escribe x^2

Cambia a Día a día para: raiz cuadrada de 81, potencia 2 elevado a 3, 55 kilos a 2.22 dolares</div>
<canvas id="graf" width="400" height="280" style="display:none"></canvas>
</div>
<script>
let modo='mate'; let chart=null;
function setMode(m){
 modo=m;
 document.getElementById('btnMate').classList.toggle('active', m=='mate');
 document.getElementById('btnDia').classList.toggle('active', m=='dia');
 if(m=='mate'){
  document.getElementById('expr').placeholder='Ej: x^2, sqrt(81), log(100)';
  document.getElementById('res').innerText='Modo Normal 🧮 activo - grafica funciones';
 } else {
  document.getElementById('expr').placeholder='Ej: raiz cuadrada de 81, 55 kilos a 2.22 dolares';
  document.getElementById('res').innerText='Modo Dia a dia 🛒 activo - escribe como hablas';
 }
 document.getElementById('graf').style.display='none';
}
async function calcular(){
 let e=document.getElementById('expr').value; if(!e) return;
 document.getElementById('res').innerText='Calculando...';
 let r=await fetch('/api/calc?expr='+encodeURIComponent(e)+'&modo='+modo);
 let data=await r.json();
 document.getElementById('res').innerText=data.texto;
 if(data.grafica && data.grafica.x){
  let ctx=document.getElementById('graf').getContext('2d');
  document.getElementById('graf').style.display='block';
  if(chart) chart.destroy();
  chart=new Chart(ctx,{type:'line',data:{labels:data.grafica.x,datasets:[{label:'f(x)',data:data.grafica.y,borderColor:'#00ff88',tension:0.1}]},options:{responsive:true}});
 } else {
  document.getElementById('graf').style.display='none';
 }
}
function hablar(){
 let rec=new (window.webkitSpeechRecognition||window.SpeechRecognition)();
 rec.lang='es-MX'; rec.start();
 rec.onresult=(ev)=>{document.getElementById('expr').value=ev.results[0][0].transcript; calcular();}
}
</script></body></html>
"""
x=sp.Symbol('x')

def ia_dia(t):
    tl=t.lower()
    nums=list(map(float, re.findall(r'\d+\.?\d*', tl.replace(',', '.'))))
    if 'raiz cuadrada' in tl or 'raíz cuadrada' in tl:
        if nums: return f"√ RAÍZ CUADRADA\n√{nums[0]} = {math.sqrt(nums[0]):.4f}"
    if 'raiz cubica' in tl or 'raíz cúbica' in tl:
        if nums: return f"∛ RAÍZ CÚBICA\n∛{nums[0]} = {nums[0]**(1/3):.4f}"
    if 'potencia' in tl or 'elevado' in tl:
        if len(nums)>=2: return f"POTENCIA\n{nums[0]} ^ {nums[1]} = {nums[0]**nums[1]}"
        if 'cuadrado' in tl and nums: return f"POTENCIA\n{nums[0]}² = {nums[0]**2}"
    if 'logaritmo' in tl or tl.strip().startswith('log'):
        if nums: return f"LOGARITMO base 10\nlog({nums[0]}) = {math.log10(nums[0]):.4f}"
    if 'cuantos kilos' in tl or 'cuántos kilos' in tl:
        if len(nums)>=2:
            total=max(nums); precio=min(nums)
            return f"DIVISIÓN\n{total} / {precio} = {total/precio:.2f} kilos"
    if any(k in tl for k in ['gastar','cuanto es en total','cada kilo vale','kilos a','zanahoria','jitomate']):
        if len(nums)>=2:
            return f"MULTIPLICACIÓN\n{nums[0]} * {nums[1]} = {nums[0]*nums[1]:.2f}"
    if 'suma' in tl:
        if len(nums)>=2: return f"SUMA\n{' + '.join(map(str,nums))} = {sum(nums)}"
    if 'sobra' in tl or 'cambio' in tl:
        if len(nums)>=2: return f"CAMBIO\n{max(nums)} - {min(nums)} = {max(nums)-min(nums):.2f}"
    if any(k in tl for k in ['pecera','sal','litro']):
        litros=nums[0] if nums else 100; return f"PECERA\n{litros} L → Sal: {litros*0.035:.2f} kg"
    if 'techo' in tl and len(nums)>=2: return f"TECHO\n{nums[0]*nums[1]} m2"
    return None

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/calc')
def calc_api():
    expr_raw=request.args.get('expr',''); modo=request.args.get('modo','mate')
    if modo=='dia':
        r=ia_dia(expr_raw)
        if r: return {"texto":r,"grafica":None}
    e=expr_raw.lower().replace('^','**').replace('raiz','sqrt').replace('raíz','sqrt')
    try:
        if 'integral' in e:
            inner=e.replace('integral','').replace('(','').replace(')','').strip()
            f=sp.sympify(inner); res=sp.integrate(f,x); texto=f"∫ {inner} dx = {res} + C"
            f_lamb=sp.lambdify(x,f,'numpy')
        elif 'derivada' in e:
            inner=e.replace('derivada','').replace('(','').replace(')','').strip()
            f=sp.sympify(inner); res=sp.diff(f,x); texto=f"derivada = {res}"
            f_lamb=sp.lambdify(x,f,'numpy')
        else:
            f=sp.sympify(e)
            if x in f.free_symbols:
                texto=f"f(x) = {f}"; f_lamb=sp.lambdify(x,f,'numpy')
            else:
                res=float(f.evalf()); texto=f"Resultado: {res}"; f_lamb=None
        gx=gy=None
        if 'f_lamb' in locals() and f_lamb is not None:
            xs=np.linspace(-10,10,200); ys=f_lamb(xs)
            ys=np.where(np.abs(ys)>1000, np.nan, ys)
            gx=xs.tolist(); gy=ys.tolist()
        return {"texto":texto,"grafica":{"x":gx,"y":gy} if gx else None}
    except Exception as ex:
        r=ia_dia(expr_raw)
        if r: return {"texto":r,"grafica":None}
        return {"texto":"Error, prueba: sqrt(81), 2**3, o en Dia a dia: raiz cuadrada de 81","grafica":None}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
