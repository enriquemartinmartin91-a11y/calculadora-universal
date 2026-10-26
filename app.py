from flask import Flask, request, render_template_string
import sympy as sp, numpy as np, re, math
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
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
.result{background:#000;padding:16px;border-radius:12px;margin-top:12px;min-height:120px;white-space:pre-wrap}
canvas{background:white;border-radius:12px;margin-top:12px}
</style></head><body><div class="card">
<h2>🛠️ Calculadora Universal IA</h2>
<div class="modes">
<button id="btnMate" class="mode active" onclick="setMode('mate')">🧮 Normal + Gráfica</button>
<button id="btnDia" class="mode" onclick="setMode('dia')">🛒 Día a día + IA</button>
</div>
<input id="expr" placeholder="Ej: 3x-9, x^2, raiz cuadrada de 81">
<button class="calc" onclick="calcular()">Calcular con IA</button>
<div id="res" class="result">Modo Normal: Escribe 3x-9
Modo Día a día: Escribe 1 kilo de cebolla cuesta 30 y tengo 50 cuanto sobra</div>
<canvas id="graf" width="400" height="280" style="display:none"></canvas>
</div>
<script>
let modo='mate'; let chart=null;
function setMode(m){
 modo=m;
 document.getElementById('btnMate').classList.toggle('active', m=='mate');
 document.getElementById('btnDia').classList.toggle('active', m=='dia');
 document.getElementById('graf').style.display='none';
 document.getElementById('res').innerText = m=='mate' ? 'Modo Normal activo: escribe 3x-9' : 'Modo Dia a dia activo: escribe como hablas';
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
  chart=new Chart(ctx,{type:'line',data:{labels:data.grafica.x,datasets:[{label:'f(x)',data:data.grafica.y,borderColor:'#00ff88',fill:false,tension:0.1,pointRadius:0}]},options:{responsive:true}});
 } else {document.getElementById('graf').style.display='none';}
}
</script></body></html>
"""
x=sp.Symbol('x')

def normalize_mate(s):
    s=s.lower().strip().replace('^','**')
    s=re.sub(r'(\d)(?=x)', r'\1*', s)
    s=re.sub(r'(x)(?=\d)', r'\1*', s)
    s=re.sub(r'(\d)(?=\()', r'\1*', s)
    s=re.sub(r'(\))(?=x|\d|\()', r'\1*', s)
    return s

def ia_dia(t):
    tl=t.lower()
    nums=list(map(float, re.findall(r'\d+\.?\d*', tl.replace(',', '.'))))
    tengo=re.search(r'tengo\s+(\d+\.?\d*)', tl)
    cuesta=re.search(r'cuesta\s+(\d+\.?\d*)', tl)
    kilos=re.search(r'(\d+\.?\d*)\s*kilo', tl)
    if any(k in tl for k in ['sobra','cambio','queda']):
        dinero=float(tengo.group(1)) if tengo else (max(nums) if nums else 0)
        if len(nums)>=3:
            cant=float(kilos.group(1)) if kilos else nums[0]
            prec=float(cuesta.group(1)) if cuesta else sorted(nums)[1]
            total=cant*prec
            return f"CAMBIO CEBOLLA\n{cant:g} kilo x ${prec:g} = ${total:.2f}\nTienes ${dinero:g} -> Te sobran ${dinero-total:.2f}\nCalculo: {dinero:g} - {total:g} = {dinero-total:.2f}"
        elif len(nums)>=2:
            prec=float(cuesta.group(1)) if cuesta else min(nums)
            return f"CAMBIO\n${dinero:g} - ${prec:g} = ${dinero-prec:.2f} te sobran"
    if 'raiz cuadrada' in tl or 'raíz cuadrada' in tl:
        if nums: return f"RAIZ\n√{nums[0]:g} = {math.sqrt(nums[0]):.4f}"
    return None

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/calc')
def calc_api():
    raw=request.args.get('expr',''); modo=request.args.get('modo','mate')
    if modo=='dia':
        r=ia_dia(raw)
        if r: return {"texto":r,"grafica":None}
    e=normalize_mate(raw)
    try:
        f=sp.sympify(e)
        if x in f.free_symbols:
            sol=sp.solve(f, x)
            texto=f"f(x) = {raw}\nSi {f}=0 -> x = {sol}"
            fl=sp.lambdify(x,f,'numpy')
        else:
            texto=f"Resultado: {raw} = {float(f.evalf())}"; fl=None
        gx=gy=None
        if 'fl' in locals() and fl is not None:
            xs=np.linspace(-10,10,200); ys=fl(xs); ys=np.where(np.abs(ys)>1000, np.nan, ys); gx=xs.tolist(); gy=ys.tolist()
        return {"texto":texto,"grafica":{"x":gx,"y":gy} if gx else None}
    except Exception as ex:
        r=ia_dia(raw)
        if r: return {"texto":r,"grafica":None}
        return {"texto":f"No pude leer '{raw}'. Prueba 3*x-9 o 3x-9","grafica":None}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
