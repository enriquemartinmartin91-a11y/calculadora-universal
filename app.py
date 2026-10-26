from flask import Flask, request, render_template_string
import sympy as sp, numpy as np, re, math
app = Flask(__name__)

HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Calculadora Universal</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{background:#0f0f0f;color:#fff;font-family:Arial;display:flex;justify-content:center;padding:20px}
.card{background:#1e1e1e;padding:22px;border-radius:22px;width:100%;max-width:580px}
.modes{display:flex;gap:10px;margin-bottom:12px}
.mode{flex:1;padding:14px;border-radius:14px;border:2px solid #333;background:#2a2a2a;color:#aaa;font-weight:bold;cursor:pointer}
.mode.active{background:#00ff88;color:#000;border-color:#00ff88}
input{width:100%;padding:16px;border-radius:12px;border:none;font-size:16px;margin-bottom:10px;box-sizing:border-box}
button.calc{width:100%;padding:15px;border-radius:12px;border:none;background:#00ff88;color:#000;font-size:18px;font-weight:bold;cursor:pointer}
button.hablar{width:100%;padding:12px;border-radius:12px;border:none;background:#fff;color:#000;margin-top:8px;cursor:pointer}
.result{background:#000;padding:16px;border-radius:12px;margin-top:12px;min-height:100px;white-space:pre-wrap;line-height:1.45}
canvas{background:white;border-radius:12px;margin-top:12px}.hist{color:#00ff88;font-size:11px;margin-top:10px}
.examples{font-size:11px;color:#888;margin-top:8px}
</style></head><body><div class="card">
<h2>🛠️ Calculadora Universal IA</h2>
<div class="modes">
<button id="btnMate" class="mode active" onclick="setMode('mate')">🧮 Normal + Gráfica</button>
<button id="btnDia" class="mode" onclick="setMode('dia')">🛒 Día a día + IA</button>
</div>
<input id="expr" placeholder="Ej: x^2, integral(x^2), sqrt(81)">
<button class="calc" onclick="calcular()">Calcular con IA</button>
<button class="hablar" onclick="hablar()">🎤 Hablar</button>
<div id="res" class="result">Modo Normal 🧮
Ej: x^2, 2**3, sqrt(81), log(100), 55*2.22

Cambia a Día a día para hablar normal.</div>
<div class="examples">En Día a día puedes escribir: suma de 5 y 10, potencia 2 elevado a 3, raíz cuadrada de 81, logaritmo de 100, 55 kilos a 2.22 dolares, etc.</div>
<canvas id="graf" width="400" height="280" style="display:none"></canvas><div id="historial" class="hist"></div>
</div>
<script>
let modo='mate'; let historial=JSON.parse(localStorage.getItem('hist')||'[]'); let chart;
function setMode(m){modo=m; document.getElementById('btnMate').classList.toggle('active', m=='mate'); document.getElementById('btnDia').classList.toggle('active', m=='dia');
 if(m=='mate'){document.getElementById('expr').placeholder='Ej: x^2, sqrt(81), log(100), 2**8'; document.getElementById('res').innerText='Modo Normal 🧮 - Matemáticas puras';}
 else{document.getElementById('expr').placeholder='Ej: raíz cuadrada de 81, potencia de 2 elevado a 3, suma de 5 y 10'; document.getElementById('res').innerText='Modo Día a día 🛒 - Escribe como hablas';}
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
 chart=new Chart(ctx,{type:'line',data:{labels:data.grafica.x,[STRIPPED]
 else{document.getElementById('graf').style.display='none';}
}
function hablar(){let rec=new (window.webkitSpeechRecognition||window.SpeechRecognition)(); rec.lang='es-MX'; rec.start(); rec.onresult=(e)=>{document.getElementById('expr').value=e.results[0][0].transcript; calcular();}}
</script></body></html>
"""
x=sp.Symbol('x')

def ia_dia_a_dia_avanzada(t):
    tl=t.lower()
    nums=list(map(float, re.findall(r'\d+\.?\d*', tl.replace(',', '.'))))
    
    # --- MATEMÁTICAS EN ESPAÑOL ---
    # Suma
    if any(k in tl for k in ['suma','sumar','más','mas']):
        if len(nums)>=2:
            s=sum(nums)
            return f"➕ SUMA\n{' + '.join(map(str,nums))} = {s}"
    # Resta
    if 'resta' in tl or ('menos' in tl and 'menos' not in tl.replace('al menos','')):
        if len(nums)>=2:
            r=nums[0]-nums[1]
            return f"➖ RESTA\n{nums[0]} - {nums[1]} = {r}"
    # Multiplicación
    if any(k in tl for k in ['multiplica','por','veces','kilos','zanahoria']) and 'cuantos kilos' not in tl:
        if 'gastar' in tl or 'vale' in tl or 'cada' in tl or 'por' in tl:
            if len(nums)>=2:
                total=nums[0]*nums[1]
                return f"✖️ MULTIPLICACIÓN\n{nums[0]} * {nums[1]} = {total:.2f}"

    # División - cuántos kilos
    if any(k in tl for k in ['cuantos kilos','entre','dividido','cuánto es','cuanto es']) or 'cuántos kilos tengo si' in tl:
        if len(nums)>=2 and ('entre' in tl or 'cuantos' in tl or '/' in tl):
            total=max(nums) if max(nums)>min(nums) else nums[0]
            precio=min(nums) if len(nums)>=2 else 1
            if 'total' in tl or 'cuantos' in tl:
                res=total/precio
                return f"➗ DIVISIÓN\n{total} / {precio} = {res:.2f}\nTe alcanza para {res:.2f} kilos"
            elif len(nums)>=2:
                res=nums[0]/nums[1]
                return f"➗ DIVISIÓN\n{nums[0]} / {nums[1]} = {res:.4f}"

    # Potencia
    if any(k in tl for k in ['potencia','elevado','al cuadrado','al cubo','^']):
        if 'al cuadrado' in tl and nums: return f"🔢 POTENCIA\n{nums[0]}² = {nums[0]**2}"
        if 'al cubo' in tl and nums: return f"🔢 POTENCIA\n{nums[0]}³ = {nums[0]**3}"
        if len(nums)>=2: return f"🔢 POTENCIA\n{nums[0]} ^ {nums[1]} = {nums[0]**nums[1]}"
        if len(nums)==1 and 'cuadrado' in tl: return f"🔢 {nums[0]}² = {nums[0]**2}"

    # Raíz cuadrada
    if any(k in tl for k in ['raiz cuadrada','raíz cuadrada','sqrt']):
        if nums: return f"√ RAÍZ CUADRADA\n√{nums[0]} = {math.sqrt(nums[0]):.4f}"
    # Raíz cúbica
    if any(k in tl for k in ['raiz cubica','raíz cúbica','cúbica']):
        if nums: return f"∛ RAÍZ CÚBICA\n∛{nums[0]} = {nums[0]**(1/3):.4f}"
    # Raíz en general
    if 'raiz' in tl or 'raíz' in tl:
        if nums: return f"√ RAÍZ\n√{nums[0]} = {math.sqrt(nums[0]):.4f}"

    # Logaritmo
    if 'logaritmo' in tl or 'log' in tl:
        if nums:
            if len(nums)>=2: # log base
                import math
                res=math.log(nums[0], nums[1]) if len(nums)>=2 else math.log10(nums[0])
                return f"📈 LOGARITMO\nlog_{nums[1]}({nums[0]}) = {res:.4f}" if len(nums)>=2 else f"📈 LOG\nlog({nums[0]}) = {res:.4f}"
            else:
                return f"📈 LOGARITMO base 10\nlog({nums[0]}) = {math.log10(nums[0]):.4f}"

    # Pecera y Techo (igual que antes)
    if any(k in tl for k in ['pecera','sal','litro']):
        m=re.search(r'(\d+)\s*[x\*]\s*(\d+)\s*[x\*]\s*(\d+)', tl)
        if m: a,b,c=map(float,m.groups()); litros=a*b*c/1000; det=f"{a}x{b}x{c} cm"
        else: litros=nums[0] if nums else 100; det=f"{litros} L"
        kg=litros*0.035; return f"🐠 PECERA\n{det} → {litros:.1f} L\n🧂 Sal: {kg:.2f} kg"
    if 'techo' in tl:
        largo,ancho=(nums[0],nums[1]) if len(nums)>=2 else (17,6); m2=largo*ancho
        return f"🧱 TECHO\n{m2} m2"
    if any(k in tl for k in ['sobra','cambio','queda']) and len(nums)>=2:
        mayor,menor=max(nums),min(nums); return f"💰 CAMBIO\n{mayor} - {menor} = {mayor-menor:.2f}"

    return None

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/calc')
def calc_api():
    expr_raw=request.args.get('expr',''); modo=request.args.get('modo','mate')
    
    # Si es modo dia, primero intenta IA avanzada
    if modo=='dia':
        res=ia_dia_a_dia_avanzada(expr_raw)
        if res: return {"texto":res,"grafica":None}

    e=expr_raw.lower().replace('^','**').strip()
    # Traduce español a sympy en modo mate también
    e=e.replace('raiz cuadrada','sqrt').replace('raíz cuadrada','sqrt')
    e=e.replace('logaritmo','log').replace('potencia','**')
    
    try:
        graf_x=graf_y=None; texto=""
        if 'integral' in e:
            inner=e.replace('integral','').replace('(','').replace(')','').strip(); f=sp.sympify(inner); res=sp.integrate(f,x); texto=f"∫ {inner} dx = {res} + C"; f_lamb=sp.lambdify(x,f,'numpy')
        elif 'derivada' in e:
            inner=e.replace('derivada','').replace('(','').replace(')','').strip(); f=sp.sympify(inner); res=sp.diff(f,x); texto=f"d/dx = {res}"; f_lamb=sp.lambdify(x,f,'numpy')
        else:
            f=sp.sympify(e)
            if x in f.free_symbols: texto=f"f(x) = {f}"; f_lamb=sp.lambdify(x,f,'numpy')
            else: res=float(f.evalf()); res=int(res) if res==int(res) else res; texto=f"Resultado: {res}"; f_lamb=None
        if 'f_lamb' in locals() and f_lamb is not None:
            xs=np.linspace(-10,10,200); ys=f_lamb(xs); ys=np.where(np.abs(ys)>1000, np.nan, ys); graf_x=xs.tolist(); graf_y=ys.tolist()
        return {"texto":texto,"grafica":{"x":graf_x,"y":graf_y} if graf_x else None}
    except Exception as ex:
        # Intenta de nuevo con IA avanzada si falló en modo mate
        res=ia_dia_a_dia_avanzada(expr_raw)
        if res: return {"texto":res,"grafica":None}
        return {"texto":f"Escribe mejor: Ej: sqrt(81), 2**3, log(100), o en Día a día: raíz cuadrada de 81","grafica":None}

if __name__ == '__main__': app.run(host='0.0.0.0', port=10000)
