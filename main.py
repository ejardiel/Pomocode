import flet as ft
import time
import threading
import winsound
from plyer import notification
import json
import sys
import os

class BotonInformacion(ft.IconButton):
    def __init__(self, icono, size, click):
        super().__init__()
        self.icon = icono
        self.icon_size = size
        self.adaptive = True
        self.icon_color = ft.Colors.WHITE60
        self.icon_color=ft.Colors.CYAN_300
        self.on_click = click

def main(page: ft.Page):
    page.opacity = 0.3
    page.title = "Pomocode"
    page.window.center()  # Posicion en la pantalla
    page.window.width = 390  # Ancho de la ventana
    page.window.height = 520  # Altura de la ventana
    page.theme_mode = ft.ThemeMode.DARK  # Tema
    page.bgcolor = ft.Colors.BLACK26
    page.window.maximizable = False  # Quito la opcion de maximizar
    page.window.resizable = False  # Quito opcion de ajustar tamaño de la pantalla
    page.adaptive = True
    page.window.icon = os.path.abspath("assets/icon.ico")
    page.update()

    global corriendo, pausado, hilo_activo
    corriendo = True
    pausado = False
    hilo_activo = None

    def resource_path(relpath):
        if getattr(sys, "frozen", False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, relpath)

    ICON_PATH = resource_path(os.path.join("assets", "icon.ico"))
    IMAGE_PATH = resource_path(os.path.join("assets", "icon.png"))
    SOUND_PATH = resource_path(os.path.join("assets", "ding.wav"))

    CONFIG_DIR = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "Pomocode")
    os.makedirs(CONFIG_DIR, exist_ok=True)
    CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

    def mostrar_popup(page, mensaje):
        popup = ft.Container(
            content=ft.Text(mensaje, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.BLUE_GREY_900,
            alignment=ft.alignment.center
        )

        page.overlay.append(popup)
        page.update()

        def quitar_popup():
            import time
            time.sleep(5)
            page.overlay.remove(popup)
            page.update()

        threading.Thread(target=quitar_popup, daemon=True).start()
    def cargar_config():
        defaults = {
            "sonido": True,
            "notificacion": True,
            "tema": "oscuro",
            "tiempo_pomodoro": 25,
            "tiempo_descanso": 5,
            "tiempo_descanso_largo": 15,
            "cantidad_pomodoros": 0
        }
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print("Error leyendo config.json:", e)

        guardar_config(defaults)
        return defaults

    def guardar_config(config):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("No se pudo guardar config.json:", e)

    global config, cantidad_pomodoro
    config = cargar_config()
    cantidad_pomodoro = config["cantidad_pomodoros"]

    def cambiar_sonido(e):
        config["sonido"] = sonido.value
        try:
            guardar_config(config)
        except Exception as ex:
            print("Error guardando sonido:", ex)

    def cambiar_notificacion(e):
        config["notificacion"] = notificacion.value
        try:
            guardar_config(config)
        except Exception as ex:
            print("Error guardando notificacion:", ex)

    def cambiar_tiempo_json(e, key, value):
        config[key] = value
        try:
            guardar_config(config)
        except Exception as ex:
            print("Error guardando tiempo:", ex)

    def iniciar_pomodoro(e):
        global corriendo, pausado, hilo_activo, config

        if hilo_activo and hilo_activo.is_alive():
            global pausado
            pausado = False
            return
        corriendo = True
        pausado = False

        cambiar_tiempo_json(e,"tiempo_pomodoro",int(tiempo_pomodoro.value))
        cambiar_tiempo_json(e,"tiempo_descanso", int(tiempo_break.value))
        cambiar_tiempo_json(e,"tiempo_descanso_largo", int(tiempo_long_break.value))
        def contar_tiempo():
            global corriendo, pausado, config, cantidad_pomodoro
            segundo = 5
            contador_short_break = 0
            descanso = tiempo_break.value

            while corriendo:
                while segundo>0 and corriendo:
                    if not pausado:
                        segundo -= 1
                        minutos_restantes = segundo // 60
                        segundos_restantes = segundo % 60
                        texto_timer.value = f"{minutos_restantes:02d}:{segundos_restantes:02d}"

                    page.update()
                    time.sleep(1)

                    if not corriendo:
                        break

                if segundo == 0:
                    if notificacion.value:
                        threading.Thread(
                            target=lambda: mostrar_popup(page, f"¡Pomodoro terminado! Descansa {descanso} min."),
                            daemon=True
                        ).start()
                    if sonido.value:
                        winsound.PlaySound(SOUND_PATH, winsound.SND_FILENAME)

                if contador_short_break < 3:
                    if segundo==0:
                        cantidad_pomodoro += 1
                    config["cantidad_pomodoros"] = cantidad_pomodoro
                    guardar_config(config)
                    segundo = int(tiempo_break.value)*60
                    descanso = int(tiempo_break.value)
                    contador_short_break += 1
                else:
                    if segundo == 0:
                        cantidad_pomodoro += 1
                    config["cantidad_pomodoros"] = cantidad_pomodoro
                    guardar_config(config)
                    segundo = int(tiempo_long_break.value)*60
                    descanso = tiempo_long_break.value
                    contador_short_break = 0

        hilo_activo = threading.Thread(target=contar_tiempo)
        hilo_activo.start()

    def detener_pomodoro(e):
        global pausado
        pausado = True

    def reiniciar_pomodoro(e):
        global corriendo, pausado
        if pausado:
            pausado = False
            corriendo = False
            texto_timer.value = f"{tiempo_pomodoro.value}:00"
            page.update()

    sonido = ft.Switch(
        active_color=ft.Colors.GREEN_600,
        value=config["sonido"],
        on_change=cambiar_sonido,
        adaptive=True
    )

    notificacion = ft.Switch(
        active_color=ft.Colors.GREEN_600,
        value=config["notificacion"],
        on_change=cambiar_notificacion,
        adaptive=True
    )
    texto_pomocoder = ft.Text(
        value="Pomocode",
        weight=ft.FontWeight.BOLD,
        font_family="Fira Code",
        size=45,
    )

    def clicktime(e):
        texto_timer.value = (f"{e.control.value}:00"f"")
        page.update()

    tiempo_pomodoro = ft.Dropdown(
        width=100,
        value="25",
        options=[
            ft.DropdownOption("25"),
            ft.DropdownOption("45"),
            ft.DropdownOption("60"),
        ],
        menu_width=30,
        border_color=ft.Colors.TRANSPARENT,
        on_change=clicktime)

    tiempo_break = ft.Dropdown(
        width=100,
        value="5",
        options=[
            ft.DropdownOption("5"),
            ft.DropdownOption("10"),
            ft.DropdownOption("15"),
        ],
        menu_width=30,
        border_color=ft.Colors.TRANSPARENT)

    tiempo_long_break = ft.Dropdown(
        width=100,
        value="15",
        options=[
            ft.DropdownOption("15"),
            ft.DropdownOption("20"),
            ft.DropdownOption("25"),
        ],
        menu_width=30,
        border_color=ft.Colors.TRANSPARENT)

    texto_info = ft.Container(content=ft.Text(f"Trabajas {tiempo_pomodoro.value} minutos concentrado,"
                                                    f"luego descansas {tiempo_break.value} minutos. "
                                                    f"Después de 2 ciclos, tomas un descanso largo de {tiempo_long_break.value} minutos.",
                                              size=15,
                                              font_family="Fira Code",
                                              color=ft.Colors.WHITE,
                                              expand=True,
                                              text_align=ft.alignment.center),
                              bgcolor=ft.Colors.BLACK12,
                              alignment=ft.alignment.center
                              )

    texto_registrada = ft.Container(content=ft.Text(value="\u00AE MJOLNIX",
                                                    size=12,
                                                    color=ft.Colors.CYAN_300,
                                                    font_family="Fira Code",
                                                    text_align=ft.alignment.center,
                                                    opacity=0.5),
                                    expand=True,
                                    bgcolor=ft.Colors.BLACK,
                                    alignment=ft.alignment.center)

    boton_play = BotonInformacion(ft.Icons.PLAY_CIRCLE_OUTLINE_OUTLINED, 40, iniciar_pomodoro)
    boton_pause = BotonInformacion(ft.Icons.PAUSE_CIRCLE_OUTLINE_OUTLINED, 40, detener_pomodoro)
    boton_refresh = BotonInformacion(ft.Icons.REFRESH_OUTLINED,40, reiniciar_pomodoro)

    boton_info = ft.PopupMenuButton(
        icon_size=20,
        icon=ft.Icons.INFO_OUTLINE,
        icon_color=ft.Colors.CYAN_300,
        menu_position=ft.PopupMenuPosition.OVER,
        bgcolor=ft.Colors.BLACK,
        items=[
            ft.PopupMenuItem(content=ft.Row(controls=[ft.Text(value="> information();",
                                                              size=15,
                                                              weight=ft.FontWeight.BOLD,
                                                              color=ft.Colors.GREEN_600,
                                                              font_family="Fira Code",)])),
            ft.PopupMenuItem(content=texto_info),
            ft.PopupMenuItem(content=ft.Container(content=texto_registrada,
                                                  margin=ft.margin.only(top=20)),
                             )
                                             ],
        )
    boton_config = ft.PopupMenuButton(
        icon_size=20,
        icon=ft.Icons.SETTINGS,
        bgcolor=ft.Colors.BLACK,
        icon_color=ft.Colors.CYAN_300,
        menu_position=ft.PopupMenuPosition.OVER,
        items=[
            ft.PopupMenuItem(content=ft.Row(controls=[ft.Text(value="> settings();",
                                                              size=15,
                                                              weight=ft.FontWeight.BOLD,
                                                              color=ft.Colors.GREEN_600,
                                                              font_family="Fira Code")])),
            ft.PopupMenuItem(content=ft.Row(controls=[
                                            ft.Text(value="Pomodoro",
                                                    expand=3,
                                                    font_family="Fira Code"),
                                            tiempo_pomodoro],)),
            ft.PopupMenuItem(content= ft.Row(controls=[
                                            ft.Text(value="Short Break",
                                                    expand=3,
                                                    font_family="Fira Code"),
                                            tiempo_break])),
            ft.PopupMenuItem(content=ft.Row(controls=[
                                            ft.Text(value="Long Break",
                                                    expand=3,
                                                    font_family="Fira Code"),
                                            tiempo_long_break])),
            ft.PopupMenuItem(content=ft.Container(content=ft.Row(controls=[ft.Text(value="Sound",
                                                                        expand=3,
                                                                        font_family="Fira Code"),
                                                                        sonido]),
                                                         margin=ft.margin.only(top=15))),
            ft.PopupMenuItem(content=ft.Container(content=ft.Row(controls=[ft.Text(value="Notification",
                                                                                   expand=3,
                                                                                   font_family="Fira Code"),
                                                                           notificacion]),
                                                  margin=ft.margin.only(top=10))),
            ft.PopupMenuItem(content=ft.Container(content=ft.Column(controls=[ft.Text(value="> productivity_log();",
                                                                                      size=15,
                                                                                      weight=ft.FontWeight.BOLD,
                                                                                      color=ft.Colors.GREEN_600,
                                                                                      font_family="Fira Code",
                                                                                      expand=True),
                                                                              ft.Text(value= f"Haz completado {config["cantidad_pomodoros"]} pomodoros",
                                                                                      size=15,
                                                                                      font_family="Fira Code")],),
                                                  margin=ft.margin.only(top=10),
                                                  padding=ft.padding.only(top=10),
                                                  border=ft.Border(top=ft.BorderSide(0.5, ft.Colors.WHITE)),
                                                  width=280))
                            ])


    texto_focus = ft.Text(value="> focusmode();",
                          size=20,
                          weight=ft.FontWeight.BOLD,
                          color=ft.Colors.GREEN_600,
                          font_family="Fira Code",
                          opacity=0.6)
    texto_timer = ft.Text(value="25:00",
                          size=70,
                          weight=ft.FontWeight.BOLD,
                          font_family="Fira Code")

    container = ft.Container(
        content= ft.Column(
            controls=[
                ft.Row(controls=[texto_pomocoder]),
                ft.Row(controls=[texto_focus]),
                ft.Container(content=texto_timer,
                             width=400,
                             alignment=ft.alignment.center,
                             padding=ft.padding.only(top=10,bottom=10)),
                ft.Container(content=ft.Row(controls=[boton_play,boton_pause,boton_refresh],
                                            alignment=ft.alignment.center),
                             margin=ft.margin.only(left=50, bottom=20,top = 10, right=50)),
                ft.Container(content=ft.Row(controls=[ft.Container(content=boton_info,
                                                                   expand=True),
                                                      ft.Container(content=boton_config,
                                                                   expand=True)],
                                            alignment=ft.alignment.center_right),
                             margin=ft.margin.only(left=50, top=5, right=50))
            ],
        )
        ,
        padding= ft.padding.only(left=20, top=20, right=20, bottom=50),
        bgcolor=ft.Colors.BLACK26,
        width=500,
        height=430,
        border_radius = ft.border_radius.all(10),
        border=ft.border.all(2, ft.Colors.WHITE70),
        margin=ft.margin.only(top=5,bottom=10,left=20,right=20),
    )

    page.add(container)
    page.update()
ft.app(target=main)