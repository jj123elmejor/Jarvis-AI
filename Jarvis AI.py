import discord
import pyttsx3
import asyncio
import aiohttp
import psutil

import wikipediaapi
from urllib.parse import quote
from imageai.Detection import ObjectDetection

# --- CONFIGURACIÓN DE VOZ ---
def jarvis_habla_local(texto):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 1.0)
        
        voices = engine.getProperty('voices')
        for voice in voices:
            if "spanish" in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break

        engine.say(texto)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"Error en el sistema de voz: {e}")


# --- CONFIGURACIÓN DE DISCORD ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# --- LLAVES API CONFIGURADAS ---
WEATHER_API_KEY = "4560f62642635638e3f6181448e78ec4"
NEWS_API_KEY = "pub_a37e062e7ffa493cb3c98d2de94ec03c"
NASA_API_KEY = "DEMO_KEY" 
MATES_API_KEY = "QPH6TL3LW5"  
PELIS_API_KEY = "274c33c5"  # ¡Su nueva clave de OMDb vinculada con éxito!

detector = ObjectDetection()

# Setting a path to the YOLOv3 model
model_path = "/content/yolov3.pt"

# Installing the YOLOv3 model and setting a path to the weights file
detector.setModelTypeAsYOLOv3()
detector.setModelPath(model_path)

# Loading the model
detector.loadModel()
detector.CustomObjects()



@client.event
async def on_ready():
    print('--- SISTEMAS LISTOS ---')
    print(f'Jarvis conectado como: {client.user.name}')
    
    loop = asyncio.get_event_loop()
    mensaje_inicio = "Sistemas en línea. Protocolos de asistencia iniciados. Estoy a su disposición, señor."
    await loop.run_in_executor(None, jarvis_habla_local, mensaje_inicio)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    msg = message.content.lower().strip()

    # --- COMANDO: !HOLA ---
    if msg == '!hola':
        await message.channel.send(f"Hola {message.author.name}, estoy operativo a su servicio.")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, jarvis_habla_local, f"Hola señor, {message.author.name} ha solicitado mi presencia.")
        
    # --- COMANDO: !ESTADO ---
    elif msg == '!estado':
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        bat = psutil.sensors_battery()
        
        embed = discord.Embed(title="🖥️ Estado de los Sistemas", color=discord.Color.green())
        embed.add_field(name="Procesador", value=f"{cpu}%", inline=True)
        embed.add_field(name="Memoria RAM", value=f"{ram}%", inline=True)
        
        if bat: 
            embed.add_field(name="Batería", value=f"{bat.percent}% {'🔌' if bat.power_plugged else '🔋'}", inline=True)
        
        await message.channel.send(embed=embed)
        
        respuesta = f"Señor, el procesador está al {cpu} por ciento y la memoria RAM al {ram} por ciento."
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, jarvis_habla_local, respuesta)
        
    # --- COMANDO: !CLIMA ---
    elif msg.startswith('!clima'):
        ciudad_cruda = msg.replace('!clima', '').strip()
        ciudad_para_buscar = ciudad_cruda if ciudad_cruda else "Cartagena, CO"
        ciudad_url = quote(ciudad_para_buscar)

        url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad_url}&appid={WEATHER_API_KEY}&units=metric&lang=es"
        
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            try:
                async with session.get(url) as r:
                    data = await r.json()
                    if r.status == 200:
                        temp = round(data['main']['temp'])
                        sensacion = round(data['main']['feels_like'])
                        humedad = data['main']['humidity']
                        viento = data['wind']['speed']
                        desc = data['weather'][0]['description'].capitalize()
                        nombre_final = data['name']
                        
                        icono = data['weather'][0]['icon']
                        url_icono = f"http://openweathermap.org/img/wn/{icono}@2x.png"
                        
                        embed = discord.Embed(title=f"🌤️ Clima en {nombre_final}", description=f"**{desc}**", color=discord.Color.blue())
                        embed.set_thumbnail(url=url_icono)
                        embed.add_field(name="🌡️ Temp.", value=f"{temp}°C", inline=True)
                        embed.add_field(name="🤔 Sensación", value=f"{sensacion}°C", inline=True)
                        embed.add_field(name="💧 Humedad", value=f"{humedad}%", inline=True)
                        embed.add_field(name="💨 Viento", value=f"{viento} m/s", inline=True)
                        embed.set_footer(text="Jarvis Intelligence System")

                        await message.channel.send(embed=embed)
                        
                        respuesta_voz = f"Señor, en {nombre_final} la temperatura es de {temp} grados con {desc}."
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, jarvis_habla_local, respuesta_voz)
                    else:
                        await message.channel.send(f"Lo siento señor, el satélite no reconoce la ubicación: **{ciudad_para_buscar}**.")
            except Exception as e:
                await message.channel.send("Error de conexión con el satélite.")
                
    # --- COMANDO: !NOTICIAS (CORREGIDO PARA NEWSDATA.IO) ---
    # --- COMANDO: !NOTICIAS CON CATEGORÍAS ---
    elif msg.startswith('!noticias'):
        # 1. Extraemos lo que escribió el usuario después de !noticias
        categoria_usuario = msg.replace('!noticias', '').strip().lower()
        
        # Diccionario para traducir lo que tú escribes al idioma que entiende la API
        categorias_validas = {
            'deportes': 'sports',
            'tecnologia': 'technology',
            'ciencia': 'science',
            'entretenimiento': 'entertainment',
            'salud': 'health',
            'politica': 'politics',
            'negocios': 'business',
            'comida': 'food',
            'ambiente': 'environment',
            'principales': 'top',
            'mundiales': 'world',
            'destacadas': 'top',
            'turismo': 'tourism',
            'cultura': 'lifestyle',
            'educacion': 'education',
            'locales': 'domestic'
        }
        
        # 2. Configurar la URL base
        url = f"https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&language=es"
        
        # 3. Si el usuario escribió una categoría válida, se la sumamos a la URL
        nombre_categoria_voz = "principales"
        if categoria_usuario in categorias_validas:
            api_category = categorias_validas[categoria_usuario]
            url += f"&category={api_category}"
            nombre_categoria_voz = categoria_usuario
        elif categoria_usuario:
            # Si escribió algo que no está en la lista, le avisamos
            categorias_lista = ", ".join(categorias_validas.keys())
            await message.channel.send(f"Señor, la categoría '**{categoria_usuario}**' no es válida.\nLas opciones son: {categorias_lista}")
            return

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            try:
                async with session.get(url) as r:
                    data = await r.json()
                    
                    if r.status == 200 and data.get('results'):
                        articulos = data['results'][:3]
                        await message.channel.send(f"📰 Estas son las noticias de la categoría **{nombre_categoria_voz.capitalize()}**, señor:")
                        
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, jarvis_habla_local, f"Le presento los titulares sobre {nombre_categoria_voz}.")
                        
                        for art in articulos:
                            titulo = art.get('title', 'Sin título')
                            enlace = art.get('link', '#')
                            await message.channel.send(f"🔹 **{titulo}**\n<{enlace}>")
                    else:
                        print(f"Error API Noticias: {data}")
                        await message.channel.send("Señor, no he podido recuperar información de prensa para esa categoría.")
            except Exception as e:
                print(f"Error en comando noticias: {e}")
                await message.channel.send("Error al intentar contactar con el servidor de noticias.")
                
    # --- COMANDO: !ESPACIO ---
    elif msg == '!espacio':
        url_nasa = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
        
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            try:
                async with session.get(url_nasa, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        titulo = data.get('title', 'Objeto Espacial')
                        explicacion = data.get('explanation', 'Sin detalles.')
                        url_imagen = data.get('url')
                        
                        if data.get('media_type') == 'video':
                            url_imagen = data.get('thumbnail_url', 'https://i.imgur.com/B9O07BR.png')

                        embed = discord.Embed(
                            title=f"🌌 Archivos de la NASA: {titulo}",
                            description=f"Señor, he recuperado esta información del archivo central. \n\n**Descripción:** {explicacion[:300]}...",
                            color=discord.Color.dark_purple()
                        )
                        embed.set_image(url=url_imagen)
                        await message.channel.send(embed=embed)
                        
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, jarvis_habla_local, f"Señor, visualizando {titulo} en el monitor principal.")
                    else:
                        await message.channel.send(f"El servidor de la NASA devolvió un error {r.status}, señor.")
            except Exception as e:
                await message.channel.send("Sistemas espaciales fuera de línea. Error de conexión.")
                
    # --- COMANDO: !MATES ---
    # --- COMANDO: !MATES ---
    elif msg.startswith('!mates'):
        pregunta_usuario = msg.replace('!mates', '').strip()
        
        if not pregunta_usuario:
            await message.channel.send("Señor, por favor proporcione una ecuación o problema para resolver.")
            return

        pregunta_url = quote(pregunta_usuario)
        url_wolfram = f"http://api.wolframalpha.com/v1/spoken?i={pregunta_url}&appid={MATES_API_KEY}"

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            try:
                async with session.get(url_wolfram) as r:
                    respuesta_texto = await r.text()
                    
                    if r.status == 200:
                        embed_mates = discord.Embed(
                            title="🧠 Cálculo de Sistemas",
                            description=f"**Pregunta:** {pregunta_usuario}\n\n**Resultado:** {respuesta_texto}",
                            color=discord.Color.orange()
                        )
                        embed_mates.set_footer(text="Procesado por el núcleo WolframAlpha")
                        
                        # Línea corregida con embed=
                        await message.channel.send(embed=embed_mates)
                        
                        loop = asyncio.get_event_loop()
                        voz_jarvis = f"Señor, el cálculo para {pregunta_usuario} es: {respuesta_texto}"
                        await loop.run_in_executor(None, jarvis_habla_local, voz_jarvis)
                    else:
                        await message.channel.send("Lo siento señor, no puedo procesar esa pregunta matemática específica o la clave es inválida.")
            except Exception as e:
                print(f"Error en mates: {e}")
                await message.channel.send("Sistemas de cálculo fuera de línea.")

    elif msg.startswith('!cine'):
        pelicula_input = msg.replace('!cine', '').strip()
        
        if not pelicula_input:
            await message.channel.send("Señor, ¿qué película desea que busque en los archivos?")
            return

        pelicula_url = quote(pelicula_input)
        url = f"http://www.omdbapi.com/?t={pelicula_url}&apikey={PELIS_API_KEY}&plot=short"

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            try:
                async with session.get(url) as r:
                    if r.status == 200:
                        data = await r.json()
                        
                        if data.get('Response') == 'True':
                            titulo = data.get('Title')
                            año = data.get('Year')
                            director = data.get('Director')
                            trama = data.get('Plot')

                            poster = data.get('Poster')
                            rating = data.get('imdbRating')
                            
                            embed = discord.Embed(
                                title=f"🎬 {titulo} ({año})",
                                description=f"**Director:** {director}\n**IMDb:** ⭐ {rating}\n\n**Trama:** {trama}",
                                color=discord.Color.dark_red()
                            )
                            
                            if poster and poster != "N/A":
                                embed.set_thumbnail(url=poster)
                                
                            embed.set_footer(text="Núcleo de búsqueda: OMDb API")
                            await message.channel.send(embed=embed)
                            
                            voz_pelicula = f"Señor, he encontrado la película {titulo}. Dirigida por {director}."
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(None, jarvis_habla_local, voz_pelicula)
                        else:
                            error_api = data.get('Error', 'Película no encontrada')
                            await message.channel.send(f"Lo siento señor, el archivo central reporta: **{error_api}**.")
                    else:
                        await message.channel.send(f"Señor, el servidor externo rechazó la conexión. Código de estado: {r.status}.")
            except Exception as e:
                await message.channel.send("Error de conexión con la base de datos cinematográfica.")
        # --- COMANDO: !WIKIPEDIA (Función 5) ---
    
   # --- COMANDO: RECONOCIMIENTO DE OBJETOS (IA) ---
  
    # --- COMANDO: !F1 (Función 11) ---
    elif msg == '!f1':
        # URL de la API de Ergast para la tabla de posiciones del campeonato actual (2026)
        url_f1 = "https://ergast.com/api/f1/current/driverStandings.json"
        
        await message.channel.send("🏁 Conectando con los satélites de la FIA. Recuperando tabla de posiciones...")

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            try:
                async with session.get(url_f1) as r:
                    if r.status == 200:
                        data = await r.json()
                        
                        # Navegamos en el JSON de la API
                        standings_list = data['MRData']['StandingsTable']['StandingsLists']
                        
                        if standings_list:
                            posiciones = standings_list[0]['DriverStandings'][:5] # Tomamos el Top 5
                            season = standings_list[0]['season']
                            
                            embed_f1 = discord.Embed(
                                title=f"🏁 Campeonato Mundial de Fórmula 1 - Temporada {season}",
                                color=discord.Color.red()
                            )
                            
                            texto_voz = f"Señor, la tabla de posiciones de la temporada {season} marcha de la siguiente manera: "
                            
                            for driver in posiciones:
                                pos = driver['position']
                                puntos = driver['points']
                                nombre = driver['Driver']['givenName']
                                apellido = driver['Driver']['familyName']
                                escuderia = driver['Constructors'][0]['name']
                                
                                # Formato estético para el Embed
                                embed_f1.add_field(
                                    name=f"{pos}° {nombre} {apellido}",
                                    value=f"🏎️ **{escuderia}**\n📊 Puntos: **{puntos}**",
                                    inline=False
                                )
                                
                                # Sumamos los 3 primeros a la locución de Jarvis para que no hable tanto
                                if int(pos) <= 3:
                                    texto_voz += f"En la posición {pos}, {nombre} {apellido} con {puntos} puntos. "
                            
                            embed_f1.set_footer(text="Datos en tiempo real vía Ergast API")
                            await message.channel.send(embed=embed_f1)
                            
                            # Jarvis habla
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(None, jarvis_habla_local, texto_voz)
                        else:
                            await message.channel.send("Señor, el campeonato de esta temporada aún no ha registrado datos.")
                    else:
                        await message.channel.send(f"Error de telemetría. La API de F1 respondió con código: {r.status}")
            except Exception as e:
                print(f"Error técnico en F1: {e}")
                await message.channel.send("Sistemas de telemetría de Fórmula 1 fuera de línea.")

# --- INICIO DEL BOT ---
# Reemplace "TU_DISCORD_TOKEN" con el token de desarrollo de Discord
# client.run("TU_DISCORD_TOKEN")
client.run("TU_TOKEN_AQUI")
