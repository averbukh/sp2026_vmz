import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

def number(text, name):
    try:
        value = float(text.strip().replace(",", "."))
    except ValueError:
        raise ValueError(f"Параметр {name} должен быть числом.")
    if not math.isfinite(value):
        raise ValueError(f"Параметр {name} должен быть конечным числом.")
    return value

class App:
    def __init__(self, root):
        self.root = root
        root.title("Сумма трёх синусоид")
        root.geometry("1000x680")
        self.xs, self.ys = [], []
        outer = ttk.Frame(root, padding=10)
        outer.pack(fill="both", expand=True)
        box = ttk.LabelFrame(outer, text="Параметры", padding=8)
        box.pack(fill="x")
        defaults = [("a1","a₁","1"),("b1","b₁","1"),("a2","a₂","0.5"),
                    ("b2","b₂","2"),("a3","a₃","0.25"),("b3","b₃","3"),
                    ("x0","x₀","0"),("xk","xк","6.28"),("dx","Δx","0.1")]
        self.fields = {}
        for i,(key,label,default) in enumerate(defaults):
            cell = ttk.Frame(box)
            cell.grid(row=i//3, column=i%3, padx=8, pady=5, sticky="w")
            ttk.Label(cell,text=label+":").pack(side="left")
            ent = ttk.Entry(cell,width=13)
            ent.insert(0,default)
            ent.pack(side="left",padx=5)
            self.fields[key] = ent
        buttons = ttk.Frame(outer); buttons.pack(fill="x",pady=8)
        ttk.Button(buttons,text="Рассчитать",command=self.calculate).pack(side="left")
        ttk.Button(buttons,text="Сохранить график SVG",command=self.save_svg).pack(side="left",padx=8)
        panes = ttk.Panedwindow(outer,orient="horizontal"); panes.pack(fill="both",expand=True)
        tf = ttk.LabelFrame(panes,text="Таблица x и y",padding=5); panes.add(tf,weight=1)
        self.table = ttk.Treeview(tf,columns=("x","y"),show="headings")
        self.table.heading("x",text="x"); self.table.heading("y",text="y(x)")
        self.table.column("x",width=100,anchor="e"); self.table.column("y",width=130,anchor="e")
        sb = ttk.Scrollbar(tf,orient="vertical",command=self.table.yview)
        self.table.configure(yscrollcommand=sb.set)
        self.table.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
        gf = ttk.LabelFrame(panes,text="График y(x)",padding=5); panes.add(gf,weight=2)
        self.canvas = tk.Canvas(gf,bg="white"); self.canvas.pack(fill="both",expand=True)
        self.status = ttk.Label(outer,text="Введите параметры и нажмите «Рассчитать».")
        self.status.pack(fill="x",pady=5)
        root.bind("<Configure>",self.resize)

    def calculate(self):
        try:
            p = {k:number(v.get(),k) for k,v in self.fields.items()}
            if p["dx"] <= 0: raise ValueError("Шаг Δx должен быть больше нуля.")
            if p["xk"] < p["x0"]: raise ValueError("xк должно быть не меньше x₀.")
            n = int(math.floor((p["xk"]-p["x0"])/p["dx"]+1e-12))+1
            if n > 10000: raise ValueError("Слишком много точек (более 10000); увеличьте шаг.")
            self.xs = [p["x0"]+i*p["dx"] for i in range(n)]
            self.ys = [p["a1"]*math.sin(p["b1"]*x)+p["a2"]*math.sin(p["b2"]*x)+
                       p["a3"]*math.sin(p["b3"]*x) for x in self.xs]
            self.table.delete(*self.table.get_children())
            for x,y in zip(self.xs,self.ys):
                self.table.insert("","end",values=(f"{x:.8g}",f"{y:.8g}"))
            self.draw()
            self.status.config(text=f"Рассчитано точек: {n}")
        except ValueError as e:
            messagebox.showerror("Ошибка ввода",str(e))

    def draw(self):
        c=self.canvas; c.delete("all")
        w=max(c.winfo_width(),300); h=max(c.winfo_height(),250)
        l,r,t,b=55,w-20,20,h-40
        if not self.xs:
            c.create_text(w/2,h/2,text="График появится после расчёта"); return
        xmin,xmax=min(self.xs),max(self.xs); ymin,ymax=min(self.ys),max(self.ys)
        if math.isclose(xmin,xmax): xmin-=.5; xmax+=.5
        if math.isclose(ymin,ymax): ymin-=.5; ymax+=.5
        margin=(ymax-ymin)*.08; ymin-=margin; ymax+=margin
        X=lambda x:l+(x-xmin)/(xmax-xmin)*(r-l)
        Y=lambda y:b-(y-ymin)/(ymax-ymin)*(b-t)
        for i in range(6):
            x=xmin+(xmax-xmin)*i/5; xx=X(x)
            c.create_line(xx,t,xx,b,fill="#ddd"); c.create_text(xx,b+15,text=f"{x:.3g}")
            y=ymin+(ymax-ymin)*i/5; yy=Y(y)
            c.create_line(l,yy,r,yy,fill="#ddd"); c.create_text(l-7,yy,text=f"{y:.3g}",anchor="e")
        c.create_line(l,t,l,b,fill="black"); c.create_line(l,b,r,b,fill="black")
        c.create_text((l+r)/2,h-8,text="x"); c.create_text(14,t,text="y")
        pts=[]
        for x,y in zip(self.xs,self.ys): pts.extend((X(x),Y(y)))
        if len(pts)>=4: c.create_line(*pts,fill="#1769aa",width=2)

    def resize(self,event):
        if event.widget==self.root and self.xs: self.draw()

    def save_svg(self):
        if not self.xs:
            messagebox.showinfo("Нет данных","Сначала выполните расчёт."); return
        name=filedialog.asksaveasfilename(defaultextension=".svg",filetypes=[("SVG","*.svg")])
        if not name: return
        width,height=900,500; left,right,top,bottom=70,870,30,450
        xmin,xmax=min(self.xs),max(self.xs); ymin,ymax=min(self.ys),max(self.ys)
        if math.isclose(xmin,xmax): xmin-=.5; xmax+=.5
        if math.isclose(ymin,ymax): ymin-=.5; ymax+=.5
        margin=(ymax-ymin)*.08; ymin-=margin; ymax+=margin
        sx=lambda x:left+(x-xmin)/(xmax-xmin)*(right-left)
        sy=lambda y:bottom-(y-ymin)/(ymax-ymin)*(bottom-top)
        points=" ".join(f"{sx(x):.2f},{sy(y):.2f}" for x,y in zip(self.xs,self.ys))
        svg=f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="white"/>
<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="black"/>
<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="black"/>
<polyline points="{points}" fill="none" stroke="#1769aa" stroke-width="2"/>
<text x="470" y="485" text-anchor="middle" font-family="sans-serif" font-size="14">x</text>
<text x="20" y="25" font-family="sans-serif" font-size="14">y</text></svg>"""
        try:
            Path(name).write_text(svg,encoding="utf-8")
            messagebox.showinfo("Готово",f"График сохранён:\n{name}")
        except OSError as e: messagebox.showerror("Ошибка сохранения",str(e))

if __name__=="__main__":
    root=tk.Tk(); App(root); root.mainloop()
