import sqlite3
import logging
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver

from config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE, LOG_LEVEL
from tools import get_all_tools, set_rag_instance
from rag import RAGModule
from security import SecurityModule, set_security_instance


logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AIAgent:
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.model = None
        self.rag = None
        self.security = None
        self.tools = get_all_tools()
        self.checkpointer = None
        self.agent = None
        
        conn = sqlite3.connect("memory.db")
        self.checkpointer = SqliteSaver(conn)
        
        self.system_prompt = """你是一个智能助手，能够使用以下工具：
- get_current_time: 获取当前时间
- calculate: 进行数学计算
- search_web: 搜索网络信息
- query_knowledge_base: 查询知识库文档
- read_file: 读取文件内容
- write_file: 写入文件内容
- list_files: 列出目录文件
- run_code: 执行简单Python代码
- get_weather: 查询天气信息
- github_search: 搜索GitHub仓库
- generate_chart: 生成数据可视化图表
- get_etf_info/price/history/knowledge: ETF相关功能

请根据用户的需求，选择合适的工具。"""
    
    def init_agent(self):
        if self.api_key:
            self.model = ChatOpenAI(
                model=MODEL_NAME,
                temperature=TEMPERATURE,
                api_key=self.api_key
            )
            self.rag = RAGModule(self.model, api_key=self.api_key)
            set_rag_instance(self.rag)
            self.security = SecurityModule()
            set_security_instance(self.security)
            self.tools = get_all_tools()
            self.agent = create_agent(
                model=self.model,
                tools=self.tools,
                system_prompt=self.system_prompt,
                checkpointer=self.checkpointer
            )
    
    def set_api_key(self, api_key: str):
        self.api_key = api_key
        self.model = None
        self.agent = None
        self.init_agent()
    
    def get_api_key_status(self):
        return {"configured": bool(self.api_key), "has_agent": self.agent is not None}
    
    def run(self, user_input: str) -> str:
        try:
            logger.info(f"User input: {user_input}")
            if not self.agent:
                self.init_agent()
            if not self.agent:
                return "❌ 错误: 请先配置 API Key。"
            
            security_check = self.security.check_input(user_input)
            if security_check["blocked"]:
                return f"❌ 输入被阻止: {security_check['reason']}"
            
            response = self.agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config={"configurable": {"thread_id": "default"}}
            )
            
            output = response.get("output", "")
            output_check = self.security.check_output(output)
            if output_check["blocked"]:
                return "❌ 输出被阻止: 包含敏感信息"
            
            return self.security.sanitize_output(output)
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return f"❌ 错误: {str(e)}"
    
    def run_stream(self, user_input: str):
        try:
            if not self.agent:
                self.init_agent()
            if not self.agent:
                yield "❌ 错误: 请先配置 API Key。"
                return
            
            last_content_length = 0
            for chunk in self.agent.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                config={"configurable": {"thread_id": "default"}},
                stream_mode="values"
            ):
                messages = chunk.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content'):
                        content = last_message.content
                        if content:
                            sanitized_output = self.security.sanitize_output(content)
                            incremental_content = sanitized_output[last_content_length:]
                            if incremental_content:
                                yield incremental_content
                                last_content_length = len(sanitized_output)
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            yield f"❌ 错误: {str(e)}"
    
    def clear_history(self):
        try:
            self.checkpointer.clear()
            return "✅ 对话历史已清除"
        except Exception as e:
            return f"❌ 清除历史失败: {str(e)}"
    
    def get_tools_list(self):
        return [tool.name for tool in self.tools] if self.tools else []
