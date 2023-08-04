皮の派派录像分析工具——Analyzer for Apex Legends beta0.40
经过jerryc05的拷打，代码相比第一版舒服不少了已经（bushi
可以通过Apex录像了解您的表现
目前已经实现了记录开火时刻与xml剪辑表输出（尽管伤害识别那么没准确（在调了在调了……
开发用源素材分辨率1920*1080,60p，目前支持1920*1080与2560*1600分辨率


2023.08.04 Upd 0.40:
为了解决打派群众日益增长的素材量和速度欠佳的分析程序的矛盾，547终于把咕了很久的多进程算法更新奉上！
1.新增多进程读取功能，再也不用担心跑程序不卡顿了（doge）(具体效果因设备而异)
2.将剪辑表生成工具集成到主程序，可以用user.py -c调用


2023.08.02 Upd 0.33:
1.更新片段读取功能————对指定了开始结束帧的视频，只读取对应区间


2023.08.01 Upd 0.32:
1.更新一些研究用文件(dev_开头)，与算法正常操作无关（目前来说，将来呢？）
2.修改OCR的部分参数，争取更准一点
3.修改weapon_dict部分数据（快S18了才想起来，有愧于三重人柱力dsr
4.优化一枪一剪的片段选取逻辑，将优先选取击中的片段
known issues:
1.OCR准确率还是不够（验证集84错4（以前是错6（zddsr，尝试一些奇奇怪怪的方法修正下，比如筛选离谱的数据发挥工人智能让用户看图填数（bushi
2.读视频的算法感觉还可以再优化一点（用了办公本这个问题越发明显
3.不要在意dev文件的errors，本来打算全部ignore掉的dsr


2023.07.26 Upd 0.31:
1.对OBS录坏的文件尝试片段读取
2.bug fixes


2023.07.12 Upd 0.3:
1.移除全片伤害采样环节，只在开火时识别首尾伤害
2.暂时停用了伤害矫正算法，解决错误蔓延的问题
3.优化了数字'6''8''9'判定算法
4.改善了状态识别算法，当倒地前开火时也能被正确记录
5.优化了模板匹配算法
6.优化了视频输入逻辑
7.新增了调取伤害记录画面的功能，可用来手动修正报表与开发参考
known issues:
1.部分视频可能因为关键帧缺失，会报'co lacated POCs unavailable'，导致不能遍历完整视频，不能存储报表的问题
2.最少化了伤害采样频次，可能会有意想不到的反馈


2023.07.09 Upd 0.21:
改进伤害识别算法，不需要装tesseract插件了


2023.07.06 Upd 0.2:
可以使用xml_maker输出剪辑表
优化了部分文件存储
新增2K 16:10分辨率支持
debuging:尝试摆脱tesseract的依赖

文件介绍
ammo_ocr: 弹药量识别文件
bullet_capture: 一发一剪解析程序
chart_analyze: 分析从视频读出的数据（默认Temp\readdata_original.feather），生成数据报表（默认在Temp\EventChart.xlsx与Temp\firing_list.feather，同时可以将开火记录累积到BigData\BigData_FiringList.xlsx）
damage_ocr: 伤害数字识别，目前需要手动确定该视频来自匹配还是排位（懒dsr）
（注：需要手动定位Tesseract-OCR文件位置）
func_cv_imread、func_cv_imwrite、func_imgproc: 中间用函数
user: 用户使用请走此路
user_feather2xlsx: 将过程生成的feather文件转成xlsx以便用户自查
video_ocr_read_opencv: 视频读取，输出原始识别数据（默认输出到Temp\ReadData_Original.xlsx）
weapon_dict: 武器字典（Season 17, 简中）
weapon_recognize: 武器识别文件
xml_maker: 剪辑表自动生成

使用方法
1. 打开cmd定位到程序文件夹根目录
2. pip install -r "requirements.txt"
3. 输入需要解析的视频地址(详见Inputs)
4. 输入python user.py -c r/b（r:一梭子一剪，b:一枪一剪） '风格(r, eg. 'cool')/武器(b,支持正则化表达式, eg. '猎兽')'
5. 启动剪辑软件（如Premiere），将Outputs文件夹下的"main_comp.xml"与"subtitle.srt"文件导入剪辑软件，即可得到剪辑序列

Inputs
方法一：cmd定位根目录，键入python user.py -a '视频地址' 开始帧（可选） 结束帧（可选）     例>python user.py -a 'D:/Videos/2023-01-01 Apex Legends.mp4' 10000 20000
方法二：在根目录新建input_videos.txt， 一行输入一条视频，如指定首末帧用逗号隔开。格式如: 视频地址, 开始帧（可选）, 结束帧（可选）   例>D:/Videos/2023-01-01 Apex Legends.mp4, 10000, 20000
