import aiosqlite
import json
import re
from collections import Counter

DB_PATH = "bot_memory.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                author_name TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS slang (
                word TEXT PRIMARY KEY,
                count INTEGER DEFAULT 1,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

# Palabras estándar a ignorar al detectar modismos (stopwords en español)
COMMON_WORDS = set([
    "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "pero", "que", "de", 
    "a", "en", "por", "para", "con", "sin", "sobre", "mi", "tu", "su", "nos", "te", "me",
    "le", "se", "si", "no", "como", "cuando", "donde", "es", "son", "fue", "era", "esta",
    "estan", "estoy", "hay", "bien", "muy", "mas", "ya", "todo", "nada", "algo", "hola",
    "bueno", "al", "del", "lo", "yo", "tu", "el", "ella", "ellos", "nosotros", "ustedes"
])

async def record_user_message(guild_id: int, user_id: int, author_name: str, content: str):
    """Registra un mensaje y analiza modismos potenciales."""
    if not content or len(content.strip()) < 2:
        return
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (guild_id, user_id, author_name, content) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, author_name, content)
        )
        
        # Extracción de posibles palabras de jerga (palabras informales, risas, modismos)
        words = re.findall(r'\b[a-záéíóúñ]{3,15}\b', content.lower())
        for w in words:
            if w not in COMMON_WORDS and not w.startswith("http"):
                await db.execute('''
                    INSERT INTO slang (word, count, last_seen) 
                    VALUES (?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(word) DO UPDATE SET 
                        count = count + 1,
                        last_seen = CURRENT_TIMESTAMP
                ''', (w,))
        await db.commit()

async def get_learned_slang(limit: int = 25):
    """Obtiene las palabras o modismos más frecuentes que los humanos usan en el servidor."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT word, count FROM slang WHERE count >= 2 ORDER BY count DESC LIMIT ?", 
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]

async def get_recent_chat_history(guild_id: int, limit: int = 10):
    """Obtiene el historial reciente para darle contexto al bot."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT author_name, content FROM messages WHERE guild_id = ? ORDER BY id DESC LIMIT ?",
            (guild_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            # Invertir para que quede cronológico
            return rows[::-1]
