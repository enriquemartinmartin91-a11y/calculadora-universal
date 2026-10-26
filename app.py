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
    
    # --- DETECTAR DINERO Y PRECIOS POR TEXTO (CORRECCIÓN CEBOLLA) ---
    tengo_match = re.search(r'tengo\s+(\d+\.?\d*)', tl)
    cuesta_match = re.search(r'cuesta\s+(\d+\.?\d*)', tl)
    kilos_match = re.search(r'(\d+\.?\d*)\s*kilo', tl)

    # CASO CEBOLLA: 1 kilo cuesta 30 y tengo 50
    if any(k in tl for k in ['sobra','cambio','queda','vueltas']) and len(nums)>=2:
        dinero = float(tengo_match.group(1)) if tengo_match else max(nums)
        precio = float(cuesta_match.group(1)) if cuesta_match else None
        
        if len(nums) >= 3:
            # Hay cantidad + precio + dinero: ej 1 kilo, 30 precio, 50 tengo
            cantidad = float(kilos_match.group(1)) if kilos_match else nums[0]
            # si precio no se detectó por texto, es el de en medio
            if precio is None:
                # ordenamos: si nums = [1,30,50], precio es 30
                sorted_nums = sorted(nums)
                # el del medio suele ser el precio
                precio = sorted_nums[1] if len(sorted_nums)>=3 else sorted_nums[0]
            
            total_a_pagar = cantidad * precio
            sobra = dinero - total_a_pagar
            return f"💰 CAMBIO - CEBOLLA\n{int(cantidad)} kilo x ${precio} = ${total_a_pagar:.2f}\nTienes ${dinero} - ${total_a_pagar:.2f} = ${sobra:.2f} te sobran\nCálculo: {dinero} - ({cantidad}*{precio}) = {sobra:.2f}"
        
        elif len(nums) == 2:
            # Caso simple: cuesta 30 y tengo 50
            if precio is None: precio = min(nums)
            sobra = dinero - precio
            return f"💰 CAMBIO\nTienes ${dinero} y cuesta ${precio}\nTe sobran: ${sobra:.2f}\nCálculo: {dinero} - {precio} = {sobra:.2f}"

    # RAIZ, POTENCIA, LOG, etc
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
    if any(k in tl for k in ['gastar','cuanto es en total','cada kilo vale','kilos a','zanahoria','jitomate','cebolla']) and 'sobra' not in tl and 'cambio' not in tl:
        if len(nums)>=2 and 'cuantos' not in tl:
            # Si hay 1 kilo a 30, es 1*30
            if len(nums)>=2:
                # si dice 55 kilos a 2.22
                cantidad = float(kilos_match.group(1)) if kilos_match else nums[0]
                precio = float(cuesta_match.group(1)) if cuesta_match else nums[1] if len(nums)>1 else nums[0]
                if cantidad == precio: precio = nums[1]
                # si es 1 kilo de cebolla a 30
                if 'kilo' in tl:
                    return f"MULTIPLICACIÓN\n{int(cantidad) if cantidad==int(cantidad) else cantidad} kilo x ${precio} = ${cantidad*precio:.2f}"
                return f"MULTIPLICACIÓN\n{nums[0]} * {nums[1]} = {nums[0]*nums[1]:.2f}"
    if 'suma' in tl and len(nums)>=2:
        return f"SUMA\n{' + '.join(map(str,nums))} = {sum(nums)}"
    if any(k in tl for k in ['pecera','sal','litro']):
        litros=nums[0] if nums else 100; return f"PECERA\n{litros} L → Sal: {litros*0.035:.2f} kg"
    if 'techo' in tl and len(nums)>=2: return f"TECHO\n{nums[0]*nums[1]} m2"
    
    return None
