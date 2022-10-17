import os
import sys



while True:
    
    filePath = input(".2HDファイルのパスを入力 : ")
    #filePath="C:\\Users\\ab324\\Downloads\\[PC98][え][エルフ] 同級生2 [D88]\\EDOS5_1.2HD"#2HDファイル

    fileDirec = os.path.split(filePath)
    filename , ext= os.path.splitext(os.path.basename(filePath))

    if os.path.exists(fileDirec[0]+'\\'+filename+'.2HD') and os.path.exists(fileDirec[0]+'\\'+filename+'.DAT'):#ファイルの存在確認
        pass
    else:
        print("エラー：同じ階層に同名の.2HDと.DATファイルの双方が必要です。")
        sys.exit()

    now = 0x00
    Syoryaku = 0
    SyoryakuAddrs=[]
    SyoryakuBytes=[]

    with open (filePath,"rb") as f:

        f.seek(now+0x0a)
        now = now+0x0a
        DiskInfo = f.read(3)
        print("トラック数："+str(DiskInfo[0]))
        print("セクタ数："+str(DiskInfo[1]))
        print("不明なパラメータ："+str(DiskInfo[2]))        
        
        f.seek(now+0x05)
        now = now+0x05
        nowbyte = 0

        try:

            while True:
                print_log=False


                for i in range(DiskInfo[1]):
                    
                    Data = f.read(8)
                    C_number=Data[0]
                    H_number=Data[1]
                    S_number=Data[2]
                    S_size1=Data[3]
                    S_size2=Data[4]
                    
                    if S_size1==S_size2:
                        if S_size1==0:
                            S_size_str="128 Byte"
                            S_size=128
                        elif S_size1==1:
                            S_size_str="256 Byte"
                            S_size=256
                        elif S_size1==2:
                            S_size_str="512 Byte"
                            S_size=512
                        elif S_size1==3:
                            S_size_str="1024 Byte"
                            S_size=1024
                        else:
                            S_size_str="Unknown sector size | num="+str(S_size1)
                    else:
                        S_size_str="Unknown sector size | not matched 1&2 1="+str(S_size1)+" 2="+str(S_size2)

                        

                    nowbyte = nowbyte+S_size #現在位置
                    
                    if Data[6]==1:
                        ImageText="【省略セクタ　"+S_size_str+"】 "#データ削除あり。もしRAW化機能つけるなら、00データを1セクタ分埋める。(1024byteなど)
                        Syoryaku = Syoryaku + 1
                        SyoryakuAddrs.append(hex(nowbyte))
                        SyoryakuBytes.append(S_size)
                    elif Data[6]==0:
                        ImageText=""#データ削除なし。
                    elif Data[6]==Data[2]:
                        pass#最終セクタはこうなってるのでよし。
                        break
                    else:
                        print(" Unknown data delete option | num="+str(Data[6]))

                        
                    if Data[7]==0:
                        pass
                    elif Data[7]==0xe5:
                        ImageText=ImageText+"【未フォーマット】"
                    else:
                        ImageText=ImageText+" Unknown data format  | num="+str(Data[7])
                    
                    now = now+0x08
                    
                    if print_log:
                        print(str(hex(nowbyte))+"  C:"+str(C_number)+"  H:"+str(H_number)+" S:"+str(S_number)+" "+S_size_str+" "+ImageText)
                
                now = now+0x08
                AddData=f.read(2)

                if AddData[0]==1:
                    ImageText="【省略セクタ　"+S_size_str+"】 "#データ削除あり。もしRAW化機能つけるなら、00データを1セクタ分埋める。(1024byteなど)
                    Syoryaku = Syoryaku + 1
                    SyoryakuAddrs.append(hex(nowbyte))
                    SyoryakuBytes.append(S_size)
                elif AddData[0]==0:
                    pass#データ削除なし。
                else:
                    print("Unknown data delete option | num="+str(AddData[0]))
                if AddData[1]==0:
                    pass
                elif AddData[1]==0xe5:
                    ImageText=ImageText+"【未フォーマット】"
                else:
                    print("Unknown data format  | num="+str(AddData[1]))

                f.seek(now+0x02)
                now=now+0x02
                
        except IndexError:
            print("\n\n==========変換が正常に終了しました。==========\n省略セクタ数："+str(Syoryaku))

    openfilepath=fileDirec[0]+'\\'+filename+'.DAT'

    with open(openfilepath,'rb')as g:

        result=g.read()
        for Addrs in SyoryakuAddrs:
            list_num = SyoryakuAddrs.index(Addrs)
            
            FileContentBefore = result[:int(Addrs, 16)]
            FileContentAfter = result[int(Addrs, 16):]
            ZeroFillBytes = SyoryakuBytes[list_num]
            write_zero = b'\x00'*ZeroFillBytes
            result = FileContentBefore+write_zero+FileContentAfter
    with open(fileDirec[0]+'\\'+filename+'.img',"wb") as h:
        h.write(result)
    print("\n\n==========書き込みが正常に終了しました。==========\n")
            
    #未フォーマットのとこ、指定あるっぽい
    #それいがいはOKかな

