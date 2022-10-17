import os
import sys
import json
import time
import shutil
import PIL.Image    #Add(pillow)
import PIL.ImageFont
import PIL.ImageDraw
import zipfile
import pygame  #Add(pygame)

from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

#必要ファイル＝button_.png、Emaker_model.mqo、Emaker_texture.png
#ogg必須化もしくは変換
#fileをaskでキャンセルされた時の動作。
#書き出し時ファイル見つからないとき
#.remと上に表示されるバグ
prog_ver="0.2"
comment="音声ファイルはoggのみ。"
wspace=None
ws_dict={}#メインの辞書かなぁ～

def play_ogg():
    global lb
    global ws_dict
    try:
        pygame.mixer.music.stop()               # もし再生中なら、終了
    except:
        pass
    try:
        file_name = list(ws_dict[lb.get(lb.curselection()[0], last=None)])[0]
    except:
        return
    pygame.mixer.init(frequency = 44100)    # 初期設定
    pygame.mixer.music.load(file_name)     # 音楽ファイルの読み込み
    pygame.mixer.music.play(1)              # 音楽の再生回数(1回)
    
    
    return 0
def pexit():#終了、が押された
    sys.exit()
    
def deldel():#ばつボタン押された
    IFileEntry3.delete(0, END)
    
def image_edit(block_name,block_id):
    global Image
    if True:
        image_path = 'button_'  #プログラムの直下に置くかな
        font_path = 'C:/Windows/Fonts/meiryo.ttc';
        font_size = 15 #文字の大きさ
        text = block_name
        color = (0,0,0)#文字の色
     
        image = PIL.Image.open(image_path+".png")
        font = PIL.ImageFont.truetype(font_path,font_size)#フォントの指定
        draw = PIL.ImageDraw.Draw(image)
        draw.text((7,4),text,font=font,fill=color)
        image.save(image_path+block_id+".png")
        return image_path+block_id+".png"
    """except:
        messagebox.showerror("error", "サムネイル画像の編集に失敗しました。\nbottun_.pngはありますか？")
        return"""
    
def listbox_del():#削除ボタン押された
    global lb
    global ws_dict
    try:
        del ws_dict[lb.get(lb.curselection()[0], last=None)]
        lb.delete(lb.curselection()[0])
    except:
        messagebox.showerror("error", "要素が選択されていません。")
def open_file():#開く、を押された
    global wspace
    global lb
    global ws_dict
    iFile = os.path.abspath(os.path.dirname(__file__))
    #iFilePath = filedialog.askopenfilename(filetype = fTyp, initialdir = iFile)
    filetypes = (
        ('Project file', '*.rem'),
        ('All files', '*.*')
    )
    wspace = filedialog.askopenfilename(title="プロジェクトを開く",filetype =filetypes, initialdir = iFile)
    if wspace=="":
        return
    for widget in frame1.winfo_children():#上のとこのPath
       widget.destroy()
    for widget in frame4.winfo_children():#listbox全削除
       widget.destroy()
    setumei = ttk.Label(frame1, text="<"+wspace+">", padding=(5, 2))
    setumei.pack(side=LEFT)
    json_open = open(wspace, 'r+',encoding="utf-8_sig")#json開く
    json_load = json.load(json_open)

    ws_dict = dict(json_load)#メイン辞書
    print(ws_dict)
    
    v = StringVar(value=list(json_load.keys()))
    lb = Listbox(frame4, bd=5, relief="groove",listvariable=v, selectmode="SINGLE", width=55)
    lb.bind(
        '<<ListboxSelect>>',
        lambda e: deldel())
    lb.grid(row=0, column=0)
    lb.select_set(0)
def save_file_over():#上書き保存
    global wspace
    global ws_dict
    if wspace is None:
        save_file_new()
    else:
        sd = json.dumps(ws_dict)
        try:
            with open(wspace,"w")as f:
                f.write(sd)

        except:
            messagebox.showerror("error", "保存に失敗しました。")
            return
def save_file_new():#新規保存
    global wspace
    global ws_dict
    sd = json.dumps(ws_dict)
    write_file_path = filedialog.asksaveasfilename(title = "名前を付けて保存",filetypes =  [("Project file","*.rem")])+".rem"
    if write_file_path==".rem":
        return
    try:
        with open(write_file_path,"w")as f:
            f.write(sd)
    except:
        messagebox.showerror("error", "保存に失敗しました。")
        return
    wspace = write_file_path
    for widget in frame1.winfo_children():#上のとこのPath
       widget.destroy()
    setumei = ttk.Label(frame1, text="<"+wspace+">", padding=(5, 2))
    setumei.pack(side=LEFT)
    
def make_file():#書き出し。
    try:
        make_path = filedialog.asksaveasfilename(title = "RTM用に出力",filetypes =  [("Zip file","*.zip")])+".zip"#保存先
        if make_path=="":
            return
        save_dir = os.path.split(make_path)[0]              #ディレクトリまでを取得。
        save_name = os.path.split(make_path)[1]
        sound_direc = str(int(time.time()))
        os.makedirs(save_dir+"/temp_RTM_Emaker/mods/RTM/Machine", exist_ok=True)             #ディレクトリ作成
        os.makedirs(save_dir+"/temp_RTM_Emaker/assets/minecraft/models/machine", exist_ok=True)
        os.makedirs(save_dir+"/temp_RTM_Emaker/assets/minecraft/textures/machine", exist_ok=True)
        os.makedirs(save_dir+"/temp_RTM_Emaker/assets/sound_"+sound_direc+"/sounds", exist_ok=True)
        
        #
        shutil.copy2("Emaker_model.mqo", save_dir+"/temp_RTM_Emaker/assets/minecraft/models/machine/")#/assets/minecraft/models/machine/にEmaker_model.mqoモデルをコピペ
        shutil.copy2("Emaker_texture.png", save_dir+"/temp_RTM_Emaker/assets/minecraft/textures/machine/")#/aasets/minecraft/textures/machine内にブロック用アイコンコピペ
        with open(save_dir+'/temp_RTM_Emaker/assets/sound_'+sound_direc+'/sounds.json','w') as f:
            f.write("{}")
        for block in ws_dict.keys():#ここからは音声の数だけfor回す。 ブロックの日本語名はblock
            block_info_list = list(ws_dict[block])#　0は音声ファイル場所、1はID
            try:
                shutil.copy2(block_info_list[0], save_dir+"/temp_RTM_Emaker/assets/sound_"+sound_direc+"/sounds")#音声ファイルをコピー（存在しないならエラーでファイル尋ねる。）
            except:
                messagebox.showerror("error", block_info_list[0]+"\nが見つからないか、アクセスできません。")
                messagebox.showerror("error", "出力に失敗しました。")
                return
            result1 = image_edit(block,block_info_list[1])#サムネ写真作成
            shutil.move(result1, save_dir+"/temp_RTM_Emaker/assets/minecraft/textures/machine/")#サムネ写真コピー
            #oggを/assets/sound_KATMAI/sounds/にコピー
            with open(save_dir+'/temp_RTM_Emaker/assets/sound_'+sound_direc+'/sounds.json','r') as f:
                df = dict(json.load(f))
            oggpath, oggext = os.path.splitext( os.path.basename(block_info_list[0]) )
            df[block_info_list[1]] = {"category":"neutral","sounds":[ oggpath ]}#/assets/sound_時間/sounds.jsonに書き加える(というよりは、ロードして書き加えて保存)
            with open(save_dir+'/temp_RTM_Emaker/assets/sound_'+sound_direc+'/sounds.json','w') as f:
                json.dump(df, f)

            model_json = {
              "name": "Emaker_"+block_info_list[1],
              "model": {
                "modelFile": "machine/Emaker_model.mqo",
                "textures": [ [ "mat1", "textures/machine/Emaker_texture.png", "AlphaBlend" ] ]
              },
              "buttonTexture": "textures/machine/"+result1,
              "machineType": "Gate",
              "sound_OnAcive": "",
              "sound_Running": "sound_"+sound_direc+":"+oggpath
            }
            with open(save_dir+"/temp_RTM_Emaker/mods/RTM/Machine/ModelMachine_Emaker_"+block_info_list[1]+".json","w") as f:
                json.dump(model_json, f)                #/mods/RTM/Machine/にjson作成、記入

        #shutil.make_archive(save_name , format='zip', root_dir=save_dir+"/temp_RTM_Emaker") #zipにする
        zipfilepointer=zipfile.ZipFile(make_path,"w",zipfile.ZIP_STORED)
        cwd = os.getcwd()
        os.chdir(save_dir+"/temp_RTM_Emaker")
        dirs=["mods","assets"]
        for dir in dirs:
            for dirname, subdirs, filenames in os.walk(dir):
                for fname in filenames:
                    zipfilepointer.write(os.path.join(dirname, fname))

        zipfilepointer.close()
        
        os.chdir(cwd)
        shutil.rmtree(save_dir+"/temp_RTM_Emaker") #一時フォルダを削除
        messagebox.showinfo("Success", "書き出しに成功しました。")

    except:
        messagebox.showerror("error", "書き出し時の一般エラーです。\n書き出す先の権限・フォルダの存在等を確認してください。")
        messagebox.showerror("error", "出力に失敗しました。")
        return


def filedialog_clicked():#ファイルの参照ボタンクリック時
    global filename
    iFile = os.path.abspath(os.path.dirname(__file__))
    #iFilePath = filedialog.askopenfilename(filetype = fTyp, initialdir = iFile)
    iFilePath = filedialog.askopenfilename(title="音声ファイルを開く", initialdir = iFile,filetypes =  [("Music file","*.ogg")])
    filename , ext= os.path.splitext(os.path.basename(iFilePath))
    entry3.set(iFilePath)
    
def conductMain():#追加ボタン押された
    global filename
    global wspace
    global lb
    global ws_dict
    print(wspace)
    modelName = entry2.get()+"\n　"+entry6.get()
    filePath = entry3.get()
    
    IFileEntry2.delete(0, END)
    IFileEntry3.delete(0, END)
    IFileEntry6.delete(0, END)
    #lb.insert(END, "c")#最終行に要素をついか。
    try:
        print(lb.get(lb.curselection()[0], last=None))  #これでどれが選択されてるかわかる
    except:
        print("要素未選択")
    if filePath:
        if modelName:
            if modelName in ws_dict:#すでにある要素を入れた場合
                messagebox.showerror("error", modelName+" は既に存在します。")
            else:
                list_temp =[filePath,"kat_"+str(int(time.time()*1000))]#一時的なlist

                ws_dict[modelName]=list_temp#辞書に要素をついか
                print(ws_dict)
                lb.insert(END, modelName)#最終行に要素をついか。
                


        else:
            messagebox.showerror("error", "名前の指定がありません。")
    else:
        messagebox.showerror("error", "音声のパスの指定がありません。")
        


    
   
if __name__ == "__main__":

 
    # rootの作成
    root = Tk()
    root.title("RTM駅メロMaker "+prog_ver)
    root.geometry("370x420")

    men = Menu(root)#メニューバー作成
    root.config(menu=men)
    menu_file = Menu(root,tearoff=False) 
    men.add_cascade(label='ファイル', menu=menu_file) 

    # Frame1の作成
    frame1 = ttk.Frame(root, padding=10)
    frame1.grid(row=0, column=1, sticky=W)
    setumei = ttk.Label(frame1, text="<新規>", padding=(5, 2))
    setumei.pack(side=LEFT)

    #親メニューに子メニュー（開く・閉じる）を追加する 
    menu_file.add_command(label='開く', command=open_file)
    menu_file.add_command(label='上書き保存', command=save_file_over)
    menu_file.add_command(label='名前を付けて保存', command=save_file_new)
    menu_file.add_command(label='RTM用に出力', command=make_file)
    #menu_file.add_separator() 
    #menu_file.add_command(label='終了', command=pexit)

    

    # Frame4の作成
    
    frame4 = ttk.Frame(root, padding=10)
    frame4.grid(row=1 ,column=1, sticky=W)

    v = StringVar(value=[])
    lb = Listbox(frame4, bd=5, relief="groove",listvariable=v, selectmode="SINGLE",height=10, width=55)
    lb.bind(
        '<<ListboxSelect>>',
        lambda e: deldel())
    lb.grid(row=0, column=0)
    lb.select_set(0)
    ybar = Scrollbar(frame4, orient=VERTICAL,)
    ybar.grid(row=0, column=1, sticky=N + S)
    ybar.config(command=lb.yview)
    lb.config(yscrollcommand=ybar.set)
    
    # Frame2の作成
    
    frame2 = ttk.Frame(root, padding=10)
    frame2.grid(row=15 ,column=1, sticky=W)

    IFileLabel2 = ttk.Label(frame2, text="社名/駅名など", padding=(5, 2))# 名前ラベルの作成
    IFileLabel2.pack(side=LEFT)
    
    entry2 = StringVar()
    IFileEntry2 = ttk.Entry(frame2, font=("meiryo","7"),textvariable=entry2, width=22)#名前エントリーの作成
    IFileEntry2.pack(side=LEFT)
    IFileLabel21 = ttk.Label(frame2, text="※枠内に収める(省略可)", padding=(5, 2))# 名前ラベルの作成
    IFileLabel21.pack(side=LEFT)
    
    frame6 = ttk.Frame(root, padding=10)
    frame6.grid(row=19 ,column=1, sticky=W)

    IFileLabel6 = ttk.Label(frame6, text="名前", padding=(5, 2))# 名前ラベルの作成
    IFileLabel6.pack(side=LEFT)
    
    entry6 = StringVar()
    IFileEntry6 = ttk.Entry(frame6, font=("meiryo","7"),textvariable=entry6, width=26)#名前エントリーの作成
    IFileEntry6.pack(side=LEFT)
    IFileLabel61 = ttk.Label(frame6, text="※枠内に収める", padding=(5, 2))# 名前ラベルの作成
    IFileLabel61.pack(side=LEFT)    


     # Frame3の作成
    frame3 = ttk.Frame(root, padding=10)
    frame3.grid(row=20, column=1, sticky=W)

    # 「ファイル参照」ラベルの作成
    IFileLabel3 = ttk.Label(frame3, text="音声ファイル", padding=(5, 2))
    IFileLabel3.pack(side=LEFT)

    # 「ファイル参照」エントリーの作成
    entry3 = StringVar()
    IFileEntry3 = ttk.Entry(frame3, textvariable=entry3, width=30)
    IFileEntry3.pack(side=LEFT)

    # 「ファイル参照」ボタンの作成
    
    IFileButton = ttk.Button(frame3, text="×", width=0 ,command=deldel)
    IFileButton.pack(side=LEFT)
    IFileButton = ttk.Button(frame3, text="参照", width=7 ,command=filedialog_clicked)
    IFileButton.pack(side=LEFT)


    # Frame5の作成
    frame5 = ttk.Frame(root, padding=10)
    frame5.grid(row=30,column=1,sticky=W)


    button1 = ttk.Button(frame5, text="追加", command=conductMain)
    button1.pack(fill = "x", padx=20, side = "left")

    button2 = ttk.Button(frame5, text=("削除"), command=listbox_del)
    button2.pack(fill = "x", padx=20, side = "left")
    
    button3 = ttk.Button(frame5, text=("再生"), command=play_ogg)
    button3.pack(fill = "x", padx=20, side = "left")
    
    

    
    root.mainloop()
