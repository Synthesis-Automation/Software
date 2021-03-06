# coding:utf-8
import json
import time
import socket
import threading
import logging
import random
import os
from pathlib import Path

import tkinter as tk
from tkinter import ttk
from tkinter import Menu, Canvas, PhotoImage, Toplevel, filedialog, scrolledtext, messagebox, simpledialog
from tkinter.ttk import Notebook, Separator, Label, Button

from combinewave.robot import robot
from combinewave.chemical_synthesis import synthesis
from combinewave.tools import custom_widgets, helper
# CAPPER = 'Z3'...
from combinewave.parameters import CAPPER, LIQUID, TABLET, VERSION, SYSTEM_NAME, NEW_PLAN_HEADER


class Main(tk.Tk):
    def __init__(self):
        super().__init__()
        self.iconbitmap(self, default=Path("./images/flash.ico"))
        self.title(SYSTEM_NAME)

        # Main menu
        self.menu = Menu(self, bg="lightgrey", fg="black")

        self.file_menu = Menu(self.menu, tearoff=0)
        self.file_menu.add_command(label="Open reagent index",
                                   command=lambda: self.synthesis_tab.open_reagent_index())
        self.file_menu.add_separator()
        self.file_menu.add_command(label="New synthesis plan",
                                   command=lambda: self.synthesis_tab.new_plan())
        self.file_menu.add_command(label="Open synthesis plan",
                                   command=lambda: self.synthesis_tab.open_plan())
        self.file_menu.add_command(label="Save synthesis plan",
                                   command=lambda: self.synthesis_tab.save_plan())
        self.file_menu.add_command(label="Save synthesis plan as new file",
                                   command=lambda: self.synthesis_tab.save_as_plan())
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Open synthesis plan as excel file",
                                   command=lambda: self.synthesis_tab.open_plan_excel(),
                                   accelerator="Ctrl+L")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.exit_gui)
        self.menu.add_cascade(label="File ", menu=self.file_menu)

        self.log_menu = Menu(self.menu, tearoff=0)
        self.log_menu.add_command(
            label="Open log book", command=lambda: self.open_log_book())
        self.log_menu.add_separator()
        self.log_menu.add_command(
            label="Empty log book", command=lambda: self.empty_log_book())
        self.menu.add_cascade(label="Log-book ", menu=self.log_menu)

        self.home_menu = Menu(self.menu, tearoff=0)
        self.home_menu.add_command(label="Home all axes",
                                   command=lambda: chem_robot.home_all())
        self.home_menu.add_command(label="Home Z axes only",
                                   command=lambda: chem_robot.home_all_z())
        self.menu.add_cascade(label="Home-robot ", menu=self.home_menu)

        self.reset_menu = Menu(self.menu, tearoff=0)
        self.reset_menu.add_command(
            label="Reset pipette", command=lambda: chem_robot.pipette.initialization())
        self.reset_menu.add_command(
            label="Reset gripper", command=lambda: chem_robot.gripper.initialization())
        self.menu.add_cascade(label="Reset  ", menu=self.reset_menu)

        self.calibration_menu = Menu(self.menu, tearoff=0)
        self.calibration_menu.add_command(
            label="Plate Calibration", command=lambda: self.plate_calibration())
        self.calibration_menu.add_command(
            label="Tip Calibration", command=lambda: self.tip_calibration())
        self.calibration_menu.add_command(
            label="Reference Point Calibration", command=lambda: self.reference_calibration())
        self.menu.add_cascade(label="Calibration ", menu=self.calibration_menu)

        self.Manual_control_menu = Menu(self.menu, tearoff=0)
        self.Manual_control_menu.add_command(
            label="Manual control", command=lambda: self.manual_control())
        self.menu.add_cascade(label="Manual-Control  ",
                              menu=self.Manual_control_menu)

        self.reagent_distrubution_menu = Menu(self.menu, tearoff=0)
        self.reagent_distrubution_menu.add_command(
            label="Liquid reagent distribution ", command=lambda: self.solvent_distrubution())
        self.menu.add_cascade(
            label="Reagents ", menu=self.reagent_distrubution_menu)

        self.cap_operation_menu = Menu(self.menu, tearoff=0)
        self.cap_operation_menu.add_command(
            label="Cap reactors", command=lambda: self.cap_reactor())
        self.cap_operation_menu.add_command(
            label="Decap reactors", command=lambda: self.decap_reactor())
        self.menu.add_cascade(label="Capper ", menu=self.cap_operation_menu)

        helpmenu = Menu(self.menu, tearoff=0)
        helpmenu.add_command(label="About", command=lambda: self.about())
        self.menu.add_cascade(label="Help", menu=helpmenu)
        tk.Tk.config(self, menu=self.menu)
        # End of main menu

        # Notebook tab
        self.notebook = Notebook(self, style='lefttab.TNotebook')

        connect_tab = Connect_tab(self.notebook)
        self.connect_img = PhotoImage(file=Path("./images/connect_t.png"))
        self.notebook.add(connect_tab, text="Connect\n",
                          image=self.connect_img, compound=tk.TOP)

        self.deck_tab = Deck_tab(self.notebook)
        self.deck_img = PhotoImage(file=Path("./images/deck_t.png"))
        self.notebook.add(self.deck_tab, text="Deck Setup\n",
                          image=self.deck_img, compound=tk.TOP)

        self.tip_tab = Tip_tab(self.notebook)
        self.tip_img = PhotoImage(
            file=Path("./images/tips.png"))
        self.notebook.add(
            self.tip_tab, text="Tip Selection\n", image=self.tip_img, compound=tk.TOP)

        self.synthesis_tab = Synthesis_tab(
            self.notebook, tip_selection=self.tip_tab)
        self.synthesis_img = PhotoImage(file=Path("./images/synthesis_t.png"))
        self.notebook.add(self.synthesis_tab, text="Synthesis\n",
                          image=self.synthesis_img, compound=tk.TOP)

        self.monitor_tab = Monitor_tab(
            self.notebook, tip_selection=self.tip_tab)
        self.monitor_img = PhotoImage(file=Path("./images/monitor.png"))
        self.notebook.add(self.monitor_tab, text="Reaction Monitor\n",
                          image=self.monitor_img, compound=tk.TOP)

        self.workup_tab = Workup_tab(self.notebook, tip_selection=self.tip_tab)
        self.workup_img = PhotoImage(file=Path("./images/workup.png"))
        self.notebook.add(self.workup_tab, text="Reaction Workup\n",
                          image=self.workup_img, compound=tk.TOP)

        self.notebook.bind("<ButtonRelease-1>", self.update_tip_by_tab_clicked)
        self.notebook.pack(fill=tk.BOTH, expand=1)
        # End of Notebook tab setup

        # Save tip position before exit main program
        self.protocol("WM_DELETE_WINDOW", self.exit_gui)

    def about(self):
        messagebox.showinfo(" ", SYSTEM_NAME + " " + VERSION)

    def solvent_distrubution(self):
        popup = Reagent_distrubution(tip_selection=self.tip_tab.tip_selector)
        self.wait_window(popup.popup_window)

    def manual_control(self):
        popup = Manual_control(tip_selector=self.tip_tab.tip_selector)
        self.wait_window(popup.popup_window)

    def cap_reactor(self):
        popup = Cap_operation(option="Cap reactors")
        self.wait_window(popup.popup_window)

    def decap_reactor(self):
        popup = Cap_operation(option="Decap reactors")
        self.wait_window(popup.popup_window)

    def plate_calibration(self):
        popup = Plate_calibration()
        self.wait_window(popup.popup_window)

    def tip_calibration(self):
        popup = Tip_calibration()
        self.wait_window(popup.popup_window)

    def reference_calibration(self):
        popup = Reference_calibration()
        self.wait_window(popup.popup_window)

    def update_tip_by_tab_clicked(self, event=None):
        # Make sure that all tip selection have the same current tip number
        self.synthesis_tab.reactor_update()
        self.workup_tab.reactor_update()
        self.monitor_tab.reactor_update()

    def open_log_book(self):
        os.startfile(".\myapp.log")

    def empty_log_book(self):
        yes = messagebox.askyesno(
            "Info", "Are you sure to empty log book?")
        if yes:
            with open(".\myapp.log", 'w'):
                pass
        else:
            return

    def exit_gui(self):
        self.tip_tab.save()
        self.destroy()


class Connect_tab(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

        Label(self, text=" ").pack()
        Label(self, text="Wellcome to\n" + SYSTEM_NAME,
              style="Title.Label").pack(pady=10)
        canvas = Canvas(self, width=800, height=400)
        canvas.pack(pady=10)
        self.img = PhotoImage(file="./images/flash.png")
        canvas.create_image(1, 1, anchor=tk.NW, image=self.img)
        self.connect_btn = Button(self, text="Connect and home robot", style="Green.TButton",
                                  command=lambda: self.run_thread())
        self.connect_btn.pack(pady=20)
        self.status = tk.Label(
            self, text="Robot Status: Not connected", fg="red", width=50)
        self.status.pack(side=tk.BOTTOM,  fill=tk.X)

    def connect(self):
        try:
            if not chem_robot.ready:
                if not chem_robot.is_connected:
                    chem_robot.connect()
                    chem_robot.home_all_z()
                    chem_robot.is_connected = True
                yes = messagebox.askyesno(
                    "Info", "Make sure it is safe to home robot, proceed?")
                if not yes:
                    return False
                chem_robot.home_xy()
                chem_robot.pipette.initialization()
                chem_robot.gripper.initialization()
                chem_robot.ready = True
            self.status.configure(text="Robot Status: Ready",
                                  fg="green")
            self.connect_btn["state"] = "disabled"
        except Exception:
            messagebox.showinfo(
                " ", "Connection failed, please check USB connection and try again.")

    def run_thread(self):
        t = threading.Thread(target=self.connect)
        t.start()


class Deck_tab(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        Label(self, text="Deck Setup", style="Title.Label").grid(
            column=0, row=0, padx=50, pady=10, columnspan=4)
        self.slot_list = chem_robot.deck.get_slot_list()
        self.btn_list = []
        self.config = []
        i = 0
        for plate_sn in chem_robot.deck.deck_config.values():
            slot = self.slot_list[i]
            plate_type = plate_sn["plate"].split(':')[0]
            plate_no = plate_sn["plate"].split(':')[1]
            assignment = chem_robot.deck.deck_config[slot]["assignment"]
            self.config.append({"slot": slot, "plate_type": plate_type,
                                "plate_no": plate_no, "assignment": assignment})
            i = i+1
        COLS = 5
        ROWS = 3
        i = 0
        self.deck_frame = tk.LabelFrame(
            self, text="  Deck  ", fg="RoyalBlue4", font="Helvetica 11 bold")
        self.deck_frame.grid(column=0, columnspan=5, row=10,
                             padx=20, pady=10, sticky=tk.W)
        for row in range(ROWS):
            for col in range(COLS):
                slot = self.config[i]["slot"]
                plate_type = self.config[i]["plate_type"]
                plate_no = self.config[i]["plate_no"]
                assignment = self.config[i]["assignment"]
                text = f"{slot}\n{plate_type} : {plate_no}\n{assignment}"
                def action(x=i): return self.slot_assignment(x)
                btn = Button(
                    self.deck_frame, text=text, style="Plate.TButton", command=action)
                if assignment in ["Tips 50uL", "Tips 1000uL"]:
                    btn.configure(style="Plate_r.TButton")
                if assignment in ["Reactor", "Trash", "Clean up"]:
                    btn["state"] = "disabled"
                btn.grid(row=row+2, column=col, pady=15, padx=10)
                self.btn_list.append(btn)
                i = i+1

        # reactor selection
        if "reactor_12p" in chem_robot.deck.deck_config["C3"]["plate"]:
            reactor_id = 0
        else:
            reactor_id = 1
        self.reactor_frame = tk.LabelFrame(
            self, text=" Select Reactor ", fg="RoyalBlue4", font="Helvetica 11 bold")
        self.reactor_frame.grid(column=0, columnspan=5, row=20,
                                padx=20, pady=20, sticky=tk.W)
        reactor_option = ["8 mL -12 position", "15 mL -27 position"]
        self.reactor_selection = tk.IntVar(None, len(reactor_option)-1)
        for i in range(len(reactor_option)):
            ttk.Radiobutton(self.reactor_frame,
                            text=reactor_option[i],
                            variable=self.reactor_selection,
                            value=i,
                            command=lambda: self.save_reactor(),
                            ).grid(column=i, row=50, padx=20, pady=2, sticky=tk.W)
        self.reactor_selection.set(reactor_id)
        canvas1 = Canvas(self.reactor_frame, width=200, height=200)
        canvas1.grid(column=0, row=60, sticky=tk.W)
        self.img1 = PhotoImage(file="./images/P12.png")
        canvas1.create_image(1, 1, anchor=tk.NW, image=self.img1)
        canvas2 = Canvas(self.reactor_frame, width=200, height=200)
        canvas2.grid(column=1, row=60, sticky=tk.W)
        self.img2 = PhotoImage(file="./images/P24.png")
        canvas2.create_image(1, 1, anchor=tk.NW, image=self.img2)

    def save_reactor(self):
        reactor_id = self.reactor_selection.get()
        reactor_slot = "C3"
        reactor_list = ["reactor_12p:001", "reactor_27p:001"]
        chem_robot.deck.deck_config[reactor_slot] = {
            "plate": reactor_list[reactor_id], "assignment": "Reactor"}
        chem_robot.deck.save_deck_config(chem_robot.deck.deck_config)
        chem_robot.deck.reset_current_reactor()

    def slot_assignment(self, x):
        popup = Slot_assignment(self.config[x])
        self.wait_window(popup.t)
        self.config = []
        i = 0
        for plate_sn in chem_robot.deck.deck_config.values():
            slot = self.slot_list[i]
            plate_type = plate_sn["plate"].split(':')[0]
            plate_no = plate_sn["plate"].split(':')[1]
            assignment = chem_robot.deck.deck_config[slot]["assignment"]
            self.config.append({"slot": slot, "plate_type": plate_type,
                                "plate_no": plate_no, "assignment": assignment})
            i = i+1
        slot = self.config[x]["slot"]
        plate_type = self.config[x]["plate_type"]
        plate_no = self.config[x]["plate_no"]
        assignmnent = self.config[x]["assignment"]
        text = f"{slot}\n{plate_type} : {plate_no}\n{assignmnent}"
        self.btn_list[x].configure(text=text)


class Slot_assignment():
    def __init__(self, slot):
        self.t = Toplevel()
        self.slots = slot
        self.t.title(slot["slot"])
        Label(self.t, text="Plate type").grid(column=0, row=0, padx=10, pady=5)
        Label(self.t, text="Plate serial No.").grid(
            column=1, row=0, padx=10, pady=5)

        self.plate_type = ttk.Combobox(self.t, width=15, state="readonly")
        plate_type_turple = ("not_used", "plate_2mL", "plate_5mL", "plate_10mL", "plate_50mL",
                             "tiprack_1000uL", "tiprack_50uL", "workup_big", "workup_small", "caps")
        self.plate_type["values"] = plate_type_turple
        current = plate_type_turple.index(slot["plate_type"])
        self.plate_type.current(current)  # set the selected item
        self.plate_type.grid(column=0, row=2, padx=10, pady=5)

        self.plate_serial = ttk.Combobox(self.t, state="readonly")
        plate_serial_turple = ("001", "002", "003", "004", "005", "006", "007",
                               "008", "009", "010")
        self.plate_serial["values"] = plate_serial_turple
        current = plate_serial_turple.index(slot["plate_no"])
        self.plate_serial.current(current)
        self.plate_serial.grid(column=1, row=2, padx=10, pady=5)

        save_btn = Button(self.t, text="Save", command=lambda: self.save())
        save_btn.grid(row=3, column=0, pady=20, padx=20)
        cancel_btn = Button(self.t, text="Cancel",
                            command=lambda: self.cancel())
        cancel_btn.grid(row=3, column=1, pady=20, padx=20)
        save_btn.focus_force()
        self.t.grab_set()  # keep this pop window focused

    def save(self):
        plate_type = self.plate_type.get()
        plate_no = self.plate_serial.get()
        plate_name = plate_type + ":" + plate_no
        assignment_dict = {
            "plate_5mL": "Reagent",
            "plate_10mL": "Reagent",
            "plate_15mL": "Reactor",
            "plate_50mL": "Reagent",
            "tiprack_1000uL": "Tips 1000uL",
            "tiprack_50uL": "Tips 50uL",
            "workup_big": "Workup",
            "workup_small": "Workup",
            "caps": "Reaction caps",
            "not_used": "Not_used",
            "plate_2mL": "GC LC"
        }
        assignment = assignment_dict[plate_type]
        slot = self.slots["slot"]
        chem_robot.deck.deck_config[slot] = {
            "plate": plate_name, "assignment": assignment}
        chem_robot.deck.save_deck_config(chem_robot.deck.deck_config)
        self.t.destroy()

    def cancel(self):
        self.t.destroy()


class Tip_tab(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        Label(self, text="Tip Selection", style="Title.Label").grid(
            column=0, row=0, padx=50, pady=10, columnspan=2)

        # Tip selector
        self.tip_frame = tk.Frame(self)
        self.tip_frame.grid(column=0, row=11, padx=20, sticky=tk.W)
        Label(self.tip_frame, text="Select current tip (1000 uL)",
              style="Default.Label").grid(row=0, pady=5)

        # show picture of tip rack
        canvas = Canvas(self.tip_frame, width=220, height=200)
        canvas.grid(column=0, row=1, padx=10, pady=10)
        self.img = PhotoImage(file="./images/tips_rack.png")
        canvas.create_image(1, 1, anchor=tk.NW, image=self.img)

        slot_list = chem_robot.deck.get_vial_list_by_plate_type(
            plate_type="tiprack_1000uL")
        col_row = chem_robot.deck.get_cols_rows_by_plate_type(
            plate_type="tiprack_1000uL")
        self.tip_selection_frame = tk.Frame(
            self.tip_frame, relief="ridge", bg="gray")
        self.tip_selection_frame.grid(row=2)
        self.current_tip = chem_robot.deck.get_current_tip()
        self.tip_selector = custom_widgets.Item_selection_on_screen(
            parent=self.tip_selection_frame, slot_list=slot_list, COLS=col_row["columns"], ROWS=col_row["rows"], current=self.current_tip)

        # Tip selector (samll tip)
        self.tip_frame_s = tk.Frame(self)
        self.tip_frame_s.grid(column=1, row=11, padx=20, sticky=tk.W)
        Label(self.tip_frame_s, text="Select current tip (50 uL)",
              style="Default.Label").grid(row=0, pady=5)

        canvas_s = Canvas(self.tip_frame_s, width=220, height=200)
        canvas_s.grid(column=0, row=1, padx=10, pady=10)
        self.img_small = PhotoImage(file="./images/tips_rack_small.png")
        canvas_s.create_image(1, 1, anchor=tk.NW, image=self.img_small)

        self.tip_selection_frame_small = tk.Frame(
            self.tip_frame_s, relief="ridge", bg="LemonChiffon4")
        self.tip_selection_frame_small.grid(row=2)
        self.current_tip_small = 0  # chem_robot.deck.get_current_tip()
        self.tip_selector_small = custom_widgets.Item_selection_on_screen(
            parent=self.tip_selection_frame_small, slot_list=slot_list, COLS=col_row["columns"], ROWS=col_row["rows"], current=self.current_tip_small)

    def save(self):
        chem_robot.deck.set_current_tip(self.tip_selector.get_current())
        chem_robot.deck.save_current_tip()

    def get_current(self, *args, **kwargs):
        return self.tip_selector.get_current(*args, **kwargs)

    def next(self, *args, **kwargs):
        self.tip_selector.next(*args, **kwargs)

    def highlight_current(self, *args, **kwargs):
        self.tip_selector.highlight_current(*args, **kwargs)


class Synthesis_tab(ttk.Frame):

    def __init__(self, parent, tip_selection=None):
        ttk.Frame.__init__(self, parent)
        self.tip_selection = tip_selection

        Label(self, text=" Reaction Setup ", style="Title.Label").grid(
            column=0, columnspan=4, row=0, padx=20, pady=5)

        ip_address = socket.gethostbyname(socket.gethostname())
        Label(self, text="Enter your reaction protocol below, you may also upload your protocol via IP address: " +
              ip_address, style="Default.Label").grid(column=0, columnspan=4, row=1, padx=15, pady=5, sticky=tk.W)

        # Reaction plan editor
        self.plan_box = scrolledtext.ScrolledText(self, width=150, height=14)
        self.plan_box.grid(column=0, rowspan=4, padx=15, columnspan=4, row=3)
        self.display_plan(NEW_PLAN_HEADER)
        self.is_excel = False
        self.plan_file_name = r".\user_files\temp.txt"

        # Additional solvent option
        self.solvent_frame = tk.Frame(self)
        self.solvent_frame.grid(column=0, row=11, sticky=tk.N)
        Label(self.solvent_frame, text=" ").grid(row=0, sticky=tk.W)
        self.solvent_addition_last = tk.IntVar()
        ttk.Checkbutton(self.solvent_frame, text="Add the below liquids at last",
                        variable=self.solvent_addition_last).grid(row=2, sticky=tk.W)
        self.reactor_no_capping = tk.IntVar()
        ttk.Checkbutton(self.solvent_frame, text="Not cap the reactor",
                        variable=self.reactor_no_capping).grid(row=1, sticky=tk.W)
        Label(self.solvent_frame, text=" ").grid(row=3, sticky=tk.W)

        Label(self.solvent_frame, style="Default.Label",
              text="Liquid name: ").grid(row=5, column=0, sticky=tk.E)
        self.solvent_selection = ttk.Combobox(
            self.solvent_frame, width=15)
        self.solvent_selection["values"] = (
            "", "Water", "DCM", "MeOH", "Ethyl-acetate", "Hexanes", "Toluene", "THF", "DCE", "Dioxane", "Acetone")
        self.solvent_selection.current(0)  # set the selected item
        self.solvent_selection.grid(row=5, column=1, pady=5, sticky=tk.W)
        Label(self.solvent_frame, style="Default.Label",
              text="Amount (mL): ").grid(row=6, column=0, sticky=tk.E)
        self.volume_entry = ttk.Entry(self.solvent_frame, width=17)
        self.volume_entry.grid(row=6, column=1, pady=2, sticky=tk.W)

        Label(self.solvent_frame, text=" ").grid(row=7, sticky=tk.W)

        Label(self.solvent_frame, style="Default.Label",
              text="Liquid name: ").grid(row=5+3, column=0, sticky=tk.E)
        self.solvent_selection_2 = ttk.Combobox(
            self.solvent_frame, width=15)
        self.solvent_selection_2["values"] = (
            "", "Water", "DCM", "MeOH", "Ethyl-acetate", "Hexanes", "Toluene", "THF", "DCE", "Dioxane", "Acetone")
        self.solvent_selection_2.current(0)  # set the selected item
        self.solvent_selection_2.grid(row=5+3, column=1, pady=5, sticky=tk.W)
        Label(self.solvent_frame, style="Default.Label",
              text="Amount (mL): ").grid(row=6+3, column=0, sticky=tk.E)
        self.volume_entry_2 = ttk.Entry(self.solvent_frame, width=17)
        self.volume_entry_2.grid(row=6+3, column=1, pady=2, sticky=tk.W)

        # Reactor selection
        self.reactor_selection_frame = tk.Frame(
            self, width=300, height=260)
        self.reactor_selection_frame.grid(column=1, row=11)
        self.current_reactor = chem_robot.deck.get_current_reactor()
        self.reactor_selection = custom_widgets.Reactor_on_screen(
            parent=self.reactor_selection_frame, reactor_type=self.current_reactor, current=0)

        # Cap selector
        self.cap_frame = tk.Frame(self)
        self.cap_frame.grid(column=2, row=11, sticky=tk.N)
        tk.Label(self.cap_frame, text="Current Cap\n",
                 fg="RoyalBlue4", font="Helvetica 11 bold").grid(row=0)
        slot_list = chem_robot.deck.get_vial_list_by_plate_type(
            plate_type="caps")
        col_row = chem_robot.deck.get_cols_rows_by_plate_type(
            plate_type="caps")
        self.cap_selection_frame = tk.Frame(
            self.cap_frame, relief="ridge", bg="gray")
        self.cap_selection_frame.grid(row=1, sticky=tk.S)
        self.cap_selection = custom_widgets.Item_selection_on_screen(
            parent=self.cap_selection_frame, slot_list=slot_list, COLS=col_row["columns"], ROWS=col_row["rows"], current=0)

        # Display information
        self.display_frame = tk.Frame(self)
        self.display_frame.grid(column=0, rowspan=6, columnspan=4,
                                row=20, padx=15, pady=10)
        self.information = custom_widgets.Information_display(
            self.display_frame, title="Parsed reaction protocol will be shown here:\n", width=150, height=12)

        # Parse, run and stop buttons
        self.parse_button = Button(
            self, text="Parse reaction protocol", style="Green.TButton", command=lambda: self.parse())
        self.parse_button.grid(column=1, row=30, pady=10)
        self.run_button = Button(
            self, text="Setup reactions", style="Green.TButton", command=lambda: self.run_thread())
        self.run_button.grid(column=2, row=30, pady=10)
        self.stop_button = Button(
            self, text="Stop running", style="Red.TButton", command=lambda: self.stop_reaction())
        self.stop_button.grid(column=3, row=30, pady=10)
        self.run_button["state"] = "disabled"

    def reactor_update(self):
        current_reactor = chem_robot.deck.get_current_reactor()
        if current_reactor != self.current_reactor:
            self.reactor_selection_frame.destroy()
            self.reactor_selection_frame = tk.Frame(
                self, width=300, height=260)
            self.reactor_selection_frame.grid(column=1, row=11)
            self.reactor_selection = custom_widgets.Reactor_on_screen(
                parent=self.reactor_selection_frame, reactor_type=current_reactor,  current=0)
            self.current_reactor = current_reactor

    def setup(self, tip=0, simulation=False):
        if not chem_robot.ready:
            simulation = True
        self.run_button["state"] = "disabled"
        if not simulation:
            chem_robot.pipette.initialization()
        reactor_no_cap = self.reactor_no_capping.get()
        solvent_last = self.solvent_addition_last.get()
        if solvent_last == 1:
            last_reagents = []
            solvent_volume_string = self.volume_entry.get()
            solvent_name = self.solvent_selection.get()
            if solvent_name == "":
                messagebox.showinfo(" ", "Please enter a valid solvent name!")
                return
            if not helper.is_float(solvent_volume_string):
                messagebox.showinfo(" ", "Please enter solvent volume in mL!")
                return
            solvent_volume = float(solvent_volume_string)
            solvent_info = chem_synthesis.locate_reagent(solvent_name)
            if "not found" in solvent_info:
                messagebox.showinfo(" ", solvent_info)
                return
            else:
                plate_name = solvent_info["plate"]
                position = solvent_info["vial"]
                reagent_type = solvent_info["type"]
            last_reagents.append({"name": solvent_name, "plate": plate_name, "position": position, "type": reagent_type,"amount": solvent_volume})    

            solvent_volume_string = self.volume_entry_2.get()
            solvent_name = self.solvent_selection_2.get()
            if solvent_name != "" and helper.is_float(solvent_volume_string):
                solvent_volume = float(solvent_volume_string)
                solvent_info = chem_synthesis.locate_reagent(solvent_name)
                if "not found" in solvent_info:
                    messagebox.showinfo(" ", solvent_info)
                    return
                else:
                    plate_name = solvent_info["plate"]
                    position = solvent_info["vial"]
                    reagent_type = solvent_info["type"]
                last_reagents.append({"name": solvent_name, "plate": plate_name, "position": position, "type": reagent_type,"amount": solvent_volume})    
            print(last_reagents)    

        ok = messagebox.askokcancel(
            "Warning", f"Please make sure:\n 1) Reactor vials are uncapped.\n 2) Enough caps are put on cap plate (from A1). \n 3) All reagent vials are secured in the plate.")
        if not ok:
            return
        missing = chem_robot.deck.check_missing_assignment(required_plates=[
                                                           "Reagent", "Reactor", "Tips 1000uL", "Trash", "Clean up", "Reaction caps"])
        if missing != "complete":
            retry = messagebox.askyesno(
                "Warning", f"Warning: No {missing} plate is assigned, continue?.")
            if not retry:
                return
        chem_robot.set_stop_flag(stop=False)
        if simulation:
            self.information.display_msg(
                "Robot not ready, run in the simulation mode:\n")
            time.sleep(1)
        else:
            self.information.display_msg("Starting running...")
        tip_no = self.tip_selection.get_current(format="A1")
        tip_plate = chem_robot.deck.get_plate_assignment("Tips 1000uL")

        cap_no = self.cap_selection.get_current(format="A1")
        cap_plate = chem_robot.deck.get_plate_assignment("Reaction caps")
        # A1 foramt
        reactor_no = self.reactor_selection.get_current(format="A1")
        reactor_plate = chem_robot.deck.get_plate_assignment("Reactor")
        reactor_no_start = reactor_no
        # 1,2 format
        reactor_start_number = self.reactor_selection.get_current()

        trash_plate = chem_robot.deck.get_plate_assignment("Trash")
        trash = (trash_plate, 'A1')
        clean_up_plate = chem_robot.deck.get_plate_assignment("Clean up")
        with open(Path("user_files/reactions.json")) as rxn_data:
            reactions = json.load(rxn_data)
        i = 1
        number_of_reaction = len(reactions)
        for reaction in reactions:  # each entry is a reaction as dict
            if self.check_pause() == "stop":
                return ("stopped by user")
            tracking_number = reaction["tracking_number"]
            output_msg = f"\nSetup reaction No. {i} of {number_of_reaction}, (tracking number: {tracking_number})"
            self.information.display_msg(output_msg, start_over=False)
            i = i+1
            reactor_vial = (reactor_plate, reactor_no)
            reagent_list = reaction["reagents"]
            for reagent in reagent_list:
                if self.check_pause() == "stop":
                    return ("stopped by user")
                reagent_type = reagent["type"]
                reagent_name = reagent["name"]
                reagent_plate = chem_robot.deck.get_slot_from_plate_name(
                    reagent["plate"])
                reagent_location = reagent["position"]
                reagent_vial = (reagent_plate, reagent_location)
                reagent_amount = reagent["amount"]
                output_msg = f'Transfer {reagent_name} ({reagent_type}) from vial@ ({reagent_plate}, {reagent_location}), amount: {reagent_amount} (mL or tablet) to reactor@ {reactor_no} ...'
                self.information.display_msg(output_msg, start_over=False)
                if not simulation:
                    if reagent_type == "pure_liquid" or reagent_type == "solution":
                        if self.check_pause() == "stop":
                            return ("stopped by user")
                        tip = (tip_plate, tip_no)
                        while not chem_robot.decap(reagent_vial):
                            retry = messagebox.askyesno(
                                "Infomation", "Cap can't be opened, retry?")
                            if not retry:
                                return
                        is_volatile = reagent["is_volatile"]
                        chem_robot.transfer_liquid(vial_from=reagent_vial, vial_to=reactor_vial,
                                                   tip=tip, trash=trash, volume=reagent_amount, is_volatile=is_volatile)
                        chem_robot.recap(reagent_vial)
                        # move to the next tip
                        self.tip_selection.next()
                        tip_no = self.tip_selection.get_current(format="A1")

                    if reagent_type == "solid":
                        if self.check_pause() == "stop":
                            return ("stopped by user")
                        while not chem_robot.decap(reagent_vial):
                            retry = messagebox.askyesno(
                                "Infomation", "Cap can't be opened, retry?")
                            if not retry:
                                return
                        chem_robot.transfer_tablet(vial_from=reagent_vial, vial_to=reactor_vial,
                                                   number_of_tablet=reagent_amount)
                        if self.check_pause() == "stop":
                            return ("stopped by user")
                        chem_robot.recap(reagent_vial)
                        if self.check_pause() == "stop":
                            return ("stopped by user")

                        clean_up_position = chem_robot.deck.convert_number_to_A1(
                            random.randint(1, 600), plate=clean_up_plate)
                        chem_robot.clean_up_needle(
                            (clean_up_plate, clean_up_position))
                        if self.check_pause() == "stop":
                            return ("stopped by user")
                else:
                    time.sleep(1)
                    if reagent_type == "pure_liquid" or reagent_type == "solution":
                        # change to next tip
                        self.tip_selection.next()
                        tip_no = self.tip_selection.get_current(format="A1")

            if self.check_pause() == "stop":
                return ("stopped by user")

            # skip capping if reactor No cap box is checked
            if not simulation and reactor_no_cap == 0 and solvent_last == 0:
                chem_robot.pickup_cap((cap_plate, cap_no))
                self.cap_selection.next()
                if self.check_pause() == "stop":
                    return ("stopped by user")
                cap_no = chem_robot.deck.next_vial(cap_no, plate=cap_plate)
                chem_robot.recap(reactor_vial)
                if self.check_pause() == "stop":
                    return ("stopped by user")
            reactor_no = chem_robot.deck.next_vial(
                reactor_no, plate=reactor_plate)
            self.reactor_selection.next()

        # Add the solvent in the last step
        if solvent_last == 1:
            for reagent in last_reagents:
                if reagent["type"] != "solid":
                    solvent_slot = chem_robot.deck.get_slot_from_plate_name(reagent["plate"])
                    solvent_vial = (solvent_slot, reagent["position"])
                    volume = reagent["amount"]
                    reagent_name = reagent["name"]
                    tip_no = self.tip_selection.get_current(format="A1")
                    tip = (tip_plate, tip_no)
                    if not simulation:
                        chem_robot.pickup_tip(tip)
                    if not simulation:
                        chem_robot.decap(solvent_vial)
                    if self.check_pause() == "stop":
                        return ("stopped by user")

                    # adding last solvent/reagents
                    self.information.display_msg(
                        "\nAdding the last solvent/reagent...\n", start_over=False)
                    self.reactor_selection.un_highlight_current()
                    reactor_no = reactor_no_start
                    self.reactor_selection.set_current(reactor_start_number)
                    self.reactor_selection.highlight_current()
                    i = 0
                    for i in range(number_of_reaction):
                        reactor_vial = (reactor_plate, reactor_no)
                        if self.check_pause() == "stop":
                            return ("stopped by user")
                        message = f"Run {i+1} of {number_of_reaction}, adding {reagent_name} {volume} mL to reactor at {reactor_vial[1]} using tip {tip[1]}"
                        self.information.display_msg(message, start_over=False)
                        if not simulation:
                            chem_robot.transfer_liquid(vial_from=solvent_vial, vial_to=reactor_vial,
                                                    tip=None, trash=trash, volume=solvent_volume)
                        else:
                            time.sleep(0.5)
                        reactor_no = chem_robot.deck.next_vial(
                            reactor_no, plate=reactor_plate)
                        self.reactor_selection.next()
                    if self.check_pause() == "stop":
                        return ("stopped by user")
                    if not simulation:
                        chem_robot.drop_tip(trash)
                    if self.check_pause() == "stop":
                        return ("stopped by user")
                    if not simulation:
                        chem_robot.recap(solvent_vial)
                    self.tip_selection.next()

            # adding cap
            if reactor_no_cap == 0:
                self.reactor_selection.un_highlight_current()
                self.information.display_msg(
                    "\nSetup reaction competed, starting to add cap\n", start_over=False)
                reactor_no = reactor_no_start
                self.reactor_selection.set_current(reactor_start_number)
                self.reactor_selection.highlight_current()
                i = 0
                for i in range(number_of_reaction):
                    reactor_vial = (reactor_plate, reactor_no)
                    if self.check_pause() == "stop":
                        return ("stopped by user")
                    message = f"Run {i+1} of {number_of_reaction}, adding cap to reactor at {reactor_vial[1]}"
                    self.information.display_msg(message, start_over=False)
                    if not simulation:
                        chem_robot.pickup_cap((cap_plate, cap_no))
                        self.cap_selection.next()
                    if not simulation:
                        chem_robot.recap(reactor_vial)

                    cap_no = chem_robot.deck.next_vial(cap_no, plate=cap_plate)
                    reactor_no = chem_robot.deck.next_vial(
                        reactor_no, plate=reactor_plate)
                    self.reactor_selection.next()

        self.run_button["state"] = "normal"
        self.update()
        self.information.display_msg(
            "\nFinished....................................................\n", start_over=False)
        self.tip_selection.save()
        self.run_button["state"] = "enabled"

    def run_thread(self):
        if chem_synthesis.ready:
            t = threading.Thread(target=self.setup)
            t.start()
        else:
            self.information.display_msg("Please load your reaction protocol.")

    def stop_reaction(self):
        chem_robot.set_stop_flag(stop=True)
        self.information.display_msg("Stopping......\n", start_over=False)

    def clean_up_after_stop(self):
        chem_robot.home_all_z()
        chem_robot.pipette.initialization()
        chem_robot.gripper.initialization()
        chem_robot.set_stop_flag(stop=False)

    def display_plan(self, msg):
        self.plan_box.delete(1.0, tk.END)
        self.plan_box.insert(tk.INSERT, msg)
        self.plan_box.see("end")
        self.update()

    def open_reagent_index(self):
        filename = filedialog.askopenfilename(title="Select protocol file", filetypes=(
            ("excel file", "*.xlsx"), ("all files", "*.*")))
        if filename:
            chem_synthesis.load_reagent_index(filename)

    def open_plan(self):
        filename = filedialog.askopenfilename(title="Select protocol file", filetypes=(
            ("txt files", "*.txt"), ("all files", "*.*")))
        plan = open(filename, "r")
        string = plan.read()
        self.display_plan(string)
        chem_synthesis.ready = True
        # self.run_button["state"] = "normal"
        self.update()
        self.plan_file_name = filename
        self.is_excel = False

    def new_plan(self):
        filename = filedialog.asksaveasfilename(title="Name your plan file", filetypes=(
            ("txt files", "*.txt"), ("all files", "*.*")))
        if filename == "":
            return
        self.plan_file_name = filename + '.txt'
        self.display_plan(NEW_PLAN_HEADER)
        chem_synthesis.ready = True
        # self.run_button["state"] = "normal"
        self.update()
        self.is_excel = False

    def save_plan(self):
        self.parse()

    def save_as_plan(self):
        filename = filedialog.asksaveasfilename(title="Name your plan file", filetypes=(
            ("txt files", "*.txt"), ("all files", "*.*")))
        if filename == "":
            return
        self.plan_file_name = filename + '.txt'
        chem_synthesis.ready = True
        # self.run_button["state"] = "normal"
        self.update()
        self.is_excel = False
        self.save_plan()

    def open_plan_excel(self):
        filename = filedialog.askopenfilename(title="Select protocol file", filetypes=(
            ("excel file", "*.xlsx"), ("all files", "*.*")))
        self.display_plan("Plan excel loaded")
        chem_synthesis.ready = True
        # self.run_button["state"] = "normal"
        self.update()
        self.plan_file_name = filename
        self.is_excel = True

    def parse(self):
        if not self.is_excel:
            self.plan_txt = self.plan_box.get("1.0", tk.END)
            # print(self.plan_txt)
            with open(self.plan_file_name, 'w') as output:
                output.write(self.plan_txt)
            # reactor_No = self.combo_reactor.get()
            res = chem_synthesis.load_synthesis_plan(self.plan_file_name)
            if "not found" in res:
                messagebox.showinfo(" ", res)
                return
            # save_file_name = self.plan_file_name.split('.')[0] + '_run.txt'
            # chem_synthesis.save_plan(
            #     save_file=save_file_name, reactor_starting_nubmer=1)
            with open(Path("user_files/reactions.json"), 'r') as output:
                parsed_plan = output.read()
            self.information.display_msg(parsed_plan)
            chem_synthesis.ready = True
            self.run_button["state"] = "enabled"
        else:
            res = chem_synthesis.load_synthesis_plan_excel(self.plan_file_name)
            if "not found" in res:
                messagebox.showinfo(" ", res)
                return
            # save_file_name = self.plan_file_name.split('.')[0] + '_run.txt'
            # chem_synthesis.save_plan(
            #     save_file=save_file_name, reactor_starting_nubmer=1)
            with open(Path("user_files/reactions.json"), 'r') as output:
                parsed_plan = output.read()
            self.information.display_msg(parsed_plan)
            chem_synthesis.ready = True
            self.run_button["state"] = "enabled"

    def check_pause(self):
        if chem_robot.stop_flag:
            res = custom_widgets.pause()
            chem_robot.set_stop_flag(stop=False)
            return res
        else:
            chem_robot.set_stop_flag(stop=False)
            return "continue"


class Monitor_tab(ttk.Frame):
    def __init__(self, parent, tip_selection=None):
        ttk.Frame.__init__(self, parent)
        self.tip_selection = tip_selection
        # Title
        Label(self, text=" Reaction Monitor ", style="Title.Label").grid(
            column=0, columnspan=4, row=0, padx=20, pady=5)

        # Reactor selection
        self.reactor_selection_frame = tk.Frame(
            self, width=300, height=260)
        self.reactor_selection_frame.grid(column=0, row=11, rowspan=2)
        self.current_reactor = chem_robot.deck.get_current_reactor()
        self.reactor_selection = custom_widgets.Reactor_on_screen(
            parent=self.reactor_selection_frame, reactor_type=self.current_reactor,  current=0)

        # show picture of arrow
        canvas = Canvas(self, width=150, height=100)
        canvas.grid(column=1, row=11, rowspan=2, padx=10, pady=10)
        self.img = PhotoImage(file="./images/right.png")
        canvas.create_image(1, 1, anchor=tk.NW, image=self.img)

        # GC-LC vial selector
        tk.Label(self, text="Current GC/LC vial", fg="RoyalBlue4",
                 font="Helvetica 11 bold").grid(column=2, row=11, padx=5)
        self.GC_LC_frame = tk.Frame(self, relief="ridge", bg="gray")
        self.GC_LC_frame.grid(column=2, row=12, sticky=tk.N)
        slot_list = chem_robot.deck.get_vial_list_by_plate_type(
            plate_type="plate_2mL")
        col_row = chem_robot.deck.get_cols_rows_by_plate_type(
            plate_type="plate_2mL")
        self.GC_LC_selection = custom_widgets.Item_selection_on_screen(
            parent=self.GC_LC_frame, slot_list=slot_list, COLS=col_row["columns"], ROWS=col_row["rows"], current=0)

        # Number of reactions selection
        self.number_frame = tk.LabelFrame(
            self, text="Number of reactions", fg="RoyalBlue4", font="Helvetica 11 bold")
        self.number_frame.grid(column=0, row=15, padx=15, pady=5, sticky=tk.NW)
        self.number_reaction = ttk.Combobox(
            self.number_frame, state="readonly", font=('Helvetica', '11'))
        self.number_reaction["values"] = (
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
        self.number_reaction.current(0)  # set the selected item
        self.number_reaction.grid(pady=5)

        # Sampling volume selector
        options = [{"text": "2 uL", "value": 2.0},
                   {"text": "5 uL", "value": 5.0},
                   {"text": "10 uL", "value": 10.0}
                   ]
        self.sampling_volume_frame = tk.Frame(self, relief="ridge", bg="gray")
        self.sampling_volume_frame.grid(
            column=0, row=16, padx=15, pady=5, sticky=tk.NW)
        self.sampling_volume_selection = custom_widgets.Volume_selection(
            parent=self.sampling_volume_frame, title="Sampling volume (uL)", options=options)

        # Solvent type selection
        self.solvent_frame = tk.LabelFrame(
            self, text="Solvent for dilution", fg="RoyalBlue4", font="Helvetica 11 bold")
        self.solvent_frame.grid(column=1, row=15, pady=5, sticky=tk.NW)
        self.solvent_selection = ttk.Combobox(
            self.solvent_frame, font=('Helvetica', '11'))
        self.solvent_selection["values"] = (
            "DCM", "MeOH", "Ethyl-acetate", "Hexanes")
        self.solvent_selection.current(0)  # set the selected item
        self.solvent_selection.grid(pady=5)

        # Dilution solvent volume selection
        options = [{"text": "0.3 mL", "value": 0.3},
                   {"text": "0.6 mL", "value": 0.6},
                   {"text": "1.0 mL", "value": 1.0}
                   ]
        self.dilution_volume_frame = tk.Frame(self, relief="ridge", bg="gray")
        self.dilution_volume_frame.grid(column=1, row=16, pady=5, sticky=tk.NW)
        self.dilution_volume_selection = custom_widgets.Volume_selection(
            parent=self.dilution_volume_frame, title="Dilution solvent volume (mL)", options=options)

        # Display information
        self.display_frame = tk.Frame(self)
        self.display_frame.grid(column=0, rowspan=6, columnspan=4,
                                row=50, padx=15, pady=10)
        self.information = custom_widgets.Information_display(
            self.display_frame, title="Progress:", width=150, height=12)

        # Run and stop buttons
        self.run_button = Button(
            self, text="Start sampling", style="Green.TButton", command=lambda: self.run())
        self.run_button.grid(column=0, row=60, padx=10, pady=10)
        self.stop_button = Button(
            self, text="Stop running", style="Red.TButton", command=lambda: self.stop())
        self.stop_button.grid(column=1, row=60, padx=10, pady=10)

    def monitor_reaction(self, simulation=False):
        chem_robot.set_stop_flag(stop=False)

        if not chem_robot.ready:
            simulation = True
            self.information.display_msg(
                "Robot not ready, run in the simulation mode:\n")
            time.sleep(1)
        else:
            self.information.display_msg("Start sampling...\n")

        tip_no = self.tip_selection.get_current(format="A1")
        tip_plate = chem_robot.deck.get_plate_assignment("Tips 1000uL")

        reactor_no = self.reactor_selection.get_current(format="A1")
        reactor_plate = chem_robot.deck.get_plate_assignment("Reactor")

        trash_plate = chem_robot.deck.get_plate_assignment("Trash")
        trash = (trash_plate, 'A1')

        GC_LC_plate = chem_robot.deck.get_plate_assignment("GC LC")
        GC_LC_no = self.GC_LC_selection.get_current(format="A1")

        GC_LC_start_number = self.GC_LC_selection.get_current()
        GC_LC_no_start = GC_LC_no

        number_of_reaction = int(self.number_reaction.get())

        solvent_name = self.solvent_selection.get()
        solvent_info = chem_synthesis.locate_reagent(solvent_name)
        if "not found" in solvent_info:
            messagebox.showinfo(" ", solvent_info)
            return
        else:
            solvent_plate_name = solvent_info["plate"]
            solvent_pos = solvent_info["vial"]
        solvent_slot = chem_robot.deck.get_slot_from_plate_name(
            solvent_plate_name)
        solvent_vial = (solvent_slot, solvent_pos)

        # sampling each reactor to GC-LC vials
        for i in range(number_of_reaction):
            if chem_robot.stop_flag:
                return ("stopped by user")

            reactor_vial = (reactor_plate, reactor_no)
            reactor_no = chem_robot.deck.next_vial(
                reactor_no, plate=reactor_plate)
            self.reactor_selection.next()

            GC_LC_vial = (GC_LC_plate, GC_LC_no)
            GC_LC_no = chem_robot.deck.next_vial(GC_LC_no, plate=GC_LC_plate)
            self.GC_LC_selection.next()

            tip = (tip_plate, tip_no)

            sample_volume = self.sampling_volume_selection.get_value()/1000  # uL convert to mL
            dilution_volume = self.dilution_volume_selection.get_value()  # in mL already

            message = f"Run {i+1} of {number_of_reaction}, sampling {sample_volume} mL from reactor {reactor_vial[1]} to GC/LC vial at {GC_LC_vial[1]} using tip {tip[1]}"
            self.information.display_msg(message, start_over=False)

            if simulation:
                time.sleep(1)  # run in the simulation mode
            else:
                if chem_robot.stop_flag:
                    return ("stopped by user")
                chem_robot.decap(reactor_vial)
                if chem_robot.stop_flag:
                    return ("stopped by user")
                chem_robot.transfer_liquid(vial_from=reactor_vial, vial_to=GC_LC_vial,
                                           tip=tip, trash=trash, volume=sample_volume)
                if chem_robot.stop_flag:
                    return ("stopped by user")
                chem_robot.recap(reactor_vial)
                if chem_robot.stop_flag:
                    return ("stopped by user")
            tip_no = chem_robot.deck.next_vial(tip_no, plate=tip_plate)
            self.tip_selection.next()
            chem_robot.deck.set_current_tip(self.tip_selection.get_current())

        if chem_robot.stop_flag:
            return ("stopped by user")

        # Add dilution solvent for each GC-LC vials
        tip = (tip_plate, tip_no)
        if not simulation:
            chem_robot.pickup_tip(tip)
        if not simulation:
            chem_robot.decap(solvent_vial)
        if chem_robot.stop_flag:
            return ("stopped by user")
        GC_LC_no = GC_LC_no_start
        self.GC_LC_selection.set_current(GC_LC_start_number)
        self.GC_LC_selection.highlight_current()

        self.information.display_msg(
            "\nSampling competed, starting to add dilution solvent\n", start_over=False)
        for i in range(number_of_reaction):
            GC_LC_vial = (GC_LC_plate, GC_LC_no)
            if chem_robot.stop_flag:
                return ("stopped by user")
            message = f"Run {i+1} of {number_of_reaction}, adding dilution solvent {solvent_name} {dilution_volume} mL to GC/LC vial at {GC_LC_vial[1]} using tip {tip[1]}"
            self.information.display_msg(message, start_over=False)
            if not simulation:
                chem_robot.transfer_liquid(vial_from=solvent_vial, vial_to=GC_LC_vial,
                                           tip=None, trash=trash, volume=dilution_volume)
            else:
                time.sleep(1)
            GC_LC_no = chem_robot.deck.next_vial(GC_LC_no, plate=GC_LC_plate)
            self.GC_LC_selection.next()

        if chem_robot.stop_flag:
            return ("stopped by user")
        if not simulation:
            chem_robot.drop_tip(trash)
        if chem_robot.stop_flag:
            return ("stopped by user")
        if not simulation:
            chem_robot.recap(solvent_vial)
        self.tip_selection.next()
        chem_robot.deck.set_current_tip(self.tip_selection.get_current())
        self.information.display_msg(
            "\nFinished....................................................\n", start_over=False)
        chem_robot.deck.save_current_tip()

    def run(self):
        self.run_button["state"] = "disabled"
        self.update()
        t = threading.Thread(target=self.monitor_reaction)
        t.start()
        self.run_button["state"] = "enabled"
        self.update()

    def stop(self):
        chem_robot.set_stop_flag(stop=True)
        self.information.display_msg("Stopping......\n", start_over=False)
        self.run_button["state"] = "normal"
        self.update()
        chem_robot.home_all_z()

    def reactor_update(self):
        current_reactor = chem_robot.deck.get_current_reactor()
        if current_reactor != self.current_reactor:
            self.reactor_selection_frame.destroy()
            self.reactor_selection_frame = tk.Frame(
                self, width=300, height=260)
            self.reactor_selection_frame.grid(column=0, row=11, rowspan=2)
            self.reactor_selection = custom_widgets.Reactor_on_screen(
                parent=self.reactor_selection_frame, reactor_type=current_reactor,  current=0)
            self.current_reactor = current_reactor


class Workup_tab(ttk.Frame):
    def __init__(self, parent, tip_selection=None):
        ttk.Frame.__init__(self, parent)
        self.tip_selection = tip_selection
        Label(self, text="Reaction Workup", style="Title.Label").grid(
            column=0, columnspan=4, row=0, pady=20)

        # Reactor selection
        self.reactor_selection_frame = tk.Frame(
            self, width=300, height=260)
        self.reactor_selection_frame.grid(column=1, row=11, rowspan=2)
        self.current_reactor = chem_robot.deck.get_current_reactor()
        self.reactor_selection = custom_widgets.Reactor_on_screen(
            parent=self.reactor_selection_frame, reactor_type=self.current_reactor,  current=0)

        # Workup cartridge selector
        tk.Label(self, text="Current workup cartridge", fg="RoyalBlue4",
                 font="Helvetica 11 bold").grid(column=3, row=11, padx=5, sticky=tk.N)
        self.workup_frame = tk.Frame(self, relief="ridge", bg="gray")
        self.workup_frame.grid(column=3, row=12, sticky=tk.N)
        slot_list = chem_robot.deck.get_vial_list_by_plate_type(
            plate_type="workup_small")
        col_row = chem_robot.deck.get_cols_rows_by_plate_type(
            plate_type="workup_small")
        self.workup_selection = custom_widgets.Item_selection_on_screen(
            parent=self.workup_frame, slot_list=slot_list, COLS=col_row["columns"], ROWS=col_row["rows"], current=0)

        # Number of reactions selector
        self.number_frame = tk.LabelFrame(
            self, text="Number of reactions", fg="RoyalBlue4", font="Helvetica 11 bold")
        self.number_frame.grid(column=0, row=11, padx=50,
                               pady=10, sticky=tk.NW)
        self.number_reaction = ttk.Combobox(
            self.number_frame, state="readonly", font=('Helvetica', '11'))
        self.number_reaction["values"] = (
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
        self.number_reaction.current(0)  # set the selected item
        self.number_reaction.grid(pady=5)

        # Reaction volume selector
        options = [{"text": "0.5 mL", "value": 0.5},
                   {"text": "1.0 mL", "value": 1.0},
                   {"text": "2.0 mL", "value": 2.0}
                   ]
        self.reaction_volume_frame = tk.Frame(self, relief="ridge", bg="gray")
        self.reaction_volume_frame.grid(
            column=0, row=12, padx=50, pady=10, sticky=tk.NW)
        self.reaction_volume_selection = custom_widgets.Volume_selection(
            parent=self.reaction_volume_frame, title="Reaction volume (mL)", options=options)

        # show picture of arrow
        canvas = Canvas(self, width=150, height=100)
        canvas.grid(column=2, row=11, rowspan=2, padx=10, pady=10)
        self.img = PhotoImage(file="./images/right.png")
        canvas.create_image(1, 1, anchor=tk.NW, image=self.img)

        # Display of information
        self.display_frame = tk.Frame(self, relief="ridge", bg="gray")
        self.display_frame.grid(column=0, rowspan=6, columnspan=4,
                                row=50, padx=15, pady=10)
        self.information = custom_widgets.Information_display(
            self.display_frame, title="Progress of operation:", width=150, height=20)

        # Run, pause and stop buttons
        self.run_button = Button(
            self, text="Start work-up", style="Green.TButton", command=lambda: self.run())
        self.run_button.grid(column=0, row=60, padx=10, pady=10)

        self.stop_button = Button(
            self, text="Stop / Pause", style="Red.TButton", command=lambda: self.stop())
        self.stop_button.grid(column=1, row=60, padx=10, pady=10)

    def workup_reaction(self, simulation=False):
        '''main entry for workup'''
        missing = chem_robot.deck.check_missing_assignment(required_plates=["Reagent", "Reactor", "Workup",
                                                                            "Tips 1000uL", "Trash", "Reaction caps"])
        if missing != "complete":
            retry = messagebox.askyesno(
                "Warning", f"Warning: No {missing} plate is assigned, continue?.")
            if not retry:
                return

        chem_robot.set_stop_flag(stop=False)
        if not chem_robot.ready:
            simulation = True
            self.information.display_msg(
                "Robot not ready, run in the simulation mode:\n")
            time.sleep(1)
        else:
            self.information.display_msg("Start work-up...\n")

        tip_no = self.tip_selection.get_current(format="A1")
        tip_plate = chem_robot.deck.get_plate_assignment("Tips 1000uL")
        reactor_no = self.reactor_selection.get_current(format="A1")
        reactor_plate = chem_robot.deck.get_plate_assignment("Reactor")
        trash_plate = chem_robot.deck.get_plate_assignment("Trash")
        trash = (trash_plate, 'A1')
        workup_cartridge_plate = chem_robot.deck.get_plate_assignment("Workup")
        workup_cartridge_no = self.workup_selection.get_current(format="A1")
        number_of_reaction = int(self.number_reaction.get())

        available_tip = len(chem_robot.deck.get_vial_list_by_plate_type(
            "tiprack_1000uL"))-self.tip_selection.get_current()
        available_reactor = len(chem_robot.deck.get_vial_list_by_plate_type(
            self.current_reactor))-self.reactor_selection.get_current()
        available_workup_cartridge = len(chem_robot.deck.get_vial_list_by_plate_type(
            "workup_small"))-self.workup_selection.get_current()
        if available_tip < number_of_reaction:
            messagebox.showinfo(
                " ", "Warning: No enough tip, please refill tips from A1")
        if available_reactor < number_of_reaction:
            messagebox.showinfo(" ", "Warning: No enough reactor!")
            return
        if available_workup_cartridge < number_of_reaction:
            messagebox.showinfo(" ", "Warning: No enough reactor!")
            return

        for i in range(number_of_reaction):
            if self.check_stop_status() == "stop":
                return
            tip = (tip_plate, tip_no)
            reactor = (reactor_plate, reactor_no)
            workup_cartridge = (workup_cartridge_plate, workup_cartridge_no)

            reaction_volume = self.reaction_volume_selection.get_value()
            message = f"Run {i+1} of {number_of_reaction}, transfer {reaction_volume} mL reaction mixture from reactor@ {reactor[1]} to workup cartridge@ {workup_cartridge_no} using tip@ {tip[1]}"
            self.information.display_msg(message, start_over=False)
            if simulation:
                time.sleep(1)  # run in the simulation mode
            else:
                if self.check_stop_status() == "stop":
                    return
                chem_robot.decap(reactor)
                if self.check_stop_status() == "stop":
                    return
                chem_robot.transfer_liquid(vial_from=reactor, vial_to=workup_cartridge,
                                           tip=tip, trash=trash, volume=reaction_volume)
                if self.check_stop_status() == "stop":
                    return
                chem_robot.recap(reactor)
                if self.check_stop_status() == "stop":
                    return

            # Move to next item (tip, reactor...)
            reactor_no = chem_robot.deck.next_vial(
                reactor_no, plate=reactor_plate)
            workup_cartridge_no = chem_robot.deck.next_vial(
                workup_cartridge_no, plate=workup_cartridge_plate)
            tip_no = chem_robot.deck.next_vial(tip_no, plate=tip_plate)
            self.tip_selection.next()
            chem_robot.deck.set_current_tip(self.tip_selection.get_current())
            self.reactor_selection.next()
            self.workup_selection.next()

        self.information.display_msg(
            "\nFinished....................................................\n", start_over=False)
        chem_robot.deck.save_current_tip()

    def run(self):
        self.run_button["state"] = "disabled"
        self.update()
        t = threading.Thread(target=self.workup_reaction)
        t.start()
        self.run_button["state"] = "enabled"
        self.update()

    def stop(self):
        chem_robot.set_stop_flag(stop=True)
        self.information.display_msg("\nStopping......\n", start_over=False)
        self.run_button["state"] = "normal"
        self.update()

    def check_stop_status(self):
        if chem_robot.stop_flag:
            yes = tk.messagebox.askyesno(
                "Warning", "Are you sure want to stop?")
            if yes:
                return "stop"
            else:
                chem_robot.set_stop_flag(False)
                return "continue"

    def reactor_update(self):
        current_reactor = chem_robot.deck.get_current_reactor()
        if current_reactor != self.current_reactor:
            self.reactor_selection_frame.destroy()
            self.reactor_selection_frame = tk.Frame(
                self, width=300, height=260)
            self.reactor_selection_frame.grid(column=1, row=11, rowspan=2)
            self.reactor_selection = custom_widgets.Reactor_on_screen(
                parent=self.reactor_selection_frame, reactor_type=current_reactor,  current=0)
            self.current_reactor = current_reactor


# Plate Calibration, accessed from menu - calibration
class Plate_calibration(ttk.Frame):
    def __init__(self):
        self.popup_window = Toplevel()
        self.popup_window.title("Plate Calibration ")

        # Slot selector
        self.current_slot = 5
        self.slot_frame = tk.Frame(
            self.popup_window, relief="ridge", bg="gray")
        self.slot_frame.grid(column=1, row=0, padx=10, pady=10, rowspan=3)
        slot_list = chem_robot.deck.get_vial_list_by_plate_type(
            plate_type="deck")
        self.slot_selection = custom_widgets.Item_selection_on_screen(
            parent=self.slot_frame, slot_list=slot_list, COLS=5, ROWS=3, current=self.current_slot)
        move_botton = Button(self.popup_window, text="Move to selected slot @", style="Default.TButton",
                             command=lambda: self.move_to_plate())
        move_botton.grid(column=1, row=5, pady=5)

        Label(self.popup_window, text=" ").grid(
            column=1, row=7, padx=10, pady=10)
        # Move functions as an LabelFrame
        self.move_frame = tk.LabelFrame(
            self.popup_window, text="Move axies (X, Y, Z1, Z2, Z3)", fg="RoyalBlue4", font="Helvetica 11 bold")
        self.move_frame.grid(column=0, columnspan=4, row=10,
                             padx=20, pady=10, sticky=tk.W)
        self.move_axies = custom_widgets.Move_axes(
            parent=self.move_frame, robot=chem_robot)

        # Save buttons
        Label(self.popup_window, text=" ").grid(
            column=1, row=16, padx=10, pady=10)
        self.button_save = Button(self.popup_window, text="Save calibration", style="Red.TButton",
                                  command=lambda: self.save_calibration_plate())
        self.button_save.grid(column=1, row=20, padx=0, pady=10)
        # Exit buttons
        self.button_exit = Button(self.popup_window, text="Exit", style="Default.TButton",
                                  command=lambda: self.exit())
        self.button_exit.grid(column=2, row=20, padx=0, pady=10)
        self.button_save.focus_force()
        self.popup_window.grab_set()  # keep this pop window focused

    def save_calibration_plate(self):
        x = chem_robot.get_axe_position("x")
        y = chem_robot.get_axe_position("y")
        current_head = self.move_axies.get_current_head()
        z = chem_robot.get_axe_position(current_head)
        plate_for_calibration = self.slot_selection.get_current(format="A1")
        coordinate_of_vial = chem_robot.deck.vial_coordinate(plate=plate_for_calibration,
                                                             vial='A1')
        calibration_data = [x-coordinate_of_vial['x']-chem_robot.deck.head_offsets[current_head][0],
                            y-coordinate_of_vial['y']-chem_robot.deck.head_offsets[current_head][1],
                            z-coordinate_of_vial['z']]
        chem_robot.deck.save_calibration(plate=plate_for_calibration,
                                         calibration_data=calibration_data)
        chem_robot.update()

    def exit(self):
        self.popup_window.destroy()

    def move_to_plate(self):
        slot = chem_robot.deck.get_vial_list_by_plate_type(
            plate_type="deck")[self.slot_selection.get_current()]
        vial_to = (slot, "A1")
        current_head = self.move_axies.get_current_head()
        chem_robot.move_to(head=current_head, vial=vial_to,
                           use_allow_list=False)


# Tip Calibration, accessed from menu - calibration
class Tip_calibration(ttk.Frame):
    def __init__(self):
        self.popup_window = Toplevel()
        self.popup_window.title("Tip Calibration ")

        # Slot selector
        move_botton = Button(self.popup_window, text="Move to tip rack @", style="Default.TButton",
                             command=lambda: self.move_to_tip_rack())
        move_botton.grid(column=1, row=0, padx=40, pady=5)
        # Label(self.popup_window, text=" ").grid(column=1, row=7, padx=10, pady=10)

        # Move functions as an LabelFrame
        self.move_frame = tk.LabelFrame(
            self.popup_window, text="Move axies (X, Y, Z1, Z2, Z3)", fg="RoyalBlue4", font="Helvetica 11 bold")
        self.move_frame.grid(column=0, columnspan=4, row=10,
                             padx=20, pady=10, sticky=tk.W)
        self.move_axies = custom_widgets.Move_axes(
            parent=self.move_frame, robot=chem_robot)

        # Save buttons
        Label(self.popup_window, text=" ").grid(
            column=1, row=16, padx=10, pady=10)
        self.button_save = Button(self.popup_window, text="Save calibration", style="Red.TButton",
                                  command=lambda: self.save_calibration_tip())
        self.button_save.grid(column=1, row=20, padx=0, pady=10)
        self.button_save.focus_force()
        self.popup_window.grab_set()  # keep this pop window focused

        # Cancel buttons
        self.button_exit = Button(self.popup_window, text="Exit ", style="Default.TButton",
                                  command=lambda: self.exit())
        self.button_exit.grid(column=2, row=20, padx=0, pady=10)

    def save_calibration_tip(self, tip="Tips_1000uL"):
        ''' the Tips was considered as plate name for simiplicity '''
        z = chem_robot.get_axe_position(axe=LIQUID)
        # tip_plate_50 = chem_robot.deck.get_plate_assignment("Tips 50uL")
        # tip_plate_1000 = chem_robot.deck.get_plate_assignment("Tips 1000uL")
        chem_robot.deck.save_calibration(plate="Tips_1000uL",
                                         calibration_data=[0, 0, z])
        chem_robot.update()

    def exit(self):
        self.popup_window.destroy()

    def move_to_tip_rack(self):
        tip_plate_1000 = chem_robot.deck.get_plate_assignment("Tips 1000uL")
        vial_to = (tip_plate_1000, "A1")
        chem_robot.move_to(head=LIQUID, vial=vial_to)


class Reference_calibration(ttk.Frame):
    def __init__(self):
        self.popup_window = Toplevel()
        self.popup_window.title("Reference Point Calibration")

        # Move functions as an LabelFrame
        self.move_frame = tk.LabelFrame(
            self.popup_window, text="Move axies (X, Y, Z1, Z2, Z3)", fg="RoyalBlue4", font="Helvetica 11 bold")
        self.move_frame.grid(column=0, columnspan=4, row=10,
                             padx=20, pady=10, sticky=tk.W)
        self.move_axies = custom_widgets.Move_axes(
            parent=self.move_frame, robot=chem_robot)
        # Save buttons
        self.button_save_z1 = Button(self.popup_window, text="Save calibration (Z1)", style="Red.TButton",
                                     command=lambda: self.save_calibration("Z1"))
        self.button_save_z1.grid(column=0, row=20, padx=0, pady=10)
        self.button_save_z2 = Button(self.popup_window, text="Save calibration (Z2)", style="Red.TButton",
                                     command=lambda: self.save_calibration("Z2"))
        self.button_save_z2.grid(column=1, row=20, padx=0, pady=10)
        Label(self.popup_window, text=" ").grid(
            column=1, row=16, padx=10, pady=10)
        self.button_save_z3 = Button(self.popup_window, text="Save calibration (Z3)", style="Red.TButton",
                                     command=lambda: self.save_calibration("Z3"))
        self.button_save_z3.grid(column=2, row=20, padx=0, pady=10)
        # Exit buttons
        self.button_exit = Button(self.popup_window, text="Exit", style="Default.TButton",
                                  command=lambda: self.exit())
        self.button_exit.grid(column=3, row=20, padx=0, pady=10)
        self.button_exit.focus_force()
        self.popup_window.grab_set()  # keep this pop window focused

    def save_calibration(self, head="Z1"):
        # the smoothieware has a strange problem on max speed, I have to work around by double (*2) the steps_per_mm
        ''' the head name Z1, Z2 or Z3 was considered as plate name for simiplicity '''
        # example: [0, 0, 132.1] is the coordinate (x, y, z) vs. the ref point
        # "Z1": [0, 0, 132.1],
        # "Z2": [0, 0, 129.6],
        # "Z3": [0, 0, 125.4],
        # "Tips": 106.5
        current_head = head
        calibration_data = chem_robot.deck.calibration[current_head]
        x = chem_robot.xy_platform.get_position('x')
        y = chem_robot.xy_platform.get_position('y')
        z = chem_robot.z_platform.get_position(head=current_head)
        calibration_data = [x, y, z]
        chem_robot.deck.save_calibration(plate=current_head,
                                         calibration_data=calibration_data)
        chem_robot.update()

    def exit(self):
        self.popup_window.destroy()


# Reagent distrubution - transfer one reagent (solvents) to multiple reacters
class Reagent_distrubution():
    def __init__(self, tip_selection=None):
        self.tip_selection = tip_selection
        self.popup_window = Toplevel()
        self.popup_window.title("Liquid distribution ")

        # Solvent option
        self.solvent_frame = tk.Frame(self.popup_window)
        self.solvent_frame.grid(column=0, row=0, sticky=tk.N)
        Label(self.solvent_frame, text=" ").grid(row=0, sticky=tk.W)
        Label(self.solvent_frame, style="Default.Label",
              text="Liquid Reagent Name:").grid(row=1, sticky=tk.W)
        self.solvent_selection = ttk.Combobox(
            self.solvent_frame, font=('Helvetica', '11'), width=20)
        self.solvent_selection["values"] = (
            "", "Water", "DCM", "MeOH", "Ethyl-acetate", "Hexanes", "Toluene", "THF", "DCE", "Dioxane", "Acetone")
        self.solvent_selection.current(0)  # set the selected item
        self.solvent_selection.grid(row=3, pady=5, sticky=tk.W)
        Label(self.solvent_frame, style="Default.Label",
              text="Liquid Volume (mL):").grid(row=4, sticky=tk.W)
        self.volume_entry = ttk.Entry(self.solvent_frame, width=20,
                                      font=('Helvetica', '11'))
        self.volume_entry.grid(row=5, pady=2, sticky=tk.W)

        # Number of reactions selection
        self.number_frame = tk.LabelFrame(
            self.popup_window, text="Number of reactions", fg="RoyalBlue4", font="Helvetica 11")
        self.number_frame.grid(column=0, row=6, padx=10, pady=10)
        self.number_reaction = ttk.Combobox(
            self.number_frame, state="readonly", font=('Helvetica', '11'))
        self.number_reaction["values"] = (
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
        self.number_reaction.current(0)  # set the selected item
        self.number_reaction.grid(pady=5)

        # Reactor selector
        self.reactor_selection_frame = tk.Frame(
            self.popup_window, width=300, height=260)
        self.reactor_selection_frame.grid(
            column=1, row=0, rowspan=9, sticky=tk.N)
        self.current_reactor = chem_robot.deck.get_current_reactor()
        self.reactor_selection = custom_widgets.Reactor_on_screen(
            parent=self.reactor_selection_frame, reactor_type=self.current_reactor,  current=0)

        # Display information
        self.display_frame = tk.Frame(self.popup_window)
        self.display_frame.grid(column=0, rowspan=6, columnspan=4,
                                row=20, padx=15, pady=10)
        self.information = custom_widgets.Information_display(
            self.display_frame, title="Progress of operation:\n", width=80, height=14)

        # Run, stop and exit buttons
        self.run_button = Button(
            self.popup_window, text="Transfer reagents", style="Green.TButton", command=lambda: self.run_thread())
        self.run_button.grid(column=0, row=30, pady=10)
        self.stop_button = Button(
            self.popup_window, text="Stop running", style="Red.TButton", command=lambda: self.stop())
        self.stop_button.grid(column=1, row=30, pady=10)
        self.exit_button = Button(self.popup_window, text="Exit", style="Default.TButton",
                                  command=lambda: self.exit())
        self.exit_button.grid(column=2, row=30, padx=0, pady=10)
        self.exit_button.focus_force()
        # self.popup_window.grab_set()  # keep this pop window focused

    def get_current_tip(self):
        screen_update_time = self.tip_selector.get_update_time()
        deck_update_time = chem_robot.deck.get_tip_update_time()
        if screen_update_time >= deck_update_time:
            chem_robot.deck.set_current_tip(self.tip_selector.get_current())
            chem_robot.deck.save_current_tip()
        else:
            self.tip_selector.set_current(chem_robot.deck.get_current_tip())
            self.tip_selector.highlight_current()
        return chem_robot.deck.get_current_tip()

    def setup(self):
        # self.button_exit.focus_force()
        # self.popup_window.grab_set()  # keep this pop window focused
        chem_robot.pipette.initialization()
        number_of_reaction = int(self.number_reaction.get())
        current_tip = self.tip_selection.get_current()
        available_tip = len(chem_robot.deck.get_vial_list_by_plate_type(
            "tiprack_1000uL"))-current_tip
        available_reactor = len(chem_robot.deck.get_vial_list_by_plate_type(
            self.current_reactor))-self.reactor_selection.get_current()
        if available_tip < number_of_reaction:
            self.information.display_msg(
                "Warning: No enough tip, please refill tips.", start_over=False)
            return
        if available_reactor < number_of_reaction:
            self.information.display_msg(
                "Warning: No enough reactor.",  start_over=False)
            return

        solvent_volume_string = self.volume_entry.get()
        solvent_name = self.solvent_selection.get()
        if solvent_name == "":
            self.information.display_msg(
                "Please enter a valid solvent name.", start_over=False)
            return
        if not helper.is_float(solvent_volume_string):
            self.information.display_msg(
                "Please enter solvent volume in mL!", start_over=False)
            return
        solvent_volume = float(solvent_volume_string)
        solvent_info = chem_synthesis.locate_reagent(solvent_name)
        if "not found" in solvent_info:
            self.information.display_msg(solvent_info, start_over=False)
            return
        else:
            solvent_plate_name = solvent_info["plate"]
            solvent_pos = solvent_info["vial"]

        if not chem_robot.ready:
            self.information.display_msg(
                "Robot not ready! Please connect and home robot.", start_over=False)
            return

        ok = messagebox.askokcancel(
            "Warning", f"Please make sure:\n 1) Reactor vials are uncapped.\n  2) All reagent vials are secured in the plate.")
        if not ok:
            return

        missing = chem_robot.deck.check_missing_assignment()
        if missing != "complete":
            retry = messagebox.askyesno(
                "Warning", f"Warning: No {missing} plate is assigned, continue?.")
            if not retry:
                return

        tip_no = self.tip_selection.get_current(format="A1")
        # tip_no = chem_robot.deck.get_current_tip(format="A1")
        tip_plate = chem_robot.deck.get_plate_assignment("Tips 1000uL")
        tip = (tip_plate, tip_no)

        reactor_no = self.reactor_selection.get_current(format="A1")
        reactor_plate = chem_robot.deck.get_plate_assignment("Reactor")
        reactor_no_start = reactor_no  # non-numerical format e.g., A1
        reactor_start_number = self.reactor_selection.get_current()  # numerical format e.g., 1

        trash_plate = chem_robot.deck.get_plate_assignment("Trash")
        trash = (trash_plate, 'A1')

        solvent_slot = chem_robot.deck.get_slot_from_plate_name(
            solvent_plate_name)
        solvent_vial = (solvent_slot, solvent_pos)

        # prepare
        self.run_button.focus_force()
        self.popup_window.grab_set()  # keep this pop window focused
        self.exit_button["state"] = "disabled"
        self.run_button["state"] = "disabled"

        # Use one tip for all transfers
        chem_robot.pickup_tip(tip)
        chem_robot.decap(solvent_vial)

        if chem_robot.stop_flag:
            return ("stopped by user")

        # adding solvent
        self.information.display_msg("Starting transfering...")
        reactor_no = reactor_no_start
        self.reactor_selection.set_current(reactor_start_number)
        self.reactor_selection.highlight_current()
        i = 0
        for i in range(number_of_reaction):
            reactor_vial = (reactor_plate, reactor_no)
            if chem_robot.stop_flag:
                return ("stopped by user")
            message = f"Run {i+1} of {number_of_reaction}, adding solvent {solvent_name} {solvent_volume} mL to reactor at {reactor_vial[1]} using tip {tip[1]}"
            self.information.display_msg(message, start_over=False)
            chem_robot.transfer_liquid(vial_from=solvent_vial, vial_to=reactor_vial,
                                       tip=None, trash=trash, volume=solvent_volume)
            reactor_no = chem_robot.deck.next_vial(
                reactor_no, plate=reactor_plate)
            self.reactor_selection.next()
        chem_robot.drop_tip(vial=trash)
        chem_robot.recap(solvent_vial)

        self.information.display_msg(
            "\nFinished....................................................\n", start_over=False)

        chem_robot.deck.set_current_tip(chem_robot.deck.get_current_tip()+1)
        chem_robot.deck.save_current_tip()
        self.tip_selection.next()
        self.popup_window.grab_release()
        self.exit_button["state"] = "normal"
        self.run_button["state"] = "normal"

    def run_thread(self):
        t = threading.Thread(target=self.setup)
        t.start()

    def exit(self):
        self.popup_window.destroy()

    def stop(self):
        chem_robot.set_stop_flag(stop=True)
        self.information.display_msg("Stopping......\n", start_over=False)
        self.run_button["state"] = "normal"


class Manual_control():
    def __init__(self, tip_selector=None):
        self.tip_selector = tip_selector
        self.popup_window = Toplevel()
        self.popup_window.title("Manual Controls ")

        # Slot selector
        self.current_slot = 5
        Label(self.popup_window, text="Select current slot",
              style="Default.Label").grid(column=0, row=4, pady=5)
        self.slot_frame = tk.Frame(
            self.popup_window, relief="ridge", bg="gray")
        self.slot_frame.grid(column=0, row=5)
        slot_list = chem_robot.deck.get_vial_list_by_plate_type(
            plate_type="deck")
        self.slot_selection = custom_widgets.Item_selection_on_screen(
            parent=self.slot_frame, slot_list=slot_list, COLS=5, ROWS=3, current=self.current_slot)

        # Vial selector
        self.current_vial = 0
        Label(self.popup_window, text="Select current vial",
              style="Default.Label").grid(column=1, row=4, pady=5)
        self.vial_frame = tk.Frame(self.popup_window)
        self.vial_frame.grid(column=1, row=5, sticky=tk.N)
        slot_list = chem_robot.deck.get_vial_list_by_plate_type(
            plate_type="plate_5mL")
        col_row = chem_robot.deck.get_cols_rows_by_plate_type(
            plate_type="plate_5mL")
        self.vial_selection = custom_widgets.Item_selection_popup(
            parent=self.vial_frame, title="Current Vial:  ", slot_list=slot_list, COLS=col_row["columns"], ROWS=col_row["rows"], current=self.current_vial)

        # # blank space
        # tk.Label(self.popup_window, text=" ".ljust(190),
        #          bg="lightgrey").grid(column=0, columnspan=3, row=6, pady=5)

        # Z1 functions
        self.labelframe_z1 = tk.LabelFrame(
            self.popup_window, text="Liquid", fg="RoyalBlue4", font="Helvetica 11 bold")
        self.labelframe_z1.grid(
            column=0, row=10, padx=20, pady=20, sticky=tk.N)
        Button(self.labelframe_z1, text="Move to selected position", style="Green.TButton",
               command=lambda: self.move_to_plate("Z1")).grid(row=0, padx=10, pady=10, sticky=tk.W)
        Button(self.labelframe_z1, text="Pickup Tip", style="Default.TButton",
               command=lambda: self.test_pickup_tip()).grid(row=1, padx=10, pady=10, sticky=tk.W)
        Button(self.labelframe_z1, text="Aspirate", style="Default.TButton",
               command=lambda: self.test_aspirate()).grid(row=2, padx=10, pady=10, sticky=tk.W)
        Button(self.labelframe_z1, text="Dispense", style="Default.TButton",
               command=lambda: self.test_dispense()).grid(row=3, padx=10, pady=10, sticky=tk.W)
        Button(self.labelframe_z1, text="Eject Tip", style="Default.TButton",
               command=lambda: self.test_eject_tip()).grid(row=4, padx=10, pady=10, sticky=tk.W)
        # Reaction volume selector
        self.volume_frame = tk.Frame(
            self.labelframe_z1, relief="ridge", bg="gray")
        self.volume_frame.grid(column=1, row=2, pady=10, sticky=tk.N)
        self.volume_selection = custom_widgets.Volume_entry(
            parent=self.volume_frame, title="Volume (mL)")
        self.slot_frame.focus_force()
        self.popup_window.grab_set()  # keep this pop window focused

        # Z2 functions
        self.labelframe_z2 = tk.LabelFrame(
            self.popup_window, text="Tablet", fg="RoyalBlue4", font="Helvetica 11 bold")
        self.labelframe_z2.grid(column=1, row=10, pady=20, sticky=tk.N)
        Button(self.labelframe_z2, text="Move to selected position", style="Green.TButton",
               command=lambda: self.move_to_plate("Z2")).grid(row=0, padx=10, pady=15, sticky=tk.W)
        Button(self.labelframe_z2, text="Pickup Tablet", style="Default.TButton",
               command=lambda: self.test_pickup_tablet()).grid(row=1, padx=10, pady=15, sticky=tk.W)
        Button(self.labelframe_z2, text="Drop Tablet", style="Default.TButton",
               command=lambda: self.test_drop_tablet()).grid(row=2, padx=10, pady=15, sticky=tk.W)
        Button(self.labelframe_z2, text="Clean Needle", style="Default.TButton",
               command=lambda: self.test_clean_needle()).grid(row=3, padx=10, pady=15, sticky=tk.W)

        # Z3 functions
        self.labelframe_z3 = tk.LabelFrame(
            self.popup_window, text="Capper", fg="RoyalBlue4", font="Helvetica 11 bold")
        self.labelframe_z3.grid(column=2, row=10, pady=20, sticky=tk.N)
        Button(self.labelframe_z3, text="Move to selected position", style="Green.TButton",
               command=lambda: self.move_to_plate("Z3")).grid(row=0, padx=10, pady=10, sticky=tk.W)
        Button(self.labelframe_z3, text="  Decap ", style="Default.TButton",
               command=lambda: self.test_decap()).grid(row=1, padx=10, pady=10, sticky=tk.W)
        Button(self.labelframe_z3, text=" Recap", style="Default.TButton",
               command=lambda: self.test_recap()).grid(row=2, padx=10, pady=10, sticky=tk.W)
        Button(self.labelframe_z3, text=" Pickup Cap from", style="Default.TButton",
               command=lambda: self.test_pickup_cap()).grid(row=3, padx=10, pady=10, sticky=tk.W)

        # Cap selector
        self.cap_frame = tk.Frame(
            self.labelframe_z3, relief="ridge", bg="gray")
        self.cap_frame.grid(column=0, row=8, rowspan=2)
        slot_list = chem_robot.deck.get_vial_list_by_plate_type(
            plate_type="caps")
        col_row = chem_robot.deck.get_cols_rows_by_plate_type(
            plate_type="caps")
        self.cap_selection = custom_widgets.Item_selection_on_screen(
            parent=self.cap_frame, slot_list=slot_list, COLS=col_row["columns"], ROWS=col_row["rows"], current=0)
        Button(self.labelframe_z3, text="Return Cap to", style="Default.TButton",
               command=lambda: self.test_return_cap()).grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)

        # Move functions as an LabelFrame
        self.move_frame = tk.LabelFrame(
            self.popup_window, text="Move axies (X, Y, Z1, Z2, Z3)", fg="RoyalBlue4", font="Helvetica 11 bold")
        self.move_frame.grid(column=0, columnspan=4, row=15,
                             padx=20, sticky=tk.W)
        self.move_axies = custom_widgets.Move_axes(
            parent=self.move_frame, robot=chem_robot)

    def move_to_plate(self, head):
        slot = self.slot_selection.get_current(format="A1")
        vial = self.vial_selection.get_current(format="A1")
        vial_to = (slot, vial)
        chem_robot.move_to(head=head, vial=vial_to, use_allow_list=False)

    def test_decap(self):
        slot = self.slot_selection.get_current(format="A1")
        vial = self.vial_selection.get_current(format="A1")
        vial_to = (slot, vial)
        chem_robot.decap(vial=vial_to)

    def test_recap(self):
        slot = self.slot_selection.get_current(format="A1")
        vial = self.vial_selection.get_current(format="A1")
        vial_to = (slot, vial)
        chem_robot.recap(vial=vial_to)

    def test_pickup_cap(self):
        cap_no = self.cap_selection.get_current(format="A1")
        cap_plate = chem_robot.deck.get_plate_assignment("Reaction caps")
        chem_robot.pickup_cap((cap_plate, cap_no))

    def test_return_cap(self):
        cap_no = self.cap_selection.get_current(format="A1")
        cap_plate = chem_robot.deck.get_plate_assignment("Reaction caps")
        chem_robot.return_cap((cap_plate, cap_no))

    def test_pickup_tablet(self):
        slot = self.slot_selection.get_current(format="A1")
        vial = self.vial_selection.get_current(format="A1")
        vial_to = (slot, vial)
        chem_robot.pickup_tablet(vial=vial_to)

    def test_drop_tablet(self):
        slot = self.slot_selection.get_current(format="A1")
        vial = self.vial_selection.get_current(format="A1")
        vial_to = (slot, vial)
        chem_robot.drop_tablet(vial=vial_to)

    def test_clean_needle(self):
        # slot = self.slot_selection.get_current(format="A1")
        # vial = self.vial_selection.get_current(format="A1")
        vial_to = ("C1", "D4")
        chem_robot.clean_up_needle(vial=vial_to)

    def test_pickup_tip(self):
        tip_no = self.tip_selector.get_current(format="A1")
        tip_plate = chem_robot.deck.get_plate_assignment("Tips 1000uL")
        chem_robot.pickup_tip((tip_plate, tip_no))

    def test_aspirate(self):
        volume = self.volume_selection.get()
        if volume == False:
            messagebox.showinfo(
                " ", "Please input a valid volume in mL.")
        slot = self.slot_selection.get_current(format="A1")
        vial = self.vial_selection.get_current(format="A1")
        vial_to = (slot, vial)
        chem_robot.aspirate(vial=vial_to, volume=int(volume*1000))
        chem_robot.back_to_safe_position(head=LIQUID)
        chem_robot.pipette.set_transport_air_volume(volume=15)

    def test_dispense(self):
        slot = self.slot_selection.get_current(format="A1")
        vial = self.vial_selection.get_current(format="A1")
        vial_to = (slot, vial)
        chem_robot.dispense(vial=vial_to)
        chem_robot.back_to_safe_position(head=LIQUID)

    def test_eject_tip(self):
        chem_robot.pipette.send_drop_tip_cmd()


# Used in reagent distrubution
class Cap_operation():
    def __init__(self, option="cap"):
        self.popup_window = Toplevel()
        self.option = option
        self.popup_window.title(self.option)

        if self.option == "Cap reactors":
            reactor_column = 2
            cap_column = 0
        else:
            reactor_column = 0
            cap_column = 2

        # Reactor selector
        self.reactor_selection_frame = tk.Frame(
            self.popup_window, width=300, height=260)
        self.reactor_selection_frame.grid(
            column=reactor_column, row=7, rowspan=9, sticky=tk.N)
        self.current_reactor = chem_robot.deck.get_current_reactor()
        self.reactor_selection = custom_widgets.Reactor_on_screen(
            parent=self.reactor_selection_frame, reactor_type=self.current_reactor,  current=0)

        # Cap selector
        self.cap_frame = tk.Frame(self.popup_window)
        self.cap_frame.grid(column=cap_column, row=8, sticky=tk.N)
        Label(self.cap_frame, text="Current Cap\n",
              style="Default.Label").grid(row=0, pady=5)
        slot_list = chem_robot.deck.get_vial_list_by_plate_type(
            plate_type="caps")
        col_row = chem_robot.deck.get_cols_rows_by_plate_type(
            plate_type="caps")
        self.cap_selection_frame = tk.Frame(
            self.cap_frame, relief="ridge", bg="gray")
        self.cap_selection_frame.grid(row=1)
        self.cap_selection = custom_widgets.Item_selection_on_screen(
            parent=self.cap_selection_frame, slot_list=slot_list, COLS=col_row["columns"], ROWS=col_row["rows"], current=0)

        direction = "  Cap\n=======>>>"
        Label(self.popup_window, text=direction,
              style="Default.Label").grid(column=1, row=8, pady=5)

        # Number of reactions selection
        self.number_frame = tk.LabelFrame(
            self.popup_window, text="Number of reactors", fg="RoyalBlue4", font="Helvetica 11")
        self.number_frame.grid(
            column=0, row=19, columnspan=2, padx=10, pady=20)
        self.number_reaction = ttk.Combobox(
            self.number_frame, state="readonly", font=('Helvetica', '11'))
        self.number_reaction["values"] = (
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)
        self.number_reaction.current(0)  # set the selected item
        self.number_reaction.grid(pady=5)

        # Display information
        self.display_frame = tk.Frame(self.popup_window)
        self.display_frame.grid(column=0, rowspan=6, columnspan=4,
                                row=20, padx=15, pady=10)
        self.information = custom_widgets.Information_display(
            self.display_frame, title="Progress of operation:\n", width=80, height=14)

        # Run, stop and exit buttons
        self.run_button = Button(
            self.popup_window, text=self.option, style="Green.TButton", command=lambda: self.run_thread())
        self.run_button.grid(column=0, row=30, pady=10)
        self.stop_button = Button(
            self.popup_window, text="Stop ", style="Red.TButton", command=lambda: self.stop())
        self.stop_button.grid(column=1, row=30, pady=10)
        self.exit_button = Button(self.popup_window, text="Exit", style="Default.TButton",
                                  command=lambda: self.exit())
        self.exit_button.grid(column=2, row=30, padx=0, pady=10)
        self.exit_button.focus_force()
        # self.popup_window.grab_set()  # keep this pop window focused

    def setup(self):
        number_of_reaction = int(self.number_reaction.get())
        current_reactor = "reactor_27p"
        available_reactor = len(chem_robot.deck.get_vial_list_by_plate_type(
            current_reactor))-self.reactor_selection.get_current()

        if available_reactor < number_of_reaction:
            self.information.display_msg(
                "Warning: No enough reactor.",  start_over=False)
            return

        available_cap = len(chem_robot.deck.get_vial_list_by_plate_type(
            "caps"))-self.cap_selection.get_current()

        if available_cap < number_of_reaction:
            self.information.display_msg(
                "Warning: No enough cap.",  start_over=False)
            return

        ok = messagebox.askokcancel(
            "Warning", f"Please make sure:\n 1) Reactor vials are uncapped.\n  2) All reagent vials are secured in the plate.")
        if not ok:
            return

        missing = chem_robot.deck.check_missing_assignment()
        if missing != "complete":
            retry = messagebox.askyesno(
                "Warning", f"Warning: No {missing} plate is assigned, continue?.")
            if not retry:
                return

        if not chem_robot.ready:
            self.information.display_msg(
                "Robot not ready! Please connect and home robot.", start_over=False)
            return

        self.run_button.focus_force()
        self.popup_window.grab_set()  # keep this pop window focused
        self.exit_button["state"] = "disabled"
        self.run_button["state"] = "disabled"

        if chem_robot.stop_flag:
            return ("stopped by user")

        # cap operations, if option = cap or decap
        reactor_no = self.reactor_selection.get_current(format="A1")
        reactor_plate = chem_robot.deck.get_plate_assignment("Reactor")
        cap_no = self.cap_selection.get_current(format="A1")
        cap_plate = chem_robot.deck.get_plate_assignment("Reaction caps")
        i = 0
        for i in range(number_of_reaction):
            reactor = (reactor_plate, reactor_no)
            cap = (cap_plate, cap_no)
            if chem_robot.stop_flag:
                return ("stopped by user")
            message = f"Run {i+1} of {number_of_reaction}, transfer cap for reactor@ {reactor[1]}"
            self.information.display_msg(message, start_over=False)
            if self.option == "Cap reactors":
                chem_robot.pickup_cap(cap)
                chem_robot.recap(reactor)
            else:
                chem_robot.decap(reactor)
                chem_robot.return_cap(cap)
            cap_no = chem_robot.deck.next_vial(cap_no, plate=cap_plate)
            reactor_no = chem_robot.deck.next_vial(
                reactor_no, plate=reactor_plate)
            self.reactor_selection.next()
            self.cap_selection.next()

        self.information.display_msg(
            "\nFinished....................................................\n", start_over=False)

        self.popup_window.grab_release()
        self.exit_button["state"] = "normal"
        self.run_button["state"] = "normal"

    def run_thread(self):
        t = threading.Thread(target=self.setup)
        t.start()

    def exit(self):
        self.popup_window.destroy()

    def stop(self):
        chem_robot.set_stop_flag(stop=True)
        self.information.display_msg("Stopping......\n", start_over=False)
        self.run_button["state"] = "normal"


# This is the main entry of program
if __name__ == "__main__":
    logging.basicConfig(filename='myapp.log',
                        format='%(asctime)s %(message)s', level=logging.INFO)
    logging.info('Start...')

    # Start robot class
    chem_robot = robot.Robot()
    chem_synthesis = synthesis.Synthesis(
        reagent_file=Path("user_files/reagent_index.xlsx"))

    # Start GUI
    app = Main()
    # define styles
    style = ttk.Style()
    style.configure('lefttab.TNotebook', tabposition='wn')
    style.configure('Title.Label',
                    foreground="light green",
                    background="dark green",
                    font=('Helvetica', 18, 'bold italic'),
                    justify=tk.CENTER,
                    relief=tk.RIDGE
                    )

    style.configure('Default.Label',
                    foreground="black",
                    #background="dark green",
                    font=('Helvetica', 11, 'italic'),
                    justify=tk.CENTER,
                    relief=tk.RIDGE
                    )

    style.configure("Default.TButton",
                    foreground="Black",
                    font=('Helvetica', 11, 'italic'),
                    background="LightGrey")

    style.configure("Green.TButton",
                    foreground="blue",
                    background="green",
                    font=('Helvetica', 11, 'italic'))

    style.configure("Red.TButton",
                    foreground="red",
                    font=('Helvetica', 11, 'italic'),
                    background="red")

    style.configure("Plate.TButton",
                    foreground="black",
                    font=('Helvetica', 11, 'italic'),
                    width=18,
                    justify=tk.LEFT,
                    background="deepskyblue")

    style.configure("Plate_r.TButton",
                    foreground="blue",
                    font=('Helvetica', 11, 'italic'),
                    width=18,
                    justify=tk.LEFT,
                    background="deepskyblue")

    app.geometry("+0+0")  # set to window to the up/left conner of screen
    # app.state('zoomed')  # full screen mode

    app.mainloop()
    # logging.info('Finished\n')
