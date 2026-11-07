// ==============================================================================
// FoxVC Private Cloud Gaming Engine - Game Catalog & Runtime
// Designed for ultra-low latency mobile cloud streaming & local execution
// ==============================================================================

const GAME_CATALOG = [
  {
    id: "space_defender",
    title: "Space Defender 2026",
    genre: "Arcade Shooter",
    badge: "60 FPS • ACTION",
    color: "#ff7a00",
    icon: "🚀",
    desc: "Pilot your fighter through asteroid fields and alien waves. Features particle explosions, shields, and laser synthesizer.",
    controls: "Joystick to Move • [A] Fire Lasers • [B] Shield"
  },
  {
    id: "cyber_snake",
    title: "Cyber Snake Neon",
    genre: "Retro Arcade",
    badge: "HYPER-LEAN",
    color: "#34d399",
    icon: "🐍",
    desc: "Cyberpunk 60FPS snake with glowing light-cycle trails, energy orbs, and dynamic speed scaling.",
    controls: "D-Pad or Swipe to Turn • [A] Turbo Boost"
  },
  {
    id: "fox_runner",
    title: "Fox Horizon Runner",
    genre: "Endless Platformer",
    badge: "PHYSICS",
    color: "#38bdf8",
    icon: "🦊",
    desc: "Leap over spikes and chasms across a parallax neon skyline. Collect energy cores to maintain hyper-speed.",
    controls: "Joystick / Left-Right to Run • [A] Jump • [B] Double Jump"
  },
  {
    id: "cyber_pong",
    title: "Cyber Pong 2.0",
    genre: "Table Sport",
    badge: "AI OPPONENT",
    color: "#f472b6",
    icon: "🏓",
    desc: "High-speed air hockey with realistic ricochet physics and an adaptive neural AI opponent.",
    controls: "Slide Paddle or D-Pad Up/Down • [A] Power Smash"
  }
];

// WebAudio Sound Synthesizer (Zero MP3/WAV dependencies - 100% synthesized)
class SoundFX {
  constructor() {
    this.ctx = null;
  }
  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
  }
  playLaser() {
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(880, this.ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(110, this.ctx.currentTime + 0.12);
    gain.gain.setValueAtTime(0.3, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.12);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start();
    osc.stop(this.ctx.currentTime + 0.12);
  }
  playExplode() {
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = "square";
    osc.frequency.setValueAtTime(140, this.ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(30, this.ctx.currentTime + 0.25);
    gain.gain.setValueAtTime(0.4, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.25);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start();
    osc.stop(this.ctx.currentTime + 0.25);
  }
  playCoin() {
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(987.77, this.ctx.currentTime); // B5
    osc.frequency.setValueAtTime(1318.51, this.ctx.currentTime + 0.08); // E6
    gain.gain.setValueAtTime(0.3, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.2);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start();
    osc.stop(this.ctx.currentTime + 0.2);
  }
}

const sfx = new SoundFX();

// ==============================================================================
// GAME 1: SPACE DEFENDER 2026
// ==============================================================================
class SpaceDefender {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.reset();
  }
  reset() {
    this.ship = { x: this.canvas.width / 2, y: this.canvas.height - 80, vx: 0, vy: 0, speed: 6, hp: 100, shield: 100 };
    this.lasers = [];
    this.enemies = [];
    this.particles = [];
    this.stars = [];
    this.score = 0;
    this.gameOver = false;
    this.lastSpawn = 0;
    this.lastShot = 0;

    for (let i = 0; i < 60; i++) {
      this.stars.push({
        x: Math.random() * this.canvas.width,
        y: Math.random() * this.canvas.height,
        speed: 0.5 + Math.random() * 2,
        size: Math.random() * 2
      });
    }
  }

  update(input, dt) {
    if (this.gameOver) {
      if (input.btnA || input.btnB) this.reset();
      return;
    }

    // Ship movement
    this.ship.x += input.stickX * this.ship.speed;
    this.ship.y += input.stickY * this.ship.speed;
    this.ship.x = Math.max(20, Math.min(this.canvas.width - 20, this.ship.x));
    this.ship.y = Math.max(30, Math.min(this.canvas.height - 30, this.ship.y));

    // Stars
    this.stars.forEach(s => {
      s.y += s.speed;
      if (s.y > this.canvas.height) s.y = 0;
    });

    // Firing
    const now = Date.now();
    if (input.btnA && now - this.lastShot > 140) {
      this.lasers.push({ x: this.ship.x - 10, y: this.ship.y - 15, vy: -12 });
      this.lasers.push({ x: this.ship.x + 10, y: this.ship.y - 15, vy: -12 });
      this.lastShot = now;
      sfx.playLaser();
    }

    // Lasers update
    this.lasers.forEach(l => l.y += l.vy);
    this.lasers = this.lasers.filter(l => l.y > -20);

    // Spawn Enemies
    if (now - this.lastSpawn > 900) {
      this.enemies.push({
        x: 30 + Math.random() * (this.canvas.width - 60),
        y: -30,
        vy: 2 + Math.random() * 2.5,
        hp: 30,
        size: 20 + Math.random() * 10,
        hue: Math.floor(Math.random() * 60) // orange to yellow
      });
      this.lastSpawn = now;
    }

    // Enemies update & collision
    for (let i = this.enemies.length - 1; i >= 0; i--) {
      const e = this.enemies[i];
      e.y += e.vy;

      // Laser collision
      for (let j = this.lasers.length - 1; j >= 0; j--) {
        const l = this.lasers[j];
        const dist = Math.hypot(e.x - l.x, e.y - l.y);
        if (dist < e.size) {
          e.hp -= 20;
          this.lasers.splice(j, 1);
          this.addParticles(l.x, l.y, 4, "#ffaa00");
          if (e.hp <= 0) {
            this.addParticles(e.x, e.y, 16, "#ff5500");
            sfx.playExplode();
            this.enemies.splice(i, 1);
            this.score += 100;
            break;
          }
        }
      }

      // Ship collision
      if (Math.hypot(e.x - this.ship.x, e.y - this.ship.y) < e.size + 15) {
        this.addParticles(e.x, e.y, 20, "#ef4444");
        this.enemies.splice(i, 1);
        this.ship.hp -= 25;
        sfx.playExplode();
        if (this.ship.hp <= 0) {
          this.gameOver = true;
        }
      }
    }
    this.enemies = this.enemies.filter(e => e.y < this.canvas.height + 40);

    // Particles
    this.particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      p.life -= 0.03;
    });
    this.particles = this.particles.filter(p => p.life > 0);
  }

  addParticles(x, y, count, color) {
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 1 + Math.random() * 4;
      this.particles.push({
        x: x, y: y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 1.0,
        color: color
      });
    }
  }

  render() {
    const ctx = this.ctx;
    ctx.fillStyle = "#07090e";
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Stars
    ctx.fillStyle = "#ffffff";
    this.stars.forEach(s => {
      ctx.fillRect(s.x, s.y, s.size, s.size);
    });

    // Lasers
    ctx.fillStyle = "#38bdf8";
    ctx.shadowColor = "#38bdf8";
    ctx.shadowBlur = 8;
    this.lasers.forEach(l => {
      ctx.fillRect(l.x - 2, l.y, 4, 14);
    });
    ctx.shadowBlur = 0;

    // Enemies
    this.enemies.forEach(e => {
      ctx.save();
      ctx.translate(e.x, e.y);
      ctx.fillStyle = "#ef4444";
      ctx.shadowColor = "#ef4444";
      ctx.shadowBlur = 10;
      ctx.beginPath();
      ctx.moveTo(0, e.size);
      ctx.lineTo(-e.size, -e.size);
      ctx.lineTo(0, -e.size / 2);
      ctx.lineTo(e.size, -e.size);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    });

    // Ship
    ctx.save();
    ctx.translate(this.ship.x, this.ship.y);
    ctx.fillStyle = "#ff7a00";
    ctx.shadowColor = "#ff7a00";
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.moveTo(0, -20);
    ctx.lineTo(-16, 18);
    ctx.lineTo(0, 10);
    ctx.lineTo(16, 18);
    ctx.closePath();
    ctx.fill();

    // Thruster flame
    ctx.fillStyle = "#38bdf8";
    ctx.beginPath();
    ctx.moveTo(-6, 14);
    ctx.lineTo(0, 24 + Math.random() * 8);
    ctx.lineTo(6, 14);
    ctx.closePath();
    ctx.fill();
    ctx.restore();

    // Particles
    this.particles.forEach(p => {
      ctx.fillStyle = p.color;
      ctx.globalAlpha = p.life;
      ctx.fillRect(p.x, p.y, 3, 3);
    });
    ctx.globalAlpha = 1.0;

    // HUD
    ctx.fillStyle = "#f1f5f9";
    ctx.font = "bold 15px sans-serif";
    ctx.fillText("SCORE: " + this.score, 20, 30);
    ctx.fillStyle = this.ship.hp > 30 ? "#34d399" : "#ef4444";
    ctx.fillText("SHIELD HP: " + Math.max(0, this.ship.hp) + "%", 20, 52);

    if (this.gameOver) {
      ctx.fillStyle = "rgba(0,0,0,0.75)";
      ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      ctx.fillStyle = "#ef4444";
      ctx.font = "bold 28px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("MISSION TERMINATED", this.canvas.width / 2, this.canvas.height / 2 - 20);
      ctx.fillStyle = "#cbd5e1";
      ctx.font = "16px sans-serif";
      ctx.fillText("Final Score: " + this.score, this.canvas.width / 2, this.canvas.height / 2 + 15);
      ctx.fillText("Tap [A] or [B] to Relaunch", this.canvas.width / 2, this.canvas.height / 2 + 50);
      ctx.textAlign = "left";
    }
  }
}

// ==============================================================================
// GAME 2: CYBER SNAKE NEON
// ==============================================================================
class CyberSnake {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.reset();
  }
  reset() {
    this.grid = 20;
    this.cols = Math.floor(this.canvas.width / this.grid);
    this.rows = Math.floor(this.canvas.height / this.grid);
    this.snake = [
      { x: 10, y: 10 },
      { x: 9, y: 10 },
      { x: 8, y: 10 }
    ];
    this.dir = { x: 1, y: 0 };
    this.nextDir = { x: 1, y: 0 };
    this.food = this.spawnFood();
    this.score = 0;
    this.gameOver = false;
    this.lastMove = 0;
    this.speed = 90; // ms per step
  }

  spawnFood() {
    return {
      x: Math.floor(Math.random() * (this.cols - 2)) + 1,
      y: Math.floor(Math.random() * (this.rows - 2)) + 1
    };
  }

  update(input, dt) {
    if (this.gameOver) {
      if (input.btnA || input.btnB) this.reset();
      return;
    }

    if (input.stickX > 0.4 && this.dir.x === 0) this.nextDir = { x: 1, y: 0 };
    else if (input.stickX < -0.4 && this.dir.x === 0) this.nextDir = { x: -1, y: 0 };
    else if (input.stickY > 0.4 && this.dir.y === 0) this.nextDir = { x: 0, y: 1 };
    else if (input.stickY < -0.4 && this.dir.y === 0) this.nextDir = { x: 0, y: -1 };

    const now = Date.now();
    const currentSpeed = input.btnA ? this.speed * 0.55 : this.speed;

    if (now - this.lastMove > currentSpeed) {
      this.dir = this.nextDir;
      const head = { x: this.snake[0].x + this.dir.x, y: this.snake[0].y + this.dir.y };

      // Wall collision
      if (head.x < 0 || head.x >= this.cols || head.y < 0 || head.y >= this.rows) {
        this.gameOver = true;
        sfx.playExplode();
        return;
      }

      // Self collision
      for (let s of this.snake) {
        if (s.x === head.x && s.y === head.y) {
          this.gameOver = true;
          sfx.playExplode();
          return;
        }
      }

      this.snake.unshift(head);

      // Food
      if (head.x === this.food.x && head.y === this.food.y) {
        this.score += 50;
        this.food = this.spawnFood();
        sfx.playCoin();
      } else {
        this.snake.pop();
      }
      this.lastMove = now;
    }
  }

  render() {
    const ctx = this.ctx;
    ctx.fillStyle = "#080b12";
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Food
    ctx.fillStyle = "#f59e0b";
    ctx.shadowColor = "#f59e0b";
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.arc(this.food.x * this.grid + this.grid / 2, this.food.y * this.grid + this.grid / 2, this.grid / 2 - 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;

    // Snake
    this.snake.forEach((seg, idx) => {
      ctx.fillStyle = idx === 0 ? "#34d399" : "#059669";
      ctx.shadowColor = "#34d399";
      ctx.shadowBlur = idx === 0 ? 10 : 4;
      ctx.fillRect(seg.x * this.grid + 1, seg.y * this.grid + 1, this.grid - 2, this.grid - 2);
    });
    ctx.shadowBlur = 0;

    // HUD
    ctx.fillStyle = "#f1f5f9";
    ctx.font = "bold 15px sans-serif";
    ctx.fillText("SCORE: " + this.score, 20, 30);
    ctx.fillStyle = "#94a3b8";
    ctx.fillText("[A] Turbo Boost", 20, 52);

    if (this.gameOver) {
      ctx.fillStyle = "rgba(0,0,0,0.8)";
      ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      ctx.fillStyle = "#ef4444";
      ctx.font = "bold 26px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("SYSTEM CRASHED", this.canvas.width / 2, this.canvas.height / 2 - 20);
      ctx.fillStyle = "#fff";
      ctx.font = "16px sans-serif";
      ctx.fillText("Score: " + this.score, this.canvas.width / 2, this.canvas.height / 2 + 15);
      ctx.fillText("Tap [A] to Restart", this.canvas.width / 2, this.canvas.height / 2 + 45);
      ctx.textAlign = "left";
    }
  }
}

// ==============================================================================
// GAME 3: FOX HORIZON RUNNER
// ==============================================================================
class FoxRunner {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.reset();
  }
  reset() {
    this.floorY = this.canvas.height - 70;
    this.fox = { x: 70, y: this.floorY - 30, vy: 0, jumps: 0, width: 28, height: 28 };
    this.gravity = 0.7;
    this.obstacles = [];
    this.coins = [];
    this.score = 0;
    this.speed = 5;
    this.gameOver = false;
    this.lastSpawn = 0;
  }

  update(input, dt) {
    if (this.gameOver) {
      if (input.btnA || input.btnB) this.reset();
      return;
    }

    // Jump logic
    if (input.btnA_pressed && this.fox.jumps < 2) {
      this.fox.vy = -12;
      this.fox.jumps++;
      sfx.playLaser();
    }

    // Physics
    this.fox.vy += this.gravity;
    this.fox.y += this.fox.vy;

    if (this.fox.y >= this.floorY - this.fox.height) {
      this.fox.y = this.floorY - this.fox.height;
      this.fox.vy = 0;
      this.fox.jumps = 0;
    }

    // Spawn Obstacles & Coins
    const now = Date.now();
    if (now - this.lastSpawn > 1400) {
      this.obstacles.push({
        x: this.canvas.width + 20,
        y: this.floorY - 32,
        w: 22, h: 32
      });
      if (Math.random() > 0.4) {
        this.coins.push({
          x: this.canvas.width + 120,
          y: this.floorY - 70 - Math.random() * 40,
          size: 8
        });
      }
      this.lastSpawn = now;
      this.score += 10;
    }

    // Move Obstacles
    for (let i = this.obstacles.length - 1; i >= 0; i--) {
      const o = this.obstacles[i];
      o.x -= this.speed;

      // Collision
      if (
        this.fox.x < o.x + o.w &&
        this.fox.x + this.fox.width > o.x &&
        this.fox.y < o.y + o.h &&
        this.fox.y + this.fox.height > o.y
      ) {
        this.gameOver = true;
        sfx.playExplode();
      }
    }
    this.obstacles = this.obstacles.filter(o => o.x > -40);

    // Coins
    for (let i = this.coins.length - 1; i >= 0; i--) {
      const c = this.coins[i];
      c.x -= this.speed;
      if (Math.hypot(this.fox.x - c.x, this.fox.y - c.y) < 30) {
        this.score += 50;
        sfx.playCoin();
        this.coins.splice(i, 1);
      }
    }
    this.coins = this.coins.filter(c => c.x > -20);
  }

  render() {
    const ctx = this.ctx;
    ctx.fillStyle = "#0c0d14";
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Floor
    ctx.strokeStyle = "#ff7a00";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(0, this.floorY);
    ctx.lineTo(this.canvas.width, this.floorY);
    ctx.stroke();

    // Floor grid
    ctx.fillStyle = "#161925";
    ctx.fillRect(0, this.floorY + 2, this.canvas.width, this.canvas.height - this.floorY);

    // Obstacles (Neon Spikes)
    ctx.fillStyle = "#ef4444";
    ctx.shadowColor = "#ef4444";
    ctx.shadowBlur = 10;
    this.obstacles.forEach(o => {
      ctx.beginPath();
      ctx.moveTo(o.x, o.y + o.h);
      ctx.lineTo(o.x + o.w / 2, o.y);
      ctx.lineTo(o.x + o.w, o.y + o.h);
      ctx.closePath();
      ctx.fill();
    });

    // Coins
    ctx.fillStyle = "#38bdf8";
    ctx.shadowColor = "#38bdf8";
    ctx.shadowBlur = 8;
    this.coins.forEach(c => {
      ctx.beginPath();
      ctx.arc(c.x, c.y, c.size, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.shadowBlur = 0;

    // Fox Character
    ctx.save();
    ctx.translate(this.fox.x, this.fox.y);
    ctx.fillStyle = "#ff7a00";
    ctx.shadowColor = "#ff7a00";
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.roundRect(0, 0, this.fox.width, this.fox.height, 6);
    ctx.fill();
    // Fox Ears
    ctx.fillStyle = "#fff";
    ctx.beginPath();
    ctx.moveTo(4, 0); ctx.lineTo(8, -8); ctx.lineTo(12, 0); ctx.fill();
    ctx.moveTo(16, 0); ctx.lineTo(20, -8); ctx.lineTo(24, 0); ctx.fill();
    ctx.restore();

    // HUD
    ctx.fillStyle = "#f1f5f9";
    ctx.font = "bold 15px sans-serif";
    ctx.fillText("SCORE: " + this.score, 20, 30);
    ctx.fillText("[A] Jump / Double Jump", 20, 52);

    if (this.gameOver) {
      ctx.fillStyle = "rgba(0,0,0,0.8)";
      ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      ctx.fillStyle = "#ff7a00";
      ctx.font = "bold 26px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("RUN ENDED", this.canvas.width / 2, this.canvas.height / 2 - 20);
      ctx.fillStyle = "#fff";
      ctx.font = "16px sans-serif";
      ctx.fillText("Score: " + this.score, this.canvas.width / 2, this.canvas.height / 2 + 15);
      ctx.fillText("Tap [A] to Run Again", this.canvas.width / 2, this.canvas.height / 2 + 45);
      ctx.textAlign = "left";
    }
  }
}

// ==============================================================================
// GAME 4: CYBER PONG 2.0
// ==============================================================================
class CyberPong {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.reset();
  }
  reset() {
    this.paddleH = 70;
    this.paddleW = 12;
    this.player = { y: this.canvas.height / 2 - this.paddleH / 2, score: 0 };
    this.ai = { y: this.canvas.height / 2 - this.paddleH / 2, score: 0, speed: 4 };
    this.ball = {
      x: this.canvas.width / 2,
      y: this.canvas.height / 2,
      vx: 6,
      vy: 3,
      r: 7
    };
  }

  update(input, dt) {
    // Player Paddle
    if (input.stickY !== 0) {
      this.player.y += input.stickY * 7;
    }
    this.player.y = Math.max(10, Math.min(this.canvas.height - this.paddleH - 10, this.player.y));

    // AI Paddle Tracking
    const aiCenter = this.ai.y + this.paddleH / 2;
    if (this.ball.x > this.canvas.width * 0.4) {
      if (aiCenter < this.ball.y - 10) this.ai.y += this.ai.speed;
      else if (aiCenter > this.ball.y + 10) this.ai.y -= this.ai.speed;
    }
    this.ai.y = Math.max(10, Math.min(this.canvas.height - this.paddleH - 10, this.ai.y));

    // Ball movement
    this.ball.x += this.ball.vx;
    this.ball.y += this.ball.vy;

    // Top/Bottom bounce
    if (this.ball.y - this.ball.r < 0 || this.ball.y + this.ball.r > this.canvas.height) {
      this.ball.vy = -this.ball.vy;
      sfx.playLaser();
    }

    // Player bounce
    if (
      this.ball.x - this.ball.r < 30 + this.paddleW &&
      this.ball.y > this.player.y &&
      this.ball.y < this.player.y + this.paddleH
    ) {
      this.ball.vx = Math.abs(this.ball.vx) * 1.05;
      const offset = (this.ball.y - (this.player.y + this.paddleH / 2)) / (this.paddleH / 2);
      this.ball.vy = offset * 6;
      sfx.playLaser();
    }

    // AI bounce
    if (
      this.ball.x + this.ball.r > this.canvas.width - 30 - this.paddleW &&
      this.ball.y > this.ai.y &&
      this.ball.y < this.ai.y + this.paddleH
    ) {
      this.ball.vx = -Math.abs(this.ball.vx) * 1.05;
      const offset = (this.ball.y - (this.ai.y + this.paddleH / 2)) / (this.paddleH / 2);
      this.ball.vy = offset * 6;
      sfx.playLaser();
    }

    // Score checks
    if (this.ball.x < -10) {
      this.ai.score++;
      sfx.playExplode();
      this.resetBall(-1);
    } else if (this.ball.x > this.canvas.width + 10) {
      this.player.score++;
      sfx.playCoin();
      this.resetBall(1);
    }
  }

  resetBall(dir) {
    this.ball.x = this.canvas.width / 2;
    this.ball.y = this.canvas.height / 2;
    this.ball.vx = dir * 6;
    this.ball.vy = (Math.random() - 0.5) * 6;
  }

  render() {
    const ctx = this.ctx;
    ctx.fillStyle = "#080b12";
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Net line
    ctx.strokeStyle = "rgba(255,255,255,0.1)";
    ctx.setLineDash([6, 6]);
    ctx.beginPath();
    ctx.moveTo(this.canvas.width / 2, 0);
    ctx.lineTo(this.canvas.width / 2, this.canvas.height);
    ctx.stroke();
    ctx.setLineDash([]);

    // Player Paddle
    ctx.fillStyle = "#ff7a00";
    ctx.shadowColor = "#ff7a00";
    ctx.shadowBlur = 10;
    ctx.fillRect(30, this.player.y, this.paddleW, this.paddleH);

    // AI Paddle
    ctx.fillStyle = "#38bdf8";
    ctx.shadowColor = "#38bdf8";
    ctx.shadowBlur = 10;
    ctx.fillRect(this.canvas.width - 30 - this.paddleW, this.ai.y, this.paddleW, this.paddleH);

    // Ball
    ctx.fillStyle = "#fff";
    ctx.shadowColor = "#fff";
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.arc(this.ball.x, this.ball.y, this.ball.r, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;

    // Scores
    ctx.font = "bold 32px sans-serif";
    ctx.fillStyle = "rgba(255, 122, 0, 0.4)";
    ctx.fillText(this.player.score, this.canvas.width / 2 - 60, 50);
    ctx.fillStyle = "rgba(56, 189, 248, 0.4)";
    ctx.fillText(this.ai.score, this.canvas.width / 2 + 40, 50);
  }
}
