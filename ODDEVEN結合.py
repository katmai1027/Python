
import os
import sys
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
prog_ver="0.1"
comment="ODD,EVENのROMを結合"

def pexit():
    sys.exit()
def deldel():
    IFileEntry.delete(0, END)

def filedialog_clicked2():
    global filename
    
    iFile = os.path.abspath(os.path.dirname(__file__))
    #iFilePath = filedialog.askopenfilename(filetype = fTyp, initialdir = iFile)
    iFilePath = filedialog.askopenfilename(title="奇数アドレスのROMイメージファイルを開く", initialdir = iFile)
    filename , ext= os.path.splitext(os.path.basename(iFilePath))
    entry2.set(iFilePath)

def filedialog_clicked3():
    global filename

    iFile = os.path.abspath(os.path.dirname(__file__))
    #iFilePath = filedialog.askopenfilename(filetype = fTyp, initialdir = iFile)
    iFilePath = filedialog.askopenfilename(title="偶数アドレスのROMのイメージファイルを開く", initialdir = iFile)
    filename , ext= os.path.splitext(os.path.basename(iFilePath))
    entry3.set(iFilePath)




def conductMain():
    #偶数奇数それぞれのデータを読み出し
    filePathODD = entry2.get()
    ODDFilename = os.path.splitext(os.path.basename(filePathODD))[0]
    odd = open(filePathODD,"rb")
    
    filePathEVEN =entry3.get()
    EVENFilename = os.path.splitext(os.path.basename(filePathEVEN))[0]
    even = open(filePathEVEN,"rb")

    #ファイルサイズは等しいか？
    ODDsize = os.path.getsize(filePathODD)
    EVENsize = os.path.getsize(filePathEVEN)
    if not ODDsize==EVENsize:
        messagebox.showerror("エラー", "奇数/偶数ファイルのサイズが一致しません ODD : "+str(ODDsize)+" Bytes / EVEN : "+EVENsize+" Bytes")
        return
    try:
        oFile = os.path.abspath(os.path.dirname(__file__))
        oFilePath = filedialog.askdirectory(title="出力先の指定", initialdir = oFile)
        if oFilePath=="":
            print("canceled")
            
        savepath=oFilePath+"/"+ODDFilename+"+"+EVENFilename
        result = open(savepath,"ab")

    except BaseException as e:
        messagebox.showerror("エラー", "出力先ファイルのオープンに失敗しました\nERROR CODE: %s\n詳細: %s"%(e.args[0],e.args[1]))
    
    try:
        count=0
        print(ODDsize)
        for count in range(ODDsize):
            #ODDが先、EVENが後
                 
            odd.seek(count)
            DataODD = odd.read(1)
            result.write(DataODD)
            even.seek(count)
            DataEVEN = even.read(1)
            result.write(DataEVEN)    
    except:
        print("finish"+str(count*2)+"Bytes")
    messagebox.showinfo("成功", "ファイルの結合に成功しました。("+str(ODDsize*2)+" Bytes)")

if __name__ == "__main__":

    # rootの作成
    root = Tk()
    root.title("偶数奇数ROM結合er")
    root.geometry("340x150")
    

    # Frame2の作成
    frame2 = ttk.Frame(root, padding=10)
    frame2.grid(row=2, column=1, sticky=E)

    # 「ファイル参照」ラベルの作成
    IFileLabel = ttk.Label(frame2, text="奇数", padding=(5, 2))
    IFileLabel.pack(side=LEFT)

    # 「ファイル参照」エントリーの作成
    entry2 = StringVar()
    IFileEntry = ttk.Entry(frame2, textvariable=entry2, width=30)
    IFileEntry.pack(side=LEFT)

    # 「ファイル参照」ボタンの作成
    

    IFileButton = ttk.Button(frame2, text="参照", width=7 ,command=filedialog_clicked2)
    IFileButton.pack(side=LEFT)
    
    # Frame3の作成
    frame3 = ttk.Frame(root, padding=10,height=50)
    frame3.grid(row=4,column=1,sticky=W)
    IFileLabel = ttk.Label(frame3, text="偶数", padding=(5, 2))
    IFileLabel.pack(side=LEFT)
    entry3 = StringVar()
    IFileEntry = ttk.Entry(frame3, textvariable=entry3, width=30)
    IFileEntry.pack(side=LEFT)

    # 「ファイル参照」ボタンの作成
    

    IFileButton = ttk.Button(frame3, text="参照", width=7 ,command=filedialog_clicked3)
    IFileButton.pack(side=LEFT)
    


    # Frame5の作成
    frame5 = ttk.Frame(root, padding=10)
    frame5.grid(row=28,column=1,sticky=W)
    # 実行ボタンの設置
    button1 = ttk.Button(frame5, text="開始", command=conductMain)
    button1.pack(fill = "x", padx=30, side = "left")
    # 終了ボタンの設置
    button2 = ttk.Button(frame5, text=("終了"), command=pexit)
    button2.pack(fill = "x", padx=30, side = "left")
    
