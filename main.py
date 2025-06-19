#为了方便后期使用pyinstaller进行构建，尽量放在一个文件，否则必须明确给出依赖图
import shutil


# 全局变量声明
global_limit_time = 60
global_base_limit_time = 60
global_past_time = 0
config = None
# 通用模块导入
import os
import time
import yaml
import json
# 截图相关部分----------------------------------------------
from PIL import ImageGrab, Image
import os
import io
import base64

def capture_screen_pil():
    """
    使用PIL库捕获整个屏幕
    返回PIL Image对象
    """
    try:
        screenshot = ImageGrab.grab()
        return screenshot
    except Exception as e:
        print(f"PIL截图失败: {e}")
        return None

def save_screenshot(image, filepath="screenshot.png"):
    """
    保存截图到文件
    """
    if image:
        try:
            image.save(filepath)
            print(f"截图已保存到: {filepath}")
            return True
        except Exception as e:
            print(f"保存截图失败: {e}")
            return False
    return False

def image_to_base64(image):
    """
    将PIL图像转换为base64字符串
    """
    if image:
        try:
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return img_base64
        except Exception as e:
            print(f"图像转base64失败: {e}")
            return None
    return None

def capture_and_save_screen(method="pil", filepath="./temp/screenshot.png"):
    """
    捕获屏幕并保存
    method: "pil", "pyautogui", "mss"
    """
    # 确保temp目录存在
    os.makedirs("./temp", exist_ok=True)
    print("不支持的截图方法，使用PIL作为默认方法")
    image = capture_screen_pil()

    if image:
        success = save_screenshot(image, filepath)
        if success:
            return filepath
    return None
# 语言聊天部分---------------------------------------------
def clear_text_in_brackets(text):
    """
    清除文本中括号内的内容，包括中文括号（）和英文括号()
    """
    import re
    # 删除中文括号（）内的内容
    text = re.sub(r'（.*?）', '', text)
    # 删除英文括号()内的内容
    text = re.sub(r'\(.*?\)', '', text)
    return text

def make_final_prompt(personalityPrompt,userInfoPrompt, text):
    """
    生成最终的提示文本
    """
    final_prompt = ""
    if text== "-1":
        final_prompt = personalityPrompt+ userInfoPrompt + "这是用户的桌面截图，请你根据桌面截图与他对话"
    else:
        final_prompt = personalityPrompt + userInfoPrompt + "用户刚刚对你说了"+text


import google.generativeai as genai
def gemini_chat(api_key,model_choice,text):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_choice)

    response = model.generate_content(
        contents=[
            {"text": text}
        ]
    )

    return response.text

def gemini_chat_with_pic(api_key,model_choice,text):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_choice)

    print("正在捕获截图")
    screenshot_path = capture_and_save_screen()

    if screenshot_path:
        print(f"屏幕截图已保存:{screenshot_path}")
        with open(screenshot_path, "rb") as f:
            image_content = f.read()

    response = model.generate_content(
        contents=[
            {
                "parts" : [
                    {"text": text},
                    {
                        "inline_data":{
                            "mime_type": "image/png",
                            "data": base64.b64encode(image_content).decode()
                        }
                    }
                ]
            }
        ]
    )

    return response.text

from openai import OpenAI
def OpenAI_chat(api_key, base_url, model_choice, personalityPrompt, userInfoPrompt, text):
    """
    使用OpenAI API进行聊天
    :param api_key: str
    :param base_url: str
    :param model_choice: str
    :param text: str
    :return: str
    """
    client = OpenAI(api_key=api_key, base_url=base_url)

    response = client.chat.completions.create(
        model=model_choice,
        messages=[
            {"role":"system", "content":personalityPrompt+userInfoPrompt},
            {"role":"user", "content":text}
        ],
        stream=False
    )
    return response.choices[0].message.content

def OpenAI_chat_with_pic(api_key, base_url, model_choice, personalityPrompt, userInfoPrompt, text):
    """
    使用OpenAI API进行聊天（带图片）
    :param api_key: str
    :param base_url: str
    :param model_choice: str (需要支持vision的模型，如gpt-4-vision-preview, gpt-4o等)
    :param personalityPrompt: str
    :param userInfoPrompt: str 
    :param text: str
    :return: str
    """
    client = OpenAI(api_key=api_key, base_url=base_url)
    print("正在捕获截图")
    screenshot_path = capture_and_save_screen()

    if screenshot_path:
        print(f"屏幕截图已保存:{screenshot_path}")
        with open(screenshot_path, "rb") as f:
            image_content = f.read()
        
        # 将图片转换为base64
        image_base64 = base64.b64encode(image_content).decode('utf-8')
        
        # 构建包含图片的消息
        response = client.chat.completions.create(
            model=model_choice,
            messages=[
                {"role":"system", "content":personalityPrompt+userInfoPrompt},
                {
                    "role":"user", 
                    "content": [
                        {"type": "text", "text": text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            stream=False
        )
        return response.choices[0].message.content
    else:
        print("⚠️ 截图失败，回退到普通聊天模式")
        return None

def Ollama_chat(base_url, model_choice, port, personalityPrompt, userInfoPrompt, text):
    import requests
    """调用局域网内另一台计算机的 Ollama 服务进行聊天

    :param base_url: 形如 "http://192.168.1.10" 的 Ollama 主机地址（不含端口）
    :param model_choice: 模型名称，例如 "llama3"、"deepseek-coder" 等。
    :param port: Ollama 服务端口，默认 11434。
    :param personalityPrompt: 系统提示词
    :param userInfoPrompt: 用户信息提示词
    :param text: 用户输入
    :return: Ollama 返回的回复文本
    """
    url = f"{base_url}:{port}/api/chat"

    payload = {
        "model": model_choice,
        "messages": [
            {"role": "system", "content": personalityPrompt + userInfoPrompt},
            {"role": "user", "content": text}
        ],
        "stream": False
    }

    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # /api/chat 返回的字段为 message.content
        return data.get("message", {}).get("content", data.get("response", ""))
    except Exception as e:
        print(f"⚠️ 调用 Ollama 失败: {e}")
        return None
    
def Ollama_chat_with_pic(base_url, model_choice, port, personalityPrompt, userInfoPrompt, text="这是用户的桌面截图，请你根据桌面截图与他对话"):
    """向远程 Ollama 发送图片+文本消息

    :param base_url: "http://192.168.1.10"
    :param model_choice: 支持视觉的模型，例如 "llava"、"bakllava" 等
    :param port: 端口
    :param personalityPrompt: str
    :param userInfoPrompt: str
    :param text: 提示文本
    :return: 回复内容
    """
    import requests

    # 捕获截图
    screenshot_path = capture_and_save_screen()
    if not screenshot_path:
        print("⚠️ 截图失败，改用纯文本模式")
        return Ollama_chat(base_url, model_choice, port, personalityPrompt, userInfoPrompt, text)

    with open(screenshot_path, "rb") as f:
        image_content = f.read()
    image_base64 = base64.b64encode(image_content).decode("utf-8")

    url = f"{base_url}:{port}/api/chat"

    payload = {
        "model": model_choice,
        "messages": [
            {"role": "system", "content": personalityPrompt + userInfoPrompt},
            {
                "role": "user",
                "content": text,
                "images": [image_base64]
            }
        ],
        "stream": False
    }

    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", data.get("response", ""))
    except Exception as e:
        print(f"⚠️ 调用 Ollama(带图) 失败: {e}")
        return None

def llm_handler(config, text):
    """
    处理LLM请求
    :param config: yaml配置文件内容
    :param text: 用户输入内容
    :return:
    """
    if config["llm_model"]["model_Interface"] == "OpenAI":
        if text == "-1":
            return OpenAI_chat_with_pic(config["llm_model"]["OpenAI_config"]["api_key"],
                                        config["llm_model"]["OpenAI_config"]["base_url"],
                                        config["llm_model"]["OpenAI_config"]["model"],
                                        config["llm_model"]["personalityPrompt"],
                                        config["llm_model"]["userInfoPrompt"],
                                        "这是用户的桌面截图，请你根据桌面截图与他对话")
        else:
            return OpenAI_chat(config["llm_model"]["OpenAI_config"]["api_key"],
                               config["llm_model"]["OpenAI_config"]["base_url"],
                               config["llm_model"]["OpenAI_config"]["model"],
                               config["llm_model"]["personalityPrompt"],
                               config["llm_model"]["userInfoPrompt"],
                               text)
    elif config["llm_model"]["model_Interface"] == "Gemini":
        if text == "-1":
            return gemini_chat_with_pic(config["llm_model"]["Gemini_config"]["api_key"],
                                        config["llm_model"]["Gemini_config"]["model"],
                                        make_final_prompt(config["llm_model"]["PersonalityPrompt"],
                                                          config["llm_model"]["UserInfoPrompt"],
                                                          "-1"))
        else:
            return gemini_chat(config["llm_model"]["Gemini_config"]["api_key"],
                                        config["llm_model"]["Gemini_config"]["model"],
                                        make_final_prompt(config["llm_model"]["PersonalityPrompt"],
                                                          config["llm_model"]["UserInfoPrompt"],
                                                          text))
    elif config["llm_model"]["model_Interface"] == "Ollama":
        if text == "-1":
            return Ollama_chat_with_pic(config["llm_model"]["Ollama_config"]["base_url"],
                                         config["llm_model"]["Ollama_config"]["model"],
                                         config["llm_model"]["Ollama_config"].get("port", 11434),
                                         config["llm_model"].get("personalityPrompt", ""),
                                         config["llm_model"].get("userInfoPrompt", ""))
        else:
            return Ollama_chat(config["llm_model"]["Ollama_config"]["base_url"],
                               config["llm_model"]["Ollama_config"]["model"],
                               config["llm_model"]["Ollama_config"].get("port", 11434),
                               config["llm_model"].get("personalityPrompt", ""),
                               config["llm_model"].get("userInfoPrompt", ""),
                               text)
    else:
        print("⚠️ 未知的模型接口类型，请检查配置文件")
# 语音合成部分-----------------------------------
import soundfile as sf
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

def tts_handler(config,text):
    import requests
    double_safety_check=False
    # 检查相关配置，确保一定有对应的tts模型
    if config["gpt-sovits"]["enable"]:
        if config["gpt-sovits"]["ckpt_model_path"] is not None:
            if config["gpt-sovits"]["pth_model_path"] is not None:
                if config["gpt-sovits"]["reference_audio_path"] is not None:
                    if config["gpt-sovits"]["port"] is not None:
                        if config["gpt-sovits"]["url"] is not None:
                            if (os.path.exists(config["gpt-sovits"]["ckpt_model_path"]) and 
                                os.path.exists(config["gpt-sovits"]["pth_model_path"]) and 
                                os.path.exists(config["gpt-sovits"]["reference_audio_path"])):
                                double_safety_check=True
                            else:
                                print("相关文件路径不存在")
                                double_safety_check=False
                                return None
    if not double_safety_check:
        print("相关文件路径不存在")
        return None
    
    session = requests.Session()
    session.proxies = {
        'http': None,
        'https': None,
        'no_proxy': '127.0.0.1,localhost'
    }
    session.trust_env = False

    try:
        # 先切换 GPT 和 SoVITS 模型
        gpt_response = session.get(config["gpt-sovits"]["url"] + "/"+config["gpt-sovits"]["port"],params={
            "weights_path": config["gpt-sovits"]["ckpt_model_path"]
        })
        print(f"GPT模型切换响应: {gpt_response.status_code}")
        sovits_response = session.get(config["gpt-sovits"]["url"] + "/"+config["gpt-sovits"]["port"], params={
            "weights_path": config["gpt-sovits"]["pth_model_path"]
        })
        print(f"SoVITS模型切换响应: {sovits_response.status_code}")

        if gpt_response.status_code != 200 or sovits_response.status_code != 200:
            print("⚠️ 模型切换失败，请检查模型路径和服务状态")
            return None

        # 然后进行 TTS 合成
        url= config["gpt-sovits"]["url"] + "/"+config["gpt-sovits"]["port"] + "/tts"
        payload = {
            "text": text,
            "text_lang": "zh",
            "ref_audio_path": config["gpt-sovits"]["reference_audio_path"],
            "text_split_method": "cut5",
            "media_type": "wav",
            "batch_size": 10#对于绝大多数设备而言，这个值完全可以承受
        }

        print(f"正在合成文本: {text}")
        response = session.post(url, json=payload)
        print(f"TTS响应状态码: {response.status_code}")
        print(f"响应内容类型: {response.headers.get('content-type', 'unknown')}")
        print(f"响应内容长度: {len(response.content)} 字节")

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
        print(f"⚠️ TTS处理过程中发生错误: {e}")
        return None

pass
#----------------------------------------------------

def check_proxy_available(proxy_host="127.0.0.1", proxy_port=7890, timeout=3):
    """检查代理是否可用"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((proxy_host, proxy_port))
        sock.close()
        return result == 0
    except Exception:
        return False


def setup_smart_proxy():
    """智能设置代理"""
    proxy_url = "http://127.0.0.1:7890"

    # 检查代理是否可用
    if check_proxy_available():
        print(f"✅ 检测到代理服务可用，使用代理: {proxy_url}")
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url
    else:
        print("⚠️ 代理服务不可用，使用直接连接")
        # 清除可能存在的代理环境变量
        for proxy_env in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
            if proxy_env in os.environ:
                del os.environ[proxy_env]

    # 确保访问本地地址时不走代理，防止启动检查 502
    for env_key in ("NO_PROXY", "no_proxy"):
        existing = os.environ.get(env_key, "")
        extra = ",127.0.0.1,localhost"
        if extra.strip(',') not in existing:
            os.environ[env_key] = existing + extra if existing else extra.strip(',')


if __name__ == "__main__":
    setup_smart_proxy()
    try:
        with open("./servereConfig.yaml","r",encoding="utf-8") as f:
            config = yaml.safe_load(f)
        print("✅ 配置文件加载成功")
    except Exception as e:
        print(f"⚠️ 配置文件加载失败: {e}")
        config = None
    if config is None:
        print("⚠️ 未加载到配置文件，请检查servereConfig.yaml是否存在")
        print("程序正在退出")
    else:
        base_limit_time=config["screenAutoShot"]
        limit_time = base_limit_time

    # 初始化三个截图循环极限时间
    global_base_limit_time=config["screenAutoShot"]
    global_limit_time = global_base_limit_time
    global_past_time = 0
    # 进入主循环
    while True:
        if os.path.exists("./Britney-v1/contact/in.txt"):
            with open("./Britney-v1/contact/in.txt", "r", encoding="utf-8") as f:
                text=f.read()
            if text:
                system_start_time = time.time()
                past_time=0
                print(f"识别到用户输入：{text}")
                os.remove("./contact/in.txt")
                output_text = llm_handler(config,text)
                if output_text:
                    print(f"LLM回复内容：{output_text}")
                else:
                    print("⚠️ LLM回复内容为空或处理失败")
                    output_text = "抱歉，我无法处理您的请求。"

                if config["gpt-sovits"]["enable"] and output_text!="抱歉，我无法处理您的请求。":
                    audio_time = tts_handler(config,output_text)
                    # 处理合成的音频
                    if audio_time is not None:
                        print(f"音频合成完成，时长: {audio_time:.2f} 秒")
                        with open("./Britney-v1/contact/out.txt", "w", encoding="utf-8") as f:
                            if audio_time > 3:
                                time_value = int(audio_time)+1
                            else:
                                time_value = int(0.5 + len(output_text) * 0.06)
                            # 将输出文本和时长写入文件，同时修改global_limit_time
                            output_data = json.dumps({"text": output_text, "time": time_value})
                            f.write(output_text)
                            global_limit_time=global_base_limit_time + time_value
                            global_past_time=0
                            # 将音频文件移动到指定目录
                            os.makedirs("./Britney-v1/contact", exist_ok=True)
                            if os.path.exists("./temp/1.wav"):
                                shutil.move("./temp/1.wav", "./Britney-v1/contact/1.wav")
                            else:
                                print("警告：服务器可能存在严重错误！音频文件未生成或被神秘的力量移动了！")
                    else:
                        print("音频合成失败或未返回有效时长")
                        with open("./Britney-v1/contact/out.txt", "w", encoding="utf-8") as f:
                            output_data = json.dumps({"text": output_text, "time": int(0.5+ len(output_text) * 0.06)})
                            f.write(output_data)
                            global_limit_time = global_base_limit_time + int(0.5+ len(output_text) * 0.06)
                            global_past_time = 0
                else:
                    print("GPT-SoVITS 未启用，跳过语音合成")
                    with open("./Britney-v1/contact/out.txt", "w", encoding="utf-8") as f:
                        output_data = json.dumps({"text": output_text, "time": int(0.5+ len(output_text) * 0.06)})
                        f.write(output_data)
                        global_limit_time = global_base_limit_time + int(0.5+ len(output_text) * 0.06)
                        global_past_time = 0
                # 计算处理时间
                cost_time = time.time() - system_start_time
                print(f"一轮处理时间: {cost_time:.2f} 秒")
                with open("./Britney-v1/contact/config.json", "r",encoding="utf-8") as f:
                    app_config_data = json.load(f)
                    app_config_data["isReacted"] = True
                    app_config_data["favoribility"] = config["favoribility"]+1;
                    with open("./Britney-v1/contact/config.json", "w", encoding="utf-8") as f:
                        json.dump(app_config_data, f, ensure_ascii=False)
            else:
                if global_past_time >= global_limit_time and global_base_limit_time!=-1:
                    print("捕获桌面")

                    with open("./Britney-v1/contact/config.json","r",encoding="utf-8") as f:
                        app_config_data = json.load(f)
                        app_config_data["isReacted"] = False
                        with open("./Britney-v1/contact/config.json", "w", encoding="utf-8") as f:
                            json.dump(app_config_data, f, ensure_ascii=False)

                    output_text = llm_handler(config, "-1")
                    if output_text:
                        print(f"LLM回复内容：{output_text}")
                    else:
                        print("⚠️ LLM回复内容为空或处理失败")
                        output_text = "抱歉，我无法处理您的请求。"

                else:
                    print(f"未检测到有效输入，等待中({global_past_time}/{global_limit_time}秒)")
                    global_past_time+=1
                    time.sleep(1)




















