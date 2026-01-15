import pygame, sys, os, json, random, math, time

# --- 1. PC CONFIG & HARDWARE EMULATION ---
SCALE = 4
SCREEN_W, SCREEN_H = 160, 128
WINDOW_W, WINDOW_H = SCREEN_W * SCALE, SCREEN_H * SCALE

pygame.init()
pygame.display.set_caption("WiFi Warriors: PC Edition")
screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
display_surface = pygame.Surface((SCREEN_W, SCREEN_H))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Courier New", 10, bold=True)

# --- COLORS ---
BLACK, WHITE = (0,0,0), (255,255,255)
GREY, RED = (128,128,128), (255,0,0)
BLUE, GREEN = (0,0,255), (0,255,0)
CYAN, MAGENTA = (0,255,255), (255,0,255)
YELLOW, BROWN = (255,255,0), (139,69,19)
SKIN = (255,224,189)
SKY_BLUE, FOREST_GREEN, DARK_GREEN = (100,180,255), (34,139,34), (0,80,0)
PAPER, INK = (150,165,145), (50,15,0)
GOLD = (200,200,50)

def color(r, g, b): return (r, g, b)

# --- 2. DRIVERS ---
class InputController:
    def __init__(self):
        self.last_press = 0
        self.debounce_ms = 150 # PC keys are fast, need debounce

    def get_input(self):
        pygame.event.pump() # Keep window alive
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            
        keys = pygame.key.get_pressed()
        now = pygame.time.get_ticks()
        
        if now - self.last_press < self.debounce_ms: return None

        if keys[pygame.K_UP]: self.last_press = now; return 'UP'
        if keys[pygame.K_DOWN]: self.last_press = now; return 'DOWN'
        if keys[pygame.K_LEFT]: self.last_press = now; return 'LEFT'
        if keys[pygame.K_RIGHT]: self.last_press = now; return 'RIGHT'
        if keys[pygame.K_z]: self.last_press = now; return 'A'
        if keys[pygame.K_x]: self.last_press = now; return 'B'
        return None

    def wait_for_input(self):
        while True:
            k = self.get_input()
            if k: return k
            pygame.time.delay(10)

class SoundEngine:
    def play(self, notes): pass
    def sfx_hit(self): pass
    def sfx_crit(self): pass
    def sfx_blip(self): pass
    def sfx_coin(self): pass
    def sfx_win(self): pass
    def sfx_lose(self): pass

class LCD:
    def fill(self, col): display_surface.fill(col)
    def fill_rect(self, x, y, w, h, col): pygame.draw.rect(display_surface, col, (int(x), int(y), int(w), int(h)))
    def rect(self, x, y, w, h, col): pygame.draw.rect(display_surface, col, (int(x), int(y), int(w), int(h)), 1)
    def line(self, x1, y1, x2, y2, col): pygame.draw.line(display_surface, col, (int(x1), int(y1)), (int(x2), int(y2)))
    def pixel(self, x, y, col):
        if 0 <= x < SCREEN_W and 0 <= y < SCREEN_H: display_surface.set_at((int(x), int(y)), col)
    def text(self, txt, x, y, col):
        s = font.render(str(txt), False, col); display_surface.blit(s, (x, y))
    def show(self):
        scaled = pygame.transform.scale(display_surface, (WINDOW_W, WINDOW_H))
        screen.blit(scaled, (0, 0)); pygame.display.flip(); clock.tick(60)

# --- 3. ASSETS & DATA ---
ELEMENTS = {
    "FIRE":   {"col": RED,    "weak": "WATER"},
    "WATER":  {"col": BLUE,   "weak": "NATURE"},
    "NATURE": {"col": GREEN,  "weak": "FIRE"},
    "SNOW":   {"col": WHITE,  "weak": "FIRE"},
    "POISON": {"col": MAGENTA, "weak": "FIRE"}
}

def draw_forest_bg(lcd):
    lcd.fill_rect(0, 0, 160, 60, SKY_BLUE); lcd.fill_rect(0, 60, 160, 15, DARK_GREEN)
    lcd.fill_rect(0, 75, 160, 53, FOREST_GREEN); lcd.fill_rect(0, 0, 12, 128, BROWN); lcd.fill_rect(148, 0, 12, 128, BROWN)
def draw_cave_bg(lcd):
    lcd.fill_rect(0, 0, 160, 128, color(40, 40, 40)); lcd.fill_rect(0, 50, 160, 78, color(80, 80, 80)) 
    for i in range(0, 160, 40): lcd.fill_rect(i, 0, 10, random.randint(10, 30), color(30, 30, 30))
def draw_lava_bg(lcd):
    lcd.fill_rect(0, 0, 160, 60, BLACK); lcd.fill_rect(0, 60, 160, 68, color(180, 0, 0)) 
    for i in range(0, 160, 20): lcd.line(i, 60, i+10, 128, color(255, 100, 0))
def draw_castle_bg(lcd):
    lcd.fill(color(100, 100, 120))
    for y in range(0, 128, 15):
        lcd.line(0, y, 160, y, BLACK); offset = 0 if (y//15)%2==0 else 10
        for x in range(offset, 160, 20): lcd.line(x, y, x, y+15, BLACK)
    lcd.fill_rect(0, 80, 160, 20, color(150, 0, 50))
def draw_snow_bg(lcd):
    lcd.fill_rect(0, 0, 160, 60, color(200, 200, 255)); lcd.fill_rect(0, 60, 160, 68, WHITE)
    for i in range(10, 150, 30):
        lcd.fill_rect(i+4, 40, 4, 20, BROWN); lcd.fill_rect(i, 30, 12, 15, DARK_GREEN); lcd.fill_rect(i+2, 20, 8, 10, DARK_GREEN)
def draw_book_bg(lcd):
    lcd.fill(PAPER); lcd.rect(5, 5, 150, 118, BROWN); lcd.rect(7, 7, 146, 114, BROWN)

UNIT_DEFS = {
    "Peasant":    {"s": GREY, "h":10, "w":4,  "r":12, "e":"NATURE"},
    "Warrior":    {"s": GREY, "h":14, "w":8,  "r":10, "e":"WATER"},
    "Archer":     {"s": GREY, "h":12, "w":7,  "r":60, "e":"NATURE"},
    "Mage":       {"s": GREY, "h":13, "w":6,  "r":50, "e":"FIRE"},
    "Cleric":     {"s": GREY, "h":13, "w":6,  "r":45, "e":"WATER"},
    "Necro":      {"s": GREY, "h":14, "w":6,  "r":50, "e":"NATURE"}, 
    "Wolf":       {"s": GREY, "h":8,  "w":12, "r":10, "e":"NATURE", "shape":"BEAST"},
    "Rat":        {"s": GREY, "h":4,  "w":8,  "r":8,  "e":"NATURE", "shape":"BEAST"},
    "Slime":      {"s": GREY, "h":8,  "w":10, "r":8,  "e":"WATER",  "shape":"BLOB"},
    "Cultist":    {"s": GREY, "h":13, "w":6,  "r":45, "e":"FIRE"},
    "Paladin":    {"s": GREY, "h":18, "w":9,  "r":10, "e":"WATER"},
    "Musketeer":  {"s": GREY, "h":14, "w":8,  "r":70, "e":"FIRE"},
    "Bard":       {"s": GREY, "h":13, "w":7,  "r":40, "e":"NATURE"},
    "Ninja":      {"s": GREY, "h":12, "w":7,  "r":15, "e":"NATURE"},
    "Bat":        {"s": GREY, "h":5,  "w":8,  "r":10, "e":"NATURE", "shape":"FLY"},
    "Spider":     {"s": GREY, "h":6,  "w":10, "r":10, "e":"NATURE", "shape":"BEAST"},
    "Boar":       {"s": GREY, "h":15, "w":12, "r":10, "e":"NATURE", "shape":"BEAST"},
    "Hawk":       {"s": GREY, "h":6,  "w":10, "r":10, "e":"NATURE", "shape":"FLY"},
    "Eagle":      {"s": GREY, "h":8,  "w":12, "r":10, "e":"NATURE", "shape":"FLY"},
    "Bear":       {"s": GREY, "h":20, "w":16, "r":10, "e":"NATURE", "shape":"BEAST"},
    "Goblin":     {"s": GREY, "h":10, "w":6,  "r":10, "e":"NATURE"},
    "Orc":        {"s": GREY, "h":20, "w":10, "r":10, "e":"NATURE"},
    "Bandit":     {"s": GREY, "h":14, "w":8,  "r":10, "e":"NATURE"},
    "Thief":      {"s": GREY, "h":10, "w":6,  "r":10, "e":"NATURE"},
    "Rogue":      {"s": GREY, "h":12, "w":7,  "r":10, "e":"NATURE"},
    "Bombardier": {"s": GREY, "h":14, "w":8,  "r":40, "e":"FIRE"},
    "Barbarian":  {"s": GREY, "h":18, "w":10, "r":10, "e":"FIRE"},
    "Samurai":    {"s": GREY, "h":16, "w":8,  "r":10, "e":"WATER"},
    "Monk":       {"s": GREY, "h":14, "w":7,  "r":10, "e":"WATER"},
    "Druid":      {"s": GREY, "h":14, "w":7,  "r":40, "e":"NATURE"},
    "Witch":      {"s": GREY, "h":13, "w":6,  "r":45, "e":"NATURE"},
    "Plague Doc": {"s": GREY, "h":13, "w":6,  "r":40, "e":"NATURE"},
    "Vampire":    {"s": GREY, "h":16, "w":8,  "r":10, "e":"FIRE"},
    "Frost Witch":{"s": GREY, "h":13, "w":6,  "r":45, "e":"SNOW"},
    "Beastmaster":{"s": GREY, "h":14, "w":8,  "r":12, "e":"NATURE"},
    "Falconer":   {"s": GREY, "h":12, "w":7,  "r":50, "e":"NATURE"},
    "Zombie":     {"s": GREY, "h":15, "w":8,  "r":10, "e":"NATURE"},
    "Skeleton":   {"s": GREY, "h":10, "w":6,  "r":10, "e":"NATURE"},
    "Lizard":     {"s": GREY, "h":8,  "w":14, "r":10, "e":"NATURE", "shape":"BEAST"},
    "Kobold":     {"s": GREY, "h":8,  "w":6,  "r":10, "e":"FIRE"},
    "Earth Golem":   {"s": GREY, "h":22, "w":12, "r":12, "e":"NATURE", "scale":1.2},
    "Rust Golem":    {"s": GREY, "h":22, "w":12, "r":12, "e":"FIRE",   "scale":1.2},
    "Iron Golem":    {"s": GREY, "h":22, "w":12, "r":12, "e":"FIRE",   "scale":1.2},
    "Abomination":   {"s": GREY, "h":22, "w":16, "r":10, "e":"NATURE", "shape":"BLOB", "scale":1.2},
    "Lich Lord":     {"s": GREY, "h":24, "w":8,  "r":60, "e":"FIRE",   "scale":1.2},
    "Alpha Wolf":    {"s": GREY, "h":12, "w":16, "r":12, "e":"SNOW",   "shape":"BEAST", "scale":1.2},
    "Fenrir":        {"s": GREY, "h":14, "w":18, "r":12, "e":"FIRE",   "shape":"BEAST", "scale":1.2},
    "Demon":         {"s": GREY, "h":26, "w":14, "r":16, "e":"FIRE",   "scale":1.2},
    "Rat King":      {"s": GREY, "h":14, "w":16, "r":10, "e":"NATURE", "shape":"BEAST", "scale":1.2},
    "Spider Queen":  {"s": GREY, "h":16, "w":18, "r":10, "e":"NATURE", "shape":"BEAST", "scale":1.2},
    "Fire Elem":     {"s": GREY, "h":22, "w":12, "r":40, "e":"FIRE",   "shape":"BLOB", "scale":1.2},
    "Ice Elem":      {"s": GREY, "h":22, "w":12, "r":40, "e":"SNOW",   "shape":"BLOB", "scale":1.2},
    "Orc Warlord":   {"s": GREY, "h":26, "w":14, "r":10, "e":"NATURE", "scale":1.2},
    "Hellhound":     {"s": GREY, "h":16, "w":16, "r":10, "e":"FIRE",   "shape":"BEAST", "scale":1.2},
    "Steam Tank":    {"s": GREY, "h":18, "w":20, "r":60, "e":"FIRE",   "shape":"BLOB", "scale":1.2},
    "Royal Guard":   {"s": GREY, "h":24, "w":10, "r":12, "e":"WATER",  "scale":1.2},
    "Storm Crow":    {"s": GREY, "h":14, "w":14, "r":10, "e":"NATURE", "shape":"FLY", "scale":1.2},
    "Crusader":      {"s": GREY, "h":24, "w":10, "r":12, "e":"WATER",  "scale":1.2},
    "Seraph":        {"s": GREY, "h":20, "w":14, "r":40, "e":"FIRE",   "shape":"FLY", "scale":1.2},
    "Death Knight":  {"s": GREY, "h":24, "w":10, "r":12, "e":"NATURE", "scale":1.2},
    "Vampire Lord":  {"s": GREY, "h":24, "w":10, "r":12, "e":"FIRE",   "scale":1.2},
    "Wyvern":        {"s": GREY, "h":18, "w":24, "r":10, "e":"POISON", "shape":"FLY", "scale":1.2},
    "Griffin":       {"s": GREY, "h":18, "w":24, "r":10, "e":"NATURE", "shape":"FLY", "scale":1.2},
    "Basilisk":      {"s": GREY, "h":12, "w":20, "r":10, "e":"POISON", "shape":"BEAST", "scale":1.2},
    "Werewolf":      {"s": GREY, "h":24, "w":12, "r":10, "e":"NATURE", "shape":"BEAST", "scale":1.2},
    "Werebear":      {"s": GREY, "h":22, "w":18, "r":10, "e":"NATURE", "shape":"BEAST", "scale":1.2},
    "Wereboar":      {"s": GREY, "h":20, "w":16, "r":10, "e":"NATURE", "shape":"BEAST", "scale":1.2},
    "Master Assassin":{"s": GREY, "h":24, "w":10, "r":12, "e":"POISON", "scale":1.2},
    "The Avatar":    {"s": GREY, "h":22, "w":10, "r":12, "e":"WATER",  "scale":1.2},
    "Dervish":       {"s": GREY, "h":24, "w":10, "r":12, "e":"NATURE", "scale":1.2},
    "Huntmaster":    {"s": GREY, "h":24, "w":10, "r":50, "e":"NATURE", "scale":1.2},
    "The Colossus":  {"s": GREY, "h":35, "w":16, "r":20, "e":"FIRE",   "scale":1.3},
    "Grave Titan":   {"s": GREY, "h":35, "w":14, "r":20, "e":"NATURE", "scale":1.3},
    "Cerberus":      {"s": GREY, "h":22, "w":30, "r":15, "e":"FIRE",   "shape":"BEAST", "scale":1.3},
    "Thunderbird":   {"s": GREY, "h":25, "w":25, "r":20, "e":"NATURE", "shape":"FLY", "scale":1.3},
    "War Mecha":     {"s": GREY, "h":30, "w":22, "r":70, "e":"FIRE",   "scale":1.3},
    "The Imperator": {"s": GREY, "h":32, "w":12, "r":15, "e":"WATER",  "scale":1.3},
    "Archangel":     {"s": GREY, "h":35, "w":18, "r":20, "e":"WATER",  "shape":"FLY", "scale":1.3},
    "Ancient Dragon":{"s": GREY, "h":25, "w":40, "r":30, "e":"FIRE",   "shape":"FLY", "scale":1.3},
    "Lich King":     {"s": GREY, "h":38, "w":12, "r":60, "e":"NATURE", "scale":1.3},
}

WILD_POOL = ["Rat", "Bat", "Spider", "Slime", "Peasant", "Cultist", "Zombie", "Skeleton", 
    "Lizard", "Kobold", "Wolf", "Boar", "Hawk", "Eagle", "Bear", "Bandit", "Thief", 
    "Rogue", "Ninja", "Goblin", "Orc", "Warrior", "Archer", "Musketeer", "Bombardier", 
    "Barbarian", "Samurai", "Mage", "Cleric", "Monk", "Druid", "Bard", "Necro", "Witch", 
    "Plague Doc", "Vampire", "Paladin", "Frost Witch"]

ITEM_TIERS = {
    "Rusty Sword":0, "Old Stick":0, "Tattered Robe":0, "Wood Axe":0, "Cloth Tunic":0,
    "Iron Broadsword":1, "Apprentice Wand":1, "Leather Vest":1, "Battle Axe":1, "Short Bow":1,
    "Steel Blade":2, "Oak Stave":2, "Rusted Mail":1, "Iron Plate":2, "Mithril Sword":2,
    "Excalibur":3, "Void Scepter":3, "Dragon Scale":3, "Diamond Plate":3, "Meteor Staff":3,
    "Ring of Health":2, "Titan Glove":3, "Lucky Coin":1, "Obsidian Gem":2
}

RECIPES = [
    {"type":"FUSION", "req":{"Mage":4,"Warrior":1}, "sac":"Warrior", "family":"GOLEM"},
    {"type":"FUSION", "req":{"Zombie":3,"Necro":1}, "sac":"Necro", "family":"UNDEAD"},
    {"type":"FUSION", "req":{"Wolf":4}, "sac":"Wolf", "family":"BEAST"},
    {"type":"FUSION", "req":{"Rat": 5}, "sac":"Rat", "spawn":"Rat King"},
    {"type":"FUSION", "req":{"Spider": 5}, "sac":"Spider", "spawn":"Spider Queen"},
    {"type":"FUSION", "req":{"Slime": 3, "Mage": 2}, "sac":"Mage", "spawn":"Fire Elem"},
    {"type":"FUSION", "req":{"Slime": 3, "Frost Witch": 2}, "sac":"Frost Witch", "spawn":"Ice Elem"},
    {"type":"FUSION", "req":{"Orc": 1, "Goblin": 4}, "sac":"Orc", "spawn":"Orc Warlord"},
    {"type":"FUSION", "req":{"Cultist":5,"Peasant":1}, "sac":"Peasant", "spawn":"Demon"},
    {"type":"FUSION", "req":{"Musketeer":3, "Bombardier":2}, "sac":"Musketeer", "spawn":"Steam Tank"},
    {"type":"FUSION", "req":{"Steam Tank":1, "Iron Golem":1}, "sac":"Steam Tank", "spawn":"War Mecha"},
    {"type":"FUSION", "req":{"Hawk":4, "Mage":1}, "sac":"Hawk", "spawn":"Storm Crow"},
    {"type":"FUSION", "req":{"Storm Crow":1, "Ice Elem":1}, "sac":"Storm Crow", "spawn":"Thunderbird"},
    {"type":"FUSION", "req":{"Warrior":3, "Samurai":2}, "sac":"Warrior", "spawn":"Royal Guard"},
    {"type":"FUSION", "req":{"Royal Guard":1, "Crusader":1}, "sac":"Royal Guard", "spawn":"The Imperator"},
    {"type":"FUSION", "req":{"Wolf":4, "Cultist":1}, "sac":"Wolf", "spawn":"Hellhound"},
    {"type":"FUSION", "req":{"Lizard":3, "Bat":2}, "sac":"Lizard", "spawn":"Wyvern"},
    {"type":"FUSION", "req":{"Eagle":2, "Wolf":2}, "sac":"Eagle", "spawn":"Griffin"},
    {"type":"FUSION", "req":{"Lizard":3, "Spider":1}, "sac":"Lizard", "spawn":"Basilisk"},
    {"type":"FUSION", "req":{"Wyvern":1, "Fire Elem":1}, "sac":"Wyvern", "spawn":"Ancient Dragon"},
    {"type":"FUSION", "req":{"Paladin":3, "Warrior":1}, "sac":"Paladin", "spawn":"Crusader"},
    {"type":"FUSION", "req":{"Cleric":3, "Eagle":1}, "sac":"Cleric", "spawn":"Seraph"},
    {"type":"FUSION", "req":{"Seraph":1, "Crusader":1}, "sac":"Seraph", "spawn":"Archangel"},
    {"type":"FUSION", "req":{"Skeleton":3, "Warrior":1}, "sac":"Warrior", "spawn":"Death Knight"},
    {"type":"FUSION", "req":{"Vampire":1, "Bat":4}, "sac":"Vampire", "spawn":"Vampire Lord"},
    {"type":"FUSION", "req":{"Death Knight":1, "Necro":1}, "sac":"Death Knight", "spawn":"Lich King"},
    {"type":"FUSION", "req":{"Wolf":3, "Druid":1}, "sac":"Druid", "spawn":"Werewolf"},
    {"type":"FUSION", "req":{"Bear":2, "Druid":1}, "sac":"Druid", "spawn":"Werebear"},
    {"type":"FUSION", "req":{"Boar":3, "Druid":1}, "sac":"Druid", "spawn":"Wereboar"},
    {"type":"FUSION", "req":{"Ninja":1, "Rogue":2, "Thief":2}, "sac":"Ninja", "spawn":"Master Assassin"},
    {"type":"FUSION", "req":{"Peasant":1, "Cleric":4}, "sac":"Peasant", "spawn":"The Avatar"},
    {"type":"FUSION", "req":{"Monk":3, "Bard":2}, "sac":"Monk", "spawn":"Dervish"},
    {"type":"FUSION", "req":{"Beastmaster":2, "Falconer":2}, "sac":"Beastmaster", "spawn":"Huntmaster"},
    {"type":"SPELL", "name":"Divine Light", "req":{"Cleric":3}, "cd":600, "heal":25, "fx":GREEN},
    {"type":"SPELL", "name":"Smite", "req":{"Paladin":3}, "cd":350, "dmg":30, "visual":"BEAM", "fx":YELLOW},
    {"type":"SPELL", "name":"Inferno", "req":{"Lizard":3, "Mage":1}, "cd":700, "dmg":15, "aoe":True, "fx":RED},
    {"type":"SPELL", "name":"Raise Dead", "req":{"Necro":3}, "cd":800, "summon":"Skeleton", "fx":WHITE},
    {"type":"SPELL", "name":"Shield Wall", "req":{"Warrior":4}, "cd":400, "buff":"DEF", "val":10, "fx":BLUE},
    {"type":"SPELL", "name":"War Cry", "req":{"Barbarian":3}, "cd":500, "buff":"SPD", "val":2, "fx":RED},
]

FUSION_RESULTS = {
    "GOLEM": {0: "Earth Golem", 2: "Rust Golem", 4: "Iron Golem", 6: "The Colossus"},
    "UNDEAD": {0: "Abomination", 3: "Lich Lord", 6: "Grave Titan"},
    "BEAST": {0: "Alpha Wolf", 3: "Fenrir", 5: "Cerberus"}
}

WEAPONS = {
    "Rusty Sword":    {"col": GREY,    "dmg": 1,  "len":4, "cost": 0,    "style":"SWORD", "classes": ["Warrior", "Paladin", "Dk.Knight", "Barbarian", "Samurai", "Skeleton", "Zombie", "Bandit"]},
    "Iron Broadsword":{"col": CYAN,    "dmg": 4,  "len":6, "cost": 150,  "style":"SWORD", "classes": ["Warrior", "Paladin", "Dk.Knight", "Barbarian", "Samurai", "Water Elem"]},
    "Steel Blade":    {"col": WHITE,   "dmg": 7,  "len":6, "cost": 450,  "style":"SWORD", "classes": ["Warrior", "Paladin", "Samurai"]},
    "Mithril Sword":  {"col": CYAN,    "dmg": 12, "len":7, "cost": 1200, "style":"SWORD", "classes": ["Warrior", "Paladin"]},
    "Katana":         {"col": WHITE,   "dmg": 10, "len":6, "cost": 900,  "style":"SWORD", "classes": ["Samurai", "Ninja"]},
    "Dark Blade":     {"col": MAGENTA, "dmg": 9,  "len":7, "cost": 600,  "style":"SWORD", "classes": ["Dk.Knight", "Necro", "Vampire"]},
    "Excalibur":      {"col": YELLOW,  "dmg": 20, "len":8, "cost": 3000, "style":"SWORD", "classes": ["Paladin", "Warrior", "Crusader"]},
    "Wood Axe":       {"col": GREY,    "dmg": 3,  "len":5, "cost": 100,  "style":"AXE",   "classes": ["Warrior", "Barbarian", "Orc", "Peasant", "Treant"]},
    "Battle Axe":     {"col": RED,     "dmg": 9,  "len":6, "cost": 800,  "style":"AXE",   "classes": ["Warrior", "Barbarian", "Orc", "Nature Elem"]},
    "Great Axe":      {"col": RED,     "dmg": 15, "len":7, "cost": 1500, "style":"AXE",   "classes": ["Barbarian", "Orc", "Orc Warlord"]},
    "Iron Knuckles":  {"col": GREY,    "dmg": 5,  "len":3, "cost": 250,  "style":"DAGGER","classes": ["Monk", "War Drummer"]},
    "Holy Hammer":    {"col": YELLOW,  "dmg": 6,  "len":5, "cost": 450,  "style":"HAMMER","classes": ["Paladin", "Cleric", "Monk", "Paladin Captain", "Crusader"]},
    "Golden Ankh":    {"col": YELLOW,  "dmg": 7,  "len":5, "cost": 600,  "style":"HAMMER","classes": ["Cleric", "Paladin", "Seraph"]},
    "Mjolnir":        {"col": CYAN,    "dmg": 18, "len":5, "cost": 2500, "style":"HAMMER","classes": ["Warrior", "Paladin"]},
    "Lute":           {"col": BROWN,   "dmg": 0,  "len":5, "cost": 300,  "style":"STAFF", "classes": ["Bard"]}, 
    "Old Stick":      {"col": BROWN,   "dmg": 1,  "len":4, "cost": 0,    "style":"STAFF", "classes": ["Mage", "Cleric", "Necro", "Lich", "Druid", "Witch", "Plague Doc", "Cultist"]},
    "Apprentice Wand":{"col": BLUE,    "dmg": 5,  "len":5, "cost": 200,  "style":"STAFF", "classes": ["Mage", "Cleric", "Necro", "Witch", "Frost Witch"]},
    "Oak Stave":      {"col": GREEN,   "dmg": 6,  "len":6, "cost": 300,  "style":"STAFF", "classes": ["Druid", "Treant"]},
    "Skull Wand":     {"col": WHITE,   "dmg": 8,  "len":5, "cost": 500,  "style":"STAFF", "classes": ["Necro", "Lich", "Cultist"]},
    "Hex Rod":        {"col": MAGENTA, "dmg": 8,  "len":5, "cost": 500,  "style":"STAFF", "classes": ["Witch", "Plague Doc", "Basilisk"]},
    "Arcane Staff":   {"col": MAGENTA, "dmg": 10, "len":8, "cost": 850,  "style":"STAFF", "classes": ["Mage", "Necro", "Witch", "Frost Witch"]},
    "Void Scepter":   {"col": RED,     "dmg": 14, "len":6, "cost": 1500, "style":"STAFF", "classes": ["Mage", "Lich"]},
    "Short Bow":      {"col": BROWN,   "dmg": 2,  "len":4, "cost": 0,    "style":"BOW",   "classes": ["Archer", "Ninja", "Rogue", "Goblin", "Thief", "Lizard"]},
    "Elven Longbow":  {"col": GREEN,   "dmg": 6,  "len":6, "cost": 350,  "style":"BOW",   "classes": ["Archer", "Rogue"]},
    "Sniper Bow":     {"col": YELLOW,  "dmg": 10, "len":7, "cost": 900,  "style":"BOW",   "classes": ["Archer"]},
    "Dragon Bow":     {"col": RED,     "dmg": 16, "len":8, "cost": 2000, "style":"BOW",   "classes": ["Archer"]},
    "Musket":         {"col": GREY,    "dmg": 12, "len":6, "cost": 600,  "style":"BOW",   "classes": ["Musketeer"]},
    "Fire Bolt":      {"col": RED,     "dmg": 8,  "len":0, "cost": 0,    "style":"BOW",   "classes": ["Fire Elem"]}, 
    "Steel Daggers":  {"col": GREY,    "dmg": 5,  "len":3, "cost": 250,  "style":"DAGGER","classes": ["Ninja", "Rogue", "Thief", "Bandit", "Vampire"]},
    "Assassin Blade": {"col": RED,     "dmg": 12, "len":4, "cost": 1000, "style":"DAGGER","classes": ["Ninja", "Rogue", "Vampire"]},
    "Bomb":           {"col": BLACK,   "dmg": 25, "len":2, "cost": 200,  "style":"DAGGER","classes": ["Bombardier"]},
    "Pitchfork":      {"col": BROWN, "dmg": 4,  "len": 6, "cost": 50,    "style": "STAFF",  "classes": ["Peasant"]},
    "Iron Claws":     {"col": GREY,   "dmg": 5,  "len": 3, "cost": 300,  "style": "DAGGER", "classes": ["Wolf", "Dire Wolf", "Bear", "Polar Bear", "Wolfman", "Hellhound", "Lizard"]},
    "Mithril Fang":   {"col": CYAN,   "dmg": 10, "len": 3, "cost": 1200, "style": "DAGGER", "classes": ["Wolf", "Dire Wolf", "Bear", "Polar Bear", "Hellhound", "Wyvern"]},
    "Magic Flute":    {"col": YELLOW, "dmg": 4,  "len": 5, "cost": 400,  "style": "STAFF",  "classes": ["Bard"]},
    "Nunchucks":      {"col": BLACK,  "dmg": 7,  "len": 4, "cost": 500,  "style": "HAMMER", "classes": ["Monk"]},
    "War Scythe":     {"col": GREY,   "dmg": 14, "len": 7, "cost": 1000, "style": "AXE",    "classes": ["Necro", "Wraith", "Peasant", "Death Knight"]}, 
    "Rusty Shiv":     {"col": BROWN,  "dmg": 3,  "len": 2, "cost": 50,   "style": "DAGGER", "classes": ["Goblin", "Thief", "Rat"]},
    "Dragon Tooth":   {"col": RED,    "dmg": 15, "len": 4, "cost": 1800, "style": "DAGGER", "classes": ["Lizard", "Wyvern", "Dragon"]},
    "Morning Star":   {"col": GOLD,   "dmg": 12, "len": 6, "cost": 1500, "style": "HAMMER", "classes": ["Cleric", "Paladin", "Crusader"]},
    "Bone Blade":     {"col": WHITE,  "dmg": 11, "len": 6, "cost": 1100, "style": "SWORD",  "classes": ["Skeleton", "Death Knight"]},
}

ARMORS = {
    "Tattered Robe":  {"def": 0, "cost": 0,   "col": GREY,   "helm": False, "classes": ["Mage", "Cleric", "Necro", "Zombie", "Witch", "Druid", "Monk", "Plague Doc", "Cultist"]},
    "Silk Robe":      {"def": 1, "cost": 100, "col": WHITE,  "helm": False, "classes": ["Mage", "Cleric", "Necro", "Witch", "Frost Witch", "Bard"]},
    "Druid Cloak":    {"def": 2, "cost": 250, "col": DARK_GREEN,"helm":False,"classes": ["Druid", "Treant"]},
    "Mystic Robe":    {"def": 4, "cost": 600, "col": MAGENTA,"helm": False, "classes": ["Mage", "Cleric", "Necro", "Witch"]},
    "Cloth Tunic":    {"def": 0, "cost": 0,   "col": BROWN,  "helm": False, "classes": ["Archer", "Ninja", "Rogue", "Barbarian", "Goblin", "Skeleton", "Peasant", "Bandit", "Thief", "Musketeer", "Lizard"]},
    "Leather Vest":   {"def": 2, "cost": 200, "col": (160, 82, 45), "helm": False, "classes": ["Archer", "Ninja", "Rogue", "Barbarian", "Bandit", "Musketeer", "Bombardier", "Lizard"]},
    "Studded Gear":   {"def": 5, "cost": 650, "col": GREY,   "helm": False, "classes": ["Archer", "Ninja", "Rogue", "Barbarian"]},
    "Shadow Cloak":   {"def": 6, "cost": 1200,"col": BLACK,  "helm": True,  "classes": ["Ninja", "Rogue", "Vampire", "Death Knight"]},
    "Rusted Mail":    {"def": 1, "cost": 0,   "col": (100,100,100), "helm": True, "classes": ["Warrior", "Paladin", "Dk.Knight", "Samurai", "Orc", "War Drummer"]},
    "Iron Plate":     {"def": 4, "cost": 350, "col": WHITE,  "helm": True, "classes": ["Warrior", "Paladin", "Dk.Knight", "Samurai", "Paladin Captain", "Crusader"]},
    "Samurai Armor":  {"def": 5, "cost": 700, "col": RED,    "helm": True, "classes": ["Samurai"]},
    "Dragon Scale":   {"def": 8, "cost": 1500,"col": (255, 215, 0), "helm": True, "classes": ["Warrior", "Paladin", "Dk.Knight", "Dragon"]},
    "Straw Hat":      {"def": 1, "cost": 25,  "col": YELLOW, "helm": True,  "classes": ["Peasant"]},
    "Spiked Collar":  {"def": 3, "cost": 250, "col": RED,    "helm": True,  "classes": ["Wolf", "Dire Wolf", "Bear", "Polar Bear", "Hellhound", "Cerberus"]},
    "Black Belt":     {"def": 2, "cost": 300, "col": BLACK,  "helm": False, "classes": ["Monk", "Ninja"]},
    "Bone Armor":     {"def": 4, "cost": 500, "col": WHITE,  "helm": False, "classes": ["Skeleton", "Necro", "Lich", "Barbarian", "Death Knight"]},
    "Blessed Plate":  {"def": 9, "cost": 2000,"col": GOLD,   "helm": True,  "classes": ["Paladin", "Crusader", "Archangel"]},
    "Void Robe":      {"def": 5, "cost": 1800,"col": BLACK,  "helm": True,  "classes": ["Necro", "Lich", "Lich King"]},
}

ARTIFACTS = {
    "Ring of Health": {"hp": 20,  "str": 0, "col": GREEN},
    "Titan Glove":    {"hp": 0,   "str": 5, "col": RED},
    "Lucky Coin":     {"hp": 5,   "str": 2, "col": YELLOW},
    "Obsidian Gem":   {"hp": 50,  "str": -2,"col": BLACK}, 
    "Holy Grail":     {"hp": 100, "str": 0, "col": GOLD},   # For Archangel
    "Cursed Crown":   {"hp": 0,   "str": 10,"col": MAGENTA},# For Lich King
    "Dragon Heart":   {"hp": 50,  "str": 5, "col": RED},    # For Ancient Dragon
}

MERCHANT_ITEMS = {
    "Pitchfork":      {"col": BROWN,  "dmg": 4,  "len": 6, "cost": 50,   "style": "STAFF",  "classes": ["Peasant"]},
    "Straw Hat":      {"def": 1, "cost": 25,  "col": YELLOW, "helm": True,  "classes": ["Peasant"]},
    "Spiked Collar":  {"def": 3, "cost": 250, "col": RED,    "helm": True,  "classes": ["Wolf", "Dire Wolf", "Bear"]},
    "Glass Dagger":   {"col": CYAN, "dmg": 25, "len":3, "cost": 500, "style":"DAGGER", "classes": ["Ninja", "Rogue", "Thief", "Vampire"]}, 
    "Meteor Staff":   {"col": RED,  "dmg": 18, "len":6, "cost": 2500, "style":"STAFF", "classes": ["Mage", "Lich", "Fire Elem"]},
    "Diamond Plate":  {"def": 10,   "cost": 3000,"col": CYAN, "helm": True, "classes": ["Warrior", "Paladin", "Golem"]},
    "Swift Boots":    {"hp": 0, "str": 0, "col": BLUE}, 
    "Vampire Fang":   {"hp": 0, "str": 3, "col": RED},  
    "Ancient Coin":   {"hp": 50,"str": 5, "col": GOLD}, 
    "Bone Blade":     {"col": WHITE,  "dmg": 11, "len": 6, "cost": 1100, "style": "SWORD",  "classes": ["Skeleton", "Death Knight"]},
    "Holy Grail":     {"hp": 100, "str": 0, "col": GOLD, "cost": 5000},
    "Cursed Crown":   {"hp": 0,   "str": 10,"col": MAGENTA, "cost": 5000},
}
WEAPONS.update({k:v for k,v in MERCHANT_ITEMS.items() if "dmg" in v})
ARMORS.update({k:v for k,v in MERCHANT_ITEMS.items() if "def" in v})
ARTIFACTS.update({k:v for k,v in MERCHANT_ITEMS.items() if "hp" in v})

DUNGEONS = [
    {"name": "Rat Cellar",    "lvl": 1, "waves": 6, "reward": 50,  "type": "CAVE"},
    {"name": "Farmers Field", "lvl": 2, "waves": 10, "reward": 100,  "type": "FOREST"},
    {"name": "Goblin Camp",   "lvl": 3, "waves": 18, "reward": 250, "type": "FOREST"},
    {"name": "Bandit Road",   "lvl": 4, "waves": 25, "reward": 500, "type": "FOREST"},
    {"name": "Old Crypt",     "lvl": 5, "waves": 35, "reward": 750, "type": "CAVE"},
    {"name": "Orc Outpost",   "lvl": 6, "waves": 45, "reward": 1000, "type": "CAVE"},
    {"name": "Frozen Waste",  "lvl": 7, "waves": 60, "reward": 1500, "type": "SNOW"}, 
    {"name": "Stone Keep",    "lvl": 8,"waves": 75,"reward": 2000, "type": "CASTLE"},
    {"name": "Haunted Wood",  "lvl": 9,"waves": 100,"reward": 3000, "type": "FOREST"},
    {"name": "Lava Pits",     "lvl": 10,"waves": 125,"reward": 3500, "type": "LAVA"},
    {"name": "Dark Tower",    "lvl": 11,"waves": 150,"reward": 4000,"type": "CASTLE"},
    {"name": "Ice Peak",      "lvl": 12,"waves": 175,"reward": 4500,"type": "SNOW"},
    {"name": "Demon Gate",    "lvl": 13,"waves": 200,"reward": 5000,"type": "LAVA"},
    {"name": "The Void",      "lvl": 14,"waves": 250,"reward": 6000,"type": "CAVE"},
    {"name": "Heaven's End",  "lvl": 15,"waves": 300,"reward": 7500,"type": "SNOW"},
    {"name": "DEV ROOM",      "lvl": 16,"waves": 500,"reward": 9999,"type": "LAVA"},
]

# --- 4. LOGIC CLASSES ---
class Particle:
    def __init__(self, x, y, color, mode="PIXEL", text="", vx=None, vy=None, grav=0.4):
        self.x = x; self.y = y; self.col = color; self.mode = mode; self.text = text
        self.life = random.randint(15, 40); self.grav = grav 
        if vx is None:
            if self.mode == "PIXEL": self.vx = random.uniform(-2.0, 2.0); self.vy = random.uniform(-3.0, -1.0)
            else: self.vx = 0; self.vy = -0.5; self.grav = 0
        else: self.vx = vx; self.vy = vy
    def update(self):
        self.x += self.vx; self.y += self.vy; self.vy += self.grav; self.life -= 1
        return self.life > 0
    def draw(self, lcd):
        if self.mode == "PIXEL": 
            lcd.pixel(int(self.x), int(self.y), self.col)
            if self.grav > 0.1: lcd.pixel(int(self.x)+1, int(self.y), self.col)
        else: lcd.text(self.text, int(self.x), int(self.y), self.col)

class Projectile:
    def __init__(self, start_x, start_y, target_walker, damage, is_crit, element):
        self.x = start_x; self.y = start_y; self.target = target_walker
        self.damage = damage; self.is_crit = is_crit; self.element = element; self.speed = 4; self.active = True
        self.col = ELEMENTS[element]['col']; self.is_arrow = (element == "NATURE") 
        dx = target_walker.x - start_x; dy = target_walker.y - start_y; dist = math.sqrt(dx*dx + dy*dy)
        if dist == 0: dist = 1
        self.vx = (dx / dist) * self.speed; self.vy = (dy / dist) * self.speed
    def update(self, particle_list):
        if not self.active: return False
        self.x += self.vx; self.y += self.vy
        dx = self.x - self.target.x; dy = self.y - self.target.y
        if math.sqrt(dx*dx + dy*dy) < 6: self.hit(particle_list); return False 
        if self.x < -10 or self.x > 170: return False
        return True
    def hit(self, particle_list):
        self.target.take_damage(self.damage, self.is_crit)
        p_col = WHITE if not self.is_crit else YELLOW
        txt = str(self.damage) + ("!" if self.is_crit else "")
        particle_list.append(Particle(self.target.x, self.target.y - 8, p_col, "TEXT", txt))
        blood_col = ELEMENTS[self.target.unit.element]['col']
        for _ in range(6): particle_list.append(Particle(self.target.x+5, self.target.y+5, blood_col, "PIXEL"))
    def draw(self, lcd):
        if self.is_arrow:
            lcd.line(int(self.x), int(self.y), int(self.x-self.vx), int(self.y-self.vy), BROWN)
            lcd.pixel(int(self.x), int(self.y), WHITE) 
        else: lcd.fill_rect(int(self.x), int(self.y), 3, 3, self.col)

class FantasyUnit:
    def __init__(self, seed=None, load_data=None, manual_type=None, level_scale=1):
        self.temp_str = 0; self.temp_def = 0; self.has_lifesteal = False; self.is_fanatic = False
        self.cd = 0; self.flash_timer = 0; self.is_firing = False
        
        if load_data:
            self.dna = load_data.get('dna', random.randint(0, 100))
            self.race = load_data['r']; self.level = load_data['l']; self.xp = load_data['x']; self.hp = load_data['hp']
            self.max_hp = load_data['mhp']; self.str = load_data['s']; self.name = load_data['n']; self.range = load_data['rng']
            if 'el' in load_data: self.element = load_data['el']
            else: self.element = UNIT_DEFS.get(self.race, UNIT_DEFS["Warrior"])['e']
            self.weapon_name = load_data.get('wpn', "Training Sword"); self.armor_name = load_data.get('arm', "Cloth Tunic")
            self.artifact = load_data.get('art', None)
        else:
            self.dna = random.randint(0, 100) 
            if seed: random.seed(seed)
            if manual_type: self.race = manual_type
            else: self.race = random.choice(WILD_POOL)
                
            if self.race not in UNIT_DEFS: self.race = "Warrior"
            d = UNIT_DEFS[self.race]; self.element = d['e']; self.level = level_scale; self.xp = 0
            
            base_hp = d['h']; base_str = d.get('w', 5)
            scale_mult = d.get('scale', 1.0)
            
            self.max_hp = int((base_hp + (self.level * 10)) * scale_mult)
            self.str = int((base_str + (self.level * 2)) * scale_mult)
            self.hp = self.max_hp
            
            self.range = d['r']; self.name = f"{self.race}"
            self.weapon_name = "Training Sword"; self.armor_name = "Cloth Tunic"
            
            if self.race in ["Mage", "Cleric", "Plague Doc", "Cultist", "Frost Witch"]: self.weapon_name = "Old Stick"; self.armor_name = "Tattered Robe"
            if self.race in ["Necro", "Lich", "Lich Lord", "Lich King"]: self.weapon_name = "Skull Wand"; self.armor_name = "Tattered Robe"
            if self.race in ["Witch", "Basilisk"]: self.weapon_name = "Hex Rod"; self.armor_name = "Tattered Robe"
            if self.race in ["Druid", "Treant"]: self.weapon_name = "Oak Stave"; self.armor_name = "Druid Cloak"
            if self.race in ["Monk", "War Drummer"]: self.weapon_name = "Iron Knuckles"; self.armor_name = "Tattered Robe"
            if self.race in ["Archer", "Rogue", "Thief", "Falconer"]: self.weapon_name = "Short Bow"
            if self.race == "Musketeer": self.weapon_name = "Musket"; self.armor_name = "Leather Vest"
            if self.race == "Bombardier": self.weapon_name = "Bomb"; self.armor_name = "Leather Vest"
            if self.race == "Bard": self.weapon_name = "Lute"; self.armor_name = "Silk Robe"
            if self.race == "Beastmaster": self.weapon_name = "Whip"; self.armor_name = "Leather Vest"
            
            d_shape = d.get('shape', 'HUMAN')
            if d_shape in ["BEAST", "FLY", "BLOB"] or d.get('scale', 1.0) > 1.2: self.weapon_name = "Claws"; self.armor_name = "Hide"
            if self.race == "Fire Elem": self.weapon_name = "Fire Bolt"; self.armor_name = "Tattered Robe"
            self.artifact = None
            if seed: random.seed(time.time())
            
    def get_power(self):
        dmg = WEAPONS.get(self.weapon_name, {'dmg':0})['dmg']
        bonus = ARTIFACTS[self.artifact]['str'] if self.artifact else 0
        return self.str + dmg + bonus + self.temp_str
    def get_defense(self): 
        base = ARMORS.get(self.armor_name, {'def':0})['def']
        return base + self.temp_def
    def reset_buffs(self):
        self.temp_str = 0; self.temp_def = 0; self.has_lifesteal = False; self.is_fanatic = False
    def gain_xp(self, amount):
        self.xp += amount; req = self.level * 100
        if self.xp >= req:
            self.xp -= req; self.level += 1; self.max_hp += 15; self.hp = self.max_hp; self.str += 3; return True
        return False
    def to_dict(self):
        return {'r': self.race, 'l': self.level, 'x': self.xp, 'hp': self.hp, 'mhp': self.max_hp, 's': self.str, 
                'n': self.name, 'rng': self.range, 'el': self.element, 'wpn': self.weapon_name, 'arm': self.armor_name, 'art': self.artifact, 'dna': self.dna}
    def draw(self, lcd, x, y, side="LEFT"):
        d = UNIT_DEFS.get(self.race, UNIT_DEFS["Warrior"])
        shape = d.get('shape', 'HUMAN')
        scale = d.get('scale', 1.0)
        body_col = d['s']
        if self.armor_name in ARMORS and "Tunic" not in self.armor_name:
             if ARMORS[self.armor_name]['col'] != GREY: body_col = ARMORS[self.armor_name]['col']
        if self.flash_timer > 0: body_col = WHITE; self.flash_timer -= 1
        w = int(d['w'] * scale); h = int(d['h'] * scale)
        if shape == "BEAST": self.draw_beast(lcd, x, y, side, w, h, body_col)
        elif shape == "FLY": self.draw_fly(lcd, x, y, side, w, h, body_col)
        elif shape == "BLOB": self.draw_blob(lcd, x, y, side, w, h, body_col)
        else: self.draw_human(lcd, x, y, side, w, h, body_col)
    def draw_human(self, lcd, x, y, side, w, h, col):
        lcd.fill_rect(x, y + (h//3), w, h - (h//3), col) 
        head_sz = w if w < 8 else w - 2
        hx = x + (w-head_sz)//2; hy = y + (h//3) - head_sz
        if hy < y: hy = y 
        head_col = SKIN
        if "Helm" in self.armor_name or "Plate" in self.armor_name or "Colossus" in self.race: head_col = col
        if col == WHITE: head_col = WHITE
        lcd.fill_rect(hx, hy, head_sz, head_sz, head_col)
        if w > 4: lcd.fill_rect(x + (w//2) - 1, y + h - 2, 2, 2, BLACK)
        self.draw_weapon(lcd, x, y, side, w, col)
    def draw_beast(self, lcd, x, y, side, w, h, col):
        body_h = h // 2; body_y = y + (h - body_h)
        lcd.fill_rect(x, body_y, w, body_h, col)
        head_sz = body_h - 2; 
        if head_sz < 4: head_sz = 4
        head_y = body_y - 2
        if side == "LEFT": head_x = x + w - 2
        else: head_x = x - head_sz + 2
        lcd.fill_rect(head_x, head_y, head_sz, head_sz, col)
        leg_w = max(2, w // 4)
        lcd.fill_rect(x+1, y+h, leg_w, 2, col)
        lcd.fill_rect(x+w-leg_w-1, y+h, leg_w, 2, col)
    def draw_fly(self, lcd, x, y, side, w, h, col):
        cx = x + (w//2); cy = y + (h//2)
        lcd.fill_rect(cx-2, cy-2, 4, 8, col)
        lcd.line(cx-2, cy, x, y, col); lcd.line(x, y, x, y+6, col); lcd.line(x, y+6, cx-2, cy+4, col)
        lcd.line(cx+2, cy, x+w, y, col); lcd.line(x+w, y, x+w, y+6, col); lcd.line(x+w, y+6, cx+2, cy+4, col)
    def draw_blob(self, lcd, x, y, side, w, h, col):
        lcd.fill_rect(x, y, w, h, col)
        if col != WHITE:
            ex = x + (w//2); ey = y + (h//3)
            lcd.pixel(ex-2, ey, WHITE); lcd.pixel(ex+2, ey, WHITE)
    def draw_weapon(self, lcd, x, y, side, w, col):
        if col == WHITE: return 
        w_data = WEAPONS.get(self.weapon_name, {"col":GREY, "len":4, "style":"SWORD"})
        w_col = w_data['col']; w_len = w_data['len']
        if self.level > 15: w_len = int(w_len * 1.5)
        wx = x+w+1 if side == "LEFT" else x-1; 
        hand_y = y + (w_len + 4); 
        if self.race in ["Rat", "Wolf", "Spider", "Werewolf", "Werebear"]: hand_y = y + 8 
        tip_y = hand_y - w_len
        style = w_data.get('style')
        if style == "BOW": 
             lcd.line(wx, hand_y+4, wx, hand_y-4, BROWN); lcd.pixel(wx+ (1 if side=="LEFT" else -1), hand_y, WHITE)
        elif style == "STAFF":
             lcd.line(wx, hand_y+4, wx, tip_y, w_col); lcd.pixel(wx, tip_y-1, RED if self.dna > 50 else BLUE) 
        else:
             lcd.line(wx, hand_y, wx, tip_y, w_col)

class Walker:
    def __init__(self, unit, side):
        self.unit = unit; self.side = side 
        self.state = "WALK"; self.target = None; self.attack_cd = 0
        if side == "LEFT": self.x = -10; self.dir = 1
        else: self.x = 170; self.dir = -1
        self.y = random.randint(60, 110); self.speed = random.uniform(0.8, 1.5)
        self.anim_offset = 0; self.status = {} 
    def draw(self, lcd):
        if self.state == "DEAD": 
            lcd.fill_rect(int(self.x), int(self.y)+8, 10, 4, (50,50,50)); return
        draw_x = int(self.x + (self.anim_offset * self.dir))
        d = UNIT_DEFS.get(self.unit.race, UNIT_DEFS["Warrior"])
        w = int(d['w'] * d.get('scale', 1.0))
        if "SHIELD" in self.status: lcd.rect(draw_x-2, int(self.y)-2, w+4, 12, BLUE)
        self.unit.draw(lcd, draw_x, int(self.y), self.side)
        el_col = ELEMENTS[self.unit.element]['col']
        lcd.fill_rect(draw_x+2, int(self.y)-3, 4, 2, el_col)
    def update(self, all_walkers, particle_list, projectile_list):
        if self.state == "DEAD": return
        if self.x < -30 or self.x > 190: self.state = "DEAD"; return
        current_speed = self.speed
        if "SPD" in self.status: current_speed *= 1.5
        if self.status:
            for k in list(self.status.keys()):
                self.status[k] -= 1
                if self.status[k] <= 0: del self.status[k]
            if "POISON" in self.status and random.randint(0, 30) == 0: self.take_damage(1, False)
        
        d = UNIT_DEFS.get(self.unit.race, UNIT_DEFS["Warrior"])
        is_necro = self.unit.race in ["Necro", "Lich", "Lich Lord", "Lich King"]
        if self.state == "WALK":
            self.x += current_speed * self.dir
            found_heal = False
            if is_necro: 
                for other in all_walkers:
                    if other.side == self.side and other.state != "DEAD" and other != self:
                        if other.unit.hp < other.unit.max_hp * 0.7:
                             if math.sqrt((self.x-other.x)**2 + (self.y-other.y)**2) < 80:
                                 self.target = other; self.state = "BUFF_MODE"; found_heal = True; break
            if not found_heal:
                closest_dist = 999; closest_enemy = None
                for other in all_walkers:
                    if other.side != self.side and other.state != "DEAD":
                        dist = math.sqrt((self.x-other.x)**2 + (self.y-other.y)**2)
                        if dist < 120 and dist < closest_dist: closest_dist = dist; closest_enemy = other
                if closest_enemy: self.state = "FIGHT"; self.target = closest_enemy
        if self.state == "FIGHT" or self.state == "BUFF_MODE":
            if self.target is None or self.target.state == "DEAD": self.state = "WALK"; self.target = None; return
            target_w = UNIT_DEFS.get(self.target.unit.race, {}).get('w', 8) * UNIT_DEFS.get(self.target.unit.race, {}).get('scale', 1.0)
            target_x_edge = self.target.x if self.side == "RIGHT" else (self.target.x + target_w)
            dist = math.sqrt((target_x_edge - self.x)**2 + (self.target.y - self.y)**2)
            req_range = self.unit.range if self.unit.range > 10 else 5 
            if dist > req_range:
                self.x += ((target_x_edge - self.x) / dist) * current_speed
                self.y += ((self.target.y - self.y) / dist) * current_speed
            else:
                self.attack_cd += 1
                if self.attack_cd > 20: 
                    self.attack_cd = 0
                    if self.state == "BUFF_MODE": 
                        heal = int(self.unit.level * 4) + 5
                        self.target.unit.hp = min(self.target.unit.hp + heal, self.target.unit.max_hp)
                        particle_list.append(Particle(self.target.x, self.target.y-10, GREEN, "TEXT", f"+{heal}"))
                        self.state = "WALK"
                    else: 
                        base_dmg = self.unit.get_power()
                        mult = 1.0 
                        final_dmg = int(base_dmg * mult); is_crit = (mult > 1.0)
                        if self.unit.range < 20:
                            self.target.take_damage(final_dmg, is_crit)
                            if self.unit.has_lifesteal: self.unit.hp = min(self.unit.hp + 2, self.unit.max_hp)
                        else:
                            projectile_list.append(Projectile(self.x, self.y, self.target, final_dmg, is_crit, self.unit.element))
    def take_damage(self, amount, is_crit):
        if self.unit.race in ["Ninja", "Ghost", "Bat", "Vampire", "Storm Crow"] and random.random() < 0.30: return 
        scale = UNIT_DEFS.get(self.unit.race, {}).get('scale', 1.0)
        mitigation_mult = 1.0
        if scale >= 1.4: mitigation_mult = 0.75 
        elif scale >= 1.2: mitigation_mult = 0.90 
        reduced_damage = int(amount * mitigation_mult)
        defense = self.unit.get_defense() + (4 if "SHIELD" in self.status else 0)
        actual_damage = max(1, reduced_damage - defense)
        self.unit.hp -= actual_damage
        if self.unit.hp <= 0: 
            self.state = "DEAD"
            if self.unit.is_fanatic: self.status['EXPLODE_ON_DEATH'] = 1

class Army:
    def __init__(self, slot_id=1):
        self.slot_id = slot_id; self.units = []; self.gold = 100; self.known_macs = []; self.beaten_levels = []
        self.save_path = f"save_{self.slot_id}.json"
        self.load_game()
    def create_new_game(self, hero_name, hero_class):
        self.units = []; self.gold = 100; self.known_macs = []
        hero = FantasyUnit(manual_type=hero_class); hero.name = hero_name; hero.max_hp += 20; hero.hp = hero.max_hp; hero.str += 2
        self.units.append(hero); self.save_game()
    def delete_save(self):
        try: os.remove(self.save_path); self.units = []
        except: pass
    def add_recruit(self, u): self.units.append(u); self.save_game()
    def remove_casualties_batch(self, dead_list):
        changed = False
        for u in dead_list:
            if len(self.units) > 0 and u == self.units[0]:
                u.hp = 1 
                changed = True
            elif u in self.units:
                self.units.remove(u)
                changed = True
        if changed: self.save_game()
    def remove_dead(self, u): self.remove_casualties_batch([u])
    def remember_mac(self, mac_int):
        if mac_int not in self.known_macs: self.known_macs.append(mac_int)
        if len(self.known_macs) > 50: self.known_macs.pop(0)
        self.save_game()
    def save_game(self):
        try:
            state = {"gold": self.gold, "known": self.known_macs, "beaten": self.beaten_levels, "units": [u.to_dict() for u in self.units]}
            with open(self.save_path, "w") as f: json.dump(state, f)
        except Exception as e: print(e)
    def load_game(self):
        try:
            with open(self.save_path, "r") as f:
                state = json.load(f); self.gold = state.get('gold', 100); self.known_macs = state.get('known', []); self.beaten_levels = state.get('beaten', [])
                for d in state['units']: 
                    u = FantasyUnit(load_data=d)
                    if u.hp <= 0: u.hp = 1
                    if u.hp > u.max_hp: u.hp = u.max_hp
                    self.units.append(u)
        except: pass

# --- 5. SYSTEM FUNCTIONS ---
def spawn_spell_fx(x, y, color, style, particle_list):
    if style == "METEOR":
        for i in range(5):
            start_x = x + random.randint(-10, 10); start_y = y - random.randint(30, 50)
            vx = (x - start_x) / 10; vy = (y - start_y) / 10
            particle_list.append(Particle(start_x, start_y, color, "PIXEL", vx=vx, vy=vy, grav=0))
    elif style == "BEAM":
        for i in range(0, int(y), 2):
            offset = random.randint(-2, 2)
            particle_list.append(Particle(x + offset, i, color, "PIXEL", vx=0, vy=0, grav=0))
        spawn_spell_fx(x, y, color, "EXPLOSION", particle_list)
    elif style == "NOVA":
        for _ in range(6):
            vx = random.uniform(-0.5, 0.5); vy = random.uniform(-1, -2.5) 
            particle_list.append(Particle(x, y, color, "PIXEL", vx=vx, vy=vy, grav=-0.05))
    elif style == "EXPLOSION":
        for _ in range(8):
            vx = random.uniform(-2, 2); vy = random.uniform(-3, 1)
            particle_list.append(Particle(x, y, color, "PIXEL", vx=vx, vy=vy))
    elif style == "POOF":
        for _ in range(12):
            vx = random.uniform(-1, 1); vy = random.uniform(-1, 1)
            particle_list.append(Particle(x, y, GREY, "PIXEL", vx=vx, vy=vy, grav=0))

def check_field_events(active_walkers, particle_list, spell_timers, army, log_list, lcd, active_channels):
    CHANNEL_DURATION = 40 
    for side in ["LEFT", "RIGHT"]:
        units = [w for w in active_walkers if w.side == side and w.state != "DEAD"]
        counts = {}
        for w in units: r = w.unit.race; counts[r] = counts.get(r, 0) + 1
        
        for r in RECIPES:
            if side == "RIGHT" and r.get('type') != "FUSION": continue
            cond_met = True
            for u_type, count in r['req'].items():
                if counts.get(u_type, 0) < count: cond_met = False; break
            
            base_id = r.get('spawn') or r.get('name')
            recipe_id = f"{side}_{base_id}"
            
            if not cond_met:
                if recipe_id in active_channels: del active_channels[recipe_id]
                continue
            
            if r.get('type') == "FUSION":
                if recipe_id in active_channels:
                    channel_data = active_channels[recipe_id]
                    target = channel_data['target']
                    if target.state == "DEAD" or target not in active_walkers: del active_channels[recipe_id]; continue
                    chan_col = YELLOW if side == "LEFT" else MAGENTA
                    spawn_spell_fx(target.x, target.y - 15, chan_col, "PIXEL", particle_list)
                    channel_data['timer'] -= 1
                    if channel_data['timer'] <= 0:
                        spawn_name = r.get('spawn')
                        if 'family' in r: spawn_name = "Earth Golem" 
                        if spawn_name:
                            if side == "LEFT": log_list.append(f"Fused: {spawn_name}")
                            spawn_spell_fx(target.x, target.y, GREY, "POOF", particle_list)
                            lvl_boost = 2 if side == "LEFT" else 5 
                            new_u = FantasyUnit(manual_type=spawn_name, level_scale=target.unit.level+lvl_boost)
                            if side == "LEFT": army.add_recruit(new_u) 
                            new_w = Walker(new_u, side)
                            if side == "LEFT": new_w.x = -15; new_w.dir = 1
                            else: new_w.x = 175; new_w.dir = -1
                            new_w.y = target.y 
                            active_walkers.append(new_w)
                            to_kill = r['req'].copy()
                            for w in units:
                                if w.unit.race in to_kill and to_kill[w.unit.race] > 0:
                                    w.state = "DEAD"; w.x = -999; to_kill[w.unit.race] -= 1
                            del active_channels[recipe_id]; return 
                else:
                    sac_target = None
                    for w in units:
                        if w.unit.race == r['sac']: sac_target = w; break
                    if sac_target:
                        active_channels[recipe_id] = {'timer': CHANNEL_DURATION, 'target': sac_target}
                        txt = "RITUAL!" if side == "LEFT" else "WARNING!"
                        col = YELLOW if side == "LEFT" else RED
                        particle_list.append(Particle(sac_target.x, sac_target.y-25, col, "TEXT", txt, vy=-0.5))
            elif r.get('type') == "SPELL" and side == "LEFT":
                 s_name = r['name']
                 if s_name not in spell_timers: spell_timers[s_name] = 0
                 if spell_timers[s_name] > 0: spell_timers[s_name] -= 1
                 else:
                     log_list.append(f"Cast: {s_name}")
                     spell_timers[s_name] = r['cd']
                     particle_list.append(Particle(80, 40, r['fx'], "TEXT", f"{s_name}!"))
                     if "dmg" in r:
                         target_side = "RIGHT"
                         enemies = [w for w in active_walkers if w.side == target_side and w.state != "DEAD"]
                         if enemies:
                             if r.get("aoe"):
                                 for target in enemies:
                                     target.take_damage(r['dmg'], True)
                                     spawn_spell_fx(target.x, target.y, r['fx'], "METEOR", particle_list)
                             else:
                                 for _ in range(3):
                                     target = random.choice(enemies)
                                     target.take_damage(r['dmg'], True)
                                     spawn_spell_fx(target.x, target.y, r['fx'], "EXPLOSION", particle_list)
                     elif "heal" in r:
                         for w in units:
                             heal_val = r['heal'] + (w.unit.max_hp // 10)
                             w.unit.hp = min(w.unit.max_hp, w.unit.hp + heal_val)
                             spawn_spell_fx(w.x, w.y, r['fx'], "NOVA", particle_list)
                     elif "buff" in r:
                         buff_type = r['buff']
                         for w in units: w.status[buff_type] = 300
                         spawn_spell_fx(w.x, w.y, r['fx'], "NOVA", particle_list)
                     elif "summon" in r:
                         u_type = r['summon']
                         new_u = FantasyUnit(manual_type=u_type, level_scale=army.units[0].level)
                         new_w = Walker(new_u, side)
                         new_w.x = -10; new_w.y = random.randint(60, 100)
                         active_walkers.append(new_w)

def cascade_equip(army, new_item_name, lcd):
    current_item = new_item_name
    for u in army.units:
        if u.artifact is None:
            u.artifact = current_item
            lcd.text(f"Given to {u.name}", 20, 80, GREEN)
            return
        else:
            old_item = u.artifact; u.artifact = current_item; current_item = old_item 
    lcd.text("Army Full!", 20, 60, WHITE); army.gold += 100
def cascade_gear(army, new_gear_name, gear_type):
    current_gear = new_gear_name
    target_db = WEAPONS if gear_type == "weapon" else ARMORS
    for u in army.units:
        item_stats = target_db.get(current_gear)
        if not item_stats: return 
        allowed = item_stats.get('classes', [])
        if allowed and u.race not in allowed: continue 
        if gear_type == "weapon": old_gear = u.weapon_name; u.weapon_name = current_gear
        else: old_gear = u.armor_name; u.armor_name = current_gear
        current_gear = old_gear
        if current_gear in ["Cloth Tunic", "Tattered Robe", "Training Sword", "Old Stick", "Wood Axe"]: return

# --- 6. GAME MODES ---
def select_champion(lcd, input_sys, audio, army):
    idx = 0
    while True:
        draw_book_bg(lcd); lcd.text("DEPLOY UNIT", 40, 10, INK)
        start = 0
        if idx > 4: start = idx - 4
        for i in range(start, min(len(army.units), start+5)):
            u = army.units[i]; prefix = ">" if i == idx else " "
            el_col = ELEMENTS[u.element]['col']
            lcd.text(f"{prefix}{u.name}", 15, 30 + ((i-start)*15), el_col)
            lcd.text(f" {u.weapon_name[:10]}", 25, 40 + ((i-start)*15), GREY)
        sel = army.units[idx]
        lcd.fill_rect(10, 100, 140, 25, INK); lcd.rect(10, 100, 140, 25, GREY) 
        lcd.text(f"HP:{sel.hp}/{sel.max_hp}", 15, 104, WHITE)
        lcd.show(); k = input_sys.get_input()
        if k == 'DOWN': idx = (idx + 1) % len(army.units); audio.sfx_blip()
        elif k == 'UP': idx = (idx - 1) % len(army.units); audio.sfx_blip()
        elif k == 'B': return None 
        elif k == 'A': return sel 

def run_wifi_scan(lcd, input_sys, audio, army):
    lcd.fill(BLACK); lcd.text("SIMULATING WIFI...", 20, 60, GREEN); lcd.show(); pygame.time.delay(1000)
    signals = []
    names = ["Neighbor_WiFi", "FBI Surveillance", "NETGEAR99", "Starbucks_Guest", "iPhone Hotspot", "Linksys"]
    for i in range(5):
        ssid = random.choice(names)
        fake_seed = random.randint(1000, 99999999)
        temp = FantasyUnit(seed=fake_seed)
        d_name = f"{temp.race} L{temp.level}"; d_col = ELEMENTS[temp.element]['col']
        signals.append({'ssid': ssid, 'seed': fake_seed, 'd_name': d_name, 'd_col': d_col, 'is_merch': (fake_seed % 5 == 0)})
    idx = 0
    while True:
        lcd.fill(BLACK); lcd.text("DETECTED SIGNALS", 20, 5, WHITE)
        for i, s in enumerate(signals):
            prefix = ">" if i == idx else " "; lcd.text(f"{prefix} {s['ssid'][:12]}", 10, 25 + (i*20), WHITE); lcd.text(f"  {s['d_name']}", 10, 35 + (i*20), s['d_col'])
        lcd.show(); k = input_sys.get_input()
        if k == 'DOWN': idx = (idx+1)%len(signals); audio.sfx_blip()
        elif k == 'UP': idx = (idx-1)%len(signals); audio.sfx_blip()
        elif k == 'B': return
        elif k == 'A':
            target_data = signals[idx]
            if target_data['is_merch']: run_merchant_shop(lcd, input_sys, audio, army, target_data['seed']); continue
            champion = select_champion(lcd, input_sys, audio, army)
            if not champion: continue 
            danger_level = champion.level + random.randint(-1, 3)
            if danger_level < 1: danger_level = 1
            enemy = FantasyUnit(seed=target_data['seed'], level_scale=danger_level)            
            lcd.fill(BLACK); lcd.text("ENCOUNTER!", 40, 50, RED); lcd.text(enemy.name, 40, 65, WHITE); lcd.show(); pygame.time.delay(1000)
            win = run_duel_walker(lcd, audio, champion, enemy); army.remember_mac(target_data['seed'])
            if win:
                reward = enemy.level * 15; army.gold += reward; army.add_recruit(enemy)
                lcd.fill(BLACK); lcd.text("VICTORY!", 40, 40, GREEN); lcd.text(f"Got {reward}g", 40, 60, WHITE); lcd.show(); audio.sfx_coin(); pygame.time.delay(1000)
            else:
                lcd.fill(BLACK); lcd.text("DEFEAT", 55, 40, RED)
                if champion.name == "Player": lcd.text("You fled...", 40, 60, GREY); champion.hp = 1 
                else: lcd.text(f"{champion.name} has", 30, 60, RED); lcd.text("FALLEN!", 50, 75, RED); army.remove_dead(champion)
                lcd.show(); audio.sfx_lose(); pygame.time.delay(3000)
            return

def run_duel_walker(lcd, audio, player, enemy):
    p_walker = Walker(player, "LEFT"); e_walker = Walker(enemy, "RIGHT")
    particles = []; projectiles = []
    player.hp = player.max_hp; enemy.hp = enemy.max_hp 
    while True:
        all_walkers = [p_walker, e_walker]
        p_walker.update(all_walkers, particles, projectiles)
        e_walker.update(all_walkers, particles, projectiles)
        particles = [p for p in particles if p.update()]
        projectiles = [p for p in projectiles if p.update(particles)]
        draw_forest_bg(lcd)
        all_walkers.sort(key=lambda w: w.y)
        for w in all_walkers: w.draw(lcd)
        for p in projectiles: p.draw(lcd)
        for p in particles: p.draw(lcd)
        lcd.fill_rect(0, 0, 160, 25, BLACK)
        lcd.text(f"{player.name} L{player.level}", 5, 5, BLUE)
        lcd.text(f"HP:{player.hp}/{player.max_hp}", 5, 15, BLUE)
        lcd.text(f"{enemy.name} L{enemy.level}", 85, 5, RED)
        lcd.text(f"HP:{enemy.hp}/{enemy.max_hp}", 85, 15, RED)
        lcd.show()
        if p_walker.state == "DEAD": 
            audio.sfx_lose(); player.hp = player.max_hp; return False
        if e_walker.state == "DEAD":
            audio.sfx_crit(); player.hp = player.max_hp; return True

def run_siege(lcd, army, dungeon_data, audio, tier=1):
    if len(army.units) == 0: return
    player_reserve = army.units[:]
    enemy_lvl = int(dungeon_data['lvl'])
    enemy_reserve = [FantasyUnit(level_scale=enemy_lvl) for _ in range(10)]
    active_walkers = []; dead_player_units = []; particles = []; projectiles = [] 
    spell_timers = {}; game_over = False; win = False; MAX_ON_FIELD = 12 
    active_channels = {}
    battle_log = []
    
    while not game_over:
        p_on_field = [w for w in active_walkers if w.side == "LEFT" and w.state != "DEAD"]
        e_on_field = [w for w in active_walkers if w.side == "RIGHT" and w.state != "DEAD"]
        if len(p_on_field) < MAX_ON_FIELD and len(player_reserve) > 0: active_walkers.append(Walker(player_reserve.pop(0), "LEFT"))
        if len(e_on_field) < MAX_ON_FIELD and len(enemy_reserve) > 0: active_walkers.append(Walker(enemy_reserve.pop(0), "RIGHT"))
        
        if len(p_on_field) == 0 and len(player_reserve) == 0: game_over = True; win = False
        elif len(e_on_field) == 0 and len(enemy_reserve) == 0: game_over = True; win = True
        
        check_field_events(active_walkers, particles, spell_timers, army, battle_log, lcd, active_channels)

        next_walkers = []
        for w in active_walkers:
            w.update(active_walkers, particles, projectiles) 
            if w.state == "DEAD":
                if w.side == "LEFT" and w.unit not in dead_player_units: dead_player_units.append(w.unit)
            else: next_walkers.append(w)
        active_walkers = next_walkers
        particles = [p for p in particles if p.update()]
        projectiles = [p for p in projectiles if p.update(particles)]
        
        if dungeon_data.get('type') == 'CAVE': draw_cave_bg(lcd)
        elif dungeon_data.get('type') == 'LAVA': draw_lava_bg(lcd)
        elif dungeon_data.get('type') == 'CASTLE': draw_castle_bg(lcd)
        elif dungeon_data.get('type') == 'SNOW': draw_snow_bg(lcd)
        else: draw_forest_bg(lcd)
        active_walkers.sort(key=lambda w: w.y)
        for w in active_walkers: w.draw(lcd)
        for p in projectiles: p.draw(lcd)
        for p in particles: p.draw(lcd)
        lcd.fill_rect(0,0,160,10,BLACK)
        lcd.text(f"YOU:{len(player_reserve)+len(p_on_field)}", 5, 3, BLUE)
        lcd.text(f"THEM:{len(enemy_reserve)+len(e_on_field)}", 80, 3, RED)
        lcd.show()
    
    if len(dead_player_units) > 0:
        lcd.fill(BLACK); lcd.text("CASUALTIES", 40, 10, RED)
        army.remove_casualties_batch(dead_player_units) 
    
    if win:
        reward = int(dungeon_data['reward'])
        lcd.fill(BLACK); lcd.text("VICTORY!", 50, 20, GREEN); army.gold += reward
        if dungeon_data['lvl'] not in army.beaten_levels: army.beaten_levels.append(dungeon_data['lvl'])
        lcd.show(); audio.sfx_win(); pygame.time.delay(3000)
    else: lcd.text("DEFEAT...", 50, 40, RED); audio.sfx_lose(); lcd.show(); pygame.time.delay(3000)
    for u in army.units: u.reset_buffs(); u.hp = u.max_hp
    army.save_game()

def run_dungeon_select(lcd, input_sys, audio, army):
    idx = 0; tier = 1
    while True:
        draw_book_bg(lcd); lcd.text("CAMPAIGN MAP", 30, 5, INK)
        d = DUNGEONS[idx]
        name_str = d['name']
        if d['lvl'] in army.beaten_levels: name_str += " *"; lcd.text("CLEARED", 100, 20, GREEN)
        lcd.text(f"< Level {d['lvl']} >", 40, 20, RED)
        lcd.text(name_str, 30, 35, INK)
        lcd.text(f"Waves: {d['waves']}", 40, 85, INK)
        lcd.fill_rect(30, 110, 100, 15, INK); lcd.text("PRESS [A]", 45, 114, PAPER)
        lcd.show(); k = input_sys.get_input()
        if k == 'RIGHT': idx = (idx+1)%len(DUNGEONS); audio.sfx_blip()
        elif k == 'LEFT': idx = (idx-1)%len(DUNGEONS); audio.sfx_blip()
        elif k == 'B': return
        elif k == 'A': 
            run_siege(lcd, army, d, audio, tier=tier); return

def run_blacksmith(lcd, input_sys, audio, army):
    u = select_champion(lcd, input_sys, audio, army)
    if not u: return
    cat_idx = 0; categories = ["WEAPONS", "ARMOR"]
    while True:
        draw_book_bg(lcd); lcd.text("BLACKSMITH", 40, 15, INK)
        lcd.text(f"Customer: {u.name}", 20, 30, BLUE); lcd.text(f"< {categories[cat_idx]} >", 40, 60, RED)
        lcd.show(); k = input_sys.get_input()
        if k == 'RIGHT': cat_idx = 1; audio.sfx_blip()
        elif k == 'LEFT': cat_idx = 0; audio.sfx_blip()
        elif k == 'B': return
        elif k == 'A': break 
    target_db = WEAPONS if cat_idx == 0 else ARMORS
    shop_items = [k for k, v in target_db.items() if u.race in v['classes']]
    shop_items.sort(key=lambda x: target_db[x]['cost'])
    if len(shop_items) == 0:
        lcd.fill(BLACK); lcd.text("NO ITEMS FOR", 30, 50, WHITE); lcd.text(f"{u.race} CLASS", 30, 65, WHITE); lcd.show(); pygame.time.delay(2000); return
    idx = 0
    while True:
        draw_book_bg(lcd); lcd.text("BLACKSMITH", 45, 10, INK); lcd.text(f"Gold: {army.gold}", 45, 115, INK)
        item_name = shop_items[idx]; stats = target_db[item_name]; col = stats.get('col', INK) 
        lcd.text(f"< {item_name} >", 10, 40, col)
        if cat_idx == 0: lcd.text(f"Damage: +{stats['dmg']}", 30, 60, INK)
        else: lcd.text(f"Defense: +{stats['def']}", 30, 60, BLUE)
        lcd.text(f"Cost: {stats['cost']}g", 30, 75, INK)
        current_gear = u.weapon_name if cat_idx == 0 else u.armor_name
        if current_gear == item_name: lcd.text("EQUIPPED", 50, 95, GREEN)
        else:
            if army.gold >= stats['cost']: lcd.text("PRESS A TO BUY", 30, 95, INK)
            else: lcd.text("TOO EXPENSIVE", 30, 95, GREY)
        lcd.show(); k = input_sys.get_input()
        if k == 'RIGHT': idx = (idx + 1) % len(shop_items); audio.sfx_blip()
        elif k == 'LEFT': idx = (idx - 1) % len(shop_items); audio.sfx_blip()
        elif k == 'B': return
        elif k == 'A':
            if current_gear != item_name and army.gold >= stats['cost']:
                army.gold -= stats['cost']
                if cat_idx == 0: u.weapon_name = item_name
                else: u.armor_name = item_name
                army.save_game(); audio.sfx_coin()
            else: audio.sfx_lose()

def run_merchant_shop(lcd, input_sys, audio, army, seed):
    random.seed(seed); keys = list(MERCHANT_ITEMS.keys())
    for_sale = []; 
    for _ in range(3): for_sale.append(random.choice(keys))
    idx = 0
    while True:
        draw_book_bg(lcd); lcd.text("MERCHANT", 45, 10, INK); lcd.text(f"Gold: {army.gold}", 45, 115, INK)
        item_name = for_sale[idx]; stats = MERCHANT_ITEMS[item_name]
        lcd.text(f"< {item_name} >", 10, 40, stats.get('col', INK))
        lcd.text(f"Cost: {stats.get('cost', 500)}g", 30, 60, INK)
        lcd.show(); k = input_sys.get_input()
        if k == 'RIGHT': idx = (idx + 1) % 3; audio.sfx_blip()
        elif k == 'LEFT': idx = (idx - 1) % 3; audio.sfx_blip()
        elif k == 'B': return
        elif k == 'A':
            cost = stats.get('cost', 500)
            if army.gold >= cost:
                army.gold -= cost
                if "hp" in stats: cascade_equip(army, item_name, lcd)
                else:
                    g_type = "weapon" if "dmg" in stats else "armor"
                    cascade_gear(army, item_name, g_type)
                    lcd.text("BOUGHT!", 40, 50, GREEN); lcd.show(); pygame.time.delay(1000)
                army.save_game(); audio.sfx_coin()
            else: audio.sfx_lose()

def run_triage(lcd, input_sys, audio, army):
    idx = 0
    while True:
        draw_book_bg(lcd); lcd.text("TRIAGE TENT", 40, 10, INK); lcd.text(f"Gold: {army.gold}", 40, 20, INK)
        start = 0
        if idx > 4: start = idx - 4
        for i in range(start, min(len(army.units), start+5)):
            u = army.units[i]; prefix = ">" if i == idx else " "
            missing_hp = u.max_hp - u.hp; cost = missing_hp 
            col = BLACK if u.hp > u.max_hp // 2 else RED
            lcd.text(f"{prefix}{u.name}", 15, 40 + ((i-start)*15), col)
            if missing_hp == 0: lcd.text("FULL", 110, 40 + ((i-start)*15), GREEN)
            else: lcd.text(f"{cost}g", 110, 40 + ((i-start)*15), INK)
        sel = army.units[idx]
        lcd.fill_rect(10, 110, 140, 15, INK); lcd.text(f"HP: {sel.hp}/{sel.max_hp}", 15, 114, WHITE)
        lcd.show(); k = input_sys.get_input()
        if k == 'DOWN': idx = (idx + 1) % len(army.units); audio.sfx_blip()
        elif k == 'UP': idx = (idx - 1) % len(army.units); audio.sfx_blip()
        elif k == 'B': return 
        elif k == 'A':
            missing = sel.max_hp - sel.hp
            if missing == 0: audio.sfx_blip() 
            elif army.gold >= missing:
                army.gold -= missing; sel.hp = sel.max_hp; army.save_game(); audio.sfx_coin() 
            else: audio.sfx_lose() 

def run_dismiss(lcd, input_sys, audio, army):
    idx = 0
    while True:
        draw_book_bg(lcd); lcd.text("DISMISS UNIT", 35, 10, INK)
        start = 0
        if idx > 4: start = idx - 4
        for i in range(start, min(len(army.units), start+5)):
            u = army.units[i]; prefix = ">" if i == idx else " "
            value = (u.level * 20) + 10; val_col = INK
            if u.artifact: value += 100; val_col = color(200, 150, 0)
            if i == 0: value = 0 
            lcd.text(f"{prefix}{u.name}", 15, 40 + ((i-start)*15), INK)
            lcd.text(f"+{value}g", 110, 40 + ((i-start)*15), val_col)
        lcd.text("Permanently remove?", 10, 115, RED); lcd.show(); k = input_sys.get_input()
        if k == 'DOWN': idx = (idx + 1) % len(army.units); audio.sfx_blip()
        elif k == 'UP': idx = (idx - 1) % len(army.units); audio.sfx_blip()
        elif k == 'B': return
        elif k == 'A':
            if idx == 0: audio.sfx_lose() 
            else:
                sel = army.units[idx]
                payout = (sel.level * 20) + 10
                if sel.artifact: payout += 100
                army.gold += payout
                lcd.fill(BLACK); lcd.text(f"Farewell", 50, 50, WHITE); lcd.text(f"{sel.name}...", 40, 65, WHITE); lcd.show(); audio.sfx_coin(); pygame.time.delay(1000)
                army.remove_dead(sel); idx = 0 
                if len(army.units) == 1: return

def run_tactics(lcd, input_sys, audio, army):
    idx = 0; selected_idx = None
    while True:
        draw_book_bg(lcd); lcd.text("TACTICS (ORDER)", 30, 10, INK)
        start = 0
        if idx > 4: start = idx - 4
        for i in range(start, min(len(army.units), start+5)):
            u = army.units[i]
            y_pos = 30 + ((i-start)*15)
            prefix = " "
            col = INK
            if i == idx: prefix = ">"
            if i == selected_idx: col = RED; prefix = "*" 
            lcd.text(f"{prefix}{i+1}. {u.name}", 15, y_pos, col)
            lcd.text(f"   Lv{u.level} {u.race}", 15, y_pos+8, GREY)
        lcd.fill_rect(10, 110, 140, 15, INK)
        if selected_idx is None: lcd.text("[A] MOVE UNIT", 25, 114, WHITE)
        else: lcd.text("[A] PLACE HERE", 25, 114, YELLOW)
        lcd.show(); k = input_sys.get_input()
        if k == 'DOWN': idx = (idx + 1) % len(army.units); audio.sfx_blip()
        elif k == 'UP': idx = (idx - 1) % len(army.units); audio.sfx_blip()
        elif k == 'B': 
            if selected_idx is not None: selected_idx = None; audio.sfx_blip()
            else: return 
        elif k == 'A':
            if selected_idx is None: selected_idx = idx; audio.sfx_blip()
            else:
                if selected_idx != idx:
                    army.units[selected_idx], army.units[idx] = army.units[idx], army.units[selected_idx]
                    army.save_game(); audio.sfx_coin() 
                else: audio.sfx_blip() 
                selected_idx = None

def run_grimoire(lcd, input_sys, audio):
    page = 0
    book_pages = [r for r in RECIPES if r.get('type') in ["FUSION", "SPELL"]]
    while True:
        draw_book_bg(lcd); lcd.text("GRIMOIRE", 45, 5, INK)
        if len(book_pages) == 0: lcd.text("Pages Empty...", 30, 60, GREY); lcd.show(); pygame.time.delay(2000); return
        r = book_pages[page]
        name = r.get('spawn') or r.get('family') or r.get('name') or "Unknown"
        r_type = r.get('type')
        name_x = 80 - (len(name) * 4) 
        lcd.text(f"[{page+1}/{len(book_pages)}]", 5, 20, GREY); lcd.text(r_type, 100, 20, GREY)
        lcd.text(name, name_x, 35, BLUE)
        lcd.line(10, 45, 150, 45, INK)
        y = 55
        if 'family' in r: lcd.text("Result depends", 20, y, INK); y+=10; lcd.text("on Gear Score!", 20, y, INK); y+=15
        for req_unit, req_count in r['req'].items():
            col = RED
            if req_unit in WILD_POOL: col = color(0, 100, 0)
            lcd.text(f"{req_count} x {req_unit}", 25, y, col); y += 12
        y_foot = 95
        if 'sac' in r: lcd.text(f"Sacrifice: {r['sac']}", 15, y_foot, RED)
        elif 'dmg' in r: lcd.text(f"Effect: {r['dmg']} Dmg", 15, y_foot, RED)
        elif 'buff' in r: lcd.text(f"Effect: {r['buff']} +{r['val']}", 15, y_foot, BLUE)
        lcd.fill_rect(0, 115, 160, 13, PAPER) 
        lcd.text("< PREV", 10, 118, INK); lcd.text("NEXT >", 100, 118, INK)
        lcd.show(); k = input_sys.get_input()
        if k == 'RIGHT': page = (page + 1) % len(book_pages); audio.sfx_blip()
        elif k == 'LEFT': page = (page - 1) % len(book_pages); audio.sfx_blip()
        elif k == 'B': return

def run_camp(lcd, input_sys, audio, army):
    menu_idx = 0; options = ["HEAL ALL", "TRIAGE", "DISMISS", "LEAVE"]
    while True:
        draw_book_bg(lcd); lcd.text("BASE CAMP", 45, 15, INK); lcd.text(f"Gold: {army.gold}", 45, 30, INK)
        total_missing = sum([(u.max_hp - u.hp) for u in army.units]); lcd.text(f"Army Dmg: {total_missing}", 30, 45, RED)
        for i, opt in enumerate(options):
            y = 70 + (i * 15); prefix = ">" if i == menu_idx else " "; col = INK; text = opt
            if i == 0: text = f"HEAL ALL ({total_missing}g)"
            lcd.text(f"{prefix} {text}", 20, y, col)
        lcd.show(); k = input_sys.get_input()
        if k == 'DOWN': menu_idx = (menu_idx + 1) % len(options); audio.sfx_blip()
        elif k == 'UP': menu_idx = (menu_idx - 1) % len(options); audio.sfx_blip()
        elif k == 'A':
            if menu_idx == 3: return 
            elif menu_idx == 0: 
                if total_missing == 0: audio.sfx_blip()
                elif army.gold >= total_missing: army.gold -= total_missing; [setattr(u, 'hp', u.max_hp) for u in army.units]; army.save_game(); audio.sfx_win(); pygame.time.delay(1000)
                else: audio.sfx_lose()
            elif menu_idx == 1: run_triage(lcd, input_sys, audio, army)
            elif menu_idx == 2: run_dismiss(lcd, input_sys, audio, army)
        elif k == 'B': return

def get_player_name(lcd, input_sys, audio):
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ "; name = ""; idx = 0
    while True:
        draw_book_bg(lcd); lcd.text("NAME HERO", 40, 15, INK); lcd.rect(30, 35, 100, 20, INK); lcd.text(name + "_", 35, 41, BLUE)
        for i in range(5):
            c = chars[(idx - 2 + i) % len(chars)]; col = RED if i == 2 else GREY 
            lcd.text(c, 35 + (i * 20), 70, col)
        lcd.text("[A] CONFIRM", 35, 115, GREEN); lcd.show(); k = input_sys.get_input()
        if k == 'RIGHT': idx = (idx + 1) % len(chars); audio.sfx_blip()
        elif k == 'LEFT': idx = (idx - 1) % len(chars); audio.sfx_blip()
        elif k == 'A': 
            if len(name) < 8: name += chars[idx]; audio.sfx_blip()
        elif k == 'B': 
            if len(name) > 0: name = name[:-1]; audio.sfx_blip()
        elif k == 'DOWN' and len(name) > 0: return name

def select_class(lcd, input_sys, audio):
    classes = ["Warrior", "Paladin", "Mage", "Cleric", "Necro", "Archer", "Ninja"]; idx = 0
    while True:
        draw_book_bg(lcd); lcd.text("CLASS", 55, 15, INK); c_name = classes[idx]; lcd.text(f"< {c_name} >", 40, 40, BLUE)
        temp = FantasyUnit(manual_type=c_name); temp.draw(lcd, 75, 75); 
        lcd.show(); k = input_sys.get_input()
        if k == 'RIGHT': idx = (idx + 1) % len(classes); audio.sfx_blip()
        elif k == 'LEFT': idx = (idx - 1) % len(classes); audio.sfx_blip()
        elif k == 'A': return c_name

def run_title_screen(lcd, input_sys):
    while True:
        draw_book_bg(lcd); lcd.text("WIFI WARRIORS", 28, 30, RED); lcd.text("PC Edition", 35, 45, INK)
        if (pygame.time.get_ticks() // 500) % 2 == 0: lcd.text("PRESS [Z] START", 20, 90, BLUE)
        lcd.show(); k = input_sys.get_input()
        if k == 'A': return 

def main():
    lcd = LCD(); c = InputController(); a = SoundEngine()
    run_title_screen(lcd, c)
    my_army = Army(slot_id=1)
    if len(my_army.units) == 0: 
        name = get_player_name(lcd, c, a); race = select_class(lcd, c, a); 
        my_army.create_new_game(hero_name=name, hero_class=race)
        
    menu_idx = 0
    menu_options = [
        {"label": "SCAN WIFI",  "action": "SCAN", "col": BLUE}, 
        {"label": "DUNGEONS",   "action": "SIEGE", "col": RED},
        {"label": "BARRACKS",   "action": "ARMY", "col": CYAN},
        {"label": "GRIMOIRE",   "action": "BOOK", "col": YELLOW}, 
        {"label": "CAMP (HEAL)","action": "CAMP", "col": GREEN}
    ]
    
    while True:
        draw_book_bg(lcd)
        lcd.text(f"{my_army.units[0].name[:8]}", 10, 10, BLUE)
        lcd.text(f"${my_army.gold}", 100, 10, INK)
        lcd.text(f"Units: {len(my_army.units)}", 10, 22, GREY)
        
        for i, item in enumerate(menu_options):
            y_pos = 45 + (i * 13) 
            prefix = ">" if i == menu_idx else " "
            col = item['col'] if i == menu_idx else GREY
            lcd.text(f"{prefix} {item['label']}", 15, y_pos, col)
            
        lcd.show(); k = c.get_input()
        
        if k == 'DOWN': menu_idx = (menu_idx + 1) % len(menu_options); a.sfx_blip()
        elif k == 'UP': menu_idx = (menu_idx - 1) % len(menu_options); a.sfx_blip()
        elif k == 'A':
            choice = menu_options[menu_idx]['action']; a.sfx_blip()
            if choice == "SCAN": run_wifi_scan(lcd, c, a, my_army)
            elif choice == "SIEGE": run_dungeon_select(lcd, c, a, my_army)
            elif choice == "CAMP": run_camp(lcd, c, a, my_army)
            elif choice == "BOOK": run_grimoire(lcd, c, a)
            elif choice == "ARMY":
                barracks_choice = 0; in_barracks = True
                while in_barracks:
                    draw_book_bg(lcd); lcd.text("--- BARRACKS ---", 20, 20, WHITE)
                    opts = ["TACTICS", "BLACKSMITH", "DISMISS", "BACK"]
                    for i, opt in enumerate(opts):
                        col = YELLOW if i == barracks_choice else GREY
                        lcd.text(opt, 30, 50 + (i*20), col)
                    lcd.show(); bk = c.get_input()
                    if bk == 'UP': barracks_choice = (barracks_choice - 1) % 4; a.sfx_blip()
                    elif bk == 'DOWN': barracks_choice = (barracks_choice + 1) % 4; a.sfx_blip()
                    elif bk == 'A':
                        if barracks_choice == 0: run_tactics(lcd, c, a, my_army)
                        elif barracks_choice == 1: run_blacksmith(lcd, c, a, my_army)
                        elif barracks_choice == 2: run_dismiss(lcd, c, a, my_army)
                        elif barracks_choice == 3: in_barracks = False 
                    elif bk == 'B': in_barracks = False

if __name__ == "__main__":
    main()
