"""
STAR EMPIRE — Космическая Idle-RPG
Стабильная версия для Android
"""

import json
import random
import time
import os

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.utils import platform


# ============== КОНФИГУРАЦИЯ ==============

UPGRADES = {
    'energy_click': {'name': 'Energy Click', 'base_cost': 10, 'cost_mult': 1.5, 'resource': 'energy'},
    'metal_click': {'name': 'Metal Click', 'base_cost': 25, 'cost_mult': 1.6, 'resource': 'metal'},
    'crystal_click': {'name': 'Crystal Click', 'base_cost': 100, 'cost_mult': 1.8, 'resource': 'crystal'},
    'energy_auto': {'name': 'Auto Energy', 'base_cost': 50, 'cost_mult': 1.7, 'resource': 'energy'},
    'metal_auto': {'name': 'Auto Metal', 'base_cost': 150, 'cost_mult': 1.8, 'resource': 'metal'},
    'crystal_auto': {'name': 'Auto Crystal', 'base_cost': 500, 'cost_mult': 2.0, 'resource': 'crystal'},
}

SHIPS = {
    'scout': {'name': 'Scout', 'cost': {'metal': 100}, 'time': 30,
              'rewards': {'energy': (50, 150), 'metal': (20, 50)}},
    'miner': {'name': 'Miner', 'cost': {'metal': 300, 'energy': 100}, 'time': 60,
              'rewards': {'metal': (100, 300), 'crystal': (5, 20)}},
    'cruiser': {'name': 'Cruiser', 'cost': {'metal': 1000, 'crystal': 50}, 'time': 120,
                'rewards': {'energy': (200, 500), 'metal': (150, 400), 'crystal': (20, 50)}},
}

BOSSES = {
    'asteroid': {'name': 'Giant Asteroid', 'hp': 100, 'reward': {'metal': 500, 'crystal': 25}, 'cooldown': 60},
    'pirate': {'name': 'Pirate Fleet', 'hp': 500, 'reward': {'energy': 1000, 'metal': 750}, 'cooldown': 180},
    'alien': {'name': 'Alien Titan', 'hp': 2000, 'reward': {'crystal': 200, 'prestige_points': 1}, 'cooldown': 600},
}


# ============== ИГРОВОЙ МЕНЕДЖЕР ==============

class GameManager:
    def __init__(self):
        self.save_path = self.get_save_path()
        self.data = self.load_game()
        self.last_save = time.time()
        self.event_text = ""
    
    def get_save_path(self):
        if platform == 'android':
            try:
                from android.storage import app_storage_path
                return os.path.join(app_storage_path(), 'save.json')
            except:
                pass
        return os.path.join(os.path.expanduser('~'), '.starempire_save.json')
    
    def load_game(self):
        default = {
            'energy': 0, 'metal': 0, 'crystal': 0,
            'upgrades': {}, 'ships': {}, 'expeditions': {},
            'bosses': {}, 'achievements': [],
            'prestige_points': 0, 'total_clicks': 0,
            'play_time': 0, 'last_daily': 0, 'bosses_killed': []
        }
        try:
            if os.path.exists(self.save_path):
                with open(self.save_path, 'r') as f:
                    saved = json.load(f)
                    for key in default:
                        if key not in saved:
                            saved[key] = default[key]
                    return saved
        except:
            pass
        return default
    
    def save_game(self):
        try:
            with open(self.save_path, 'w') as f:
                json.dump(self.data, f)
        except:
            pass
    
    def get_prestige_mult(self):
        return 1.0 + (self.data.get('prestige_points', 0) * 0.1)
    
    def mine(self, resource):
        mult = self.get_prestige_mult()
        if resource == 'energy':
            amount = max(1, self.data['upgrades'].get('energy_click', 0) + 1) * mult
        elif resource == 'metal':
            amount = self.data['upgrades'].get('metal_click', 0) * mult
        elif resource == 'crystal':
            amount = self.data['upgrades'].get('crystal_click', 0) * mult
        else:
            return
        
        self.data[resource] = self.data.get(resource, 0) + amount
        self.data['total_clicks'] = self.data.get('total_clicks', 0) + 1
        
        if random.random() < 0.03:
            bonus = random.choice(['energy', 'metal', 'crystal'])
            bonus_amount = int(random.randint(10, 50) * mult)
            self.data[bonus] += bonus_amount
            self.event_text = f"BONUS! +{bonus_amount} {bonus.upper()}"
    
    def buy_upgrade(self, key):
        if key not in UPGRADES:
            return False
        upg = UPGRADES[key]
        level = self.data['upgrades'].get(key, 0)
        cost = int(upg['base_cost'] * (upg['cost_mult'] ** level))
        
        if self.data[upg['resource']] >= cost:
            self.data[upg['resource']] -= cost
            self.data['upgrades'][key] = level + 1
            return True
        return False
    
    def buy_ship(self, key):
        if key not in SHIPS:
            return
        ship = SHIPS[key]
        
        if key in self.data.get('expeditions', {}):
            exp_time = self.data['expeditions'][key]
            if time.time() >= exp_time:
                for res, (min_r, max_r) in ship['rewards'].items():
                    amount = int(random.randint(min_r, max_r) * self.get_prestige_mult())
                    self.data[res] = self.data.get(res, 0) + amount
                del self.data['expeditions'][key]
                self.event_text = f"{ship['name']} returned!"
            return
        
        ships_owned = self.data.get('ships', {})
        if ships_owned.get(key, 0) > 0:
            if 'expeditions' not in self.data:
                self.data['expeditions'] = {}
            self.data['expeditions'][key] = time.time() + ship['time']
            self.event_text = f"{ship['name']} sent!"
            return
        
        can_buy = all(self.data.get(res, 0) >= cost for res, cost in ship['cost'].items())
        if can_buy:
            for res, cost in ship['cost'].items():
                self.data[res] -= cost
            if 'ships' not in self.data:
                self.data['ships'] = {}
            self.data['ships'][key] = self.data['ships'].get(key, 0) + 1
    
    def attack_boss(self, key):
        if key not in BOSSES:
            return
        boss = BOSSES[key]
        
        if 'bosses' not in self.data:
            self.data['bosses'] = {}
        if key not in self.data['bosses']:
            self.data['bosses'][key] = {'hp': boss['hp'], 'cooldown': 0}
        
        bd = self.data['bosses'][key]
        
        if time.time() < bd.get('cooldown', 0):
            return
        if bd['hp'] <= 0:
            bd['hp'] = boss['hp']
            return
        
        total_ships = sum(self.data.get('ships', {}).values())
        base_damage = 1 + self.data['upgrades'].get('energy_click', 0)
        damage = int((base_damage + total_ships * 5) * self.get_prestige_mult())
        
        bd['hp'] = max(0, bd['hp'] - damage)
        
        if bd['hp'] <= 0:
            for res, amount in boss['reward'].items():
                if res == 'prestige_points':
                    self.data['prestige_points'] = self.data.get('prestige_points', 0) + amount
                else:
                    self.data[res] = self.data.get(res, 0) + amount
            bd['cooldown'] = time.time() + boss['cooldown']
            self.event_text = f"BOSS {boss['name']} DEFEATED!"
    
    def can_claim_daily(self):
        last = self.data.get('last_daily', 0)
        return time.time() - last >= 86400
    
    def claim_daily(self):
        if self.can_claim_daily():
            mult = self.get_prestige_mult()
            self.data['energy'] += int(100 * mult)
            self.data['metal'] += int(50 * mult)
            self.data['crystal'] += int(10 * mult)
            self.data['last_daily'] = time.time()
            self.event_text = "Daily bonus claimed!"
            return True
        return False
    
    def do_prestige(self):
        total = self.data['energy'] + self.data['metal'] * 2 + self.data['crystal'] * 5
        earn = int(total ** 0.5 / 50)
        
        if earn > 0 and total >= 10000:
            self.data['prestige_points'] = self.data.get('prestige_points', 0) + earn
            self.data['energy'] = 0
            self.data['metal'] = 0
            self.data['crystal'] = 0
            self.data['upgrades'] = {}
            self.data['ships'] = {}
            self.data['expeditions'] = {}
            self.data['bosses'] = {}
            self.event_text = f"PRESTIGE! +{earn} points!"
            return True
        return False
    
    def auto_collect(self, dt):
        mult = self.get_prestige_mult()
        self.data['energy'] += self.data['upgrades'].get('energy_auto', 0) * mult * dt
        self.data['metal'] += self.data['upgrades'].get('metal_auto', 0) * mult * dt
        self.data['crystal'] += self.data['upgrades'].get('crystal_auto', 0) * mult * dt
        self.data['play_time'] = self.data.get('play_time', 0) + dt
        
        if time.time() - self.last_save > 30:
            self.save_game()
            self.last_save = time.time()


# ============== БАЗОВЫЙ ЭКРАН ==============

class BaseScreen(Screen):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        
        with self.canvas.before:
            Color(0.05, 0.05, 0.12, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)
    
    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size


# ============== ГЛАВНЫЙ ЭКРАН ==============

class MainScreen(BaseScreen):
    def __init__(self, game, **kwargs):
        super().__init__(game, **kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        
        # Заголовок
        layout.add_widget(Label(
            text='STAR EMPIRE',
            font_size=sp(32),
            size_hint=(1, 0.08),
            bold=True,
            color=(0.9, 0.8, 1, 1)
        ))
        
        # Престиж
        self.prestige_lbl = Label(
            text='Prestige: x1.0',
            font_size=sp(14),
            size_hint=(1, 0.04),
            color=(1, 0.9, 0.3, 1)
        )
        layout.add_widget(self.prestige_lbl)
        
        # Ресурсы
        res_box = BoxLayout(size_hint=(1, 0.12), spacing=dp(5))
        
        self.energy_lbl = Label(text='[E] 0', font_size=sp(18), color=(0.3, 0.8, 1, 1))
        self.metal_lbl = Label(text='[M] 0', font_size=sp(18), color=(0.7, 0.7, 0.7, 1))
        self.crystal_lbl = Label(text='[C] 0', font_size=sp(18), color=(0.9, 0.4, 1, 1))
        
        res_box.add_widget(self.energy_lbl)
        res_box.add_widget(self.metal_lbl)
        res_box.add_widget(self.crystal_lbl)
        layout.add_widget(res_box)
        
        # Авто-доход
        self.auto_lbl = Label(
            text='Auto: +0/s',
            font_size=sp(12),
            size_hint=(1, 0.03),
            color=(0.5, 0.5, 0.5, 1)
        )
        layout.add_widget(self.auto_lbl)
        
        # Кнопки добычи
        mine_grid = GridLayout(cols=3, size_hint=(1, 0.25), spacing=dp(8))
        
        self.energy_btn = Button(
            text='ENERGY\n+1',
            font_size=sp(16),
            background_color=(0.1, 0.3, 0.6, 1),
            background_normal=''
        )
        self.energy_btn.bind(on_release=lambda x: self.do_mine('energy'))
        
        self.metal_btn = Button(
            text='METAL\n+0',
            font_size=sp(16),
            background_color=(0.3, 0.3, 0.35, 1),
            background_normal=''
        )
        self.metal_btn.bind(on_release=lambda x: self.do_mine('metal'))
        
        self.crystal_btn = Button(
            text='CRYSTAL\n+0',
            font_size=sp(16),
            background_color=(0.4, 0.1, 0.5, 1),
            background_normal=''
        )
        self.crystal_btn.bind(on_release=lambda x: self.do_mine('crystal'))
        
        mine_grid.add_widget(self.energy_btn)
        mine_grid.add_widget(self.metal_btn)
        mine_grid.add_widget(self.crystal_btn)
        layout.add_widget(mine_grid)
        
        # Ивент
        self.event_lbl = Label(
            text='',
            font_size=sp(14),
            size_hint=(1, 0.05),
            color=(1, 1, 0.3, 1)
        )
        layout.add_widget(self.event_lbl)
        
        # Daily
        self.daily_btn = Button(
            text='DAILY BONUS',
            font_size=sp(14),
            size_hint=(1, 0.07),
            background_color=(0.2, 0.5, 0.2, 1),
            background_normal=''
        )
        self.daily_btn.bind(on_release=lambda x: self.game.claim_daily())
        layout.add_widget(self.daily_btn)
        
        # Навигация
        nav = GridLayout(cols=5, size_hint=(1, 0.1), spacing=dp(3))
        
        nav_btns = [
            ('HOME', 'main'),
            ('UPGRADE', 'upgrades'),
            ('SHIPS', 'ships'),
            ('BOSS', 'boss'),
            ('PRESTIGE', 'prestige'),
        ]
        
        for text, screen in nav_btns:
            btn = Button(
                text=text,
                font_size=sp(11),
                background_color=(0.2, 0.2, 0.3, 1),
                background_normal=''
            )
            btn.bind(on_release=lambda x, s=screen: self.change_screen(s))
            nav.add_widget(btn)
        
        layout.add_widget(nav)
        self.add_widget(layout)
    
    def change_screen(self, name):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = name
    
    def do_mine(self, resource):
        self.game.mine(resource)
        self.update()
    
    def format_num(self, n):
        n = int(n)
        if n >= 1000000:
            return f"{n/1000000:.1f}M"
        if n >= 1000:
            return f"{n/1000:.1f}K"
        return str(n)
    
    def update(self, dt=0):
        d = self.game.data
        mult = self.game.get_prestige_mult()
        
        self.energy_lbl.text = f"[E] {self.format_num(d['energy'])}"
        self.metal_lbl.text = f"[M] {self.format_num(d['metal'])}"
        self.crystal_lbl.text = f"[C] {self.format_num(d['crystal'])}"
        
        e_click = max(1, d['upgrades'].get('energy_click', 0) + 1) * mult
        m_click = d['upgrades'].get('metal_click', 0) * mult
        c_click = d['upgrades'].get('crystal_click', 0) * mult
        
        self.energy_btn.text = f"ENERGY\n+{int(e_click)}"
        self.metal_btn.text = f"METAL\n+{int(m_click)}"
        self.crystal_btn.text = f"CRYSTAL\n+{int(c_click)}"
        
        e_auto = d['upgrades'].get('energy_auto', 0) * mult
        m_auto = d['upgrades'].get('metal_auto', 0) * mult
        c_auto = d['upgrades'].get('crystal_auto', 0) * mult
        self.auto_lbl.text = f"Auto: +{int(e_auto)}E +{int(m_auto)}M +{int(c_auto)}C /sec"
        
        self.prestige_lbl.text = f"Prestige: x{mult:.1f} | Points: {d.get('prestige_points', 0)}"
        
        if self.game.can_claim_daily():
            self.daily_btn.text = "DAILY BONUS READY!"
            self.daily_btn.background_color = (0.2, 0.6, 0.2, 1)
        else:
            remaining = 86400 - (time.time() - d.get('last_daily', 0))
            h = int(remaining // 3600)
            m = int((remaining % 3600) // 60)
            self.daily_btn.text = f"Daily in: {h}h {m}m"
            self.daily_btn.background_color = (0.3, 0.3, 0.3, 1)
        
        if self.game.event_text:
            self.event_lbl.text = self.game.event_text
            self.game.event_text = ""


# ============== ЭКРАН УЛУЧШЕНИЙ ==============

class UpgradesScreen(BaseScreen):
    def __init__(self, game, **kwargs):
        super().__init__(game, **kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))
        
        layout.add_widget(Label(
            text='UPGRADES',
            font_size=sp(24),
            size_hint=(1, 0.08),
            color=(0.5, 1, 0.5, 1)
        ))
        
        scroll = ScrollView(size_hint=(1, 0.8))
        self.grid = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=dp(5))
        self.grid.bind(minimum_height=self.grid.setter('height'))
        
        self.buttons = {}
        for key in UPGRADES:
            btn = Button(
                text='',
                font_size=sp(14),
                size_hint_y=None,
                height=dp(60),
                background_color=(0.15, 0.2, 0.25, 1),
                background_normal=''
            )
            btn.bind(on_release=lambda x, k=key: self.buy(k))
            self.buttons[key] = btn
            self.grid.add_widget(btn)
        
        scroll.add_widget(self.grid)
        layout.add_widget(scroll)
        
        back = Button(
            text='< BACK',
            font_size=sp(16),
            size_hint=(1, 0.08),
            background_color=(0.3, 0.3, 0.4, 1),
            background_normal=''
        )
        back.bind(on_release=lambda x: self.go_back())
        layout.add_widget(back)
        
        self.add_widget(layout)
    
    def buy(self, key):
        self.game.buy_upgrade(key)
        self.update()
    
    def go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'main'
    
    def update(self, dt=0):
        d = self.game.data
        for key, upg in UPGRADES.items():
            level = d['upgrades'].get(key, 0)
            cost = int(upg['base_cost'] * (upg['cost_mult'] ** level))
            res = upg['resource'][0].upper()
            current = d[upg['resource']]
            
            can = current >= cost
            color = (0.2, 0.4, 0.2, 1) if can else (0.2, 0.2, 0.25, 1)
            
            self.buttons[key].text = f"{upg['name']}\nLevel: {level} | Cost: {cost} {res}"
            self.buttons[key].background_color = color


# ============== ЭКРАН КОРАБЛЕЙ ==============

class ShipsScreen(BaseScreen):
    def __init__(self, game, **kwargs):
        super().__init__(game, **kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))
        
        layout.add_widget(Label(
            text='FLEET',
            font_size=sp(24),
            size_hint=(1, 0.08),
            color=(0.5, 0.8, 1, 1)
        ))
        
        self.fleet_lbl = Label(
            text='Ships: 0',
            font_size=sp(14),
            size_hint=(1, 0.05)
        )
        layout.add_widget(self.fleet_lbl)
        
        scroll = ScrollView(size_hint=(1, 0.75))
        self.grid = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=dp(5))
        self.grid.bind(minimum_height=self.grid.setter('height'))
        
        self.ship_widgets = {}
        for key, ship in SHIPS.items():
            box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80))
            
            btn = Button(
                text='',
                font_size=sp(13),
                background_color=(0.15, 0.2, 0.3, 1),
                background_normal='',
                size_hint=(1, 0.7)
            )
            btn.bind(on_release=lambda x, k=key: self.handle_ship(k))
            
            status = Label(text='', font_size=sp(11), size_hint=(1, 0.3), color=(0.7, 1, 0.7, 1))
            
            box.add_widget(btn)
            box.add_widget(status)
            self.grid.add_widget(box)
            
            self.ship_widgets[key] = {'btn': btn, 'status': status}
        
        scroll.add_widget(self.grid)
        layout.add_widget(scroll)
        
        back = Button(
            text='< BACK',
            font_size=sp(16),
            size_hint=(1, 0.08),
            background_color=(0.3, 0.3, 0.4, 1),
            background_normal=''
        )
        back.bind(on_release=lambda x: self.go_back())
        layout.add_widget(back)
        
        self.add_widget(layout)
    
    def handle_ship(self, key):
        self.game.buy_ship(key)
        self.update()
    
    def go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'main'
    
    def update(self, dt=0):
        d = self.game.data
        ships = d.get('ships', {})
        exps = d.get('expeditions', {})
        
        self.fleet_lbl.text = f"Ships owned: {sum(ships.values())}"
        
        for key, ship in SHIPS.items():
            owned = ships.get(key, 0)
            w = self.ship_widgets[key]
            
            cost_str = ', '.join([f"{v}{k[0].upper()}" for k, v in ship['cost'].items()])
            can = all(d.get(r, 0) >= c for r, c in ship['cost'].items())
            
            w['btn'].text = f"{ship['name']} (x{owned})\nCost: {cost_str}"
            w['btn'].background_color = (0.2, 0.35, 0.2, 1) if can or owned > 0 else (0.15, 0.15, 0.2, 1)
            
            if key in exps:
                remaining = max(0, int(exps[key] - time.time()))
                if remaining > 0:
                    w['status'].text = f"In expedition: {remaining}s"
                    w['status'].color = (1, 1, 0.5, 1)
                else:
                    w['status'].text = "READY! Tap to collect"
                    w['status'].color = (0.5, 1, 0.5, 1)
            elif owned > 0:
                w['status'].text = "Tap to send expedition"
                w['status'].color = (0.6, 0.8, 1, 1)
            else:
                w['status'].text = ""


# ============== ЭКРАН БОССОВ ==============

class BossScreen(BaseScreen):
    def __init__(self, game, **kwargs):
        super().__init__(game, **kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))
        
        layout.add_widget(Label(
            text='BOSS ARENA',
            font_size=sp(24),
            size_hint=(1, 0.08),
            color=(1, 0.5, 0.5, 1)
        ))
        
        self.boss_widgets = {}
        for key, boss in BOSSES.items():
            box = BoxLayout(orientation='vertical', size_hint=(1, 0.25), padding=dp(3))
            
            name = Label(text=boss['name'], font_size=sp(16), size_hint=(1, 0.25))
            hp_bar = ProgressBar(max=boss['hp'], value=boss['hp'], size_hint=(1, 0.2))
            hp_lbl = Label(text=f"HP: {boss['hp']}/{boss['hp']}", font_size=sp(12), size_hint=(1, 0.2))
            
            atk_btn = Button(
                text='ATTACK',
                font_size=sp(14),
                size_hint=(1, 0.35),
                background_color=(0.5, 0.2, 0.2, 1),
                background_normal=''
            )
            atk_btn.bind(on_release=lambda x, k=key: self.attack(k))
            
            box.add_widget(name)
            box.add_widget(hp_bar)
            box.add_widget(hp_lbl)
            box.add_widget(atk_btn)
            layout.add_widget(box)
            
            self.boss_widgets[key] = {'hp_bar': hp_bar, 'hp_lbl': hp_lbl, 'btn': atk_btn}
        
        back = Button(
            text='< BACK',
            font_size=sp(16),
            size_hint=(1, 0.08),
            background_color=(0.3, 0.3, 0.4, 1),
            background_normal=''
        )
        back.bind(on_release=lambda x: self.go_back())
        layout.add_widget(back)
        
        self.add_widget(layout)
    
    def attack(self, key):
        self.game.attack_boss(key)
        self.update()
    
    def go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'main'
    
    def update(self, dt=0):
        d = self.game.data
        boss_data = d.get('bosses', {})
        
        for key, boss in BOSSES.items():
            w = self.boss_widgets[key]
            bd = boss_data.get(key, {'hp': boss['hp'], 'cooldown': 0})
            
            hp = bd.get('hp', boss['hp'])
            cd = bd.get('cooldown', 0)
            remaining = max(0, int(cd - time.time()))
            
            w['hp_bar'].value = hp
            w['hp_lbl'].text = f"HP: {hp}/{boss['hp']}"
            
            if remaining > 0:
                w['btn'].text = f"Respawn: {remaining}s"
                w['btn'].background_color = (0.3, 0.3, 0.3, 1)
            elif hp <= 0:
                w['btn'].text = "Respawning..."
                w['btn'].background_color = (0.3, 0.3, 0.3, 1)
            else:
                w['btn'].text = "ATTACK"
                w['btn'].background_color = (0.6, 0.2, 0.2, 1)


# ============== ЭКРАН ПРЕСТИЖА ==============

class PrestigeScreen(BaseScreen):
    def __init__(self, game, **kwargs):
        super().__init__(game, **kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        layout.add_widget(Label(
            text='PRESTIGE',
            font_size=sp(28),
            size_hint=(1, 0.1),
            color=(1, 0.9, 0.3, 1)
        ))
        
        layout.add_widget(Label(
            text='Reset progress for\npermanent bonuses!\n\nEach point = +10% production',
            font_size=sp(14),
            size_hint=(1, 0.2),
            halign='center'
        ))
        
        self.current_lbl = Label(
            text='Current points: 0\nMultiplier: x1.0',
            font_size=sp(18),
            size_hint=(1, 0.15),
            color=(1, 0.85, 0.4, 1)
        )
        layout.add_widget(self.current_lbl)
        
        self.earn_lbl = Label(
            text='You will earn: 0 points',
            font_size=sp(16),
            size_hint=(1, 0.1),
            color=(0.7, 1, 0.7, 1)
        )
        layout.add_widget(self.earn_lbl)
        
        self.prestige_btn = Button(
            text='PRESTIGE',
            font_size=sp(24),
            size_hint=(0.8, 0.15),
            pos_hint={'center_x': 0.5},
            background_color=(0.5, 0.4, 0.1, 1),
            background_normal=''
        )
        self.prestige_btn.bind(on_release=lambda x: self.do_prestige())
        layout.add_widget(self.prestige_btn)
        
        self.req_lbl = Label(
            text='Need: 10000 total resources',
            font_size=sp(12),
            size_hint=(1, 0.08),
            color=(0.6, 0.6, 0.6, 1)
        )
        layout.add_widget(self.req_lbl)
        
        back = Button(
            text='< BACK',
            font_size=sp(16),
            size_hint=(1, 0.08),
            background_color=(0.3, 0.3, 0.4, 1),
            background_normal=''
        )
        back.bind(on_release=lambda x: self.go_back())
        layout.add_widget(back)
        
        self.add_widget(layout)
    
    def do_prestige(self):
        if self.game.do_prestige():
            self.go_back()
    
    def go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'main'
    
    def update(self, dt=0):
        d = self.game.data
        points = d.get('prestige_points', 0)
        mult = self.game.get_prestige_mult()
        
        total = d['energy'] + d['metal'] * 2 + d['crystal'] * 5
        earn = int(total ** 0.5 / 50)
        total_res = d['energy'] + d['metal'] + d['crystal']
        
        self.current_lbl.text = f"Current points: {points}\nMultiplier: x{mult:.1f}"
        self.earn_lbl.text = f"You will earn: {earn} points"
        
        if total_res >= 10000 and earn > 0:
            self.prestige_btn.background_color = (0.6, 0.5, 0.1, 1)
            self.req_lbl.text = "Ready to prestige!"
            self.req_lbl.color = (0.5, 1, 0.5, 1)
        else:
            self.prestige_btn.background_color = (0.3, 0.3, 0.3, 1)
            self.req_lbl.text = f"Need: 10000 resources (have: {int(total_res)})"
            self.req_lbl.color = (0.6, 0.6, 0.6, 1)


# ============== ПРИЛОЖЕНИЕ ==============

class StarEmpireApp(App):
    def build(self):
        self.title = 'Star Empire'
        self.game = GameManager()
        
        sm = ScreenManager()
        
        self.main_screen = MainScreen(self.game, name='main')
        self.upgrades_screen = UpgradesScreen(self.game, name='upgrades')
        self.ships_screen = ShipsScreen(self.game, name='ships')
        self.boss_screen = BossScreen(self.game, name='boss')
        self.prestige_screen = PrestigeScreen(self.game, name='prestige')
        
        sm.add_widget(self.main_screen)
        sm.add_widget(self.upgrades_screen)
        sm.add_widget(self.ships_screen)
        sm.add_widget(self.boss_screen)
        sm.add_widget(self.prestige_screen)
        
        Clock.schedule_interval(self.update_all, 0.2)
        Clock.schedule_interval(self.game.auto_collect, 1)
        
        return sm
    
    def update_all(self, dt):
        self.main_screen.update(dt)
        self.upgrades_screen.update(dt)
        self.ships_screen.update(dt)
        self.boss_screen.update(dt)
        self.prestige_screen.update(dt)
    
    def on_stop(self):
        self.game.save_game()


if __name__ == '__main__':
    StarEmpireApp().run()
