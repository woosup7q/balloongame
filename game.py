import pygame
import sys
import random
import math
import array
import json
import os

# sound must be set up BEFORE pygame.init()
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("🎈 Balloon Game")

# --- Colors ---
WHITE  = (255, 255, 255)
BLACK  = (0, 0, 0)
BROWN  = (101, 67, 33)
GRAY   = (200, 200, 200)
BLUE   = (30, 144, 255)
GREEN  = (50, 205, 50)
YELLOW = (255, 215, 0)
ORANGE = (255, 140, 0)
RED    = (220, 20, 60)
SILVER = (192, 192, 192)
PURPLE = (148, 0, 211)
GOLD   = (255, 200, 0)
DARK   = (30, 30, 30)
CYAN   = (0, 220, 255)

# =================== SOUND GENERATION ===================

def _tone(freq, dur, vol=0.25, wave='square', sr=44100):
    n   = int(sr * dur)
    buf = array.array('h')
    for i in range(n):
        t    = i / sr
        fade = min(1.0, (n - i) / max(1, sr * 0.008))
        if wave == 'square':
            raw = 1.0 if math.sin(2*math.pi*freq*t) >= 0 else -1.0
        elif wave == 'sine':
            raw = math.sin(2*math.pi*freq*t)
        else:
            raw = random.uniform(-1, 1)
        buf.append(int(raw * vol * fade * 32767))
    return buf

def make_pop_sound():
    sr  = 44100
    n   = int(sr * 0.09)
    buf = array.array('h')
    for i in range(n):
        fade = 1 - i/n
        buf.append(int(random.uniform(-1,1) * 0.45 * fade * 32767))
    return pygame.mixer.Sound(buffer=buf)

def make_shoot_sound():
    sr  = 44100
    n   = int(sr * 0.08)
    buf = array.array('h')
    for i in range(n):
        t    = i / sr
        freq = max(80, 700 - i * 5)
        fade = 1 - i/n
        buf.append(int(math.sin(2*math.pi*freq*t) * 0.25 * fade * 32767))
    return pygame.mixer.Sound(buffer=buf)

def make_boss_hit_sound():
    buf = array.array('h')
    buf.extend(_tone(120, 0.18, 0.4, 'sine'))
    return pygame.mixer.Sound(buffer=buf)

def make_level_clear_sound():
    buf = array.array('h')
    for f, d in [(523,0.1),(659,0.1),(784,0.1),(1047,0.25)]:
        buf.extend(_tone(f, d, 0.3, 'square'))
    return pygame.mixer.Sound(buffer=buf)

def make_bgm():
    # upbeat 8-bit melody — World 1 & 3 theme
    melody = [
        (784,0.15),(659,0.15),(523,0.15),(659,0.15),
        (784,0.3 ),(784,0.15),(784,0.15),
        (880,0.15),(784,0.15),(698,0.15),(784,0.15),
        (880,0.3 ),(880,0.3 ),
        (784,0.15),(698,0.15),(659,0.15),(698,0.15),
        (784,0.3 ),(659,0.3 ),
        (587,0.15),(659,0.15),(698,0.15),(659,0.15),
        (587,0.3 ),(523,0.45),
    ]
    buf = array.array('h')
    for freq, dur in melody:
        buf.extend(_tone(freq, dur, 0.18, 'square'))
    return pygame.mixer.Sound(buffer=buf)

def make_bgm2():
    # mysterious/sunset melody — World 2 & 4 theme
    melody = [
        (392,0.2),(370,0.2),(330,0.2),(294,0.4),
        (330,0.2),(370,0.2),(392,0.4),(392,0.2),
        (440,0.2),(494,0.2),(523,0.4),(494,0.2),
        (440,0.2),(392,0.4),(370,0.4),
        (330,0.2),(294,0.2),(262,0.4),(247,0.4),
        (262,0.2),(294,0.2),(330,0.6),(294,0.6),
    ]
    buf = array.array('h')
    for freq, dur in melody:
        buf.extend(_tone(freq, dur, 0.16, 'square'))
    return pygame.mixer.Sound(buffer=buf)

def make_bgm3():
    # cosmic/deep-sea melody — World 5 theme
    melody = [
        (220,0.3),(247,0.15),(220,0.15),(196,0.3),(220,0.6),
        (247,0.3),(277,0.15),(247,0.15),(220,0.3),(247,0.6),
        (294,0.3),(330,0.15),(294,0.15),(262,0.3),(294,0.6),
        (277,0.3),(247,0.15),(220,0.15),(196,0.6),(165,0.6),
        (196,0.3),(220,0.3),(247,0.3),(294,0.6),(262,0.6),
    ]
    buf = array.array('h')
    for freq, dur in melody:
        buf.extend(_tone(freq, dur, 0.20, 'square'))
    return pygame.mixer.Sound(buffer=buf)

# generate sounds
snd_pop         = make_pop_sound()
snd_shoot       = make_shoot_sound()
snd_boss_hit    = make_boss_hit_sound()
snd_level_clear = make_level_clear_sound()
bgm1            = make_bgm()
bgm2            = make_bgm2()
bgm3            = make_bgm3()
bgm_list        = [bgm1, bgm2, bgm3, bgm2, bgm3]  # one per world theme (cycles)
bgm_channel     = pygame.mixer.Channel(0)
bgm_channel.play(bgm1, loops=-1)
bgm_channel.set_volume(0.4)

# =================== HIGH SCORE ===================

HIGHSCORE_FILE = os.path.join(os.path.dirname(__file__), "highscore.json")

def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"level": 1, "world": 1, "score": 0}

def save_highscore(level, world, score):
    data = load_highscore()
    changed = False
    if world > data["world"] or (world == data["world"] and level > data["level"]):
        data["level"] = level
        data["world"] = world
        changed = True
    if score > data["score"]:
        data["score"] = score
        changed = True
    if changed:
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump(data, f)

highscore = load_highscore()

# =================== WORLD THEMES ===================

WORLD_THEMES = [
    # (sky_top, sky_bottom, ground, cloud_color, name)
    ((100,180,255), (180,230,255), (34,139,34),   (255,255,255), "World 1"),
    ((255,120,40),  (255,200,100), (139,90,30),   (255,180,120), "World 2: Sunset"),
    ((15, 15, 50),  (40, 40, 100), (20,60,20),    (100,100,140), "World 3: Night"),
    ((5,  5,  20),  (20, 0,  60),  (40,40,40),    (80, 60, 140), "World 4: Space"),
    ((0,  80, 60),  (0,  160,120), (20,80,60),    (100,220,180), "World 5: Deep Sea"),
]

def get_theme(world):
    return WORLD_THEMES[(world - 1) % len(WORLD_THEMES)]

# =================== CLOUDS ===================

clouds = [{"x": random.randint(0, SCREEN_WIDTH),
           "y": random.randint(40, 200),
           "w": random.randint(80, 160),
           "h": random.randint(30, 55),
           "spd": random.uniform(0.2, 0.5)} for _ in range(6)]

def update_clouds():
    for c in clouds:
        c["x"] += c["spd"]
        if c["x"] > SCREEN_WIDTH + c["w"]:
            c["x"] = -c["w"]
            c["y"] = random.randint(40, 200)

def draw_background(surface, world):
    theme = get_theme(world)
    sky_t, sky_b, gnd, cld_col, _ = theme

    # sky gradient (draw horizontal strips)
    for row in range(SCREEN_HEIGHT - 40):
        t   = row / (SCREEN_HEIGHT - 40)
        r   = int(sky_t[0] + (sky_b[0]-sky_t[0]) * t)
        g   = int(sky_t[1] + (sky_b[1]-sky_t[1]) * t)
        b   = int(sky_t[2] + (sky_b[2]-sky_t[2]) * t)
        pygame.draw.line(surface, (r,g,b), (0, row), (SCREEN_WIDTH, row))

    # stars for night/space worlds
    if world in (3, 4):
        random.seed(42)
        for _ in range(80):
            sx = random.randint(0, SCREEN_WIDTH)
            sy = random.randint(0, SCREEN_HEIGHT - 80)
            pygame.draw.circle(surface, WHITE, (sx, sy), 1)
        random.seed()  # restore randomness

    # clouds
    for c in clouds:
        pygame.draw.ellipse(surface, cld_col, (int(c["x"]), int(c["y"]), c["w"], c["h"]))
        pygame.draw.ellipse(surface, cld_col, (int(c["x"])+15, int(c["y"])-12, c["w"]-20, c["h"]))

    # ground strip
    pygame.draw.rect(surface, gnd, (0, SCREEN_HEIGHT-40, SCREEN_WIDTH, 40))
    darker = tuple(max(0, v-30) for v in gnd)
    pygame.draw.rect(surface, darker, (0, SCREEN_HEIGHT-40, SCREEN_WIDTH, 5))

# =================== DIFFICULTY ===================

DIFFICULTIES = {
    "easy": {
        "label": "EASY", "color": (60, 220, 100), "btn": (30, 140, 55),
        "speed": 0.65, "time_mult": 1.5, "score_mult": 0.6, "start_arrows": 20,
        "cost_mult": 0.4, "boss_hp_mult": 0.5,
        "desc": ["Balloons move slowly", "50% more time per level",
                 "Shop prices 60% OFF!", "Weaker bosses"],
    },
    "normal": {
        "label": "NORMAL", "color": (80, 160, 255), "btn": (30, 90, 190),
        "speed": 1.0, "time_mult": 1.0, "score_mult": 1.0, "start_arrows": 10,
        "cost_mult": 1.0, "boss_hp_mult": 1.0,
        "desc": ["Standard balloon speed", "Normal time limits",
                 "Normal shop prices", "Standard bosses"],
    },
    "hard": {
        "label": "HARD", "color": (255, 80, 60), "btn": (170, 25, 20),
        "speed": 1.5, "time_mult": 0.65, "score_mult": 1.4, "start_arrows": 5,
        "cost_mult": 2.0, "boss_hp_mult": 2.0,
        "desc": ["Balloons move fast!", "35% less time per level",
                 "Shop prices DOUBLED!", "Tougher bosses"],
    },
}

# active difficulty — updated when player picks one on the menu
diff_settings = DIFFICULTIES["normal"]

# =================== LEVEL HELPERS ===================

def get_target_score(level, world):
    base = 30 + (level - 1) * 10
    return int(base * (1 + (world - 1) * 0.5) * diff_settings["score_mult"])

def get_time_limit(level):
    base = max(60 - ((level - 1) // 10) * 10, 20)
    return int(base * diff_settings["time_mult"])

def get_speed_multiplier(world):
    return (1.0 + (world - 1) * 0.3) * diff_settings["speed"]

# =================== BALLOON DATA ===================

BASE_BALLOONS = [
    {"color": (30,144,255),  "points": 1,  "speed": 1.5, "pattern": "straight", "weight": 10},
    {"color": (50,205,50),   "points": 3,  "speed": 2.0, "pattern": "straight", "weight": 8},
    {"color": (255,215,0),   "points": 5,  "speed": 2.5, "pattern": "zigzag",   "weight": 6},
    {"color": (255,140,0),   "points": 7,  "speed": 3.0, "pattern": "zigzag",   "weight": 5},
    {"color": (220,20,60),   "points": 10, "speed": 3.5, "pattern": "zigzag",   "weight": 4},
    {"color": (192,192,192), "points": 15, "speed": 4.0, "pattern": "circle",   "weight": 2},
    {"color": (148,0,211),   "points": 20, "speed": 4.5, "pattern": "circle",   "weight": 1},
]

LUCKY_WEIGHTS = [
    [10, 8, 6, 5, 4, 2, 1],   # 0  not bought
    [9,  8, 6, 5, 5, 3, 2],   # 1
    [8,  7, 6, 5, 5, 4, 2],   # 2
    [7,  7, 6, 6, 5, 4, 3],   # 3
    [6,  6, 6, 5, 5, 4, 3],   # 4
    [5,  5, 5, 5, 5, 5, 4],   # 5
    [4,  4, 5, 5, 5, 5, 4],   # 6
    [3,  4, 4, 4, 5, 5, 5],   # 7
    [2,  3, 4, 4, 4, 5, 6],   # 8
    [2,  2, 3, 4, 4, 5, 7],   # 9
    [1,  1, 2, 3, 4, 5, 10],  # 10
    [1,  1, 2, 2, 4, 5, 12],  # 11
    [1,  1, 1, 2, 3, 5, 14],  # 12
    [1,  1, 1, 2, 3, 4, 15],  # 13
    [1,  1, 1, 1, 3, 4, 16],  # 14
    [1,  1, 1, 1, 2, 4, 17],  # 15
    [1,  1, 1, 1, 2, 4, 18],  # 16
    [1,  1, 1, 1, 2, 3, 18],  # 17
    [1,  1, 1, 1, 1, 3, 18],  # 18
    [1,  1, 1, 1, 1, 3, 20],  # 19
    [1,  1, 1, 1, 1, 2, 20],  # 20
    [1,  1, 1, 1, 1, 2, 25],  # 21
    [1,  1, 1, 1, 1, 2, 30],  # 22
    [1,  1, 1, 1, 1, 1, 30],  # 23
    [1,  1, 1, 1, 1, 1, 35],  # 24
    [1,  1, 1, 1, 1, 1, 40],  # 25
    [1,  1, 1, 1, 1, 1, 50],  # 26
    [1,  1, 1, 1, 1, 1, 60],  # 27
    [1,  1, 1, 1, 1, 1, 75],  # 28
    [1,  1, 1, 1, 1, 1, 90],  # 29
    [1,  1, 1, 1, 1, 1, 100], # 30  PURPLE OMEGA
]

def pick_balloon_type(lucky_lvl):
    weights = LUCKY_WEIGHTS[min(lucky_lvl, 30)]
    total   = sum(weights)
    r       = random.randint(0, total - 1)
    cumul   = 0
    for i, w in enumerate(weights):
        cumul += w
        if r < cumul:
            return BASE_BALLOONS[i]
    return BASE_BALLOONS[-1]

# =================== MOD TABLES ===================

# All tables: index 0 = not bought, indices 1-30 = level 1-30
FREEZE_TIMES = [
    0,  3,   5,    7,    9,   12,   16,   21,   27,   35,   60,
    75, 90, 110,  135,  165,  205,  250,  310,  385,  480,
    600, 750, 940, 1175, 1470, 1840, 2300, 2880, 3600, 9999,
]
SLOW_FACTORS = [
    1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05,
    0.04, 0.035, 0.03, 0.025, 0.02, 0.016, 0.012, 0.009, 0.007, 0.005,
    0.004, 0.003, 0.002, 0.0015, 0.001, 0.0008, 0.0005, 0.0003, 0.0001, 0.00001,
]
EXPLOSIVE_RADII = [
    0,  40,  60,   80,  100,  130,  165,  205,  250,  310,  400,
    470, 550, 640,  750,  875, 1020, 1190, 1390, 1620, 1890,
    2200, 2560, 2990, 3490, 4070, 4750, 5545, 6470, 7550, 10000,
]
LIGHTNING_CHAINS = [
    0, 1, 2, 3, 4, 5, 6, 8, 10, 13, 999,
    999, 999, 999, 999, 999, 999, 999, 999, 999, 999,
    999, 999, 999, 999, 999, 999, 999, 999, 999, 999,
]
HOMING_STRENGTHS = [
    0,   1,   2,   3,   4,   5,   7,   9,  12,  16,  22,
    28,  36,  46,  59,  76,  97, 124, 159, 204, 261,
    334, 428, 548, 702, 899, 1151, 1473, 1886, 2415, 3090,
]
RICOCHET_BOUNCES = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 20,
    25, 30, 35, 40, 45, 50, 60, 70, 80, 90,
    100, 120, 140, 160, 180, 200, 250, 300, 400, 999,
]
DOUBLE_MULTIPLIERS = [
    1,  2,  3,   4,   5,   6,   8,  10,  15,  20,   30,
    40, 55, 75, 100, 135, 185, 250, 340, 460,  620,
    840, 1140, 1540, 2090, 2825, 3820, 5175, 7000, 9500, 12800,
]
BOOMERANG_RETURNS = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
    12, 14, 17, 20, 24, 28, 33, 39, 46, 54,
    64, 75, 88, 103, 121, 142, 166, 195, 228, 300,
]
MAGNET_STRENGTHS = [
    0, 0.5, 1.0, 1.8, 2.8, 4.0, 5.5, 7.5, 10.0, 14.0, 20.0,
    27, 36, 49, 66, 89, 120, 162, 219, 296, 400,
    540, 729, 985, 1330, 1796, 2425, 3274, 4420, 5967, 8000,
]
ARROW_CAPACITY = [
    10, 20, 30, 45, 65, 90, 120, 160, 220, 300, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
]
EAGLE_EYE_STEPS = [
    0,  15,  25,  38,  55,  75, 100, 130, 170, 220, 300,
    350, 400, 450, 500, 550, 600, 650, 700, 750, 800,
    850, 900, 950, 1000, 1000, 1000, 1000, 1000, 1000, 1000,
]
MULTISHOT_COUNTS = [
    1,   3,   5,   7,  10,  15,  20,  25,  30,  40,   50,
    60,  70,  80,  90, 100, 120, 150, 200, 250, 300,
    350, 400, 500, 600, 700, 800, 1000, 1500, 2000, 5000,
]
PIERCING_COUNTS = [
    0, 1, 2, 4, 6, 9, 13, 18, 25, 35, 999,
    999, 999, 999, 999, 999, 999, 999, 999, 999, 999,
    999, 999, 999, 999, 999, 999, 999, 999, 999, 999,
]

_T1 = [20,35,55,80,110,150,200,260,335,425,
       545,700,900,1160,1490,1915,2460,3160,4060,5215,
       6705,8615,11065,14220,18275,23480,30175,38775,49825,64045]
_T2 = [30,55,85,125,175,240,320,415,535,685,
       880,1130,1455,1870,2400,3085,3965,5095,6545,8410,
       10810,13890,17850,22935,29470,37870,48675,62545,80370,103280]
_TI = [30,50,75,110,155,215,290,385,505,655,
       880,1130,1455,1870,2400,3085,3965,5095,6545,8410,
       10810,13890,17850,22935,29470,37870,48675,62545,80370,103280]
_TF = [25,45,70,100,140,190,250,325,420,540,
       695,890,1145,1475,1895,2430,3125,4015,5160,6630,
       8520,10950,14070,18080,23235,29855,38385,49325,63385,81450]
_TE = [40,70,110,160,225,305,405,530,685,880,
       1130,1455,1870,2400,3085,3965,5095,6545,8410,10810,
       13890,17850,22940,29475,37875,48670,62540,80365,103270,132705]
_TL = [35,65,100,145,205,280,375,490,635,815,
       1045,1345,1730,2220,2855,3670,4715,6060,7790,10010,
       12865,16530,21240,27295,35075,45070,57915,74420,95625,122880]
_TEE= [15,28,45,65,90,125,170,225,295,385,
       495,635,815,1050,1350,1735,2230,2865,3680,4730,
       6075,7810,10035,12895,16570,21290,27360,35165,45190,58065]
_TDP= [40,75,120,180,255,350,470,620,810,1050,
       1350,1735,2230,2865,3680,4730,6080,7810,10035,12895,
       16570,21295,27365,35165,45185,58065,74610,95875,123200,158320]

_PRESTIGE = ["(Elite)","(Elite+)","(Epic)","(Epic+)","(Rare+)",
             "(Legend)","(Legend+)","(Myth)","(Myth+)","(Divine)",
             "(Divine+)","(Ancient)","(Cosmic)","(Cosmos+)","(Celest.)",
             "(Celest+)","(Supreme)","(Supr+)","(SUPREME+)","OMEGA"]

SHOP_ITEMS = [
    {"id": "multishot", "name": "Multishot", "cost": _T1,
     "desc": [
         "3 arrows","5 arrows","7 arrows","10 arrows","15 arrows",
         "20 arrows","25 arrows","30 arrows","40 arrows","50 arrows",
         "60 arrows","70 arrows","80 arrows","90 arrows","100 arrows",
         "120 arrows","150 arrows","200 arrows","250 arrows","300 arrows",
         "350 arrows","400 arrows","500 arrows","600 arrows","700 arrows",
         "800 arrows","1000 arrows","1500 arrows","2000 arrows","5000 arrows",
     ]},
    {"id": "piercing", "name": "Piercing", "cost": _T1,
     "desc": [
         "Through 2","Through 3","Through 5","Through 7","Through 10",
         "Through 14","Through 19","Through 26","Through 36","ALL balloons",
         *[f"ALL {p}" for p in _PRESTIGE],
     ]},
    {"id": "infinite", "name": "Inf.Arrows", "cost": _TI,
     "desc": [
         "+10 arrows","+20 arrows","+35 arrows","+55 arrows","+80 arrows",
         "+110 arrows","+150 arrows","+210 arrows","+290 arrows","UNLIMITED!",
         *[f"∞ {p}" for p in _PRESTIGE],
     ]},
    {"id": "freezer", "name": "Freezer", "cost": _TF,
     "desc": [
         "3 sec","5 sec","7 sec","9 sec","12 sec",
         "16 sec","21 sec","27 sec","35 sec","60 sec",
         "75 sec","90 sec","110 sec","2.3 min","2.8 min",
         "3.4 min","4.2 min","5 min","6.5 min","8 min",
         "10 min","12.5 min","15 min","20 min","25 min",
         "30 min","38 min","48 min","60 min","∞ freeze!",
     ]},
    {"id": "explosive", "name": "Explosive", "cost": _TE,
     "desc": [
         "Radius 40","Radius 60","Radius 80","Radius 100","Radius 130",
         "Radius 165","Radius 205","Radius 250","Radius 310","Radius 400",
         "Radius 470","Radius 550","Radius 640","Radius 750","Radius 875",
         "Radius 1020","Radius 1190","Radius 1390","Radius 1620","Radius 1890",
         "Radius 2200","Radius 2560","Radius 2990","Radius 3490","Radius 4070",
         "Radius 4750","Radius 5545","Radius 6470","Radius 7550","MEGA BOOM!",
     ]},
    {"id": "lightning", "name": "Lightning", "cost": _TL,
     "desc": [
         "Chain 1","Chain 2","Chain 3","Chain 4","Chain 5",
         "Chain 6","Chain 8","Chain 10","Chain 13","Chain ALL",
         *[f"ALL {p}" for p in _PRESTIGE[:-1]], "THUNDERGOD",
     ]},
    {"id": "boomerang", "name": "Boomerang", "cost": _T2,
     "desc": [
         "1 return","2 returns","3 returns","4 returns","5 returns",
         "6 returns","7 returns","8 returns","9 returns","10 returns",
         "12 returns","14 returns","17 returns","20 returns","24 returns",
         "28 returns","33 returns","39 returns","46 returns","54 returns",
         "64 returns","75 returns","88 returns","103 returns","121 returns",
         "142 returns","166 returns","195 returns","228 returns","300 returns",
     ]},
    {"id": "magnet", "name": "Magnet", "cost": _T1,
     "desc": [
         "Tiny pull","Weak pull","Light pull","Pull x2.8","Pull x4",
         "Pull x5.5","Pull x7.5","Pull x10","Pull x14","Pull x20",
         "Pull x27","Pull x36","Pull x49","Pull x66","Pull x89",
         "Pull x120","Pull x162","Pull x219","Pull x296","Pull x400",
         "Pull x540","Pull x729","Pull x985","Pull x1330","Pull x1796",
         "Pull x2425","Pull x3274","Pull x4420","Pull x5967","Pull x8000",
     ]},
    {"id": "slow", "name": "Slow", "cost": _T1,
     "desc": [
         "10% slow","20% slow","30% slow","40% slow","50% slow",
         "60% slow","70% slow","80% slow","90% slow","95% slow",
         "96% slow","96.5% slow","97% slow","97.5% slow","98% slow",
         "98.4% slow","98.8% slow","99% slow","99.3% slow","99.5% slow",
         "99.6% slow","99.7% slow","99.8% slow","99.85% slow","99.9% slow",
         "99.92% slow","99.95% slow","99.97% slow","99.99% slow","99.999% slow",
     ]},
    {"id": "eagleeye", "name": "Eagle Eye", "cost": _TEE,
     "desc": [
         "15 steps","25 steps","38 steps","55 steps","75 steps",
         "100 steps","130 steps","170 steps","220 steps","Full path",
         "Full+350","Full+400","Full+450","Full+500","Full+550",
         "Full+600","Full+650","Full+700","Full+750","Full+800",
         "Full+850","Full+900","Full+950","Full+1000","Full (Elite)",
         "Full (Epic)","Full (Rare)","Full (Legend)","Full (Myth)","Full OMEGA",
     ]},
    {"id": "lucky", "name": "Lucky", "cost": _T1,
     "desc": [
         "Slight rare+","+2 rare","+3 rare","+4 rare","+5 rare",
         "+6 rare","+7 rare","+8 rare","+9 rare","Purple rain!",
         "+11 rare","+12 rare","+13 rare","+14 rare","+15 rare",
         "+16 rare","+17 rare","+18 rare","+19 rare","Purple storm",
         "Pure Purple","All Purple","Purple God","Purple King","Purple Emperor",
         "Purple Legend","Purple Elite","Purple Myth","Purple Divine","PURPLE OMEGA",
     ]},
    {"id": "doublepoints", "name": "Double Pts", "cost": _TDP,
     "desc": [
         "x2","x3","x4","x5","x6",
         "x8","x10","x15","x20","x30",
         "x40","x55","x75","x100","x135",
         "x185","x250","x340","x460","x620",
         "x840","x1140","x1540","x2090","x2825",
         "x3820","x5175","x7000","x9500","x12800",
     ]},
    {"id": "homing", "name": "Homing", "cost": _T2,
     "desc": [
         "Weak x1","Light x2","Medium x3","Strong x4","x5 steer",
         "x7 steer","x9 steer","x12 steer","x16 steer","x22 steer",
         "x28 steer","x36 steer","x46 steer","x59 steer","x76 steer",
         "x97 steer","x124 steer","x159 steer","x204 steer","x261 steer",
         "x334 steer","x428 steer","x548 steer","x702 steer","x899 steer",
         "x1151","x1473","x1886","x2415 steer","PERFECT AIM",
     ]},
    {"id": "ricochet", "name": "Ricochet", "cost": _T1,
     "desc": [
         "1 bounce","2 bounces","3 bounces","4 bounces","5 bounces",
         "6 bounces","7 bounces","8 bounces","9 bounces","20 bounces",
         "25 bounces","30 bounces","35 bounces","40 bounces","45 bounces",
         "50 bounces","60 bounces","70 bounces","80 bounces","90 bounces",
         "100 bounces","120 bounces","140 bounces","160 bounces","180 bounces",
         "200 bounces","250 bounces","300 bounces","400 bounces","∞ bounces",
     ]},
]

# =================== EFFECTS ===================

class PopEffect:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.color  = color
        self.radius = 10
        self.alpha  = 255

    def update(self):
        self.radius += 4
        self.alpha  -= 20

    def draw(self, surface):
        if self.alpha <= 0: return
        s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, max(0,self.alpha)), (self.radius, self.radius), self.radius)
        surface.blit(s, (int(self.x - self.radius), int(self.y - self.radius)))

    def is_done(self): return self.alpha <= 0


class ExplosionEffect:
    def __init__(self, x, y, radius):
        self.x, self.y = x, y
        self.max_r = radius
        self.cur_r = 10
        self.alpha = 200

    def update(self):
        self.cur_r += (self.max_r - self.cur_r) * 0.2 + 3
        self.alpha -= 18

    def draw(self, surface):
        if self.alpha <= 0: return
        s  = pygame.Surface((self.max_r*2+10, self.max_r*2+10), pygame.SRCALPHA)
        cx = self.max_r + 5
        pygame.draw.circle(s, (255,150,0,  max(0,self.alpha)),    (cx,cx), int(self.cur_r))
        pygame.draw.circle(s, (255,255,100,max(0,self.alpha//2)), (cx,cx), int(self.cur_r), 4)
        surface.blit(s, (int(self.x-cx), int(self.y-cx)))

    def is_done(self): return self.alpha <= 0


class LightningEffect:
    def __init__(self, x1, y1, x2, y2):
        self.x1,self.y1 = x1,y1
        self.x2,self.y2 = x2,y2
        self.alpha = 255

    def update(self): self.alpha -= 35

    def draw(self, surface):
        if self.alpha <= 0: return
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(s, (255,255,100,max(0,self.alpha)),
                         (int(self.x1),int(self.y1)), (int(self.x2),int(self.y2)), 3)
        surface.blit(s, (0,0))

    def is_done(self): return self.alpha <= 0


class ScorePopup:
    def __init__(self, x, y, points, color):
        self.x, self.y = x, y
        self.points    = points
        self.color     = color          # matches balloon color!
        self.alpha     = 255
        self.font      = pygame.font.SysFont(None, 36)

    def update(self):
        self.y     -= 2
        self.alpha -= 8

    def draw(self, surface):
        if self.alpha <= 0: return
        t = self.font.render(f"+{self.points}", True, self.color)
        t.set_alpha(max(0, self.alpha))
        surface.blit(t, (int(self.x), int(self.y)))

    def is_done(self): return self.alpha <= 0

# =================== BALLOON ===================

class Balloon:
    def __init__(self, lucky_lvl=0, speed_mult=1.0):
        b            = pick_balloon_type(lucky_lvl)
        self.color   = b["color"]
        self.points  = b["points"]
        self.speed   = b["speed"] * speed_mult
        self.pattern = b["pattern"]
        self.radius  = 30
        self.x       = random.randint(50, SCREEN_WIDTH - 50)
        self.y       = SCREEN_HEIGHT + self.radius
        self.time    = 0

    def update(self, slow_factor=1.0):
        self.time += 0.05
        spd = self.speed * slow_factor
        if   self.pattern == "straight":
            self.y -= spd
        elif self.pattern == "zigzag":
            self.y -= spd
            self.x += 3 * (1 if int(self.time*10) % 2 == 0 else -1)
        elif self.pattern == "circle":
            self.y -= spd * 0.5
            self.x += 3 * pygame.math.Vector2(1,0).rotate(self.time*100).x
        self.x = max(self.radius, min(SCREEN_WIDTH-self.radius, self.x))

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE,      (int(self.x)-8, int(self.y)-8), 7)
        pygame.draw.line(surface, BLACK,
                         (int(self.x), int(self.y)+self.radius),
                         (int(self.x), int(self.y)+self.radius+15), 2)

    def is_off_screen(self): return self.y < -self.radius

# =================== BOSS BALLOON ===================

class BossBalloon:
    def __init__(self, world, is_final=False):
        self.is_final  = is_final
        base_hp        = (10 if is_final else 5) * world
        self.max_hp    = max(1, round(base_hp * diff_settings["boss_hp_mult"]))
        self.hp        = self.max_hp
        self.radius    = 70 if is_final else 55
        self.color     = (148,0,211) if is_final else (220,20,60)
        self.name      = "FINAL BOSS" if is_final else "MID BOSS"
        self.points    = (500 if is_final else 200) * world
        self.x         = float(SCREEN_WIDTH // 2)
        self.y         = float(-self.radius)     # start above screen
        self.time      = 0
        self.hit_flash = 0  # flashes white when hit

    def update(self):
        self.time += 0.02
        # boss enters from top, then hovers and moves
        if self.y < 120:
            self.y += 2.0
        else:
            if self.is_final:
                # figure-8 movement
                self.x = SCREEN_WIDTH//2 + math.sin(self.time * 1.2) * 280
                self.y = 130 + math.sin(self.time * 2.4) * 60
            else:
                # wide zigzag
                self.x = SCREEN_WIDTH//2 + math.sin(self.time * 1.5) * 240
                self.y = 120 + math.sin(self.time * 0.8) * 40
        if self.hit_flash > 0:
            self.hit_flash -= 1

    def hit(self):
        self.hp        -= 1
        self.hit_flash  = 8
        snd_boss_hit.play()

    def is_dead(self): return self.hp <= 0

    def draw(self, surface):
        col = WHITE if self.hit_flash > 0 else self.color
        # body
        pygame.draw.circle(surface, col, (int(self.x), int(self.y)), self.radius)
        shine_col = (min(255,col[0]+80),min(255,col[1]+80),min(255,col[2]+80))
        pygame.draw.circle(surface, shine_col, (int(self.x)-18, int(self.y)-18), 16)
        # string
        pygame.draw.line(surface, BLACK,
                         (int(self.x), int(self.y)+self.radius),
                         (int(self.x), int(self.y)+self.radius+20), 3)
        # name label
        font = pygame.font.SysFont(None, 26)
        label = font.render(self.name, True, WHITE)
        surface.blit(label, (int(self.x)-label.get_width()//2, int(self.y)-8))
        # health bar
        bw = 120
        bx = int(self.x) - bw//2
        by = int(self.y) - self.radius - 22
        pygame.draw.rect(surface, (80,0,0),   (bx,    by, bw, 12), border_radius=4)
        hp_w = int(bw * self.hp / self.max_hp)
        pygame.draw.rect(surface, RED,        (bx,    by, hp_w, 12), border_radius=4)
        pygame.draw.rect(surface, BLACK,      (bx,    by, bw, 12), 2, border_radius=4)
        hf = pygame.font.SysFont(None, 22)
        ht = hf.render(f"{self.hp}/{self.max_hp}", True, WHITE)
        surface.blit(ht, (bx + bw//2 - ht.get_width()//2, by - 14))

# =================== ARROW ===================

class Arrow:
    def __init__(self, x, y, angle, piercing=0, explosive_r=0,
                 homing_str=0, bounces=0, boomerang_count=0):
        self.x, self.y      = x, y
        self.speed          = 12
        self.dx = math.cos(math.radians(angle)) * self.speed
        self.dy = math.sin(math.radians(angle)) * self.speed
        self.trail          = []
        self.hits           = 0
        self.piercing       = piercing
        self.explosive_r    = explosive_r
        self.homing_str     = homing_str
        self.bounces_left   = bounces
        self.boomerang_left = boomerang_count

    def update(self, targets):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8: self.trail.pop(0)

        if self.homing_str > 0 and targets:
            nearest = min(targets, key=lambda b: math.hypot(b.x-self.x, b.y-self.y))
            tgt  = math.degrees(math.atan2(nearest.y-self.y, nearest.x-self.x))
            cur  = math.degrees(math.atan2(self.dy, self.dx))
            diff = (tgt - cur + 180) % 360 - 180
            turn = min(abs(diff), self.homing_str) * (1 if diff > 0 else -1)
            spd  = math.hypot(self.dx, self.dy)
            a    = cur + turn
            self.dx = math.cos(math.radians(a)) * spd
            self.dy = math.sin(math.radians(a)) * spd

        self.x += self.dx
        self.y += self.dy

        if (self.x < 0 or self.x > SCREEN_WIDTH) and self.bounces_left > 0:
            self.dx = -self.dx
            self.x  = max(0, min(SCREEN_WIDTH, self.x))
            self.bounces_left -= 1

        if self.boomerang_left > 0 and self.y < 0:
            self.dy = abs(self.dy)
            self.boomerang_left -= 1

    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            r = i / max(len(self.trail), 1)
            pygame.draw.circle(surface, (200,200,int(255*r)), (int(tx),int(ty)), 2)
        ex = self.x - self.dx * 2
        ey = self.y - self.dy * 2
        pygame.draw.line(surface, BLACK, (int(self.x),int(self.y)), (int(ex),int(ey)), 4)
        pygame.draw.circle(surface, (150,75,0), (int(self.x),int(self.y)), 5)

    def can_still_pierce(self): return self.hits <= self.piercing

    def is_off_screen(self):
        if self.boomerang_left > 0:
            return self.y > SCREEN_HEIGHT + 30
        off_y = self.y < -30 or self.y > SCREEN_HEIGHT + 30
        off_x = self.bounces_left <= 0 and (self.x < -30 or self.x > SCREEN_WIDTH + 30)
        return off_y or off_x

# =================== BOW ===================

class Bow:
    def __init__(self):
        self.x           = SCREEN_WIDTH // 2
        self.y           = SCREEN_HEIGHT - 40
        self.angle       = -90
        self.length      = 60
        self.charging    = False
        self.charge_time = 0

    def rotate(self, d):
        self.angle = max(-170, min(-10, self.angle + d * 3))

    def get_tip(self):
        return (self.x + math.cos(math.radians(self.angle)) * self.length,
                self.y + math.sin(math.radians(self.angle)) * self.length)

    def draw(self, surface):
        tx, ty  = self.get_tip()
        stretch = int(self.charge_time * 3) if self.charging else 0
        mx = self.x - math.cos(math.radians(self.angle)) * stretch
        my = self.y - math.sin(math.radians(self.angle)) * stretch
        pa = self.angle + 90
        px,py = math.cos(math.radians(pa))*25, math.sin(math.radians(pa))*25
        lx,ly = int(self.x+px), int(self.y+py)
        rx,ry = int(self.x-px), int(self.y-py)
        pygame.draw.line(surface, BROWN, (lx,ly), (int(tx),int(ty)), 5)
        pygame.draw.line(surface, BROWN, (rx,ry), (int(tx),int(ty)), 5)
        pygame.draw.line(surface, BLACK, (lx,ly), (int(mx),int(my)), 2)
        pygame.draw.line(surface, BLACK, (rx,ry), (int(mx),int(my)), 2)
        pygame.draw.circle(surface, BROWN, (self.x, self.y), 12)

# =================== OVERLAY ===================

def draw_overlay(title, subtitle, color, wait=2500):
    ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    ov.fill((0,0,0,160))
    screen.blit(ov, (0,0))
    bf = pygame.font.SysFont(None, 80)
    sf = pygame.font.SysFont(None, 40)
    ts = bf.render(title,    True, color)
    ss = sf.render(subtitle, True, WHITE)
    screen.blit(ts, (SCREEN_WIDTH//2 - ts.get_width()//2, 200))
    screen.blit(ss, (SCREEN_WIDTH//2 - ss.get_width()//2, 300))
    pygame.display.flip()
    pygame.time.wait(wait)

# =================== HELP ===================

_HELP_LINES = [
    ("CONTROLS",        "header"),
    ("← → Arrow Keys",  "Aim your bow left and right"),
    ("SPACE (hold)",    "Hold to charge power, release to shoot"),
    ("SHOP button",     "Open the enchantment shop"),
    ("Mouse Scroll",    "Scroll the shop or this help screen"),
    ("",                "blank"),
    ("BALLOONS",        "header"),
    ("Red",             "1 pt  — most common"),
    ("Blue",            "2 pts — common"),
    ("Green",           "4 pts — uncommon"),
    ("Purple",          "8 pts — rare! Upgrade Lucky to see more"),
    ("Silver",          "Gives you arrows — don't miss!"),
    ("Gold",            "Big bonus points!"),
    ("",                "blank"),
    ("GAME FLOW",       "header"),
    ("Levels",          "Pop balloons to reach the target score"),
    ("Worlds",          "5 worlds — complete levels to advance"),
    ("Mid-Boss",        "Appears halfway through each world"),
    ("Final Boss",      "Tough! Appears at the end of each world"),
    ("",                "blank"),
    ("ENCHANTMENTS",    "header"),
    ("Multishot",       "Shoot multiple arrows at once"),
    ("Explosive",       "Arrows explode, popping nearby balloons"),
    ("Freeze",          "Freezes balloons in place on hit"),
    ("Slow",            "Slows ALL balloons on screen"),
    ("Piercing",        "Arrows pass through multiple balloons"),
    ("Lightning",       "Chain lightning jumps to nearby balloons"),
    ("Homing",          "Arrows curve toward the nearest balloon"),
    ("Ricochet",        "Arrows bounce off walls"),
    ("Double Score",    "Multiplies points earned per balloon"),
    ("Boomerang",       "Arrow returns after reaching max distance"),
    ("Magnet",          "Pulls balloons toward screen center"),
    ("Infinite",        "Unlimited arrows — never run out!"),
    ("Eagle Eye",       "Shows predicted arrow path"),
    ("Lucky",           "Increases purple balloon spawn rate"),
]
_HELP_LINE_H   = 26
_HELP_MAX_SCR  = max(0, len(_HELP_LINES) - 14)

def draw_help(surface, scroll):
    pw, ph = 610, 460
    px = SCREEN_WIDTH//2 - pw//2
    py = SCREEN_HEIGHT//2 - ph//2

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    surface.blit(overlay, (0, 0))

    pygame.draw.rect(surface, (18, 18, 38), (px, py, pw, ph), border_radius=14)
    pygame.draw.rect(surface, GOLD, (px, py, pw, ph), border_radius=14, width=2)

    title = font.render("❓  HOW TO PLAY", True, GOLD)
    surface.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, py + 10))

    close_r = pygame.Rect(px + pw - 40, py + 10, 30, 30)
    pygame.draw.rect(surface, (160, 30, 30), close_r, border_radius=6)
    ct = small_font.render("X", True, WHITE)
    surface.blit(ct, (close_r.centerx - ct.get_width()//2, close_r.centery - ct.get_height()//2))

    content_y = py + 52
    content_h = ph - 68
    clip_surf = pygame.Surface((pw - 16, content_h), pygame.SRCALPHA)
    clip_surf.fill((0, 0, 0, 0))

    y = -scroll * _HELP_LINE_H
    for (name, desc) in _HELP_LINES:
        if desc == "blank":
            y += _HELP_LINE_H // 2
            continue
        if desc == "header":
            t = small_font.render(f"— {name} —", True, GOLD)
            clip_surf.blit(t, (10, y + 4))
            pygame.draw.line(clip_surf, (80, 70, 20), (10, y + 22), (pw - 30, y + 22), 1)
        else:
            nt = small_font.render(name, True, (160, 210, 255))
            clip_surf.blit(nt, (14, y))
            dt = small_font.render(desc, True, (200, 200, 200))
            clip_surf.blit(dt, (200, y))
        y += _HELP_LINE_H

    surface.blit(clip_surf, (px + 8, content_y))

    # scroll hint
    if scroll < _HELP_MAX_SCR:
        ht = small_font.render("▼ scroll for more", True, (120, 120, 120))
        surface.blit(ht, (SCREEN_WIDTH//2 - ht.get_width()//2, py + ph - 22))

    return close_r

# =================== SHOP ===================

def draw_shop(surface, upgrades, total_score, sfont, scroll):
    pw, ph = 530, 410
    px = SCREEN_WIDTH//2  - pw//2
    py = SCREEN_HEIGHT//2 - ph//2

    dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    dim.fill((0,0,0,170))
    surface.blit(dim, (0,0))

    pygame.draw.rect(surface, (25,25,45), (px,py,pw,ph), border_radius=14)
    pygame.draw.rect(surface, GOLD,       (px,py,pw,ph), 2, border_radius=14)
    surface.blit(sfont.render("ENCHANTMENTS", True, GOLD), (px+12, py+10))
    ws = sfont.render(f"Wallet: {total_score}pts", True, GOLD)
    surface.blit(ws, (px+pw-ws.get_width()-12, py+10))
    pygame.draw.line(surface, GOLD, (px, py+36), (px+pw, py+36), 1)

    up_rect = pygame.Rect(px+pw-28, py+40,     22, 18)
    dn_rect = pygame.Rect(px+pw-28, py+ph-55,  22, 18)
    for r, lbl in [(up_rect,"▲"),(dn_rect,"▼")]:
        pygame.draw.rect(surface, GRAY, r, border_radius=4)
        lt = sfont.render(lbl, True, BLACK)
        surface.blit(lt, (r.centerx-lt.get_width()//2, r.centery-lt.get_height()//2))

    buy_btns  = []
    sell_btns = []
    row_h     = 53
    surface.set_clip(pygame.Rect(px+2, py+38, pw-32, ph-80))

    for i, item in enumerate(SHOP_ITEMS):
        cur = upgrades.get(item["id"], 0)
        mx_ = len(item["cost"])
        ry  = py + 42 + (i - scroll) * row_h

        if ry < py+36 or ry+row_h > py+ph-42:
            buy_btns.append( (pygame.Rect(0,0,0,0), item["id"]) )
            sell_btns.append((pygame.Rect(0,0,0,0), item["id"]) )
            continue

        pygame.draw.rect(surface, (38,38,62), (px+4, ry, pw-34, row_h-4), border_radius=6)
        surface.blit(sfont.render(item["name"], True, WHITE), (px+10, ry+7))

        lv_col = GOLD if cur > 0 else GRAY
        lv_t   = sfont.render(f"Lv.{cur}/{mx_}", True, lv_col)
        surface.blit(lv_t, (px+10, ry+32))

        ds = sfont.render(f"Lv{cur}: {item['desc'][cur-1]}", True, (170,255,170)) if cur > 0 \
             else sfont.render("Not owned", True, GRAY)
        surface.blit(ds, (px+130, ry+24))

        br = pygame.Rect(px+pw-198, ry+9, 84, 28)
        if cur >= mx_:
            pygame.draw.rect(surface, (55,55,55), br, border_radius=5)
            bt = sfont.render("MAX", True, GRAY)
        else:
            cost = max(1, int(item["cost"][cur] * diff_settings["cost_mult"]))
            pygame.draw.rect(surface, GREEN if total_score>=cost else (75,75,75), br, border_radius=5)
            bt = sfont.render(f"{cost}pts", True, WHITE)
        surface.blit(bt, (br.centerx-bt.get_width()//2, br.centery-bt.get_height()//2))
        buy_btns.append((br, item["id"]))

        sr = pygame.Rect(px+pw-108, ry+9, 84, 28)
        if cur > 0:
            refund = int(item["cost"][cur-1] * 0.75 * diff_settings["cost_mult"])
            pygame.draw.rect(surface, (170,50,50), sr, border_radius=5)
            st = sfont.render(f"+{refund}", True, WHITE)
        else:
            pygame.draw.rect(surface, (55,55,55), sr, border_radius=5)
            st = sfont.render("Sell", True, GRAY)
        surface.blit(st, (sr.centerx-st.get_width()//2, sr.centery-st.get_height()//2))
        sell_btns.append((sr, item["id"]))

    surface.set_clip(None)
    close_rect = pygame.Rect(px+pw//2-60, py+ph-38, 120, 28)
    pygame.draw.rect(surface, (140,35,35), close_rect, border_radius=8)
    ct = sfont.render("Close", True, WHITE)
    surface.blit(ct, (close_rect.centerx-ct.get_width()//2, close_rect.centery-ct.get_height()//2))
    return buy_btns, sell_btns, close_rect, up_rect, dn_rect

# =================== GAME STATE ===================

MIN_CHARGE   = 0
MAX_CHARGE   = 10
MAX_SCROLL   = max(0, len(SHOP_ITEMS) - 7)

game_state   = "menu"   # "menu" | "playing"

world        = 1
level        = 1
score        = 0
total_score  = 0
time_left    = get_time_limit(level)
target_score = get_target_score(level, world)
freeze_timer = 0
arrows_left  = 10
refill_timer = 0
shop_open    = False
shop_scroll  = 0
boss         = None   # current boss balloon (or None)
boss_spawned = False  # did we already spawn a boss this level?

upgrades = {item["id"]: 0 for item in SHOP_ITEMS}

balloons   = []
arrows_    = []   # renamed to avoid conflict with arrows_left
effects    = []
popups     = []
lightnings = []
spawn_timer = 0
bow         = Bow()

_shop_buy_btns  = []
_shop_sell_btns = []
_shop_close     = None
_shop_up        = None
_shop_dn        = None

font       = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 27)
shop_btn   = pygame.Rect(10, SCREEN_HEIGHT - 50, 110, 38)
exit_btn      = pygame.Rect(SCREEN_WIDTH - 70, 5, 60, 36)   # top-right exit
help_btn_pos  = (130, SCREEN_HEIGHT - 31)                   # ? circle next to shop
help_btn_r    = 15                                          # ? circle radius
help_open     = False
help_scroll   = 0
clock         = pygame.time.Clock()

# =================== MENU ===================

def draw_menu(surface, hover):
    """Draw the difficulty-select title screen. Returns list of (rect, key) for buttons."""
    # dark gradient background
    for row in range(SCREEN_HEIGHT):
        t = row / SCREEN_HEIGHT
        r = int(10 + 20 * t); g = int(10 + 15 * t); b = int(30 + 40 * t)
        pygame.draw.line(surface, (r, g, b), (0, row), (SCREEN_WIDTH, row))

    # title
    tf  = pygame.font.SysFont(None, 100)
    sf2 = pygame.font.SysFont(None, 36)
    sf3 = pygame.font.SysFont(None, 26)
    title = tf.render("🎈 BALLOON GAME", True, GOLD)
    surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 55))
    sub = sf2.render("Choose your difficulty!", True, (200, 200, 255))
    surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 155))

    keys   = ["easy", "normal", "hard"]
    bw, bh = 200, 64
    gap    = 28
    total  = len(keys) * bw + (len(keys) - 1) * gap
    bx0    = SCREEN_WIDTH // 2 - total // 2
    btns   = []

    for i, key in enumerate(keys):
        d    = DIFFICULTIES[key]
        bx   = bx0 + i * (bw + gap)
        by   = 210
        rect = pygame.Rect(bx, by, bw, bh)
        btns.append((rect, key))

        col  = d["btn"] if hover != key else tuple(min(255, v + 50) for v in d["btn"])
        pygame.draw.rect(surface, col,     rect, border_radius=14)
        pygame.draw.rect(surface, d["color"], rect, 3, border_radius=14)

        lf  = pygame.font.SysFont(None, 46)
        lt  = lf.render(d["label"], True, WHITE)
        surface.blit(lt, (rect.centerx - lt.get_width() // 2, rect.centery - lt.get_height() // 2))

        # description lines below each button
        for j, line in enumerate(d["desc"]):
            lt2 = sf3.render(line, True, d["color"])
            surface.blit(lt2, (rect.centerx - lt2.get_width() // 2, by + bh + 12 + j * 22))

    # highscore
    hs     = load_highscore()
    hs_txt = sf2.render(f"Best: World {hs['world']}  Level {hs['level']}  |  Score {hs['score']}", True, GOLD)
    surface.blit(hs_txt, (SCREEN_WIDTH // 2 - hs_txt.get_width() // 2, SCREEN_HEIGHT - 55))

    # exit button
    pygame.draw.rect(surface, (130, 25, 25), exit_btn, border_radius=8)
    et = small_font.render("EXIT", True, WHITE)
    surface.blit(et, (exit_btn.centerx - et.get_width() // 2, exit_btn.centery - et.get_height() // 2))

    return btns

def reset_game(chosen_diff):
    """Reset all game variables and apply the chosen difficulty."""
    global diff_settings, world, level, score, total_score, time_left, target_score
    global freeze_timer, arrows_left, refill_timer, shop_open, shop_scroll
    global boss, boss_spawned, upgrades, game_state
    diff_settings = DIFFICULTIES[chosen_diff]
    world = 1; level = 1; score = 0; total_score = 0
    freeze_timer = 0; refill_timer = 0
    arrows_left  = diff_settings["start_arrows"]
    shop_open    = False; shop_scroll = 0
    boss         = None;  boss_spawned = False
    upgrades     = {item["id"]: 0 for item in SHOP_ITEMS}
    time_left    = get_time_limit(level)
    target_score = get_target_score(level, world)
    balloons.clear(); arrows_.clear(); effects.clear(); popups.clear(); lightnings.clear()
    bgm_channel.play(bgm1, loops=-1); bgm_channel.set_volume(0.4)
    game_state   = "playing"

# =================== GAME LOOP ===================

_menu_hover = None   # which difficulty button the mouse is over
_menu_btns  = []     # filled each frame by draw_menu()

while True:
    dt = clock.tick(60) / 1000

    # ---- EVENTS ----
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_highscore(level, world, total_score)
            pygame.quit(); sys.exit()

        # ---- MENU STATE ----
        if game_state == "menu":
            if event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                _menu_hover = None
                for rect, key in _menu_btns:
                    if rect.collidepoint(mx, my):
                        _menu_hover = key
                if exit_btn.collidepoint(mx, my):
                    _menu_hover = "exit"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if exit_btn.collidepoint(mx, my):
                    pygame.quit(); sys.exit()
                for rect, key in _menu_btns:
                    if rect.collidepoint(mx, my):
                        reset_game(key)
            continue  # skip the rest of event handling while in menu

        # ---- PLAYING STATE ----
        if event.type == pygame.MOUSEWHEEL:
            if help_open:
                help_scroll = max(0, min(_HELP_MAX_SCR, help_scroll - event.y))
            elif shop_open:
                shop_scroll = max(0, min(MAX_SCROLL, shop_scroll - event.y))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # help close button
            if help_open:
                if _help_close and _help_close.collidepoint(mx, my):
                    help_open = False
                continue
            # ? help button
            if math.hypot(mx - help_btn_pos[0], my - help_btn_pos[1]) <= help_btn_r:
                help_open  = True
                help_scroll = 0
                continue
            # exit button (top-right)
            if exit_btn.collidepoint(mx, my):
                save_highscore(level, world, total_score)
                game_state = "menu"
                bgm_channel.play(bgm1, loops=-1); bgm_channel.set_volume(0.4)
                continue
            if not shop_open and shop_btn.collidepoint(mx, my):
                shop_open = True
            elif shop_open:
                if _shop_close and _shop_close.collidepoint(mx, my):
                    shop_open = False
                elif _shop_up and _shop_up.collidepoint(mx, my):
                    shop_scroll = max(0, shop_scroll - 1)
                elif _shop_dn and _shop_dn.collidepoint(mx, my):
                    shop_scroll = min(MAX_SCROLL, shop_scroll + 1)
                else:
                    for br, iid in _shop_buy_btns:
                        if br.collidepoint(mx, my):
                            item = next(i for i in SHOP_ITEMS if i["id"] == iid)
                            cur  = upgrades[iid]
                            if cur < len(item["cost"]):
                                cost = max(1, int(item["cost"][cur] * diff_settings["cost_mult"]))
                                if total_score >= cost:
                                    total_score   -= cost
                                    upgrades[iid] += 1
                    for sr, iid in _shop_sell_btns:
                        if sr.collidepoint(mx, my):
                            item = next(i for i in SHOP_ITEMS if i["id"] == iid)
                            cur  = upgrades[iid]
                            if cur > 0:
                                refund         = int(item["cost"][cur-1] * 0.75 * diff_settings["cost_mult"])
                                total_score   += refund
                                upgrades[iid] -= 1

        if not shop_open and not help_open:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                bow.charging    = True
                bow.charge_time = 0

            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                capacity  = ARROW_CAPACITY[upgrades["infinite"]]
                can_shoot = (capacity == -1) or (arrows_left > 0)
                if bow.charging and bow.charge_time >= MIN_CHARGE and can_shoot:
                    tip_x, tip_y = bow.get_tip()
                    num_arr  = MULTISHOT_COUNTS[upgrades["multishot"]]
                    piercing = PIERCING_COUNTS[upgrades["piercing"]]
                    exp_r    = EXPLOSIVE_RADII[upgrades["explosive"]]
                    homing   = HOMING_STRENGTHS[upgrades["homing"]]
                    bounces  = RICOCHET_BOUNCES[upgrades["ricochet"]]
                    boomers  = BOOMERANG_RETURNS[upgrades["boomerang"]]
                    spread   = 10
                    start_a  = bow.angle - (num_arr - 1) * spread / 2
                    for j in range(num_arr):
                        arrows_.append(Arrow(tip_x, tip_y, start_a + j*spread,
                                             piercing, exp_r, homing, bounces, boomers))
                    if capacity != -1:
                        arrows_left = max(0, arrows_left - 1)
                    snd_shoot.play()
                bow.charging    = False
                bow.charge_time = 0

    if game_state == "menu":
        _menu_btns = draw_menu(screen, _menu_hover)
        pygame.display.flip()
        continue

    # ---- UPDATE ----
    if not shop_open and not help_open:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:  bow.rotate(-1)
        if keys[pygame.K_RIGHT]: bow.rotate(1)

        if bow.charging:
            bow.charge_time = min(bow.charge_time + dt, MAX_CHARGE)

        if freeze_timer > 0:
            freeze_timer = max(0, freeze_timer - dt)
        else:
            time_left -= dt

        capacity = ARROW_CAPACITY[upgrades["infinite"]]
        if capacity != -1 and arrows_left < capacity:
            refill_timer += dt
            if refill_timer >= 3.0:
                arrows_left  += 1
                refill_timer  = 0

        # spawn boss at level 50 and 100
        if not boss_spawned:
            if level % 100 == 50:
                boss         = BossBalloon(world, is_final=False)
                boss_spawned = True
            elif level % 100 == 0:
                boss         = BossBalloon(world, is_final=True)
                boss_spawned = True

        # update boss
        if boss: boss.update()

        # spawn balloons (slower when boss is active)
        spawn_timer += 1
        interval = 90 if boss else 60
        if spawn_timer >= interval:
            spd_mult = get_speed_multiplier(world)
            balloons.append(Balloon(upgrades["lucky"], spd_mult))
            spawn_timer = 0

        slow = SLOW_FACTORS[upgrades["slow"]]
        if freeze_timer <= 0:
            for b in balloons: b.update(slow)

        # all arrow targets (balloons + boss if present)
        all_targets = balloons + ([boss] if boss else [])
        for a in arrows_: a.update(all_targets)

        mag = MAGNET_STRENGTHS[upgrades["magnet"]]
        if mag > 0:
            for b in balloons:
                for a in arrows_:
                    d = math.hypot(a.x-b.x, a.y-b.y)
                    if 0 < d < 160:
                        b.x += (a.x-b.x) / d * mag
                        b.y += (a.y-b.y) / d * mag

        for e in effects:    e.update()
        for p in popups:     p.update()
        for l in lightnings: l.update()

        # ---- COLLISION ----
        mult = DOUBLE_MULTIPLIERS[upgrades["doublepoints"]]

        def pop_balloon_at(bln):
            if bln not in balloons: return 0
            pts = bln.points * mult
            effects.append(PopEffect(bln.x, bln.y, bln.color))
            popups.append(ScorePopup(bln.x, bln.y, pts, bln.color))  # color matched!
            snd_pop.play()
            balloons.remove(bln)
            return pts

        for arrow in arrows_[:]:
            hit_something = False

            # hit boss?
            if boss:
                d = math.hypot(arrow.x-boss.x, arrow.y-boss.y)
                if d < boss.radius:
                    boss.hit()
                    if boss.is_dead():
                        pts = boss.points * mult
                        score       += pts
                        total_score += pts
                        popups.append(ScorePopup(boss.x, boss.y-50, pts, boss.color))
                        effects.append(ExplosionEffect(boss.x, boss.y, 120))
                        snd_level_clear.play()
                        boss         = None
                        boss_spawned = False
                    if arrow in arrows_: arrows_.remove(arrow)
                    hit_something = True

            if not hit_something:
                for balloon in balloons[:]:
                    dist = math.hypot(arrow.x-balloon.x, arrow.y-balloon.y)
                    if dist < balloon.radius:
                        gained       = pop_balloon_at(balloon)
                        score       += gained
                        total_score += gained

                        if arrow.explosive_r > 0:
                            effects.append(ExplosionEffect(arrow.x, arrow.y, arrow.explosive_r))
                            for nb in balloons[:]:
                                d2 = math.hypot(arrow.x-nb.x, arrow.y-nb.y)
                                if d2 < arrow.explosive_r:
                                    g = pop_balloon_at(nb)
                                    score += g; total_score += g

                        n_chains = LIGHTNING_CHAINS[upgrades["lightning"]]
                        if n_chains > 0:
                            nearby = sorted(balloons[:],
                                            key=lambda b: math.hypot(balloon.x-b.x, balloon.y-b.y))[:n_chains]
                            for nb in nearby:
                                lightnings.append(LightningEffect(balloon.x,balloon.y, nb.x,nb.y))
                                g = pop_balloon_at(nb)
                                score += g; total_score += g

                        if upgrades["freezer"] > 0 and freeze_timer <= 0:
                            freeze_timer = FREEZE_TIMES[upgrades["freezer"]]

                        arrow.hits += 1
                        if not arrow.can_still_pierce() and arrow in arrows_:
                            arrows_.remove(arrow)
                        break

        balloons   = [b for b in balloons   if not b.is_off_screen()]
        arrows_    = [a for a in arrows_    if not a.is_off_screen()]
        effects    = [e for e in effects    if not e.is_done()]
        popups     = [p for p in popups     if not p.is_done()]
        lightnings = [l for l in lightnings if not l.is_done()]

        # level clear (only if no boss active)
        if score >= target_score and boss is None:
            snd_level_clear.play()
            save_highscore(level, world, total_score)

            if level % 100 == 0:
                # world clear!
                draw_overlay(f"WORLD {world} CLEAR! 🎉",
                             f"Entering World {world+1}...", GOLD, wait=3500)
                world       += 1
                level        = 1
                total_score  = 0   # reset wallet
                upgrades     = {item["id"]: 0 for item in SHOP_ITEMS}  # reset abilities
                arrows_left  = 10
                refill_timer = 0
                # switch to new world's BGM
                new_bgm = bgm_list[(world - 1) % len(bgm_list)]
                bgm_channel.play(new_bgm, loops=-1)
                bgm_channel.set_volume(0.4)
            else:
                draw_overlay(f"LEVEL {level} CLEAR!", f"→ Level {level+1}", GREEN)
                level       += 1

            score        = 0
            boss_spawned = False
            time_left    = get_time_limit(level)
            target_score = get_target_score(level, world)
            balloons.clear(); arrows_.clear()

        # game over
        if time_left <= 0:
            save_highscore(level, world, total_score)
            hs = load_highscore()
            draw_overlay("GAME OVER",
                         f"World {world}  Level {level}  |  Best: W{hs['world']} L{hs['level']}", RED)
            game_state = "menu"
            bgm_channel.play(bgm1, loops=-1); bgm_channel.set_volume(0.4)

    # ---- DRAW ----
    update_clouds()
    draw_background(screen, world)

    for b in balloons:   b.draw(screen)
    if boss:             boss.draw(screen)
    for a in arrows_:    a.draw(screen)
    for e in effects:    e.draw(screen)
    for l in lightnings: l.draw(screen)
    for p in popups:     p.draw(screen)
    bow.draw(screen)

    # eagle eye
    if bow.charging and upgrades["eagleeye"] > 0:
        px2, py2 = bow.get_tip()
        pdx = math.cos(math.radians(bow.angle)) * 12
        pdy = math.sin(math.radians(bow.angle)) * 12
        steps = EAGLE_EYE_STEPS[upgrades["eagleeye"]]
        for _ in range(steps):
            px2 += pdx; py2 += pdy
            if px2 < 0 or px2 > SCREEN_WIDTH or py2 < 0: break
            pygame.draw.circle(screen, (150,150,255), (int(px2),int(py2)), 3)

    # HUD — dark background strip for readability
    pygame.draw.rect(screen, (0,0,0,120), (0,0,SCREEN_WIDTH,50))

    hs = load_highscore()
    screen.blit(font.render(f"Score: {score} / {target_score}", True, WHITE), (10, 8))
    theme_name = get_theme(world)[4]
    wt = font.render(f"Lv {level}  {theme_name}", True, GOLD)
    screen.blit(wt, (SCREEN_WIDTH//2 - wt.get_width()//2, 8))
    tc = RED if time_left < 10 else WHITE
    tt = font.render(f"{max(0,int(time_left))}s", True, tc)
    screen.blit(tt, (SCREEN_WIDTH - tt.get_width() - 80, 8))

    # exit button (top-right)
    pygame.draw.rect(screen, (130, 25, 25), exit_btn, border_radius=8)
    et = small_font.render("EXIT", True, WHITE)
    screen.blit(et, (exit_btn.centerx - et.get_width()//2, exit_btn.centery - et.get_height()//2))

    # difficulty badge (top-left, below score)
    d_col  = diff_settings["color"]
    d_lbl  = diff_settings["label"]
    d_txt  = small_font.render(d_lbl, True, d_col)
    screen.blit(d_txt, (10, 54))

    # wallet + quiver + highscore
    ws2 = small_font.render(f"Wallet: {total_score}pts", True, GOLD)
    screen.blit(ws2, (SCREEN_WIDTH - ws2.get_width() - 10, 55))
    cap = ARROW_CAPACITY[upgrades["infinite"]]
    qt  = small_font.render("Arrows: ∞" if cap==-1 else f"Arrows: {arrows_left}/{cap}",
                            True, WHITE if arrows_left > 0 or cap==-1 else RED)
    screen.blit(qt, (SCREEN_WIDTH - qt.get_width() - 10, 75))
    hs_txt = small_font.render(f"Best: W{hs['world']} L{hs['level']}", True, GOLD)
    screen.blit(hs_txt, (SCREEN_WIDTH - hs_txt.get_width() - 10, 95))

    # charge bar
    if bow.charging:
        bw2 = int((bow.charge_time / MAX_CHARGE) * 200)
        pygame.draw.rect(screen, GREEN, (300, SCREEN_HEIGHT-25, bw2, 15))
        pygame.draw.rect(screen, BLACK, (300, SCREEN_HEIGHT-25, 200, 15), 2)
        ht = small_font.render("RELEASE!", True, BLACK)
        screen.blit(ht, (310, SCREEN_HEIGHT-50))

    # freeze overlay
    if freeze_timer > 0:
        fs = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        fs.fill((100,200,255,35))
        screen.blit(fs, (0,0))
        ft = font.render(f"FROZEN! {freeze_timer:.1f}s", True, CYAN)
        screen.blit(ft, (SCREEN_WIDTH//2 - ft.get_width()//2, 60))

    # boss warning banner
    if boss:
        bw_surf = font.render(f"⚠ {boss.name} ⚠", True, RED)
        screen.blit(bw_surf, (SCREEN_WIDTH//2 - bw_surf.get_width()//2, SCREEN_HEIGHT//2 + 180))

    # shop button
    pygame.draw.rect(screen, DARK, shop_btn, border_radius=8)
    sl2 = small_font.render("SHOP", True, GOLD)
    screen.blit(sl2, (shop_btn.centerx-sl2.get_width()//2, shop_btn.centery-sl2.get_height()//2))

    # ? help button (right of shop)
    pygame.draw.circle(screen, (60, 80, 180), help_btn_pos, help_btn_r)
    pygame.draw.circle(screen, (140, 160, 255), help_btn_pos, help_btn_r, 2)
    qt2 = small_font.render("?", True, WHITE)
    screen.blit(qt2, (help_btn_pos[0] - qt2.get_width()//2, help_btn_pos[1] - qt2.get_height()//2))

    if shop_open:
        _shop_buy_btns, _shop_sell_btns, _shop_close, _shop_up, _shop_dn = \
            draw_shop(screen, upgrades, total_score, small_font, shop_scroll)

    if help_open:
        _help_close = draw_help(screen, help_scroll)
    else:
        _help_close = None

    ch2 = small_font.render("← → aim  |  SPACE to shoot", True, GRAY)
    screen.blit(ch2, (SCREEN_WIDTH//2 - ch2.get_width()//2, SCREEN_HEIGHT-70))

    pygame.display.flip()
