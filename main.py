from agent import AIAgent
import sys


def print_banner():
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    AI Agent 智能助手                         ║
║              Powered by LangChain + LangGraph               ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def main():
    print_banner()
    print("输入 'help' 查看帮助信息")
    print("=" * 60)
    
    agent = AIAgent()
    print(f"✅ Agent 初始化成功，可用工具: {len(agent.get_tools_list())} 个")
    
    while True:
        try:
            user_input = input("\n你: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("\nAI: 再见！")
                break
            if user_input.lower() == "clear":
                print(f"\nAI: {agent.clear_history()}")
                continue
            
            print("\nAI: ", end="", flush=True)
            for chunk in agent.run_stream(user_input):
                print(chunk, end="", flush=True)
            print()
        except KeyboardInterrupt:
            print("\n\nAI: 程序已中断")
            break


if __name__ == "__main__":
    main()
