# coding=UTF-8
from lxml import etree as et
from urllib import parse
import pandas as pd
import numpy as np
import weapon_dict
from operator import itemgetter
from pathlib import Path


def frame2time(frame: int, fps=60) -> str:
    second = int(frame / fps)
    minute = int(second / 60)
    hour = int(minute / 60)
    minute %= 60
    second %= 60
    millisecond = int(frame % fps / fps * 1000)
    return str(hour) + ':' + str(minute) + ':' + str(second) + '.' + str(millisecond)


def style_normal(original_list):  # 剔除单发错误、打炸蛛之类的部分
    args = list()
    for i in range(len(original_list)):
        if (
            weapon_dict.weapon_dict[original_list[i, 3]].is_auto == False
            or original_list[i, -2] > 1
        ):
            args.append(i)
    return original_list[args, :]


def style_cook(original_list):  # 马
    args = list()
    for i in range(len(original_list)):
        if original_list[i, -2] > 10 and original_list[i, -1] < 40:  # 10发以上打了40以下
            args.append(i)
        if (
            weapon_dict.weapon_dict[original_list[i, 3]].group == 's'
            and original_list[i, -1] < 20
        ):  # 马喷
            args.append(i)
    return original_list[args, :]


def main(style=None):
    firing_list = pd.read_excel('./BigData/BigData_FiringList.xlsx').values
    if style == 'normal':
        firing_list = style_normal(firing_list)
    if style == 'cook':
        firing_list = style_cook(firing_list)
    MAXVIDS = len(firing_list)
    mtx_clipitem = np.zeros([MAXVIDS, 7], dtype=np.uint32)
    mtx_in = firing_list[:, 1]
    mtx_out = firing_list[:, 2]
    mtx_weapon = firing_list[:, 3]
    mtx_ammo = firing_list[:, 4]
    mtx_damage = firing_list[:, 5]
    mtx_start = np.zeros([MAXVIDS], dtype=np.uint32)
    mtx_end = np.zeros([MAXVIDS], dtype=np.uint32)
    mtx_duration = mtx_out - mtx_in
    mtx_clipitem[0, 0] = 1
    list_masterlip = [0]
    dict_masterclip = dict()
    p_masterclip = 1
    for i in range(MAXVIDS):
        video_name = firing_list[i, 0]
        if not video_name in list_masterlip:
            list_masterlip.append(video_name)
            dict_masterclip[video_name] = p_masterclip
            p_masterclip += 1
        for j in range(7):
            if j:
                mtx_clipitem[i, j] = mtx_clipitem[i, j - 1] + 1
            else:
                mtx_clipitem[i, 0] = mtx_clipitem[i - 1, -1] + 1
        if i:
            mtx_start[i] = mtx_start[i - 1] + mtx_duration[i - 1]
        mtx_end[i] = mtx_duration[i] + mtx_start[i]

    # write srt file
    OUTPUT_DIR = Path('./Output/')
    if not OUTPUT_DIR.exists():
        Path.mkdir()
    srtdata = open(str(OUTPUT_DIR) + '/subtitle.srt', 'w', encoding='utf-8')
    for vidclip_no in range(MAXVIDS):
        print('%d' % (vidclip_no + 1), file=srtdata)
        print(
            '%s --> %s' % (frame2time(mtx_start[vidclip_no]), frame2time(mtx_end[vidclip_no])),
            file=srtdata,
        )
        print(
            '%s%d发打了%d\n'
            % (mtx_weapon[vidclip_no], mtx_ammo[vidclip_no], mtx_damage[vidclip_no]),
            file=srtdata,
        )
    srtdata.close()

    # write xml file
    with open('./Output/main_comp.xml', 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!DOCTYPE xmeml>\n')
        root = et.Element('xmeml', {'version': '4'})
        sequence = et.SubElement(
            root,
            'sequence',
            {
                'id': 'sequence-1',
                'TL.SQAudioVisibleBase': '0',
                'TL.SQVideoVisibleBase': '0',
                'TL.SQVisibleBaseTime': '0',
                'TL.SQAVDividerPosition': '0.5',
                'TL.SQHideShyTracks': '0',
                'TL.SQHeaderWidth': '236',
                'Monitor.ProgramZoomOut': '14216428800000',
                'Monitor.ProgramZoomIn': '0',
                'TL.SQTimePerPixel': '0.19999999999999338',
                'MZ.EditLine': '0',
                'MZ.Sequence.PreviewFrameSizeHeight': '1080',
                'MZ.Sequence.PreviewFrameSizeWidth': '1920',
                'MZ.Sequence.AudioTimeDisplayFormat': '200',
                'MZ.Sequence.VideoTimeDisplayFormat': '108',
                'explodedTracks': 'true',
            },
        )
        sequence_rate = et.SubElement(sequence, 'rate')
        rate_timebase = et.SubElement(sequence_rate, 'timebase')
        rate_timebase.text = '60'
        rate_ntsc = et.SubElement(sequence_rate, 'ntsc')
        rate_ntsc.text = 'FALSE'
        sequence_name = et.SubElement(sequence, 'name')
        sequence_name.text = 'MainComp'
        if style == 'cook':
            sequence_name.text = '唐门盛宴'
        sequence_media = et.SubElement(sequence, 'media')
        media_video = et.SubElement(sequence_media, 'video')
        video_format = et.SubElement(media_video, 'format')
        format_samplecharacteristics = et.SubElement(video_format, 'samplecharacteristics')
        samplecharacteristics_rate = et.SubElement(format_samplecharacteristics, 'rate')

        rate_timebase = et.SubElement(samplecharacteristics_rate, 'timebase')
        rate_timebase.text = '60'
        rate_ntsc = et.SubElement(samplecharacteristics_rate, 'ntsc')
        rate_ntsc.text = 'FALSE'
        samplecharacteristics_codec = et.SubElement(format_samplecharacteristics, 'codec')
        codec_name = et.SubElement(samplecharacteristics_codec, 'name')
        codec_name.text = 'Apple ProRes 422'
        codec_appspecificdata = et.SubElement(samplecharacteristics_codec, 'appspecificdata')
        appspecificdata_appname = et.SubElement(codec_appspecificdata, 'appname')
        appspecificdata_appname.text = 'Final Cut Pro'
        appspecificdata_appmanufacturer = et.SubElement(
            codec_appspecificdata, 'appmanufacturer'
        )
        appspecificdata_appmanufacturer.text = 'Apple Inc.'
        appspecificdata_appversion = et.SubElement(codec_appspecificdata, 'appversion')
        appspecificdata_appversion.text = '7.0'
        appspecificdata_data = et.SubElement(codec_appspecificdata, 'data')
        data_qtcodec = et.SubElement(appspecificdata_data, 'qtcodec')
        qtcodec_codecname = et.SubElement(data_qtcodec, 'codecname')
        qtcodec_codecname.text = 'Apple ProRes 422'
        qtcodec_codectypename = et.SubElement(data_qtcodec, 'codectypename')
        qtcodec_codectypename.text = 'Apple ProRes 422'
        qtcodec_codectypecode = et.SubElement(data_qtcodec, 'codectypecode')
        qtcodec_codectypecode.text = 'apcn'
        qtcodec_codecvendorcode = et.SubElement(data_qtcodec, 'codecvendorcode')
        qtcodec_codecvendorcode.text = 'appl'
        spatialquality = et.SubElement(data_qtcodec, 'spatialquality')
        spatialquality.text = '1024'
        temporalquality = et.SubElement(data_qtcodec, 'temporalquality')
        temporalquality.text = '0'
        keyframerate = et.SubElement(data_qtcodec, 'keyframerate')
        keyframerate.text = '0'
        datarate = et.SubElement(data_qtcodec, 'datarate')
        datarate.text = '0'
        width = et.SubElement(format_samplecharacteristics, 'width')
        width.text = '1920'
        height = et.SubElement(format_samplecharacteristics, 'height')
        height.text = '1080'
        anamorphic = et.SubElement(format_samplecharacteristics, 'anamorphic')
        anamorphic.text = 'FALSE'
        pixelaspectratio = et.SubElement(format_samplecharacteristics, 'pixelaspectratio')
        pixelaspectratio.text = 'square'
        fielddominance = et.SubElement(format_samplecharacteristics, 'fielddominance')
        fielddominance.text = 'none'
        colordepth = et.SubElement(format_samplecharacteristics, 'colordepth')
        colordepth.text = '24'

        track = et.SubElement(
            media_video,
            'track',
            {
                'TL.SQTrackShy': '0',
                'TL.SQTrackExpandedHeight': '25',
                'TL.SQTrackExpanded': '0',
                'MZ.TrackTargeted': '1',
            },
        )

        for vidclip_no in range(MAXVIDS):
            clipitem = et.SubElement(
                track, 'clipitem', {'id': 'clipitem-' + str(mtx_clipitem[vidclip_no, 0])}
            )
            vidname = firing_list[vidclip_no, 0]
            masterclipid = et.SubElement(clipitem, 'masterclipid')
            masterclipid.text = 'masterclip-' + str(dict_masterclip[vidname])
            Vidpath = 'file://localhost/' + vidname
            name = et.SubElement(clipitem, 'name')
            name.text = vidname
            enabled = et.SubElement(clipitem, 'enabled')
            enabled.text = 'TRUE'
            rate = et.SubElement(clipitem, 'rate')
            timebase = et.SubElement(rate, 'timebase')
            timebase.text = '60'
            ntsc = et.SubElement(rate, 'ntsc')
            ntsc.text = 'FALSE'
            start = et.SubElement(clipitem, 'start')
            start.text = str(mtx_start[vidclip_no])
            end = et.SubElement(clipitem, 'end')
            end.text = str(mtx_end[vidclip_no])
            clipitem_in = et.SubElement(clipitem, 'in')
            clipitem_in.text = str(mtx_in[vidclip_no])
            clipitem_out = et.SubElement(clipitem, 'out')
            clipitem_out.text = str(mtx_out[vidclip_no])
            alphatype = et.SubElement(clipitem, 'alphatype')
            alphatype.text = 'none'
            pixelaspectratio = et.SubElement(clipitem, 'pixelaspectratio')
            pixelaspectratio.text = 'square'
            anamorphic = et.SubElement(clipitem, 'anamorphic')
            anamorphic.text = 'FALSE'
            file = et.SubElement(
                clipitem, 'file', {'id': 'file-' + str(dict_masterclip[vidname])}
            )
            # if vidclip_no == 0:
            name = et.SubElement(file, 'name')
            name.text = vidname
            pathurl = et.SubElement(file, 'pathurl')
            pathurl.text = parse.quote(Vidpath)
            media = et.SubElement(file, 'media')
            video = et.SubElement(media, 'video')
            samplecharacteristics = et.SubElement(video, 'samplecharacteristics')
            rate = et.SubElement(samplecharacteristics, 'rate')
            timebase = et.SubElement(rate, 'timebase')
            timebase.text = '60'
            ntsc = et.SubElement(rate, 'ntsc')
            ntsc.text = 'FALSE'
            width = et.SubElement(samplecharacteristics, 'width')
            width.text = '1920'
            height = et.SubElement(samplecharacteristics, 'height')
            height.text = '1080'
            anamorphic = et.SubElement(samplecharacteristics, 'anamorphic')
            anamorphic.text = 'FALSE'
            pixelaspectratio = et.SubElement(samplecharacteristics, 'pixelaspectratio')
            pixelaspectratio.text = 'square'
            fielddominance = et.SubElement(samplecharacteristics, 'fielddominance')
            fielddominance.text = 'none'

            for i in range(2):  # 素材有多条音轨
                audio = et.SubElement(media, 'audio')
                samplecharacteristics = et.SubElement(audio, 'samplecharacteristics')
                depth = et.SubElement(samplecharacteristics, 'depth')
                depth.text = '16'
                samplerate = et.SubElement(samplecharacteristics, 'samplerate')
                samplerate.text = '48000'
                channelcount = et.SubElement(audio, 'channelcount')
                channelcount.text = '2'

            for i in range(5):
                link = et.SubElement(clipitem, 'link')  # 音视频关联
                linkclipref = et.SubElement(link, 'linkclipref')
                linkclipref.text = 'clipitem-' + str(mtx_clipitem[vidclip_no, i])
                mediatype = et.SubElement(link, 'mediatype')
                if i > 0:
                    mediatype.text = 'audio'
                else:
                    mediatype.text = 'video'
                trackindex = et.SubElement(link, 'trackindex')
                trackindex.text = str(i)
                if i == 0:
                    trackindex.text = '1'
                clipindex = et.SubElement(link, 'clipindex')
                clipindex.text = '1'
                if i == 0:
                    continue
                groupindex = et.SubElement(link, 'groupindex')
                groupindex.text = '1'

        audio = et.SubElement(sequence_media, 'audio')
        numOutputChannels = et.SubElement(audio, 'numOutputChannels')
        numOutputChannels.text = '2'
        audio_format = et.SubElement(audio, 'format')
        samplecharacteristics = et.SubElement(audio_format, 'samplecharacteristics')
        depth = et.SubElement(samplecharacteristics, 'depth')
        depth.text = '16'
        samplerate = et.SubElement(samplecharacteristics, 'samplerate')
        samplerate.text = '48000'
        outputs = et.SubElement(audio, 'outputs')
        for i in range(1, 3):
            group = et.SubElement(outputs, 'group')
            index = et.SubElement(group, 'index')
            index.text = str(i)
            numchannels = et.SubElement(group, 'numchannels')
            numchannels.text = '1'
            downmix = et.SubElement(group, 'downmix')
            downmix.text = '0'
            channel = et.SubElement(group, 'channel')
            index = et.SubElement(channel, 'index')
            index.text = str(i)
        Clipitem_num = 2
        for _audio_trk in range(6):
            track = et.SubElement(
                audio,
                'track',
                {
                    'TL.SQTrackAudioKeyframeStyle': "0",
                    'TL.SQTrackShy': "0",
                    'TL.SQTrackExpandedHeight': "25",
                    'TL.SQTrackExpanded': "0",
                    'MZ.TrackTargeted': "1",
                    'PannerCurrentValue': "0.5",
                    'PannerIsInverted': "true",
                    'PannerStartKeyframe': "-91445760000000000,0.5,0,0,0,0,0,0",
                    'PannerName': "平衡",
                    'currentExplodedTrackIndex': str(_audio_trk % 2),
                    'totalExplodedTrackCount': "2",
                    'premiereTrackType': "Stereo",
                },
            )
            for audclip_no in range(MAXVIDS):
                clipitem = et.SubElement(
                    track,
                    'clipitem',
                    {
                        'id': 'clipitem-' + str(mtx_clipitem[audclip_no, _audio_trk + 1]),
                        'premiereChannelType': "Stereo",
                    },
                )
                Clipitem_num += 1
                vidname = firing_list[audclip_no, 0]
                masterclipid = et.SubElement(clipitem, 'masterclipid')
                masterclipid.text = 'masterclip-' + str(dict_masterclip[vidname])
                name = et.SubElement(clipitem, 'name')
                name.text = vidname
                enabled = et.SubElement(clipitem, 'enabled')
                enabled.text = 'TRUE'
                rate = et.SubElement(clipitem, 'rate')
                timebase = et.SubElement(rate, 'timebase')
                timebase.text = '60'
                ntsc = et.SubElement(rate, 'ntsc')
                ntsc.text = 'FALSE'
                start = et.SubElement(clipitem, 'start')
                start.text = str(mtx_start[audclip_no])
                end = et.SubElement(clipitem, 'end')
                end.text = str(mtx_end[audclip_no])
                clipitem_in = et.SubElement(clipitem, 'in')
                clipitem_in.text = str(mtx_in[audclip_no])
                clipitem_out = et.SubElement(clipitem, 'out')
                clipitem_out.text = str(mtx_out[audclip_no])
                file = et.SubElement(
                    clipitem, 'file', {'id': 'file-' + str(dict_masterclip[vidname])}
                )
                sourcetrack = et.SubElement(clipitem, 'sourcetrack')
                mediatype = et.SubElement(sourcetrack, 'mediatype')
                mediatype.text = 'audio'
                trackindex = et.SubElement(sourcetrack, 'trackindex')
                trackindex.text = str(_audio_trk // 2 + 1)
                for i in range(7):
                    link = et.SubElement(clipitem, 'link')  # 音视频关联
                    linkclipref = et.SubElement(link, 'linkclipref')
                    linkclipref.text = 'clipitem-' + str(mtx_clipitem[audclip_no, i])
                    mediatype = et.SubElement(link, 'mediatype')
                    if i > 0:
                        mediatype.text = 'audio'
                    else:
                        mediatype.text = 'video'
                    trackindex = et.SubElement(link, 'trackindex')
                    trackindex.text = str(i)
                    if i == 0:
                        trackindex.text = '1'
                    clipindex = et.SubElement(link, 'clipindex')
                    clipindex.text = '1'
                    if i == 0:
                        continue
                    groupindex = et.SubElement(link, 'groupindex')
                    groupindex.text = '1'

            # 轨道收尾数据
            enabled = et.SubElement(track, 'enabled')
            enabled.text = 'TRUE'
            locked = et.SubElement(track, 'locked')
            locked.text = 'FALSE'
            outputchannelindex = et.SubElement(track, 'outputchannelindex')
            outputchannelindex.text = str(_audio_trk % 2 + 1)
        timecode = et.SubElement(sequence, 'timecode')
        rate = et.SubElement(timecode, 'rate')
        timebase = et.SubElement(rate, 'timebase')
        timebase.text = '60'
        ntsc = et.SubElement(rate, 'ntsc')
        ntsc.text = 'FALSE'
        string = et.SubElement(timecode, 'string')
        string.text = '00:00:00:00'
        timecode_frame = et.SubElement(timecode, 'frame')
        timecode_frame.text = '0'
        displayformat = et.SubElement(timecode, 'displayformat')
        displayformat.text = 'NDF'

        # 美化和输出
        xml_data = et.tostring(root, encoding='utf-8', pretty_print=True).decode('utf-8')
        f.write(xml_data)


if __name__ == '__main__':
    main(style='normal')
