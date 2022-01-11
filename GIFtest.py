from tkinter import *
import time
import os
root = Tk()

frameCnt = 35
frames = [PhotoImage(file='res/loader/frame-{}.png'.format(i)) for i in range(1, frameCnt+1)]

def update(ind=0):

    frame = frames[ind]
    ind += 1
    if ind == frameCnt:
        ind = 0
    label.configure(image=frame)
    root.after(20, update, ind)

bg0_img = PhotoImage(file="res/wait.png")
canvas = Canvas(root, width=500, height=540, bg='white', bd=0, highlightthickness=0)
canvas.create_image(0, 0, image=bg0_img, anchor="nw")	# id = 1
canvas.pack(fill="both", expand=True)

label = Label(canvas, bg="#84C3EF")
canvas.create_window(250, 270, anchor="c", window=label)
root.after(0, update)
root.mainloop()