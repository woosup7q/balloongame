const express = require('express');
const http    = require('http');
const { Server } = require('socket.io');
const path    = require('path');

const app    = express();
const server = http.createServer(app);
const io     = new Server(server);

app.use(express.static(path.join(__dirname)));

// ===== 방 목록 =====
const rooms = {};
// { code: { players:[id,...], diff, scores:{}, name } }

// ===== 리더보드 (서버 저장) =====
const leaderboard = [];  // { name, score, world, level, diff, date }
const MAX_LB = 20;

function makeCode() {
  return Math.random().toString(36).substring(2,6).toUpperCase();
}

function broadcastRooms() {
  const list = Object.entries(rooms)
    .filter(([,r]) => r.players.length < 2)
    .map(([code, r]) => ({ code, diff: r.diff, name: r.name }));
  io.emit('roomsUpdate', list);
}

io.on('connection', (socket) => {
  console.log('접속:', socket.id);

  // ===== 방 만들기 =====
  socket.on('createRoom', ({ diff, name }) => {
    const code = makeCode();
    rooms[code] = {
      players: [socket.id],
      diff,
      name: name || `${diff.toUpperCase()} 방`,
      scores: { [socket.id]: 0 },
    };
    socket.join(code);
    socket.roomCode = code;
    socket.playerNum = 1;
    socket.emit('roomCreated', { code, playerNum: 1 });
    broadcastRooms();
    console.log(`방 생성: ${code} (${diff})`);
  });

  // ===== 방 목록 요청 =====
  socket.on('getRooms', () => {
    const list = Object.entries(rooms)
      .filter(([,r]) => r.players.length < 2)
      .map(([code, r]) => ({ code, diff: r.diff, name: r.name }));
    socket.emit('roomsUpdate', list);
  });

  // ===== 방 입장 =====
  socket.on('joinRoom', (code) => {
    const room = rooms[code];
    if (!room)               { socket.emit('joinError', '방을 찾을 수 없어!'); return; }
    if (room.players.length >= 2) { socket.emit('joinError', '방이 꽉 찼어!');     return; }
    room.players.push(socket.id);
    room.scores[socket.id] = 0;
    socket.join(code);
    socket.roomCode  = code;
    socket.playerNum = 2;
    socket.emit('joinedRoom', { code, playerNum: 2, diff: room.diff });
    io.to(code).emit('gameStart', { diff: room.diff });
    broadcastRooms();
    console.log(`방 입장: ${code}`);
  });

  // ===== 게임 화면 상태 전달 =====
  socket.on('stateUpdate', (state) => {
    const code = socket.roomCode;
    if (!code || !rooms[code]) return;
    socket.to(code).emit('opponentState', state);
  });

  // ===== 점수 업데이트 =====
  socket.on('scoreUpdate', (score) => {
    const code = socket.roomCode;
    if (!code || !rooms[code]) return;
    rooms[code].scores[socket.id] = score;
    socket.to(code).emit('opponentScore', score);
  });

  // ===== 게임 끝 =====
  socket.on('gameOver', () => {
    const code = socket.roomCode;
    if (!code || !rooms[code]) return;
    const room   = rooms[code];
    const scores = room.players.map(id => room.scores[id] || 0);
    io.to(code).emit('matchResult', {
      scores,
      winner: scores[0] > scores[1] ? 1 : scores[1] > scores[0] ? 2 : 0,
    });
  });

  // ===== 점수 저장 (싱글 & 멀티 공통) =====
  socket.on('saveScore', ({ playerName, score, world, level, diff }) => {
    leaderboard.push({
      name:  playerName || '익명',
      score, world, level, diff,
      date:  new Date().toLocaleDateString('ko-KR'),
    });
    leaderboard.sort((a, b) => b.score - a.score);
    if (leaderboard.length > MAX_LB) leaderboard.length = MAX_LB;
    io.emit('leaderboardUpdate', leaderboard);
    console.log(`점수 저장: ${playerName} ${score}pts`);
  });

  // ===== 리더보드 요청 =====
  socket.on('getLeaderboard', () => {
    socket.emit('leaderboardUpdate', leaderboard);
  });

  // ===== 연결 끊김 =====
  socket.on('disconnect', () => {
    const code = socket.roomCode;
    if (code && rooms[code]) {
      socket.to(code).emit('opponentLeft');
      delete rooms[code];
      broadcastRooms();
    }
    console.log('퇴장:', socket.id);
  });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`서버 켜짐! 포트: ${PORT}`);
});
