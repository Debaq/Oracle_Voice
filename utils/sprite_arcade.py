import arcade
import json
from pathlib import Path

class SpriteAtlasEditor(arcade.Window):
    """Editor simple para crear atlas de sprites y generar JSON de configuración"""
    
    def __init__(self, atlas_path: str, width=1200, height=800):
        super().__init__(width, height, "Sprite Atlas Editor")
        
        # Configuración
        self.atlas_path = Path(atlas_path)
        if not self.atlas_path.exists():
            raise FileNotFoundError(f"Atlas no encontrado: {atlas_path}")
            
        # Cargar atlas
        self.atlas_texture = arcade.load_texture(str(self.atlas_path))
        
        # Estado del editor
        self.current_layer = "base"
        self.layers = {
            "base": [],
            "hands": [],
            "eyes": [],
            "mouths": [],
            "glow": []
        }
        
        # Offsets para cada capa (posición relativa a la base)
        self.offsets = {
            "hands": [0, 0],
            "eyes": [0, 0],
            "mouths": [0, 0],
            "glow": [0, 0]
        }
        
        # Control de vista
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        # Control de selección
        self.selecting = False
        self.start_x = 0
        self.start_y = 0
        self.current_rect = None
        
        # Colores para cada capa
        self.layer_colors = {
            "base": arcade.color.YELLOW,
            "hands": arcade.color.CYAN,
            "eyes": arcade.color.LIME_GREEN,
            "mouths": arcade.color.PINK,
            "glow": arcade.color.LIGHT_BLUE
        }
        
        # Centrar atlas al inicio
        self.center_atlas()
        
        # Cargar configuración existente si existe
        config_path = self.atlas_path.with_suffix('.json')
        if config_path.exists():
            self.load_config(config_path)

    def center_atlas(self):
        """Centra el atlas en la ventana"""
        # Calcular escala para que el atlas quepa en la ventana
        scale_x = (self.width * 0.8) / self.atlas_texture.width
        scale_y = (self.height * 0.8) / self.atlas_texture.height
        self.zoom = min(scale_x, scale_y, 1.0)  # No agrandar más que el tamaño original
        
        # Centrar
        self.pan_x = self.width // 2
        self.pan_y = self.height // 2

    def world_to_screen(self, x, y):
        """Convierte coordenadas del atlas a coordenadas de pantalla"""
        # El atlas se dibuja centrado en (pan_x, pan_y)
        atlas_center_x = self.pan_x
        atlas_center_y = self.pan_y
        
        # Posición en pantalla
        screen_x = atlas_center_x + (x - self.atlas_texture.width/2) * self.zoom
        screen_y = atlas_center_y + (y - self.atlas_texture.height/2) * self.zoom
        
        return screen_x, screen_y

    def screen_to_world(self, screen_x, screen_y):
        """Convierte coordenadas de pantalla a coordenadas del atlas"""
        atlas_center_x = self.pan_x
        atlas_center_y = self.pan_y
        
        # Posición en el atlas
        x = (screen_x - atlas_center_x) / self.zoom + self.atlas_texture.width/2
        y = (screen_y - atlas_center_y) / self.zoom + self.atlas_texture.height/2
        
        return x, y

    def on_draw(self):
        self.clear()
        arcade.set_background_color(arcade.color.DARK_GRAY)
        
        # Dibujar atlas
        atlas_width = self.atlas_texture.width * self.zoom
        atlas_height = self.atlas_texture.height * self.zoom
        
        arcade.draw_texture_rect(
            self.atlas_texture,
            rect=arcade.XYWH(self.pan_x, self.pan_y, atlas_width, atlas_height),
            pixelated=True
        )
        
        # Dibujar rectángulos guardados
        for layer_name, rects in self.layers.items():
            color = self.layer_colors[layer_name]
            for rect in rects:
                x, y, w, h = rect
                screen_x, screen_y = self.world_to_screen(x, y)
                arcade.draw_lbwh_rectangle_outline(
                    screen_x,
                    screen_y,
                    w * self.zoom,
                    h * self.zoom,
                    color,
                    2
                )
        
        # Dibujar rectángulo actual (mientras se selecciona)
        if self.selecting and self.current_rect:
            x, y, w, h = self.current_rect
            screen_x, screen_y = self.world_to_screen(x, y)
            color = self.layer_colors[self.current_layer]
            arcade.draw_lbwh_rectangle_outline(
                screen_x,
                screen_y,
                w * self.zoom,
                h * self.zoom,
                color,
                3
            )
        
        # Dibujar UI
        self.draw_ui()

    def draw_ui(self):
        """Dibuja la interfaz de usuario"""
        y_pos = self.height - 30
        
        # Instrucciones
        instructions = [
            "CONTROLES:",
            "1-5: Cambiar capa (Base, Manos, Ojos, Bocas, Brillo)",
            "Click y arrastra: Seleccionar área",
            "Z: Deshacer último rectángulo",
            "C: Limpiar capa actual",
            "S: Guardar configuración",
            "Rueda del mouse: Zoom",
            "Click derecho y arrastra: Mover vista"
        ]
        
        for instruction in instructions:
            arcade.draw_text(instruction, 10, y_pos, arcade.color.WHITE, 12)
            y_pos -= 20
        
        # Estado actual
        arcade.draw_text(f"Capa actual: {self.current_layer.upper()}", 
                        10, 50, self.layer_colors[self.current_layer], 16)
        
        arcade.draw_text(f"Zoom: {self.zoom:.2f}", 10, 30, arcade.color.WHITE, 12)
        
        # Contador de sprites por capa
        arcade.draw_text(f"Sprites en {self.current_layer}: {len(self.layers[self.current_layer])}", 
                        10, 10, arcade.color.WHITE, 12)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.selecting = True
            self.start_x, self.start_y = self.screen_to_world(x, y)
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            # Inicio de paneo
            self.pan_start_x = x - self.pan_x
            self.pan_start_y = y - self.pan_y

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT and self.selecting:
            self.selecting = False
            end_x, end_y = self.screen_to_world(x, y)
            
            # Calcular rectángulo
            min_x = min(self.start_x, end_x)
            min_y = min(self.start_y, end_y)
            width = abs(end_x - self.start_x)
            height = abs(end_y - self.start_y)
            
            # Solo agregar si el rectángulo tiene tamaño mínimo
            if width > 5 and height > 5:
                # Asegurar que esté dentro del atlas
                min_x = max(0, min(min_x, self.atlas_texture.width))
                min_y = max(0, min(min_y, self.atlas_texture.height))
                width = min(width, self.atlas_texture.width - min_x)
                height = min(height, self.atlas_texture.height - min_y)
                
                rect = [int(min_x), int(min_y), int(width), int(height)]
                self.layers[self.current_layer].append(rect)
            
            self.current_rect = None

    def on_mouse_motion(self, x, y, dx, dy):
        if self.selecting:
            end_x, end_y = self.screen_to_world(x, y)
            
            # Actualizar rectángulo actual
            min_x = min(self.start_x, end_x)
            min_y = min(self.start_y, end_y)
            width = abs(end_x - self.start_x)
            height = abs(end_y - self.start_y)
            
            self.current_rect = [min_x, min_y, width, height]

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons == arcade.MOUSE_BUTTON_RIGHT:
            # Paneo
            self.pan_x = x - self.pan_start_x
            self.pan_y = y - self.pan_start_y

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        # Zoom
        old_zoom = self.zoom
        zoom_factor = 1.1 if scroll_y > 0 else 1/1.1
        self.zoom *= zoom_factor
        self.zoom = max(0.1, min(5.0, self.zoom))  # Limitar zoom
        
        # Ajustar paneo para hacer zoom hacia el cursor
        zoom_change = self.zoom / old_zoom
        self.pan_x = x + (self.pan_x - x) * zoom_change
        self.pan_y = y + (self.pan_y - y) * zoom_change

    def on_key_press(self, key, modifiers):
        # Cambio de capas
        if key == arcade.key.KEY_1:
            self.current_layer = "base"
        elif key == arcade.key.KEY_2:
            self.current_layer = "hands"
        elif key == arcade.key.KEY_3:
            self.current_layer = "eyes"
        elif key == arcade.key.KEY_4:
            self.current_layer = "mouths"
        elif key == arcade.key.KEY_5:
            self.current_layer = "glow"
        
        # Acciones
        elif key == arcade.key.Z:  # Deshacer
            if self.layers[self.current_layer]:
                self.layers[self.current_layer].pop()
        
        elif key == arcade.key.C:  # Limpiar capa
            self.layers[self.current_layer].clear()
        
        elif key == arcade.key.S:  # Guardar
            self.save_config()
        
        elif key == arcade.key.R:  # Reset vista
            self.center_atlas()

    def save_config(self):
        """Guarda la configuración en un archivo JSON"""
        config = {
            "base": self.layers["base"],
            "hands": self.layers["hands"],
            "eyes": self.layers["eyes"],
            "mouths": self.layers["mouths"],
            "glow": self.layers["glow"],
            "offsets": self.offsets
        }
        
        config_path = self.atlas_path.with_suffix('.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        print(f"Configuración guardada en: {config_path}")
        print(f"Total de sprites: {sum(len(rects) for rects in self.layers.values())}")

    def load_config(self, config_path):
        """Carga una configuración existente"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            for layer in self.layers.keys():
                if layer in config:
                    self.layers[layer] = config[layer]
            
            if "offsets" in config:
                self.offsets.update(config["offsets"])
            
            print(f"Configuración cargada desde: {config_path}")
        except Exception as e:
            print(f"Error cargando configuración: {e}")


def main():
    """Función principal"""
    import sys
    
    if len(sys.argv) != 2:
        print("Uso: python atlas_editor.py <ruta_al_atlas.png>")
        print("Ejemplo: python atlas_editor.py assets/atlas.png")
        return
    
    atlas_path = sys.argv[1]
    
    try:
        editor = SpriteAtlasEditor(atlas_path)
        arcade.run()
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")


if __name__ == "__main__":
    main()