皮のEA风格代码作——Analyzer for Apex Legends beta0.1
可以通过Apex录像了解您的表现
目前已经实现了记录开火时刻与xml剪辑表输出（后期加入）
开发用源素材分辨率1920*1080,60p

请先下载安装Tesseract-OCR与pytesseract，训练好的文件Tesseract traihneddata\num.traineddata，拷贝到 %YourPath%\Tesseract-OCR\tessdata

文件介绍
ammo_ocr: 弹药量识别文件
chart_analyze: 分析从视频读出的数据（默认Temp\ReadData_Original.xlsx），生成数据报表（默认在Temp\EventChart.xlsx与Temp\Firing_List.xlsx，同时可以将开火记录累积到BigData\BigData_FiringList.xlsx）
damage_ocr: 伤害数字识别，目前需要手动确定该视频来自匹配还是排位（懒dsr）
（注：需要手动定位Tesseract-OCR文件位置）
func_cv_imread、func_cv_imwrite、func_imgproc: 中间用函数
user: 用户使用请走此路
video_ocr_read_opencv: 视频读取，输出原始识别数据（默认输出到Temp\ReadData_Original.xlsx）
weapon_dict: 武器字典（Season 17, 简中）
weapon_recognize: 武器识别文件

使用方法
1. 在damage_ocr中修改Tesseract-OCR文件位置
2. 启动user.py