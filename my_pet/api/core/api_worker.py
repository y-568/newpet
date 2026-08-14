from PySide6.QtCore import QThread, Signal
from openai import OpenAI

class APIWorker(QThread):
    """后台 API 调用线程"""
    
    finished = Signal(str)      # 完成信号，传递完整回复
    error = Signal(str)         # 错误信号，传递错误信息
    progress = Signal(str)      # 进度信号，流式输出
    
    def __init__(self, api_key, message, model="deepseek-chat", 
                 temperature=0.7, max_tokens=2000):
        super().__init__()
        self.api_key = api_key
        self.message = message
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
    def run(self):
        """执行 API 调用"""
        try:
            # 在子线程中独立创建客户端
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com/v1"
            )
            
            messages = [
                {
                    "role": "system", 
                    "content": "你是一个友好、专业的AI助手，请用简洁清晰的语言回答问题。"
                },
                {
                    "role": "user", 
                    "content": self.message
                }
            ]
            
            # 使用流式输出
            stream = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    # 发送进度更新
                    self.progress.emit(full_response)
            
            # 发送完整回复
            self.finished.emit(full_response)
            
        except Exception as e:
            error_msg = str(e)
            # 优化错误信息
            if "Incorrect API key" in error_msg:
                error_msg = "API Key 无效，请检查设置。"
            elif "Connection" in error_msg:
                error_msg = "网络连接失败，请检查网络设置。"
            elif "Rate limit" in error_msg:
                error_msg = "请求过于频繁，请稍后再试。"
                
            self.error.emit(error_msg)