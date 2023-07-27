皮の派派录像分析工具——Analyzer for Apex Legends beta0.31
经过jerryc05的拷打，代码相比第一版舒服不少了已经（bushi
可以通过Apex录像了解您的表现
目前已经实现了记录开火时刻与xml剪辑表输出（尽管伤害识别那么没准确（在调了在调了……
开发用源素材分辨率1920*1080,60p，目前支持1920*1080与2560*1600分辨率

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
3. python user.py "You APEX Video File" 或在根目录新建input_videos.txt，输入需要解析的视频地址
4. 运行xml_maker.py
5. 启动剪辑软件（如Premiere），将Outputs文件夹下的"main_comp.xml"与"subtitle.srt"文件导入剪辑软件，即可得到剪辑序列