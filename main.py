import os
import sys
import argparse
import logging

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("md2docx")


def run_cli(args):
    from core.converter import DocumentConverter

    target_dir = os.path.abspath(args.directory)
    logger.info(f"=== Markdown to DOCX Engine Pro ===")
    logger.info(f"Target Directory: {target_dir}")
    logger.info(f"Style Preset    : {args.preset}")

    converter = DocumentConverter()

    if args.file:
        files = [os.path.abspath(args.file)]
    else:
        if args.recursive:
            files = []
            for root, _, fs in os.walk(target_dir):
                for f in fs:
                    if f.lower().endswith('.md') and not f.endswith('.debug.md'):
                        files.append(os.path.join(root, f))
        else:
            files = [
                os.path.join(target_dir, f)
                for f in os.listdir(target_dir)
                if f.lower().endswith('.md') and not f.endswith('.debug.md')
            ]

    if not files:
        logger.info("未发现需要处理的 .md 文件。")
        return

    logger.info(f"找到 {len(files)} 个文件，开始转换...\n")
    success_cnt = 0
    fail_cnt = 0

    for f_path in files:
        res = converter.convert_file(f_path, preset=args.preset)
        if res.success:
            logger.info(f"  [√] 成功: {os.path.basename(f_path)} -> {os.path.basename(res.output_path)} ({res.elapsed_time}s)")
            success_cnt += 1
        else:
            logger.error(f"  [X] 失败: {os.path.basename(f_path)} - {res.error_message}")
            fail_cnt += 1

    logger.info(f"\n转换完成: 成功 {success_cnt} | 失败 {fail_cnt} | 总数 {len(files)}")


def main():
    if len(sys.argv) > 1 and not (len(sys.argv) == 2 and sys.argv[1] in ['--tray', '--minimized']):
        parser = argparse.ArgumentParser(description="Markdown to DOCX High-Fidelity Converter")
        parser.add_argument('-d', '--directory', default=os.getcwd(), help="目标目录")
        parser.add_argument('-f', '--file', default=None, help="转换单个指定 .md 文件")
        parser.add_argument('-p', '--preset', default='modern', choices=['modern', 'academic', 'minimal'], help="排版预设风格 (modern, academic, minimal)")
        parser.add_argument('-r', '--recursive', action='store_true', help="递归遍历子目录")
        args = parser.parse_args()
        run_cli(args)
    else:
        # Launch GUI
        from app import main as gui_main
        gui_main()


if __name__ == "__main__":
    main()
