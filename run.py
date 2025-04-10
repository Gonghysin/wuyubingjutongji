from app import create_app
import argparse

app = create_app()

if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='运行Flask应用服务器')
    parser.add_argument('--port', type=int, default=5000, help='服务器端口号，默认为5000')
    args = parser.parse_args()
    
    # 使用指定的端口运行应用
    app.run(host='0.0.0.0', port=args.port, debug=False)