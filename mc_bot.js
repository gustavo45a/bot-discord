const mineflayer = require('mineflayer');
const { pathfinder, Movements, goals } = require('mineflayer-pathfinder');
const GoalFollow = goals.GoalFollow;

const host = process.env.MC_HOST || '127.0.0.1';
const port = parseInt(process.env.MC_PORT || '25565');
const username = process.env.MC_USERNAME || 'Kai';
const authType = process.env.MC_AUTH || 'offline'; // 'offline' para mundos locales / no-premium, 'microsoft' para cuentas oficiales

console.log([MC-BOT] Conectando a System.Management.Automation.Internal.Host.InternalHost: como '' (Auth: )...);

const bot = mineflayer.createBot({
  host: host,
  port: port,
  username: username,
  auth: authType
});

bot.loadPlugin(pathfinder);

bot.on('login', () => {
  console.log([MC-BOT] ¡Kai ha iniciado sesión exitosamente en el servidor de Minecraft!);
});

bot.on('spawn', () => {
  console.log([MC-BOT] Kai ha spawneado en el mundo (Coordenadas: ).);
  const mcData = require('minecraft-data')(bot.version);
  const defaultMove = new Movements(bot, mcData);
  bot.pathfinder.setMovements(defaultMove);
});

// Respuestas a comandos del chat en el juego
bot.on('chat', (sender, message) => {
  if (sender === bot.username) return;
  console.log([MC-CHAT] <> );

  const msg = message.toLowerCase().trim();

  // Seguir a un jugador
  if (msg.includes('sigueme') || msg.includes('ven')) {
    const target = bot.players[sender]?.entity;
    if (!target) {
      bot.chat(
o te veo , acércate un poco xd);
      return;
    }
    bot.chat(ya voy );
    bot.pathfinder.setGoal(new GoalFollow(target, 2), true);
  }

  // Parar de seguir
  if (msg.includes('para') || msg.includes('quieto') || msg.includes('stop')) {
    bot.pathfinder.setGoal(null);
    bot.chat('aquí me quedo');
  }

  // Saltar
  if (msg.includes('salta')) {
    bot.setControlState('jump', true);
    setTimeout(() => bot.setControlState('jump', false), 500);
  }
});

bot.on('kicked', (reason) => {
  console.log([MC-BOT] Desconectado del servidor: );
});

bot.on('error', (err) => {
  console.error([MC-BOT ERROR] );
});
