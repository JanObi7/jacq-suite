from JacqSuite import Fabric
from JacqScan import selectScanPoint
from functools import partial

fabric = Fabric("c:/temp/jacq-suite/data/P2383i")

import tkinter as tk
import tkinter.filedialog as fd, tkinter.simpledialog as sd
import os.path as path

window = tk.Tk()
window.title("JacqSuite - "+fabric.path)
window.geometry('600x400')

scan_buttons = []

def create_scan():
  idx = fabric.createScan()
  update_scans()
  open_scan_dialog(idx)

def update_scans():
  global scan_buttons

  # remove btns from grid
  for btn in scan_buttons:
    btn.grid_remove()

  # empty btn list
  scan_buttons = []

  # update scan list
  for s in range(len(fabric.config["scans"])):
    button = tk.Button(window, text=f"Scan {s} digitalisieren", command=partial(fabric.digitizeScan,s))
    button.grid(row=3+s, column=2)
    scan_buttons.append(button)

    button = tk.Button(window, text=f"Scan {s} bearbeiten", command=partial(edit_scan,s))
    button.grid(row=3+s, column=3)
    scan_buttons.append(button)

def edit_scan(idx):
  open_scan_dialog(idx)

def open_scan_dialog(idx):
  scan = fabric.config["scans"][idx]

  pop = tk.Toplevel(window)
  pop.title("Scan bearbeiten")
  # pop.geometry("300x150")
  for c in range(1,4): pop.columnconfigure(c, minsize=100)
  for r in range(1,5): pop.rowconfigure(r)

  def select_filename():
    pathname = fd.askopenfilename(parent=pop, initialdir=fabric.path+"/scans", title="Please select a scan file:")
    scan["filename"] = path.basename(pathname)
    update_dialog()

  def select_tl():
    scan["point_tl"] = selectScanPoint(fabric.path+"/scans/"+scan["filename"])
    update_dialog()

  def select_tr():
    scan["point_tr"] = selectScanPoint(fabric.path+"/scans/"+scan["filename"])
    update_dialog()

  def select_bl():
    scan["point_bl"] = selectScanPoint(fabric.path+"/scans/"+scan["filename"])
    update_dialog()

  def select_br():
    scan["point_br"] = selectScanPoint(fabric.path+"/scans/"+scan["filename"])
    update_dialog()

  def select_kmin():
    scan["kmin"] = sd.askinteger(parent=pop, title="Kmin", prompt="minimale Kette", initialvalue=scan["kmin"])
    update_dialog()

  def select_kmax():
    scan["kmax"] = sd.askinteger(parent=pop, title="Kmax", prompt="maximale Kette", initialvalue=scan["kmax"])
    update_dialog()

  def select_smin():
    scan["smin"] = sd.askinteger(parent=pop, title="Smin", prompt="minimaler Schuss", initialvalue=scan["smin"])
    update_dialog()

  def select_smax():
    scan["smax"] = sd.askinteger(parent=pop, title="Smax", prompt="maximaler Schuss", initialvalue=scan["smax"])
    update_dialog()

  def save_scan():
    fabric.saveConfig()
    pop.destroy()

  def delete_scan():
    fabric.deleteScan(idx)
    pop.destroy()
    update_scans()

  def update_dialog():
    button1["text"] = scan["filename"]
    button_kmin["text"] = scan["kmin"]
    button_kmax["text"] = scan["kmax"]
    button_smin["text"] = scan["smin"]
    button_smax["text"] = scan["smax"]
    button_tl["text"] = scan["point_tl"]
    button_tr["text"] = scan["point_tr"]
    button_bl["text"] = scan["point_bl"]
    button_br["text"] = scan["point_br"]

  button1 = tk.Button(pop, text=scan["filename"], command=select_filename)
  button1.grid(row=1, column=1, columnspan=3, sticky="nswe")

  button_tl = tk.Button(pop, text=scan["point_tl"], command=select_tl)
  button_tl.grid(row=2, column=1, sticky="nswe")
  button_tr = tk.Button(pop, text=scan["point_tr"], command=select_tr)
  button_tr.grid(row=2, column=3, sticky="nswe")
  button_bl = tk.Button(pop, text=scan["point_bl"], command=select_bl)
  button_bl.grid(row=4, column=1, sticky="nswe")
  button_br = tk.Button(pop, text=scan["point_br"], command=select_br)
  button_br.grid(row=4, column=3, sticky="nswe")

  button_smax = tk.Button(pop, text=scan["smax"], command=select_smax)
  button_smax.grid(row=2, column=2, sticky="nswe")
  button_smin = tk.Button(pop, text=scan["smin"], command=select_smin)
  button_smin.grid(row=4, column=2, sticky="nswe")
  button_kmin = tk.Button(pop, text=scan["kmin"], command=select_kmin)
  button_kmin.grid(row=3, column=1, sticky="nswe")
  button_kmax = tk.Button(pop, text=scan["kmax"], command=select_kmax)
  button_kmax.grid(row=3, column=3, sticky="nswe")

  button_save = tk.Button(pop, text="Speichern", command=save_scan)
  button_save.grid(row=5, column=3, sticky="nswe")

  button_delete = tk.Button(pop, text="Löschen", command=delete_scan)
  button_delete.grid(row=5, column=1, sticky="nswe")

tk.Label(text="Muster").grid(row=1,column=1)
tk.Button(text="Muster bearbeiten", command=fabric.editPattern).grid(row=2,column=1)
tk.Button(text="Muster generieren", command=fabric.renderPattern).grid(row=3,column=1)
tk.Button(text="Muster zurücksetzen", command=fabric.initPattern, background="red").grid(row=4,column=1)

tk.Label(text="Scans").grid(row=1,column=2,columnspan=2)
tk.Button(text="Scan hinzufügen", command=create_scan).grid(row=2,column=2,columnspan=2,sticky="we")
update_scans()

tk.Label(text="Karten").grid(row=1,column=4)
tk.Button(text="Karten generieren", command=fabric.generateCards).grid(row=2, column=4)

tk.Label(text="Texturen").grid(row=1,column=5)
tk.Button(text="Textur generieren", command=fabric.renderTexture).grid(row=2, column=5)


window.mainloop()
