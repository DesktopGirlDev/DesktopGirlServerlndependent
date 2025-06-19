import requests
import json
import soundfile as sf
import shutil
import os
import time


def get_audio_duration(audio_path):
    """
    获取音频文件的时长（秒）
    """
    try:
        # 等待文件生成完成
        max_wait = 10  # 最大等待时间（秒）
        wait_time = 0
        while not os.path.exists(audio_path) and wait_time < max_wait:
            time.sleep(0.5)
            wait_time += 0.5
        
        if not os.path.exists(audio_path):
            print(f"等待音频文件生成超时: {audio_path}")
            return None
            
        # 使用soundfile获取音频信息
        info = sf.info(audio_path)
        duration = info.duration
        return duration
    except Exception as e:
        print(f"获取音频时长时出错: {str(e)}")
        return None

def gpt_sovits_v2_gradioAPI_function(text):
    # 读取配置文件
    with open('./gpt_sovits_model_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 选择要使用的语音模型
    voice_name = "纳西妲"  # 例如使用 Fairy 模型
    model_config = config[voice_name]

    # 创建一个完全绕过代理的session（包括环境变量中的代理）
    session = requests.Session()
    session.proxies = {
        'http': None,
        'https': None,
        'no_proxy': '127.0.0.1,localhost'
    }
    # 清除环境变量中的代理设置（仅对此session有效）
    session.trust_env = False

    try:
        # 先切换 GPT 和 SoVITS 模型
        gpt_response = session.get("http://127.0.0.1:9880/set_gpt_weights", params={
            "weights_path": model_config["weight-path"]
        })
        print(f"GPT模型切换响应: {gpt_response.status_code}")
        
        sovits_response = session.get("http://127.0.0.1:9880/set_sovits_weights", params={
            "weights_path": model_config["sovits-path"]
        })
        print(f"SoVITS模型切换响应: {sovits_response.status_code}")

        # 然后进行 TTS 合成
        url = "http://127.0.0.1:9880/tts"
        payload = {
            "text": text,
            "text_lang": "zh",
            "ref_audio_path": model_config["ref-audio-path"],
            "prompt_text": model_config["prompt-text"],
            "prompt_lang": "zh",
            "text_split_method": "cut5",
            "media_type": "wav"
        }

        print(f"正在合成文本: {text}")
        response = session.post(url, json=payload)
        print(f"TTS响应状态码: {response.status_code}")
        print(f"响应内容类型: {response.headers.get('content-type', 'unknown')}")
        print(f"响应内容长度: {len(response.content)} 字节")
        
        # 检查响应是否成功
        if response.status_code != 200:
            print(f"TTS请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
        
        # 确保temp目录存在
        os.makedirs("./temp", exist_ok=True)
        
        # 保存音频文件
        audio_path = "./temp/1.wav"
        with open(audio_path, "wb") as f:
            f.write(response.content)
        
        # 检查文件大小
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            print(f"保存的音频文件大小: {file_size} 字节")
            if file_size < 1000:  # 如果文件太小，可能是错误响应
                print("警告：音频文件大小异常小，可能包含错误信息")
                with open(audio_path, 'rb') as f:
                    first_bytes = f.read(100)
                    print(f"文件前100字节: {first_bytes}")
        
        # 获取生成的音频时长
        duration = get_audio_duration(audio_path)
        if duration is not None:
            print(f"生成的音频时长: {duration:.2f} 秒")
        
        return duration
        
    except Exception as e:
        print(f"TTS合成过程中发生错误: {str(e)}")
        return None

if __name__ == "__main__":
    # 测试函数
    text = "主人，我爱你！"
    duration = gpt_sovits_v2_gradioAPI_function(text)
    print(f"音频生成完成，时长: {duration:.2f} 秒")