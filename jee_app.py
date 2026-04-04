from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

class JEEApp(App):
    def build(self):
        # Layout setup
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        # Title
        self.label = Label(text="BABU'S JEE APP", font_size='30sp', color=(1, 1, 0, 1))
        layout.add_widget(self.label)
        
        # Physics Button
        btn1 = Button(text="Physics: Unit of Force?", size_hint=(1, 0.5), background_color=(0, 0.7, 1, 1))
        btn1.bind(on_press=self.check_physics)
        layout.add_widget(btn1)
        
        # Chemistry Button
        btn2 = Button(text="Chemistry: Water Formula?", size_hint=(1, 0.5), background_color=(0.2, 0.8, 0.2, 1))
        btn2.bind(on_press=self.check_chemistry)
        layout.add_widget(btn2)
        
        return layout

    def check_physics(self, instance):
        self.label.text = "Answer: NEWTON ✅"

    def check_chemistry(self, instance):
        self.label.text = "Answer: H2O ✅"

if __name__ == "__main__":
    JEEApp().run()
