"""
Простая игра-кликер на Kivy
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation
import random


class ClickerGame(BoxLayout):
    """Основной виджет игры"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 20
        self.score = 0
        self.click_power = 1
        
        # Фон
        with self.canvas.before:
            self.bg_color = Color(0.15, 0.15, 0.25, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Заголовок
        self.title_label = Label(
            text='CLICKER GAME',
            font_size='36sp',
            size_hint=(1, 0.15),
            bold=True
        )
        self.add_widget(self.title_label)
        
        # Счётчик
        self.score_label = Label(
            text='Score: 0',
            font_size='48sp',
            size_hint=(1, 0.25),
            color=(1, 0.8, 0, 1)
        )
        self.add_widget(self.score_label)
        
        # Кнопка клика
        self.click_button = Button(
            text='TAP ME!',
            font_size='32sp',
            size_hint=(0.8, 0.35),
            pos_hint={'center_x': 0.5},
            background_color=(0.2, 0.7, 0.3, 1),
            background_normal='',
            bold=True
        )
        self.click_button.bind(on_press=self._on_click)
        self.add_widget(self.click_button)
        
        # Кнопка улучшения
        self.upgrade_button = Button(
            text='Upgrade (+1 power) - 50 pts',
            font_size='18sp',
            size_hint=(0.9, 0.12),
            pos_hint={'center_x': 0.5},
            background_color=(0.4, 0.4, 0.4, 1),
            background_normal=''
        )
        self.upgrade_button.bind(on_press=self._on_upgrade)
        self.add_widget(self.upgrade_button)
        
        # Статус
        self.status_label = Label(
            text='Power: 1',
            font_size='20sp',
            size_hint=(1, 0.1),
            color=(0.7, 0.7, 0.7, 1)
        )
        self.add_widget(self.status_label)
    
    def _update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def _on_click(self, instance):
        self.score += self.click_power
        self.score_label.text = f'Score: {self.score}'
        
        # Меняем цвет фона
        self.bg_color.r = random.uniform(0.1, 0.4)
        self.bg_color.g = random.uniform(0.1, 0.4)
        self.bg_color.b = random.uniform(0.2, 0.5)
        
        # Анимация
        anim = Animation(size_hint=(0.75, 0.32), duration=0.05)
        anim += Animation(size_hint=(0.8, 0.35), duration=0.05)
        anim.start(instance)
        
        self._update_upgrade_button()
    
    def _on_upgrade(self, instance):
        cost = self.click_power * 50
        if self.score >= cost:
            self.score -= cost
            self.click_power += 1
            self.score_label.text = f'Score: {self.score}'
            self.status_label.text = f'Power: {self.click_power}'
            self._update_upgrade_button()
            
            self.bg_color.r = 0.2
            self.bg_color.g = 0.6
            self.bg_color.b = 0.2
    
    def _update_upgrade_button(self):
        cost = self.click_power * 50
        self.upgrade_button.text = f'Upgrade (+1 power) - {cost} pts'
        if self.score >= cost:
            self.upgrade_button.background_color = (0.3, 0.6, 0.3, 1)
        else:
            self.upgrade_button.background_color = (0.4, 0.4, 0.4, 1)


class ClickerApp(App):
    def build(self):
        self.title = 'Clicker'
        return ClickerGame()


if __name__ == '__main__':
    ClickerApp().run()
