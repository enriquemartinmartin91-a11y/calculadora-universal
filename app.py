from flask import Flask, request, render_template_string
import sympy as sp, numpy as np, re, math
app = Flask(__name__)

HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Calculadora Universal IA 100%</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{background:#0f0f0f;color:#fff;font-family:Arial;display:flex;justify-content:center;padding:15px}
.card{background:#1e1e1e;padding:20px;border-radius:22px;width:100%;max-width:600px}
.modes{display:flex;gap:10px;margin-bottom:12px}
.mode{flex:1;padding:14px;border-radius:14px;border:2px solid #333;background:#2a2a2a;color:#aaa;font-weight:bold;cursor:pointer}
.mode.active{background:#00ff88;color:#000;border-color:#00ff88}
input{width:100%;padding:16px;border-radius:12px;border:none;font-size:16px;margin-bottom:10px;box-sizing:border-box}
button.calc{width:100%;padding:15px;border-radius:12px;border:none;background:#00ff88;color:#000;font-size:18px;font-weight:bold;cursor:pointer}
.result{background:#000;padding:16px;border-radius:12px;margin-top:12px;min-height:150px;white-space:pre-wrap;line-height:1.5}
canvas{background:white;border-radius:12px;margin-top:12px}
</style></head><body><div class="card">
<h2>🛠️ Universal 100% - Auto Ayuda</h2>
<div class="modes">
<button id="btnMate" class="mode" onclick="setMode('mate')">🧮 Mate + Gráfica</button>
<button id="btnDia" class="mode active" onclick="setMode('dia')">🛒 Día a día + IA 100%</button>
</div>
<input id="expr" placeholder="Ej: pared 16x6, acuario 500L 5ml por cada 80L, 3x-9">
<button class="calc" onclick="calcular()">Calcular</button>
<div id="res" class="result">✅ Modo 100% Activo
Yo ya no doy error. Si me falta un dato, te lo pido y te ayudo con un estimado.

Prueba:
- mi pared mide 16x6 y quiero pintarla
- 500 litros, 5 ml por cada 80 litros
- 1 kilo cebolla cuesta 30 y tengo 50 cuanto sobra
- 3x-9</div>
<canvas id="graf" width="400" height="280" style="display:none"></canvas>
</div>
<script>
let modo='dia'; let chart=null;
function setMode(m){modo=m;
 document.getElementById('btnMate').classList.toggle('active', m=='mate');
 document.getElementById('btnDia').classList.toggle('active', m=='dia');
 document.getElementById('graf').style.display='none';}
async function calcular(){
 let e=document.getElementById('expr').value; if(!e) return;
 document.getElementById('res').innerText='🧠 Analizando al 100%...';
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
    s=re.sub(r'(\d)(?=\()', r'\1*', s)
    return s

def ia_100(t):
    tl=t.lower()
    nums = list(map(float, re.findall(r'\d+\.?\d*', tl.replace(',', '.'))))
    if not nums and 'x' not in tl:
        return "🤔 No vi números. ¿Me puedes decir las medidas o cantidades? Ej: 'pared 16x6'"

    # --- MOTOR 1: PARED / PINTURA (Tu ejemplo) ---
    if any(k in tl for k in ['pared','pintar','pintura','cuarto','muro']):
        # busca 16x6, 16 por 6, 16*6
        m = re.search(r'(\d+\.?\d*)\s*[xX*por]+\s*(\d+\.?\d*)', tl)
        if m:
            a=float(m.group(1)); b=float(m.group(2)); area=a*b
            # logica auto-ayuda
            texto = f"✅ PARED DETECTADA\nMedidas: {a:g} x {b:g} = {area:g} m²\n\n"
            texto += f"Para pintarla necesitas:\n- 1 mano: {area/10:.2f} litros (rinde estándar 10m²/L)\n- 2 manos (recomendado): {area/5:.2f} litros\n\n"
            texto += f"👉 LO MÍNIMO: Con {math.ceil(area/10)} litro(s) le das 1 mano.\n👉 RECOMENDADO: Compra {math.ceil(area/5)} litros para que quede bien.\n\n"
            texto += f"⚠️ Para darte el resultado exacto al 100% necesito:\n1. ¿Cuántas manos quieres? (1 o 2)\n2. ¿Tu pintura dice cuánto rinde? (Ej: 10m²/L)\n\nSi no lo sabes, usa mi estimado de 10m² por litro, que es el estándar. Si me dices tu rendimiento, te lo calculo exacto."
            return texto
        else:
            return f"✅ Veo que quieres pintar pero me faltan medidas.\nPara completar tu resultado necesito más datos:\n- ¿Cuánto mide tu pared? Ej: '16x6'\n- ¿Cuántas manos?\n\nSi no lo sabes, dime 'mi pared mide 4 por 3' y yo te ayudo con el estimado estándar."

    # --- MOTOR 2: POR CADA (Regla de 3 universal) ---
    if 'por cada' in tl:
        m = re.search(r'(\d+\.?\d*)\s*([a-z$%]+)?\s*por cada\s*(\d+\.?\d*)\s*([a-z$%]+)?', tl)
        if m:
            dosis=float(m.group(1)); dosis_u=(m.group(2) or '').strip()
            base=float(m.group(3)); base_u=(m.group(4) or '').strip()
            restantes=nums.copy()
            try: restantes.remove(dosis)
            except: pass
            try: restantes.remove(base)
            except: pass
            total = max(restantes) if restantes else max(nums)
            if total==dosis or total==base:
                # si no encontró total, pide dato
                return f"✅ Detecté regla 'por cada': {dosis:g} {dosis_u} por cada {base:g} {base_u}\n\nPara completar tu resultado necesito más datos:\n- ¿Cuál es tu total? Ej: 'tengo 500 litros'\n\nSi me dices el total, te calculo: (total / {base:g}) * {dosis:g}"
            res=(total/base)*dosis
            return f"✅ AUTO-COMPRENDE (Regla de 3)\nDetectado: {dosis:g} {dosis_u} por cada {base:g} {base_u}\nTu total: {total:g} {base_u}\n\nOperación: ({total:g}/{base:g})*{dosis:g} = {res:.2f} {dosis_u}\n\nResultado: {res:.2f} {dosis_u}"

    # --- MOTOR 3: CAMBIO / SOBRA ---
    if any(k in tl for k in ['sobra','cambio','queda','vueltas','cuesta','tengo']):
        tengo_m=re.search(r'tengo\s+(\d+\.?\d*)', tl)
        cuesta_m=re.search(r'cuesta[s]?\s+(\d+\.?\d*)', tl)
        kilos_m=re.search(r'(\d+\.?\d*)\s*kilos?', tl)
        dinero=float(tengo_m.group(1)) if tengo_m else (max(nums) if nums else None)
        if dinero is None:
            return "Para calcular tu cambio necesito saber cuánto dinero tienes. Ej: 'tengo 50 pesos'"
        if cuesta_m and kilos_m:
            cant=float(kilos_m.group(1)); prec=float(cuesta_m.group(1))
            return f"✅ CAMBIO\n{cant:g} x ${prec:g} = ${cant*prec:.2f}\nTienes ${dinero:g}, te sobran ${dinero-cant*prec:.2f}"
        if cuesta_m:
            prec=float(cuesta_m.group(1))
            return f"✅ CAMBIO\n${dinero:g} - ${prec:g} = ${dinero-prec:.2f} te sobran"
        if len(nums)>=2:
            # fallback
            return f"✅ CAMBIO (estimado)\n${max(nums):g} - ${min(nums):g} = ${max(nums)-min(nums):.2f} te sobran\n\nSi quieres exacto dime: 'cuesta X y tengo Y'"

    # --- MOTOR 4: SI NO ENTENDIÓ NADA, NO DA ERROR, PIDE DATOS ---
    if len(nums)>=1:
        return f"🤖 Casi lo tengo. Vi estos números: {nums}\nPero me falta contexto.\n\nPara completar tu resultado necesito más datos:\n- ¿Qué quieres calcular? (area, cambio, dosis por cada...)\n\nEjemplos que sí entiendo al 100%:\n- 'pared 16x6'\n- '500 litros, 5 ml por cada 80 litros'\n- '1 kilo cuesta 30 y tengo 50'\n\nSi no sabes el dato exacto, dime lo que sí sabes y yo te ayudo con un estimado estándar."
    return None

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/calc')
def calc_api():
    raw=request.args.get('expr',''); modo=request.args.get('modo','dia')
    r=ia_100(raw)
    if r: return {"texto":r,"grafica":None}
    e=normalize_mate(raw)
    try:
        f=sp.sympify(e)
        if x in f.free_symbols:
            sol=sp.solve(f,x); texto=f"f(x) = {raw}\nSol x={sol}"; fl=sp.lambdify(x,f,'numpy')
        else:
            texto=f"Resultado: {raw} = {float(f.evalf()):.4f}"; fl=None
        gx=gy=None
        if 'fl' in locals() and fl is not None:
            xs=np.linspace(-10,10,200); ys=fl(xs); ys=np.where(np.abs(ys)>1000, np.nan, ys); gx=xs.tolist(); gy=ys.tolist()
        return {"texto":texto,"grafica":{"x":gx,"y":gy} if gx else None}
    except:
        return {"texto":f"🤖 Para completar tu resultado necesito más datos sobre '{raw}'.\nVi números: {re.findall(r'\\d+\\.?\\d*', raw)}\n\nDime:\n- Si es pared: medidas Ej '16x6'\n- Si es dosis: '5ml por cada 80L y tengo 500L'\n- Si es compra: 'cuesta 30 y tengo 50'\n\nSi no sabes el dato, yo te pongo el estándar y te ayudo a resolverlo.","grafica":None}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
