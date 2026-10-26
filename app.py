from flask import Flask, request, render_template_string
import sympy as sp, numpy as np, re, math
app = Flask(__name__)

HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Calculadora Universal IA</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{background:#0f0f0f;color:#fff;font-family:Arial;display:flex;justify-content:center;padding:15px}
.card{background:#1e1e1e;padding:20px;border-radius:22px;width:100%;max-width:560px}
.modes{display:flex;gap:10px;margin-bottom:12px}
.mode{flex:1;padding:14px;border-radius:14px;border:2px solid #333;background:#2a2a2a;color:#aaa;font-weight:bold;cursor:pointer}
.mode.active{background:#00ff88;color:#000;border-color:#00ff88}
input{width:100%;padding:16px;border-radius:12px;border:none;font-size:16px;margin-bottom:10px;box-sizing:border-box}
button.calc{width:100%;padding:15px;border-radius:12px;border:none;background:#00ff88;color:#000;font-size:18px;font-weight:bold;cursor:pointer}
.result{background:#000;padding:16px;border-radius:12px;margin-top:12px;min-height:100px;white-space:pre-wrap}
canvas{background:white;border-radius:12px;margin-top:12px}
</style></head><body><div class="card">
<h2>Calculadora Universal IA</h2>
<div class="modes">
<button id="btnMate" class="mode active" onclick="setMode('mate')">Normal + Grafica</button>
<button id="btnDia" class="mode" onclick="setMode('dia')">Dia a dia + IA</button>
</div>
<input id="expr" placeholder="Ej: 3x-9, x^2, raiz cuadrada de 81">
<button class="calc" onclick="calcular()">Calcular con IA</button>
<div id="res" class="result">Modo Normal: puedes poner 3x-9, 2x^2, sqrt(81)
Modo Dia a dia: 1 kilo cebolla cuesta 30 y tengo 50 cuanto sobra</div>
<canvas id="graf" width="400" height="280" style="display:none"></canvas>
</div>
<script>
let modo='mate'; let chart=null;
function setMode(m){modo=m;
 document.getElementById('btnMate').classList.toggle('active', m=='mate');
 document.getElementById('btnDia').classList.toggle('active', m=='dia');
 document.getElementById('graf').style.display='none';}
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
  chart=new Chart(ctx,{type:'line',data:{labels:data.grafica.x,[STRIPPED]
 } else {document.getElementById('graf').style.display='none';}
}
</script></body></html>"""
x=sp.Symbol('x')

def normalize_mate(s):
    s=s.lower().strip()
    s=s.replace('^','**').replace('raiz','sqrt').replace('raíz','sqrt')
    # FIX PRINCIPAL: 3x -> 3*x
    s=re.sub(r'(\d)(?=x)', r'\1*', s)
    s=re.sub(r'(x)(?=\d)', r'\1*', s)
    s=re.sub(r'(\d)(?=\()', r'\1*', s)
    s=re.sub(r'(\))(?=\d|x|\()', r'\1*', s)
    return s

def ia_dia(t):
    tl=t.lower()
    nums=list(map(float, re.findall(r'\d+\.?\d*', tl.replace(',', '.'))))
    tengo_match=re.search(r'tengo\s+(\d+\.?\d*)', tl)
    cuesta_match=re.search(r'cuesta\s+(\d+\.?\d*)', tl)
    kilos_match=re.search(r'(\d+\.?\d*)\s*kilo', tl)
    if any(k in tl for k in ['sobra','cambio','queda','vueltas']):
        dinero=float(tengo_match.group(1)) if tengo_match else max(nums) if nums else 0
        if len(nums)>=3:
            cantidad=float(kilos_match.group(1)) if kilos_match else nums[0]
            precio=float(cuesta_match.group(1)) if cuesta_match else sorted(nums)[1]
            total=cantidad*precio; sobra=dinero-total
            return f"CAMBIO\n{int(cantidad)} kilo x ${precio} = ${total:.2f}\nTienes ${dinero} - ${total:.2f} = ${sobra:.2f} te sobran"
        elif len(nums)>=2:
            precio=float(cuesta_match.group(1)) if cuesta_match else min(nums)
            return f"CAMBIO\n${dinero} - ${precio} = ${dinero-precio:.2f}"
    if 'raiz cuadrada' in tl or 'raíz cuadrada' in tl and nums:
        return f"RAIZ CUADRADA\n√{nums[0]} = {math.sqrt(nums[0]):.4f}"
    if 'potencia' in tl or 'elevado' in tl and len(nums)>=2:
        return f"POTENCIA\n{nums[0]} ^ {nums[1]} = {nums[0]**nums[1]}"
    return None

@app.route('/')
def home(): return render_template_string(HTML)
@app.route('/api/calc')
def calc_api():
    expr_raw=request.args.get('expr',''); modo=request.args.get('modo','mate')
    if modo=='dia':
        r=ia_dia(expr_raw)
        if r: return {"texto":r,"grafica":None}
    e=normalize_mate(expr_raw)
    try:
        f=sp.sympify(e)
        if x in f.free_symbols:
            # resolver si es 3x-9 = 0
            sol=sp.solve(f, x)
            texto=f"f(x) = {expr_raw}\nSolucion {f}=0 -> x={sol}\n"
            f_lamb=sp.lambdify(x,f,'numpy')
            texto+=f"Grafica lista"
        else:
            res=float(f.evalf()); texto=f"Resultado: {expr_raw} = {res}"; f_lamb=None
        gx=gy=None
        if 'f_lamb' in locals() and f_lamb is not None:
            xs=np.linspace(-10,10,200); ys=f_lamb(xs); ys=np.where(np.abs(ys)>1000, np.nan, ys); gx=xs.tolist(); gy=ys.tolist()
        return {"texto":texto,"grafica":{"x":gx,"y":gy} if gx else None}
    except Exception as ex:
        r=ia_dia(expr_raw)
        if r: return {"texto":r,"grafica":None}
        return {"texto":f"Error: {ex}\nIntenta: 3*x-9, x**2, sqrt(81)","grafica":None}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
