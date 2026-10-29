import os
import sys

def get_startup_dir() -> str:
    appdata = os.environ.get('APPDATA')
    if appdata:
        return os.path.join(appdata, r'Microsoft\Windows\Start Menu\Programs\Startup')
    return os.path.expanduser(r'~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup')

def create_startup_vbs():
    startup_dir = get_startup_dir()
    os.makedirs(startup_dir, exist_ok=True)
    vbs_path = os.path.join(startup_dir, 'MarkdownToDOCX_AutoStart.vbs')
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_pyw = os.path.join(script_dir, 'app.pyw')

    content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pythonw \"\"\"{app_pyw}\"\"\" --tray", 0, False
'''
    with open(vbs_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[√] 已创建开机自启快捷方式: {vbs_path}")

def remove_startup_vbs():
    startup_dir = get_startup_dir()
    vbs_path = os.path.join(startup_dir, 'MarkdownToDOCX_AutoStart.vbs')
    if os.path.exists(vbs_path):
        os.remove(vbs_path)
        print(f"[√] 已移除开机自启快捷方式: {vbs_path}")
    else:
        print("未检测到开机自启文件。")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--remove':
        remove_startup_vbs()
    else:
        create_startup_vbs()
