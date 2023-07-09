皮の派派录像分析工具——Analyzer for Apex Legends beta0.21
经过jerryc05的拷打，代码相比第一版舒服不少了已经（bushi
可以通过Apex录像了解您的表现
目前已经实现了记录开火时刻与xml剪辑表输出（尽管伤害识别那么没准确（在调了在调了……
开发用源素材分辨率1920*1080,60p，目前支持1920*1080与2560*1600分辨率


2023.07.09 Upd 0.21:
改进伤害识别算法，不需要装tesseract插件了


2023.07.06 Upd 0.2:
可以使用xml_maker输出剪辑表
优化了部分文件存储
新增2K 16:10分辨率支持
debuging:尝试摆脱tesseract的依赖

文件介绍
ammo_ocr: 弹药量识别文件
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
3. python user.py "You APEX Video File"
4. 运行xml_maker.py
5. 启动剪辑软件（如Premiere），将Outputs文件夹下的"main_comp.xml"与"subtitle.srt"文件导入剪辑软件，即可得到剪辑序列