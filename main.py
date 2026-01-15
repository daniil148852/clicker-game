"""
STAR EMPIRE — Космическая Idle-RPG
Автор: AI Assistant
Версия: 1.0
"""

import json
import random
import time
from pathlib import Path
from functools import partial

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty, StringProperty, ListProperty


# ============== КОНФИГУРАЦИЯ ИГРЫ ==============

UPGRADES = {
    'energy_click': {
        'name': '⚡ Энергия за клик',
        'base_cost': 10,
        'cost_mult': 1.5,
        'resource': 'energy'
    },
    'metal_click': {
        'name': '🔩 Металл за клик',
        'base_cost': 25,
        'cost_mult': 1.6,
        'resource': 'metal'
    },
    'crystal_click': {
        'name': '💎 Кристаллы за клик',
        'base_cost': 100,
        'cost_mult': 1.8,
        'resource': 'crystal'
    },
    'energy_auto': {
        'name': '🔋 Авто-энергия',
        'base_cost': 50,
        'cost_mult': 1.7,
        'resource': 'energy'
    },
    'metal_auto': {
        'name': '⚙️ Авто-металл',
        'base_cost': 150,
        'cost_mult': 1.8,
        'resource': 'metal'
    },
    'crystal_auto': {
        'name': '🌟 Авто-кристаллы',
        'base_cost': 500,
        'cost_mult': 2.0,
        'resource': 'crystal'
    },
}

SHIPS = {
    'scout': {
        'name': '🛸 Разведчик',
        'cost': {'metal': 100},
        'time': 30,
        'rewards': {'energy': (50, 150), 'metal': (20, 50)}
    },
    'miner': {
        'name': '⛏️ Шахтёр',
        'cost': {'metal': 300, 'energy': 100},
        'time': 60,
        'rewards': {'metal': (100, 300), 'crystal': (5, 20)}
    },
    'cruiser': {
        'name': '🚀 Крейсер',
        'cost': {'metal': 1000, 'crystal': 50},
        'time': 120,
        'rewards': {'energy': (200, 500), 'metal': (150, 400), 'crystal': (20, 50)}
    },
    'battleship': {
        'name': '⚔️ Линкор',
        'cost': {'metal': 5000, 'crystal': 200, 'energy': 1000},
        'time': 300,
        'rewards': {'energy': (500, 1500), 'metal': (400, 1000), 'crystal': (50, 150)}
    },
}

BOSSES = {
    'asteroid': {
        'name': '☄️ Астероид-Гигант',
        'hp': 100,
        'reward': {'metal': 500, 'crystal': 25},
        'cooldown': 60
    },
    'pirate': {
        'name': '🏴‍☠️ Пиратский Флот',
        'hp': 500,
        'reward': {'energy': 1000, 'metal': 750, 'crystal': 50},
        'cooldown': 180
    },
    'alien': {
        'name': '👾 Инопланетный Титан',
        'hp': 2000,
        'reward': {'energy': 3000, 'metal': 2000, 'crystal': 200, 'prestige_points': 1},
        'cooldown': 600
    },
}

ACHIEVEMENTS = {
    'first_click': {'name': '👆 Первый клик', 'desc': 'Сделай первый клик', 'reward': 10},
    'energy_100': {'name': '⚡ Энергетик', 'desc': 'Накопи 100 энергии', 'reward': 25},
    'energy_1000': {'name': '⚡ Электростанция', 'desc': 'Накопи 1000 энергии', 'reward': 100},
    'energy_10000': {'name': '⚡ Термояд', 'desc': 'Накопи 10000 энергии', 'reward': 500},
    'metal_100': {'name': '🔩 Кузнец', 'desc': 'Накопи 100 металла', 'reward': 25},
    'metal_1000': {'name': '🔩 Фабрикант', 'desc': 'Накопи 1000 металла', 'reward': 100},
    'crystal_50': {'name': '💎 Старатель', 'desc': 'Накопи 50 кристаллов', 'reward': 50},
    'crystal_500': {'name': '💎 Ювелир', 'desc': 'Накопи 500 кристаллов', 'reward': 250},
    'first_ship': {'name': '🚀 Капитан', 'desc': 'Купи первый корабль', 'reward': 50},
    'fleet_5': {'name': '🛸 Адмирал', 'desc': 'Имей 5 кораблей', 'reward': 200},
    'first_boss': {'name': '⚔️ Охотник', 'desc': 'Победи первого босса', 'reward': 100},
    'all_bosses': {'name': '🏆 Легенда', 'desc': 'Победи всех боссов', 'reward': 1000},
    'upgrades_10': {'name': '📈 Прогресс', 'desc': 'Купи 10 улучшений', 'reward': 75},
    'prestige_1': {'name': '⭐ Возрождение', 'desc': 'Сделай первый престиж', 'reward': 500},
    'clicks_1000': {'name': '🖱️ Кликер', 'desc': 'Сделай 1000 кликов', 'reward': 150},
}


# ============== ЗВЁЗДНЫЙ ФОН ==============

class StarField(Widget):
    """Анимированное звёздное небо"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stars = []
        self.bind(size=self.create_stars)
        Clock.schedule_interval(self.twinkle, 0.1)
    
    def create_stars(self, *args):
        self.canvas.before.clear()
        self.stars = []
        
        with self.canvas.before:
            # Градиентный фон
            Color(0.02, 0.02, 0.08, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Создаём звёзды
            for _ in range(80):
                x = random.uniform(0, self.width)
                y = random.uniform(0, self.height)
                size = random.uniform(1, 3)
                brightness = random.uniform(0.3, 1.0)
                
                color = Color(brightness, brightness, brightness * 1.1, brightness)
                star = Ellipse(pos=(x, y), size=(size, size))
                self.stars.append((color, star, brightness))
    
    def twinkle(self, dt):
        for color, star, base_brightness in self.stars:
            # Мерцание звёзд
            flicker = random.uniform(-0.2, 0.2)
            new_brightness = max(0.1, min(1.0, base_brightness + flicker))
            color.a = new_brightness


# ============== КНОПКИ С ЭФФЕКТАМИ ==============

class GlowButton(Button):
    """Кнопка со свечением"""
    
    def __init__(self, glow_color=(0.3, 0.6, 1, 0.3), **kwargs):
        super().__init__(**kwargs)
        self.glow_color = glow_color
        self.background_normal = ''
        self.background_down = ''
        self.bind(pos=self.update_glow, size=self.update_glow)
        Clock.schedule_once(self.update_glow, 0)
    
    def update_glow(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Свечение
            Color(*self.glow_color)
            Rectangle(
                pos=(self.x - 3, self.y - 3),
                size=(self.width + 6, self.height + 6)
            )
    
    def on_press(self):
        anim = Animation(size_hint=(self.size_hint[0] * 0.95, self.size_hint[1] * 0.95), duration=0.05)
        anim.start(self)
    
    def on_release(self):
        anim = Animation(size_hint=(self.size_hint[0] / 0.95, self.size_hint[1] / 0.95), duration=0.05)
        anim.start(self)


# ============== ГЛАВНЫЙ ЭКРАН ДОБЫЧИ ==============

class MiningTab(BoxLayout):
    """Вкладка добычи ресурсов"""
    
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # Заголовок
        title = Label(
            text='🌌 STAR EMPIRE 🌌',
            font_size=sp(28),
            size_hint=(1, 0.08),
            bold=True,
            color=(0.9, 0.8, 1, 1)
        )
        self.add_widget(title)
        
        # Престиж-множитель
        self.prestige_label = Label(
            text='⭐ Престиж: x1.0',
            font_size=sp(14),
            size_hint=(1, 0.04),
            color=(1, 0.9, 0.3, 1)
        )
        self.add_widget(self.prestige_label)
        
        # Панель ресурсов
        self.resources_panel = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.12),
            spacing=dp(5)
        )
        
        self.energy_label = self.create_resource_label('⚡', '0', (0.3, 0.8, 1, 1))
        self.metal_label = self.create_resource_label('🔩', '0', (0.7, 0.7, 0.7, 1))
        self.crystal_label = self.create_resource_label('💎', '0', (0.9, 0.4, 1, 1))
        
        self.resources_panel.add_widget(self.energy_label)
        self.resources_panel.add_widget(self.metal_label)
        self.resources_panel.add_widget(self.crystal_label)
        self.add_widget(self.resources_panel)
        
        # Авто-доход
        self.auto_label = Label(
            text='📊 Авто: +0⚡ +0🔩 +0💎 /сек',
            font_size=sp(12),
            size_hint=(1, 0.04),
            color=(0.6, 0.6, 0.6, 1)
        )
        self.add_widget(self.auto_label)
        
        # Кнопки добычи
        mining_grid = GridLayout(cols=3, size_hint=(1, 0.35), spacing=dp(10), padding=dp(5))
        
        self.energy_btn = GlowButton(
            text='⚡\nЭнергия\n+1',
            font_size=sp(16),
            background_color=(0.1, 0.3, 0.6, 1),
            glow_color=(0.2, 0.5, 1, 0.4)
        )
        self.energy_btn.bind(on_release=lambda x: self.game.mine('energy'))
        
        self.metal_btn = GlowButton(
            text='🔩\nМеталл\n+0',
            font_size=sp(16),
            background_color=(0.3, 0.3, 0.35, 1),
            glow_color=(0.5, 0.5, 0.5, 0.4)
        )
        self.metal_btn.bind(on_release=lambda x: self.game.mine('metal'))
        
        self.crystal_btn = GlowButton(
            text='💎\nКристаллы\n+0',
            font_size=sp(16),
            background_color=(0.4, 0.1, 0.5, 1),
            glow_color=(0.7, 0.3, 1, 0.4)
        )
        self.crystal_btn.bind(on_release=lambda x: self.game.mine('crystal'))
        
        mining_grid.add_widget(self.energy_btn)
        mining_grid.add_widget(self.metal_btn)
        mining_grid.add_widget(self.crystal_btn)
        self.add_widget(mining_grid)
        
        # Статистика
        self.stats_label = Label(
            text='📈 Кликов: 0 | Время: 0:00',
            font_size=sp(12),
            size_hint=(1, 0.04),
            color=(0.5, 0.5, 0.5, 1)
        )
        self.add_widget(self.stats_label)
        
        # Кнопка ежедневного бонуса
        self.daily_btn = GlowButton(
            text='🎁 Ежедневный бонус!',
            font_size=sp(16),
            size_hint=(1, 0.08),
            background_color=(0.2, 0.5, 0.2, 1),
            glow_color=(0.3, 0.8, 0.3, 0.5)
        )
        self.daily_btn.bind(on_release=lambda x: self.game.claim_daily())
        self.add_widget(self.daily_btn)
        
        # Мини-ивент
        self.event_label = Label(
            text='',
            font_size=sp(14),
            size_hint=(1, 0.06),
            color=(1, 1, 0.5, 1)
        )
        self.add_widget(self.event_label)
    
    def create_resource_label(self, icon, value, color):
        box = BoxLayout(orientation='vertical')
        lbl = Label(
            text=f'{icon}\n{value}',
            font_size=sp(18),
            halign='center',
            color=color
        )
        box.add_widget(lbl)
        return lbl
    
    def update(self):
        data = self.game.data
        mult = self.game.get_prestige_mult()
        
        self.energy_label.text = f"⚡\n{self.format_number(data['energy'])}"
        self.metal_label.text = f"🔩\n{self.format_number(data['metal'])}"
        self.crystal_label.text = f"💎\n{self.format_number(data['crystal'])}"
        
        e_click = max(1, data['upgrades'].get('energy_click', 0)) * mult
        m_click = data['upgrades'].get('metal_click', 0) * mult
        c_click = data['upgrades'].get('crystal_click', 0) * mult
        
        self.energy_btn.text = f"⚡\nЭнергия\n+{self.format_number(e_click)}"
        self.metal_btn.text = f"🔩\nМеталл\n+{self.format_number(m_click)}"
        self.crystal_btn.text = f"💎\nКристаллы\n+{self.format_number(c_click)}"
        
        e_auto = data['upgrades'].get('energy_auto', 0) * mult
        m_auto = data['upgrades'].get('metal_auto', 0) * mult
        c_auto = data['upgrades'].get('crystal_auto', 0) * mult
        
        self.auto_label.text = f"📊 Авто: +{e_auto:.0f}⚡ +{m_auto:.0f}🔩 +{c_auto:.0f}💎 /сек"
        self.prestige_label.text = f"⭐ Престиж: x{mult:.1f} | Очки: {data.get('prestige_points', 0)}"
        
        play_time = int(data.get('play_time', 0))
        mins, secs = divmod(play_time, 60)
        hours, mins = divmod(mins, 60)
        time_str = f"{hours}:{mins:02d}:{secs:02d}" if hours else f"{mins}:{secs:02d}"
        self.stats_label.text = f"📈 Кликов: {data.get('total_clicks', 0)} | Время: {time_str}"
        
        # Ежедневный бонус
        if self.game.can_claim_daily():
            self.daily_btn.text = '🎁 Ежедневный бонус ГОТОВ!'
            self.daily_btn.background_color = (0.2, 0.6, 0.2, 1)
        else:
            remaining = self.game.daily_cooldown_remaining()
            self.daily_btn.text = f'🎁 Бонус через: {remaining}'
            self.daily_btn.background_color = (0.3, 0.3, 0.3, 1)
    
    def format_number(self, n):
        n = int(n)
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)
    
    def show_event(self, text):
        self.event_label.text = text
        self.event_label.color = (1, 1, 0.5, 1)
        anim = Animation(color=(1, 1, 0.5, 0), duration=3)
        anim.start(self.event_label)


# ============== ВКЛАДКА УЛУЧШЕНИЙ ==============

class UpgradesTab(ScrollView):
    """Вкладка улучшений"""
    
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        
        self.layout = GridLayout(
            cols=1,
            spacing=dp(8),
            padding=dp(10),
            size_hint_y=None
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))
        
        self.buttons = {}
        for key, upg in UPGRADES.items():
            btn = Button(
                text=f"{upg['name']}\nУровень: 0 | Цена: {upg['base_cost']}⚡",
                font_size=sp(14),
                size_hint_y=None,
                height=dp(70),
                background_color=(0.15, 0.15, 0.25, 1),
                background_normal=''
            )
            btn.bind(on_release=partial(self.buy_upgrade, key))
            self.buttons[key] = btn
            self.layout.add_widget(btn)
        
        self.add_widget(self.layout)
    
    def buy_upgrade(self, key, *args):
        self.game.buy_upgrade(key)
    
    def update(self):
        data = self.game.data
        for key, upg in UPGRADES.items():
            level = data['upgrades'].get(key, 0)
            cost = int(upg['base_cost'] * (upg['cost_mult'] ** level))
            
            res_icon = {'energy': '⚡', 'metal': '🔩', 'crystal': '💎'}[upg['resource']]
            current = data[upg['resource']]
            
            can_buy = current >= cost
            color = (0.2, 0.4, 0.2, 1) if can_buy else (0.2, 0.2, 0.2, 1)
            
            self.buttons[key].text = f"{upg['name']}\nУровень: {level} | Цена: {cost}{res_icon}"
            self.buttons[key].background_color = color


# ============== ВКЛАДКА КОРАБЛЕЙ ==============

class ShipsTab(ScrollView):
    """Вкладка кораблей и экспедиций"""
    
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        
        self.layout = GridLayout(
            cols=1,
            spacing=dp(8),
            padding=dp(10),
            size_hint_y=None
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))
        
        # Заголовок
        title = Label(
            text='🚀 КОСМОФЛОТ 🚀',
            font_size=sp(22),
            size_hint_y=None,
            height=dp(40),
            color=(0.8, 0.9, 1, 1)
        )
        self.layout.add_widget(title)
        
        self.fleet_label = Label(
            text='Кораблей: 0',
            font_size=sp(16),
            size_hint_y=None,
            height=dp(30)
        )
        self.layout.add_widget(self.fleet_label)
        
        self.ship_buttons = {}
        self.expedition_labels = {}
        
        for key, ship in SHIPS.items():
            # Кнопка покупки
            cost_str = ' '.join([f"{v}{'⚡' if k=='energy' else '🔩' if k=='metal' else '💎'}" 
                                for k, v in ship['cost'].items()])
            
            box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100))
            
            btn = Button(
                text=f"{ship['name']}\nЦена: {cost_str}\nВремя: {ship['time']}сек",
                font_size=sp(13),
                background_color=(0.15, 0.2, 0.3, 1),
                background_normal='',
                size_hint_y=None,
                height=dp(65)
            )
            btn.bind(on_release=partial(self.buy_ship, key))
            self.ship_buttons[key] = btn
            box.add_widget(btn)
            
            # Статус экспедиции
            exp_label = Label(
                text='',
                font_size=sp(11),
                size_hint_y=None,
                height=dp(25),
                color=(0.7, 1, 0.7, 1)
            )
            self.expedition_labels[key] = exp_label
            box.add_widget(exp_label)
            
            self.layout.add_widget(box)
        
        self.add_widget(self.layout)
    
    def buy_ship(self, key, *args):
        self.game.buy_ship(key)
    
    def update(self):
        data = self.game.data
        ships_owned = data.get('ships', {})
        expeditions = data.get('expeditions', {})
        
        total_ships = sum(ships_owned.values())
        self.fleet_label.text = f'🛸 Кораблей в флоте: {total_ships}'
        
        for key, ship in SHIPS.items():
            owned = ships_owned.get(key, 0)
            can_buy = all(data.get(res, 0) >= cost for res, cost in ship['cost'].items())
            
            cost_str = ' '.join([f"{v}{'⚡' if k=='energy' else '🔩' if k=='metal' else '💎'}" 
                                for k, v in ship['cost'].items()])
            
            color = (0.2, 0.35, 0.2, 1) if can_buy else (0.15, 0.15, 0.2, 1)
            self.ship_buttons[key].text = f"{ship['name']} (x{owned})\nЦена: {cost_str}"
            self.ship_buttons[key].background_color = color
            
            # Экспедиция
            if key in expeditions:
                remaining = max(0, expeditions[key] - time.time())
                if remaining > 0:
                    self.expedition_labels[key].text = f"🚀 В экспедиции: {int(remaining)} сек"
                    self.expedition_labels[key].color = (1, 1, 0.5, 1)
                else:
                    self.expedition_labels[key].text = "✅ Экспедиция завершена! Нажми для сбора"
                    self.expedition_labels[key].color = (0.5, 1, 0.5, 1)
            elif owned > 0:
                self.expedition_labels[key].text = "🎯 Нажми чтобы отправить"
                self.expedition_labels[key].color = (0.6, 0.8, 1, 1)
            else:
                self.expedition_labels[key].text = ""


# ============== ВКЛАДКА БОССОВ ==============

class BossTab(BoxLayout):
    """Вкладка боссов"""
    
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(8)
        
        title = Label(
            text='⚔️ АРЕНА БОССОВ ⚔️',
            font_size=sp(24),
            size_hint=(1, 0.1),
            color=(1, 0.5, 0.5, 1)
        )
        self.add_widget(title)
        
        self.boss_widgets = {}
        
        for key, boss in BOSSES.items():
            box = BoxLayout(orientation='vertical', size_hint=(1, 0.25), padding=dp(5))
            
            # Имя и HP
            name_lbl = Label(
                text=f"{boss['name']}",
                font_size=sp(18),
                size_hint=(1, 0.3)
            )
            box.add_widget(name_lbl)
            
            # HP бар
            hp_bar = ProgressBar(max=boss['hp'], value=boss['hp'], size_hint=(1, 0.2))
            box.add_widget(hp_bar)
            
            hp_lbl = Label(
                text=f"HP: {boss['hp']}/{boss['hp']}",
                font_size=sp(12),
                size_hint=(1, 0.2)
            )
            box.add_widget(hp_lbl)
            
            # Кнопка атаки
            atk_btn = Button(
                text='⚔️ АТАКОВАТЬ',
                font_size=sp(14),
                size_hint=(1, 0.3),
                background_color=(0.5, 0.2, 0.2, 1),
                background_normal=''
            )
            atk_btn.bind(on_release=partial(self.attack_boss, key))
            box.add_widget(atk_btn)
            
            self.boss_widgets[key] = {
                'name': name_lbl,
                'hp_bar': hp_bar,
                'hp_lbl': hp_lbl,
                'btn': atk_btn
            }
            
            self.add_widget(box)
    
    def attack_boss(self, key, *args):
        self.game.attack_boss(key)
    
    def update(self):
        data = self.game.data
        boss_data = data.get('bosses', {})
        
        for key, boss in BOSSES.items():
            widgets = self.boss_widgets[key]
            bd = boss_data.get(key, {'hp': boss['hp'], 'cooldown': 0})
            
            current_hp = bd.get('hp', boss['hp'])
            cooldown = bd.get('cooldown', 0)
            remaining = max(0, cooldown - time.time())
            
            widgets['hp_bar'].value = current_hp
            widgets['hp_lbl'].text = f"HP: {current_hp}/{boss['hp']}"
            
            if remaining > 0:
                widgets['btn'].text = f"⏳ Возрождение: {int(remaining)}с"
                widgets['btn'].background_color = (0.3, 0.3, 0.3, 1)
            elif current_hp <= 0:
                widgets['btn'].text = f"⏳ Возрождение..."
                widgets['btn'].background_color = (0.3, 0.3, 0.3, 1)
            else:
                widgets['btn'].text = "⚔️ АТАКОВАТЬ"
                widgets['btn'].background_color = (0.6, 0.2, 0.2, 1)


# ============== ВКЛАДКА ДОСТИЖЕНИЙ ==============

class AchievementsTab(ScrollView):
    """Вкладка достижений"""
    
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        
        self.layout = GridLayout(
            cols=1,
            spacing=dp(5),
            padding=dp(10),
            size_hint_y=None
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))
        
        title = Label(
            text='🏆 ДОСТИЖЕНИЯ 🏆',
            font_size=sp(22),
            size_hint_y=None,
            height=dp(40),
            color=(1, 0.85, 0.3, 1)
        )
        self.layout.add_widget(title)
        
        self.ach_labels = {}
        
        for key, ach in ACHIEVEMENTS.items():
            lbl = Label(
                text=f"🔒 {ach['name']}\n{ach['desc']} | +{ach['reward']}⚡",
                font_size=sp(13),
                size_hint_y=None,
                height=dp(50),
                color=(0.5, 0.5, 0.5, 1),
                halign='left',
                text_size=(Window.width - dp(40), None)
            )
            self.ach_labels[key] = lbl
            self.layout.add_widget(lbl)
        
        self.add_widget(self.layout)
    
    def update(self):
        data = self.game.data
        unlocked = data.get('achievements', [])
        
        for key, ach in ACHIEVEMENTS.items():
            if key in unlocked:
                self.ach_labels[key].text = f"✅ {ach['name']}\n{ach['desc']}"
                self.ach_labels[key].color = (0.5, 1, 0.5, 1)
            else:
                self.ach_labels[key].text = f"🔒 {ach['name']}\n{ach['desc']} | +{ach['reward']}⚡"
                self.ach_labels[key].color = (0.5, 0.5, 0.5, 1)


# ============== ВКЛАДКА ПРЕСТИЖА ==============

class PrestigeTab(BoxLayout):
    """Вкладка престижа"""
    
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.orientation = 'vertical'
        self.padding = dp(20)
        self.spacing = dp(15)
        
        title = Label(
            text='⭐ ПРЕСТИЖ ⭐',
            font_size=sp(28),
            size_hint=(1, 0.1),
            color=(1, 0.9, 0.3, 1)
        )
        self.add_widget(title)
        
        desc = Label(
            text='Сбросьте прогресс, чтобы получить\nпостоянные бонусы к добыче!\n\n'
                 'Каждое очко престижа даёт +10% к добыче.',
            font_size=sp(14),
            size_hint=(1, 0.2),
            halign='center'
        )
        self.add_widget(desc)
        
        self.current_label = Label(
            text='Текущие очки престижа: 0\nМножитель: x1.0',
            font_size=sp(18),
            size_hint=(1, 0.15),
            color=(1, 0.85, 0.4, 1)
        )
        self.add_widget(self.current_label)
        
        self.earn_label = Label(
            text='При престиже вы получите: 0 очков',
            font_size=sp(16),
            size_hint=(1, 0.1),
            color=(0.7, 1, 0.7, 1)
        )
        self.add_widget(self.earn_label)
        
        self.prestige_btn = GlowButton(
            text='🌟 ПРЕСТИЖ 🌟',
            font_size=sp(24),
            size_hint=(0.8, 0.15),
            pos_hint={'center_x': 0.5},
            background_color=(0.6, 0.5, 0.1, 1),
            glow_color=(1, 0.9, 0.3, 0.5)
        )
        self.prestige_btn.bind(on_release=lambda x: self.game.do_prestige())
        self.add_widget(self.prestige_btn)
        
        self.req_label = Label(
            text='Требуется: 10000 всего ресурсов',
            font_size=sp(12),
            size_hint=(1, 0.1),
            color=(0.6, 0.6, 0.6, 1)
        )
        self.add_widget(self.req_label)
    
    def update(self):
        data = self.game.data
        points = data.get('prestige_points', 0)
        mult = self.game.get_prestige_mult()
        
        self.current_label.text = f"Текущие очки престижа: {points}\nМножитель: x{mult:.1f}"
        
        earn = self.game.calculate_prestige_earn()
        self.earn_label.text = f"При престиже вы получите: {earn} очков"
        
        total = data['energy'] + data['metal'] + data['crystal']
        if total >= 10000 and earn > 0:
            self.prestige_btn.background_color = (0.7, 0.6, 0.1, 1)
            self.req_label.text = "✅ Можно сделать престиж!"
            self.req_label.color = (0.5, 1, 0.5, 1)
        else:
            self.prestige_btn.background_color = (0.3, 0.3, 0.3, 1)
            self.req_label.text = f"Требуется: 10000 ресурсов (сейчас: {int(total)})"
            self.req_label.color = (0.6, 0.6, 0.6, 1)


# ============== ГЛАВНЫЙ ИГРОВОЙ КЛАСС ==============

class GameManager:
    """Управление игровыми данными и логикой"""
    
    def __init__(self, ui_callback=None):
        self.ui_callback = ui_callback
        self.save_path = self.get_save_path()
        self.data = self.load_game()
        self.last_save = time.time()
        self.session_start = time.time()
    
    def get_save_path(self):
        try:
            from android.storage import app_storage_path
            return Path(app_storage_path()) / 'save.json'
        except:
            return Path.home() / '.starempire_save.json'
    
    def load_game(self):
        default = {
            'energy': 0,
            'metal': 0,
            'crystal': 0,
            'upgrades': {},
            'ships': {},
            'expeditions': {},
            'bosses': {},
            'achievements': [],
            'prestige_points': 0,
            'total_clicks': 0,
            'play_time': 0,
            'last_daily': 0,
            'bosses_killed': []
        }
        
        try:
            if self.save_path.exists():
                with open(self.save_path, 'r') as f:
                    saved = json.load(f)
                    for key in default:
                        if key not in saved:
                            saved[key] = default[key]
                    return saved
        except Exception as e:
            print(f"Load error: {e}")
        
        return default
    
    def save_game(self):
        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.save_path, 'w') as f:
                json.dump(self.data, f)
        except Exception as e:
            print(f"Save error: {e}")
    
    def get_prestige_mult(self):
        return 1.0 + (self.data.get('prestige_points', 0) * 0.1)
    
    def mine(self, resource):
        mult = self.get_prestige_mult()
        
        if resource == 'energy':
            amount = max(1, self.data['upgrades'].get('energy_click', 0)) * mult
        elif resource == 'metal':
            amount = self.data['upgrades'].get('metal_click', 0) * mult
        elif resource == 'crystal':
            amount = self.data['upgrades'].get('crystal_click', 0) * mult
        else:
            return
        
        self.data[resource] = self.data.get(resource, 0) + amount
        self.data['total_clicks'] = self.data.get('total_clicks', 0) + 1
        
        self.check_achievements()
        
        # Случайный ивент
        if random.random() < 0.02:
            bonus = random.choice(['energy', 'metal', 'crystal'])
            bonus_amount = random.randint(10, 50) * mult
            self.data[bonus] += bonus_amount
            icon = {'energy': '⚡', 'metal': '🔩', 'crystal': '💎'}[bonus]
            if self.ui_callback:
                self.ui_callback('event', f"🌟 Бонус! +{int(bonus_amount)}{icon}")
    
    def buy_upgrade(self, key):
        if key not in UPGRADES:
            return
        
        upg = UPGRADES[key]
        level = self.data['upgrades'].get(key, 0)
        cost = int(upg['base_cost'] * (upg['cost_mult'] ** level))
        
        if self.data[upg['resource']] >= cost:
            self.data[upg['resource']] -= cost
            self.data['upgrades'][key] = level + 1
            self.check_achievements()
    
    def buy_ship(self, key):
        if key not in SHIPS:
            return
        
        ship = SHIPS[key]
        
        # Проверка наличия экспедиции
        if key in self.data.get('expeditions', {}):
            exp_time = self.data['expeditions'][key]
            if time.time() >= exp_time:
                # Собираем награду
                rewards = ship['rewards']
                for res, (min_r, max_r) in rewards.items():
                    amount = random.randint(min_r, max_r) * self.get_prestige_mult()
                    self.data[res] = self.data.get(res, 0) + amount
                
                del self.data['expeditions'][key]
                if self.ui_callback:
                    self.ui_callback('event', f"✅ Экспедиция {ship['name']} завершена!")
                return
            else:
                return  # Ещё в полёте
        
        # Если есть корабль — отправляем в экспедицию
        ships_owned = self.data.get('ships', {})
        if ships_owned.get(key, 0) > 0:
            if 'expeditions' not in self.data:
                self.data['expeditions'] = {}
            self.data['expeditions'][key] = time.time() + ship['time']
            if self.ui_callback:
                self.ui_callback('event', f"🚀 {ship['name']} отправлен в экспедицию!")
            return
        
        # Покупка корабля
        can_buy = all(self.data.get(res, 0) >= cost for res, cost in ship['cost'].items())
        if can_buy:
            for res, cost in ship['cost'].items():
                self.data[res] -= cost
            
            if 'ships' not in self.data:
                self.data['ships'] = {}
            self.data['ships'][key] = self.data['ships'].get(key, 0) + 1
            self.check_achievements()
    
    def attack_boss(self, key):
        if key not in BOSSES:
            return
        
        boss = BOSSES[key]
        
        if 'bosses' not in self.data:
            self.data['bosses'] = {}
        
        if key not in self.data['bosses']:
            self.data['bosses'][key] = {'hp': boss['hp'], 'cooldown': 0}
        
        bd = self.data['bosses'][key]
        
        # Проверка кулдауна
        if time.time() < bd.get('cooldown', 0):
            return
        
        if bd['hp'] <= 0:
            bd['hp'] = boss['hp']
            return
        
        # Расчёт урона
        total_ships = sum(self.data.get('ships', {}).values())
        base_damage = 1 + self.data['upgrades'].get('energy_click', 0)
        damage = (base_damage + total_ships * 5) * self.get_prestige_mult()
        
        bd['hp'] = max(0, bd['hp'] - damage)
        
        if bd['hp'] <= 0:
            # Победа!
            for res, amount in boss['reward'].items():
                if res == 'prestige_points':
                    self.data['prestige_points'] = self.data.get('prestige_points', 0) + amount
                else:
                    self.data[res] = self.data.get(res, 0) + amount
            
            bd['cooldown'] = time.time() + boss['cooldown']
            
            if key not in self.data.get('bosses_killed', []):
                if 'bosses_killed' not in self.data:
                    self.data['bosses_killed'] = []
                self.data['bosses_killed'].append(key)
            
            if self.ui_callback:
                self.ui_callback('event', f"🏆 Босс {boss['name']} повержен!")
            
            self.check_achievements()
    
    def can_claim_daily(self):
        last = self.data.get('last_daily', 0)
        return time.time() - last >= 86400  # 24 часа
    
    def daily_cooldown_remaining(self):
        last = self.data.get('last_daily', 0)
        remaining = max(0, 86400 - (time.time() - last))
        hours = int(remaining // 3600)
        mins = int((remaining % 3600) // 60)
        return f"{hours}ч {mins}м"
    
    def claim_daily(self):
        if self.can_claim_daily():
            mult = self.get_prestige_mult()
            self.data['energy'] += int(100 * mult)
            self.data['metal'] += int(50 * mult)
            self.data['crystal'] += int(10 * mult)
            self.data['last_daily'] = time.time()
            
            if self.ui_callback:
                self.ui_callback('event', "🎁 Ежедневный бонус получен!")
    
    def calculate_prestige_earn(self):
        total = self.data['energy'] + self.data['metal'] * 2 + self.data['crystal'] * 5
        return int(total ** 0.5 / 50)
    
    def do_prestige(self):
        earn = self.calculate_prestige_earn()
        total = self.data['energy'] + self.data['metal'] + self.data['crystal']
        
        if earn > 0 and total >= 10000:
            self.data['prestige_points'] = self.data.get('prestige_points', 0) + earn
            
            # Сброс прогресса
            self.data['energy'] = 0
            self.data['metal'] = 0
            self.data['crystal'] = 0
            self.data['upgrades'] = {}
            self.data['ships'] = {}
            self.data['expeditions'] = {}
            self.data['bosses'] = {}
            
            self.check_achievements()
            
            if self.ui_callback:
                self.ui_callback('event', f"⭐ ПРЕСТИЖ! +{earn} очков!")
    
    def check_achievements(self):
        unlocked = self.data.get('achievements', [])
        new_unlocks = []
        
        checks = {
            'first_click': self.data.get('total_clicks', 0) >= 1,
            'energy_100': self.data['energy'] >= 100,
            'energy_1000': self.data['energy'] >= 1000,
            'energy_10000': self.data['energy'] >= 10000,
            'metal_100': self.data['metal'] >= 100,
            'metal_1000': self.data['metal'] >= 1000,
            'crystal_50': self.data['crystal'] >= 50,
            'crystal_500': self.data['crystal'] >= 500,
            'first_ship': sum(self.data.get('ships', {}).values()) >= 1,
            'fleet_5': sum(self.data.get('ships', {}).values()) >= 5,
            'first_boss': len(self.data.get('bosses_killed', [])) >= 1,
            'all_bosses': len(self.data.get('bosses_killed', [])) >= len(BOSSES),
            'upgrades_10': sum(self.data.get('upgrades', {}).values()) >= 10,
            'prestige_1': self.data.get('prestige_points', 0) >= 1,
            'clicks_1000': self.data.get('total_clicks', 0) >= 1000,
        }
        
        for key, condition in checks.items():
            if condition and key not in unlocked:
                unlocked.append(key)
                new_unlocks.append(key)
                self.data['energy'] += ACHIEVEMENTS[key]['reward']
        
        self.data['achievements'] = unlocked
        
        if new_unlocks and self.ui_callback:
            for key in new_unlocks:
                self.ui_callback('event', f"🏆 Достижение: {ACHIEVEMENTS[key]['name']}!")
    
    def auto_collect(self, dt):
        mult = self.get_prestige_mult()
        
        e_auto = self.data['upgrades'].get('energy_auto', 0) * mult
        m_auto = self.data['upgrades'].get('metal_auto', 0) * mult
        c_auto = self.data['upgrades'].get('crystal_auto', 0) * mult
        
        self.data['energy'] += e_auto * dt
        self.data['metal'] += m_auto * dt
        self.data['crystal'] += c_auto * dt
        
        self.data['play_time'] = self.data.get('play_time', 0) + dt
        
        # Автосохранение каждые 30 сек
        if time.time() - self.last_save > 30:
            self.save_game()
            self.last_save = time.time()


# ============== ГЛАВНОЕ ПРИЛОЖЕНИЕ ==============

class StarEmpireApp(App):
    """Главное приложение"""
    
    def build(self):
        self.title = 'Star Empire'
        
        # Основной layout со звёздами
        self.root = BoxLayout(orientation='vertical')
        self.stars = StarField()
        
        # Игровой менеджер
        self.game = GameManager(ui_callback=self.handle_event)
        
        # Табы
        self.tabs = TabbedPanel(
            do_default_tab=False,
            tab_width=Window.width / 5 - dp(5),
            background_color=(0.05, 0.05, 0.12, 0.95)
        )
        
        # Вкладки
        self.mining_tab = MiningTab(self.game)
        self.upgrades_tab = UpgradesTab(self.game)
        self.ships_tab = ShipsTab(self.game)
        self.boss_tab = BossTab(self.game)
        self.achievements_tab = AchievementsTab(self.game)
        self.prestige_tab = PrestigeTab(self.game)
        
        # Добавляем вкладки
        tabs_config = [
            ('⚡', self.mining_tab),
            ('📈', self.upgrades_tab),
            ('🚀', self.ships_tab),
            ('⚔️', self.boss_tab),
            ('🏆', self.achievements_tab),
            ('⭐', self.prestige_tab),
        ]
        
        for text, content in tabs_config:
            item = TabbedPanelItem(text=text, font_size=sp(16))
            item.add_widget(content)
            self.tabs.add_widget(item)
        
        # Звёздный фон + табы
        self.root.add_widget(self.stars)
        self.root.add_widget(self.tabs)
        
        # Обновление UI
        Clock.schedule_interval(self.update, 0.1)
        Clock.schedule_interval(self.game.auto_collect, 1)
        
        return self.root
    
    def handle_event(self, event_type, data):
        if event_type == 'event':
            self.mining_tab.show_event(data)
    
    def update(self, dt):
        self.mining_tab.update()
        self.upgrades_tab.update()
        self.ships_tab.update()
        self.boss_tab.update()
        self.achievements_tab.update()
        self.prestige_tab.update()
    
    def on_stop(self):
        self.game.save_game()


if __name__ == '__main__':
    StarEmpireApp().run()
