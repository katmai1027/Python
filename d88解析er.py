import os
import sys
#from tkinter import *
#from tkinter import ttk
#from tkinter import messagebox
#from tkinter import filedialog

prog_ver="0.1"
comment=".d88イメージの解析を行います"
"""
def pexit():
    sys.exit()
def deldel():
    IFileEntry.delete(0, END)
# ファイル指定の関数
def filedialog_clicked():
    global filename
    #fTyp = [("", "FDI"),("", "fdi"),("", "NFD"),("", "nfd"),("", "FIM"),("", "fim"),("", "DCU"),("", "dcu"),("", "DCP"),("", "dcp"),("", "DIP"),("", "dip"),("", "FDD"),("", "fdd"),]

    iFile = os.path.abspath(os.path.dirname(__file__))
    #iFilePath = filedialog.askopenfilename(filetype = fTyp, initialdir = iFile)
    iFilePath = filedialog.askopenfilename(title="d88イメージファイルを開く", initialdir = iFile)
    filename , ext= os.path.splitext(os.path.basename(iFilePath))
    entry2.set(iFilePath)
    
"""
def conductMain():
    #filePath = entry2.get()
    filePath = input(".d88ファイルのパスを入力 >").replace("\"","")
    if filePath:
        filesize=os.path.getsize(filePath)
        filename = os.path.splitext(os.path.basename(filePath))[0] #ファイルの名前のみ
        fileext = os.path.splitext(os.path.basename(filePath))[1].replace(" ","")#拡張子
        if fileext==".d88" or fileext==".D88":
            
            with open (filePath,"rb") as f:
                
                fileseek=0
                headerseek=0
                try:
                    datanew=0
                    filecnt=0
                    while True:
                        f.seek(datanew+0x1c)
                        data=f.read(4)
                        datasize = int(data[0])+int(data[1])*256+int(data[2])*256*256+int(data[3])*256*256*256
                        
                        filecnt = filecnt+1
                        
                        datanew=datanew+datasize
                        #ﾃﾞｨｽｸの名前
                        f.seek(headerseek)
                        data=f.read(16)
                        
                        try:
                            diskname= data.decode()
                        except:
                            diskname=str(data)
                        #ライトプロテクト
                        f.seek(headerseek+0x1a)
                        data=f.read(1)
                        if data[0]==00:#0x00
                            writeprotect="なし"
                        elif data[0]==16:#0x10
                            writeprotect="あり"
                        else:
                            writeprotect="ERROR "+hex(data[0])
                        #メディアの種類
                        f.seek(headerseek+0x1b)
                        data=f.read(1)
                        if data[0]==32:#0x20
                            mediatype="2HD"
                        elif data[0]==16:#0x10
                            mediatype="2DD"
                        elif data[0]==00:#0x00
                            mediatype="2D"
                        else:
                            mediatype="ERROR "+hex(data[0])


                       
                        print("\n------------------------------------\n"+str(filecnt)+" 個目のファイル")
                        print("ディスク名： "+str(diskname))
                        print("書き込み禁止： "+writeprotect)
                        print("メディアタイプ： "+mediatype)


    
                        datastart = 0x2B0
                        myoldplace=[999,999,999,999]
                        try:
                            while True:
                                if fileseek+datastart > datanew:
                                    raise IndexError()
                                f.seek(fileseek+datastart+0x06)
                                #print(hex(fileseek+datastart+0x06))
                                data=f.read(1)  #セクタがFMかMFMか。       あとでflagの場所にする。
                                if data[0]==00:
                                    sec_mitsudo="MFM"
                                elif data[0]==64:
                                    sec_mitsudo="FM "
                                else:
                                    sec_mitsudo="------ERROR-----"+hex(data[0])
                                f.seek(fileseek+datastart+0x04)
                                data=f.read(2)  #セクタの数。
                                sec_count = int(data[0])+int(data[1])*256
                                f.seek(fileseek+datastart)
                                data=f.read(4)  #セクタサイズ読取り
                                myplace = data
                                if myoldplace[0]==myplace[0] and myoldplace[1]==myplace[1]:#一回前のと同じトラック・面なら
                                    f.seek(fileseek+datastart+0x0E)
                                    data=f.read(2)
                                    sector_size = int(data[0])+int(data[1])*256     #セクタサイズ計算
                                    #result= result+" | R:"+str(myplace[2])+"-"+str(sector_size)       #この部分は、詳細表示が必要なときのみ。
                                else:
                                    if myplace[0]==0 and myplace[1]==0:
                                        pass
                                    else:
                                        print(result)#今までのresultを吐き出す。その後新規作成
                                    f.seek(fileseek+datastart+0x0E)
                                    data=f.read(2)
                                    sector_size = int(data[0])+int(data[1])*256     #セクタサイズ計算
                                    if myplace[0]<10:
                                        result = sec_mitsudo+" C:  "+str(myplace[0])+" H: "+str(myplace[1])+" | "+str(sector_size)+" Byte - " +str(sec_count)+" Sectors"
                                    else:
                                        result = sec_mitsudo+" C: "+str(myplace[0])+" H: "+str(myplace[1])+" | "+str(sector_size)+" Byte - " +str(sec_count)+" Sectors"
                            
                                myoldplace = myplace
                        
                        
                                #f.seek(fileseek+datastart+0x10)
                                #data=f.read(sector_size)
                                #書きこみするなら上２行を有効化して、ここに処理入れる。
                                datastart=datastart+16+sector_size
                                #print("datastart: "+str(hex(datastart)))
                        except IndexError:
                             fileseek=datanew-0x10
                             headerseek=datanew
                        except Exception as e:
                            print("-----ERROR----- in dumping data\n"+str(e))
                        
                except IndexError:
                    pass
                except Exception as e:
                    print("-----ERROR----- \n"+str(e))
                print("ファイルの総数は "+str(filecnt)+" 個です。\n")
                print("解析は終了しました。")
                a = input("終了するには何かキーを押して下さい")
                
        else:
            #messagebox.showerror("err",".d88拡張子以外は対応しておりません。")
            print(".d88拡張子以外は対応しておりません。")
                        
    else:
        #messagebox.showerror("error", "パスの指定がありません。")

        print("パスの指定がありません。")
    

if __name__ == "__main__":
    conductMain()
    
    """
    # rootの作成
    root = Tk()
    root.title("d88ファイルの解析")
    root.geometry("340x100")


    # Frame2の作成
    frame2 = ttk.Frame(root, padding=10)
    frame2.grid(row=2, column=1, sticky=E)

    # 「ファイル参照」ラベルの作成
    IFileLabel = ttk.Label(frame2, text="ファイル", padding=(5, 2))
    IFileLabel.pack(side=LEFT)

    # 「ファイル参照」エントリーの作成
    entry2 = StringVar()
    IFileEntry = ttk.Entry(frame2, textvariable=entry2, width=30)
    IFileEntry.pack(side=LEFT)

    # 「ファイル参照」ボタンの作成
    
    IFileButton = ttk.Button(frame2, text="×", width=0 ,command=deldel)
    IFileButton.pack(side=LEFT)
    IFileButton = ttk.Button(frame2, text="参照", width=7 ,command=filedialog_clicked)
    IFileButton.pack(side=LEFT)
    

    frame5 = ttk.Frame(root, padding=10)
    frame5.grid(row=28,column=1,sticky=W)
    # 実行ボタンの設置
    button1 = ttk.Button(frame5, text="開始", command=conductMain)
    button1.pack(fill = "x", padx=30, side = "left")
    # 終了ボタンの設置
    button2 = ttk.Button(frame5, text=("終了"), command=pexit)
    button2.pack(fill = "x", padx=30, side = "left")
    """
    #一部のディスクで読めない。
    #どうして！！！！
    #うんち！！！！！！！！！

