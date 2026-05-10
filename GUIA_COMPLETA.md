# 🚀 Guía Completa: LLM en Vast.ai desde cero

Guía paso a paso para crear una instancia en Vast.ai, lanzar un modelo LLM (Qwen) con SGLang y conversar con él tanto por SSH como desde tu portátil.

---

## 📋 Requisitos previos

### Instalar herramientas
```bash
pip install --upgrade vastai openai requests
sudo apt install sshpass jq  # Linux
```

### Configurar tu API key de Vast.ai
```bash
vastai set api-key "TU_API_KEY_AQUI"
```
> Tu API key la encuentras en https://vast.ai/console/account

### Asegurarte de tener una clave SSH registrada en Vast.ai
Ve a https://vast.ai/console/account y añade tu clave pública SSH (`~/.ssh/id_rsa.pub`).

---

## PASO 1 — Buscar una GPU disponible

### Para modelos pequeños (7B) — cualquier RTX 3090/4090 de 24GB
```bash
vastai search offers "gpu_ram>=24 num_gpus=1 direct_port_count>=1 rentable=true disk_space>=200 cuda_vers>=12.2 dph<=2" -o dph
```

### Para modelos medianos-grandes (27B) — necesitas ~54GB VRAM (A100/H100)
```bash
vastai search offers "gpu_ram>=54 num_gpus=1 direct_port_count>=1 rentable=true disk_space>=200 cuda_vers>=12.2" -o dph
```

> Apunta el **OFFER_ID** del resultado que te interese (primera columna).

---

## PASO 2 — Crear la instancia

Elige el modelo que quieras desplegar:

### Opción A: Qwen2.5-7B (ligero, cabe en 24GB)
```bash
vastai create instance <OFFER_ID> \
  --image lmsysorg/sglang:latest \
  --disk 200 \
  --label "qwen-7b" \
  --onstart-cmd 'python3 -m sglang.launch_server --model-path Qwen/Qwen2.5-7B-Instruct --host 0.0.0.0 --port 8000 --tp-size 1 --context-length 32768 --mem-fraction-static 0.85'
```

### Opción B: Qwen3.5-27B FP16 (requiere ~54GB VRAM)
```bash
vastai create instance <OFFER_ID> \
  --image lmsysorg/sglang:latest \
  --disk 200 \
  --label "qwen-27b" \
  --onstart-cmd 'python3 -m sglang.launch_server --model-path Qwen/Qwen3.5-27B --host 0.0.0.0 --port 8000 --tp-size 1 --context-length 32768 --reasoning-parser qwen3 --mem-fraction-static 0.85'
```

> El comando devuelve un **INSTANCE_ID**. Apúntalo.

---

## PASO 3 — Exportar variables de entorno (una sola vez por sesión)

Rellena con los valores reales y ejecuta. Así el resto de scripts funcionan sin argumentos:

```bash
export VASTAI_INSTANCE_ID="TU_INSTANCE_ID"   # ID de tu instancia (consúltalo con vastai show instances)
export VASTAI_SSH_HOST="ssh3.vast.ai"        # Host SSH
export VASTAI_SSH_PORT=10874                  # Puerto SSH
export VASTAI_INSTANCE_API_KEY="TU_API_KEY"  # API key de la instancia (paso 4)
export VASTAI_CONTAINER_PORT=8000             # Puerto del servidor dentro del contenedor
export VASTAI_LOCAL_PORT=8080                 # Puerto local para el túnel SSH
export VASTAI_MODEL_NAME="Qwen2.5-7B-Instruct"  # Nombre del modelo
```

---

## PASO 4 — Esperar a que la instancia arranque

### Obtener SSH host/port e instance API key
```bash
# Ver estado y datos de conexión
vastai show instance $VASTAI_INSTANCE_ID --raw | jq -r '.actual_status, .ssh_host, .ssh_port, .instance_api_key'

# O con el comando de URL directa
vastai ssh-url $VASTAI_INSTANCE_ID
```

> Actualiza las variables `VASTAI_SSH_HOST`, `VASTAI_SSH_PORT` y `VASTAI_INSTANCE_API_KEY` con los valores que obtengas.

### Monitorizar hasta que esté en estado "running"

**Opción 1** — Script bash simple (sale cuando deja de estar en "loading"):
```bash
./monitor.sh $VASTAI_INSTANCE_ID
```

**Opción 2** — Script bash que espera exactamente "running":
```bash
./poll_status.sh $VASTAI_INSTANCE_ID
```

**Opción 3** — Python con mensajes detallados:
```bash
python3 poller.py --instance-id $VASTAI_INSTANCE_ID
```

> ⏳ La primera vez puede tardar **10-30 minutos** porque descarga la imagen Docker y el modelo.

---

## PASO 5 — Verificar que el servidor SGLang está listo

```bash
python3 test_ready.py \
  --ssh-host $VASTAI_SSH_HOST \
  --ssh-port $VASTAI_SSH_PORT \
  --container-port 8000
```

El script hace health checks via SSH cada 30 segundos hasta que el servidor responde `200 OK`. Cuando esté listo te imprime el comando exacto del túnel.

> Si usas las variables de entorno del paso 3, puedes ejecutarlo sin argumentos:
> ```bash
> python3 test_ready.py
> ```

---

## PASO 6 — Conectarse por SSH (acceso directo a la instancia)

```bash
# Usando tu clave SSH (si la tienes registrada en Vast.ai)
ssh -o StrictHostKeyChecking=no root@$VASTAI_SSH_HOST -p $VASTAI_SSH_PORT

# Usando la instance API key como contraseña
sshpass -p "$VASTAI_INSTANCE_API_KEY" ssh -o StrictHostKeyChecking=no root@$VASTAI_SSH_HOST -p $VASTAI_SSH_PORT
```

### Ver logs del servidor dentro de la instancia
```bash
# Una vez dentro por SSH:
tail -f /tmp/sglang.log
```

### 🔍 Debug paso a paso DENTRO de la instancia (ya conectado por SSH)

Una vez dentro con `ssh -p 10874 root@ssh3.vast.ai`:

**1. Verificar que el proceso está corriendo:**
```bash
ps aux | grep sglang
```

**2. Ver qué puertos están escuchando:**
```bash
ss -lnt | grep -E ":8000|:8080"
# O con netstat:
netstat -tlnp | grep -E ":8000|:8080"
```
Deberías ver algo como `0.0.0.0:8000` o `:::8000` si el servidor está levantado.

**3. Comprobar el health endpoint localmente:**
```bash
curl -v http://localhost:8000/health
```
Debe devolver `200 OK` con `{"status":"ok"}` o similar.

**4. Probar una request real del modelo:**
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "Hola"}],
    "max_tokens": 50
  }'
```

**5. Ver logs en tiempo real:**
```bash
tail -f /tmp/sglang.log
# O si SGLang usa otro log:
journalctl -u sglang -f
```

**6. Si no hay proceso corriendo, diagnosticar por qué falló el onstart:**
```bash
# Ver logs del contenedor/sistema
dmesg | tail -50
journalctl -n 100

# Verificar si python3 y sglang están instalados
which python3
python3 -m sglang.launch_server --help 2>&1 | head -20

# Ver si hay logs de intentos previos
ls -lh /tmp/sglang* /var/log/sglang* 2>/dev/null
cat /tmp/sglang.log 2>/dev/null | tail -100
```

**7. Arrancar el servidor manualmente (dentro de la instancia):**
```bash
# En background con logs a archivo
python3 -m sglang.launch_server \
  --model-path Qwen/Qwen2.5-7B-Instruct \
  --host 0.0.0.0 --port 8000 \
  --tp-size 1 --context-length 32768 \
  --mem-fraction-static 0.85 > /tmp/sglang.log 2>&1 &

# Ver el PID del proceso
echo $!

# Seguir los logs en tiempo real
tail -f /tmp/sglang.log
```

**8. Si el modelo no se descargó, descargarlo manualmente:**
```bash
pip install huggingface_hub
python3 -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-7B-Instruct')"
```



---

### Arrancar el servidor manualmente desde tu portátil (si el onstart falló)
```bash
sshpass -p "$VASTAI_INSTANCE_API_KEY" ssh -o StrictHostKeyChecking=no root@$VASTAI_SSH_HOST -p $VASTAI_SSH_PORT \
  'python3 -m sglang.launch_server \
    --model-path Qwen/Qwen2.5-7B-Instruct \
    --host 0.0.0.0 --port 8000 \
    --tp-size 1 --context-length 32768 \
    --mem-fraction-static 0.85 > /tmp/sglang.log 2>&1 &'
```

---

## PASO 7 — Crear el túnel SSH (acceso desde tu portátil)

El servidor corre en el puerto 8000 **dentro** del contenedor. Para acceder desde tu máquina local necesitas un túnel SSH.

### Editar start_tunnel.sh con tus datos actuales
```bash
# Edita las variables en start_tunnel.sh:
# SSH_HOST="ssh4.vast.ai"
# SSH_PORT="12345"
# INSTANCE_API_KEY="abc123..."

./start_tunnel.sh
```

### O manualmente en background:
```bash
sshpass -p "$VASTAI_INSTANCE_API_KEY" ssh \
  -o StrictHostKeyChecking=no \
  -L 8080:localhost:8000 \
  -p $VASTAI_SSH_PORT \
  root@$VASTAI_SSH_HOST \
  -N &

echo "Túnel activo en localhost:8080"
```

### Verificar que el túnel funciona
```bash
curl http://localhost:8080/health
# Debe devolver: {"status": "ok"}
```

---

## PASO 8 — Conversar con el modelo

### 🗣️ Chat interactivo desde el portátil
```bash
# Con variables de entorno configuradas:
export VASTAI_BASE_URL="http://localhost:8080/v1"
export VASTAI_MODEL_NAME="Qwen2.5-7B-Instruct"

python3 chat_qwen.py
```

Opciones del chat:
```bash
python3 chat_qwen.py --hide-reasoning    # Oculta el razonamiento interno del modelo
python3 chat_qwen.py --max-tokens 4000   # Más tokens por respuesta
python3 chat_qwen.py --temperature 0.3   # Respuestas más deterministas
```

Comandos dentro del chat:
- `/quit` — salir
- `/clear` — limpiar el historial de conversación
- `/help` — ayuda
- `/models` — listar modelos disponibles

### 🔬 Test rápido de la API
```bash
python3 test_api.py
```

### 🧪 Test manual con Python
```bash
python3 - <<'EOF'
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8080/v1", api_key="EMPTY")
response = client.chat.completions.create(
    model="Qwen2.5-7B-Instruct",
    messages=[{"role": "user", "content": "Hola, ¿qué tal?"}],
    max_tokens=500
)
print(response.choices[0].message.content)
EOF
```

---

## PASO 9 — Parar y destruir la instancia

```bash
# Parar (conserva el disco, para el cobro de GPU)
vastai stop instance $VASTAI_INSTANCE_ID

# Volver a arrancar una instancia parada
vastai start instance $VASTAI_INSTANCE_ID

# ⚠️  DESTRUIR (elimina todo, irreversible)
vastai destroy instance $VASTAI_INSTANCE_ID
```

### Parar el túnel SSH local
```bash
./stop_tunnel.sh
```

---

## 📊 Resumen rápido de scripts

| Script | Uso |
|--------|-----|
| `monitor.sh` | Espera hasta que la instancia salga de "loading" |
| `poll_status.sh` | Espera hasta que la instancia esté en "running" |
| `poller.py` | Como poll_status.sh pero con mensajes detallados |
| `test_ready.py` | Espera a que el servidor SGLang esté respondiendo |
| `test_api.py` | Test completo con túnel SSH automático |
| `start_tunnel.sh` | Abre el túnel SSH en background |
| `stop_tunnel.sh` | Cierra el túnel SSH |
| `chat_qwen.py` | Chat interactivo con el modelo |

---

## 🔧 Troubleshooting

### GPU Out of Memory (OOM)
- Usa un modelo más pequeño (7B en vez de 27B)
- Busca modelos cuantizados (sufijo `-A3B`, `-A10B`)
- Reduce `--mem-fraction-static 0.75`

### Instancia atascada en "loading"
```bash
vastai logs $VASTAI_INSTANCE_ID  # Ver qué está pasando
vastai start instance $VASTAI_INSTANCE_ID  # Reintentar
```

### Error de conexión SSH
- Espera 1-2 minutos más (la instancia puede seguir arrancando)
- Comprueba que el estado sea "running": `vastai show instance $VASTAI_INSTANCE_ID --raw | jq -r '.actual_status'`

### El túnel no funciona
```bash
# Matar cualquier proceso en el puerto 18000
./stop_tunnel.sh
# Volver a lanzar
./start_tunnel.sh
```

### Ver instancias activas
```bash
vastai search instances
```
