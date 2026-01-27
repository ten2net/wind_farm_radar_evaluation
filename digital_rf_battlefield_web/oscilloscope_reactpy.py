from reactpy import component, html, run 

# 定义你的组件
@component
def HelloWorld():
    return html.h1("Hello, World!")

# 在开发服务器上运行它。仅用于测试目的。
run(HelloWorld)