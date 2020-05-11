#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2020. ZZL
# @Time     : 2020/4/10
# @Author   : ZL.Z
# @Reference: None
# @Email    : zzl1124@mail.ustc.edu.cn
# @FileName : audio_split.py
# @Software : Python3.6;PyCharm;Windows10
# @Hardware : Intel Core i7-4712MQ
# @Version  : V4.0: 2020/5/11
#             1. 升级voice_activity_detection.py为acoustic_feature.py
#             V3.0: 2020/4/18
#             1. 对分割后的语音再进行采用端点检测方法进行分割
#             2. 限制分割后的语音长度为1.5s
#             3. 更新voice_activity_detection.py文件
# @License  : GPLv3
# @Brief    : 音频分割
import os
import subprocess
import shutil
import soundfile as sf
from acoustic_feature import VAD


audio_path_raw = "./raw_audio/"  # 原始音频文件夹
audio_path_wav = "./convert2wav/"  # 原始音频转换为.wav文件 文件夹
save_path_split1 = "./detected_split1/"  # 第一次分割后音频保存目录
save_path_split2 = "./detected_split2/"  # 第二次分割后音频保存目录
save_path_duration = "./duration_limit/"  # 限制语音时长后保存目录


def save_wave_file(filename, wave_data, sampling_rate=16000, subtype="PCM_16"):
    """
    将原始数据存储为wav格式文件
    :param filename: 文件路径+文件名
    :param wave_data: 数组形式数据原始数据
    :param sampling_rate: 采样率，默认16kHz
    :param subtype: 声音文件类型，默认"PCM_16"
    :return: None
    """
    sf.write(filename, wave_data, sampling_rate, subtype)


def audio_split(input_file_folder=audio_path_raw, output_file_folder=audio_path_wav,
                save_chunks_file_folder=(save_path_split1, save_path_split2), audio_type="wav", frame_len=(400, 240),
                min_interval=(20, 20), e_low_multifactor=(1.0, 0.5), zcr_multifactor=(0.8, 1.0)):
    """
    音频转换与分割
    :param input_file_folder: 音频输入文件夹
    :param output_file_folder: 音频转换输出文件夹
    :param save_chunks_file_folder: 分割后音频保存文件夹:第一次和第二次
    :param audio_type: 输出音频文件格式
    :param frame_len: 一帧时长，单位采样点数，默认为400/240，包括第一次端点检测[0]和之后的再次端点检测[1]
    :param min_interval: 最小浊音间隔，默认都为20帧
    :param e_low_multifactor: 能量低阈值倍乘因子，默认第一次1.0，第二次0.5
    :param zcr_multifactor: 过零率阈值倍乘因子，默认第一次0.8，第二次1.0
    :return: None
    """
    if os.path.exists(output_file_folder):
        shutil.rmtree(output_file_folder)  # 先删除输出文件夹
    os.mkdir(output_file_folder)  # 重新创建
    if os.path.exists(save_chunks_file_folder[0]):
        shutil.rmtree(save_chunks_file_folder[0])  # 先删除输出文件夹
    os.mkdir(save_chunks_file_folder[0])  # 重新创建
    if os.path.exists(save_chunks_file_folder[1]):
        shutil.rmtree(save_chunks_file_folder[1])  # 先删除输出文件夹
    os.mkdir(save_chunks_file_folder[1])  # 重新创建
    for each_file in os.listdir(input_file_folder):  # 遍历原始音频文件
        audio_raw = os.path.join(input_file_folder, each_file)  # 原始音频文件相对路径
        audio_path = output_file_folder + each_file.split(".")[0] + "." + audio_type  # 转换后存储路径，文件名
        print(each_file + "音频数据处理中...")
        # 调用ffmpeg，将任意格式音频文件转换为.wav文件，pcm有符号16bit,1：单通道,16kHz，不显示打印信息
        subprocess.run("ffmpeg -loglevel quiet -y -i %s -acodec pcm_s16le -ac 1 -ar 16000 %s" % (audio_raw, audio_path))
        print("----------{} STEP1: 总体端点检测，分割长音频----------".format(each_file))
        vad = VAD(audio_path, frame_len=frame_len[0], min_interval=min_interval[0],
                  e_low_multifactor=e_low_multifactor[0], zcr_multifactor=zcr_multifactor[0])  # 语音端点检测
        vad.plot()
        print("共生成{}段语音".format(len(vad.wav_dat_split)))
        print("----------{} STEP2: 对分割后的音频再次进行端点检测----------".format(each_file))
        wave_num = 0
        for index in range(len(vad.wav_dat_split)):
            file_name = save_chunks_file_folder[0] + each_file.split(".")[0] + \
                        "_%03d.%s" % (index, audio_type)  # 000_000-999_999.wav式命名
            save_wave_file(file_name, vad.wav_dat_split[index])
            _vad = VAD(file_name, frame_len=frame_len[1], min_interval=min_interval[1],
                       e_low_multifactor=e_low_multifactor[1], zcr_multifactor=zcr_multifactor[1], pt=False)  # 语音端点检测
            wave_num += len(_vad.wav_dat_split)
            for i in range(len(_vad.wav_dat_split)):  # 依次保存端点检测后语音文件中所有的有效语音段
                if i == 0:  # 若仅分割成一段，直接保存
                    file_name = save_chunks_file_folder[1] + each_file.split(".")[0] + \
                        "_%03d.%s" % (index, audio_type)  # 000_000-999_999.wav式命名
                else:  # 否则按名_序号保存
                    file_name = save_chunks_file_folder[1] + each_file.split(".")[0] + \
                        "_%03d_%d.%s" % (index, i, audio_type)  # 000_000_0-999_999_9.wav式命名
                save_wave_file(file_name, _vad.wav_dat_split[i])
        print("最终共{}段语音保存完毕".format(wave_num))


def audio_duration_limit(input_file_folder=save_path_split2, output_file_folder=save_path_duration,
                         min_dura=200, max_dura=1500):
    """
    通过变速，限制音频时长
    :param input_file_folder: 输入音频文件夹
    :param output_file_folder: 输出音频文件夹
    :param min_dura: 最小音频时长，默认200ms
    :param max_dura: 最大音频时长，默认1500ms
    :return: None
    """
    if input_file_folder == output_file_folder:
        print("输入和输出路径相同，请选择不同的输出文件路径")
        return
    empty = True  # 当前输入路径是否存在非音频文件
    if os.path.exists(output_file_folder):
        shutil.rmtree(output_file_folder)  # 先删除输出文件夹
    os.mkdir(output_file_folder)  # 重新创建
    try:
        for each_file in os.listdir(input_file_folder):  # 遍历原始音频文件
            audio_raw = os.path.join(input_file_folder, each_file)  # 原始音频文件相对路径
            shutil.copy(audio_raw, output_file_folder)  # 复制原始音频至输出路径
            _input = output_file_folder + each_file  # ffmpeg输入文件
            audio_duration_original = len(sf.read(_input)[0]) / sf.read(_input)[1] * 1000  # 原始音频时长
            i = 0  # 每次加减速编号
            while len(sf.read(_input)[0]) / sf.read(_input)[1] * 1000 > max_dura:  # 当输入音频超过max_dura ms时
                _output = output_file_folder + each_file.split(".")[0] + "_%03d.%s" % (i, each_file.split(".")[1])
                # 每次1.2倍速度加快音频，不显示打印信息
                subprocess.run("ffmpeg -loglevel quiet -y -i %s -af atempo=%s %s" % (_input, 1.2, _output))
                os.remove(_input)  # 删除原音频文件
                os.rename(_output, output_file_folder + each_file)  # 重新命名已倍速音频文件名为原文件名
                i += 1  # 编号递增
            while len(sf.read(_input)[0]) / sf.read(_input)[1] * 1000 < min_dura:  # 当输入音频低于min_dura ms时
                _output = output_file_folder + each_file.split(".")[0] + "_%03d.%s" % (i, each_file.split(".")[1])
                # 每次0.8倍速度减缓音频，不显示打印信息
                subprocess.run("ffmpeg -loglevel quiet -y -i %s -af atempo=%s %s" % (_input, 0.8, _output))
                os.remove(_input)  # 删除原音频文件
                os.rename(_output, output_file_folder + each_file)  # 重新命名已倍速音频文件名为原文件名
                i += 1  # 编号递增
            audio_duration_now = len(sf.read(_input)[0]) / sf.read(_input)[1] * 1000  # 变速后音频时长
            print("{}: {}ms -> {}ms".format(each_file, audio_duration_original, audio_duration_now))
        empty = False
    except PermissionError:
        pass
    else:
        print("----------已完成----------")
    finally:
        if empty:
            print("当前输入路径存在非音频文件或格式错误")


if __name__ == "__main__":
    audio_split(input_file_folder=audio_path_raw, output_file_folder=audio_path_wav,
                save_chunks_file_folder=(save_path_split1, save_path_split2), audio_type="wav", frame_len=(400, 240),
                min_interval=(15, 15), e_low_multifactor=(1.0, 0.5), zcr_multifactor=(0.8, 0.8))
    print("----------STEP3: 限制最终的音频时长为0ms ~ 1500ms----------")
    audio_duration_limit(input_file_folder=save_path_split2, min_dura=0, max_dura=1500)
