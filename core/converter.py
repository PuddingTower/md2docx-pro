import os
import time
import logging
from dataclasses import dataclass
from typing import Optional, Tuple
import pypandoc

from .cleaner import MarkdownCleaner
from .templates import TemplateManager
from .postprocessor import DocxPostProcessor

logger = logging.getLogger("md2docx.converter")


@dataclass
class ConversionResult:
    success: bool
    input_source: str       # Path to .md file or '<Clipboard Text>'
    output_path: str        # Resulting .docx path
    elapsed_time: float     # In seconds
    file_size_bytes: int    # Output file size
    error_message: str = ""
    is_text_source: bool = False


class DocumentConverter:
    """
    Coordinates high-fidelity Markdown to Word conversion:
    1. Pre-cleaning (cleaner.py)
    2. Pandoc compilation with designed Reference Template (templates.py)
    3. Post-processing layout and table polish (postprocessor.py)
    """

    def __init__(self, templates_dir: Optional[str] = None):
        self.cleaner = MarkdownCleaner()
        self.template_mgr = TemplateManager(templates_dir)
        self._ensure_pandoc()

    def _ensure_pandoc(self):
        try:
            pypandoc.get_pandoc_version()
        except OSError:
            logger.info("Pandoc binary not detected, attempting auto-download...")
            pypandoc.download_pandoc()

    def _resolve_output_path(self, target_docx: str) -> str:
        """
        If the file is currently locked/opened in Word, append (1), (2), etc.
        to avoid PermissionError and file corruptions.
        """
        if not os.path.exists(target_docx):
            return target_docx
        
        # Test if target file is locked
        try:
            with open(target_docx, 'r+b'):
                return target_docx
        except PermissionError:
            pass

        # Target is locked, find an alternate name
        base, ext = os.path.splitext(target_docx)
        counter = 1
        while True:
            candidate = f"{base} ({counter}){ext}"
            if not os.path.exists(candidate):
                return candidate
            try:
                with open(candidate, 'r+b'):
                    return candidate
            except PermissionError:
                counter += 1

    def convert_file(self, md_path: str, preset: str = "modern", output_docx: Optional[str] = None) -> ConversionResult:
        """
        Converts an existing .md file into a .docx file located in the SAME directory.
        """
        t0 = time.time()
        md_path = os.path.abspath(md_path)

        if not os.path.exists(md_path):
            return ConversionResult(
                success=False,
                input_source=md_path,
                output_path="",
                elapsed_time=0.0,
                file_size_bytes=0,
                error_message="文件不存在"
            )

        # Output in the same directory as the .md file if not explicitly specified
        if output_docx is None:
            output_docx = os.path.splitext(md_path)[0] + ".docx"
        output_docx = self._resolve_output_path(output_docx)

        try:
            with open(md_path, 'r', encoding='utf-8', errors='replace') as f:
                raw_text = f.read()

            # 1. Clean
            cleaned_text = self.cleaner.process(raw_text)

            # 2. Template
            ref_template = self.template_mgr.get_template_path(preset)

            # 3. Pandoc args
            markdown_format = (
                'markdown'
                '-raw_tex'
                '+tex_math_dollars'
                '+yaml_metadata_block'
                '+implicit_figures'
                '+pipe_tables'
                '+fenced_code_blocks'
                '+backtick_code_blocks'
                '+strikeout'
                '+task_lists'
            )
            extra_args = [
                '-s',
                '--quiet',
                f'--reference-doc={ref_template}'
            ]

            pypandoc.convert_text(
                cleaned_text,
                'docx',
                format=markdown_format,
                outputfile=output_docx,
                extra_args=extra_args
            )

            # 4. Post-processing
            post_proc = DocxPostProcessor(output_docx, preset=preset)
            post_proc.run()

            file_size = os.path.getsize(output_docx) if os.path.exists(output_docx) else 0
            elapsed = time.time() - t0

            return ConversionResult(
                success=True,
                input_source=md_path,
                output_path=output_docx,
                elapsed_time=round(elapsed, 2),
                file_size_bytes=file_size
            )

        except Exception as e:
            logger.exception("Conversion failed")
            return ConversionResult(
                success=False,
                input_source=md_path,
                output_path=output_docx if 'output_docx' in locals() else "",
                elapsed_time=round(time.time() - t0, 2),
                file_size_bytes=0,
                error_message=str(e)
            )

    def convert_text(self, markdown_text: str, preset: str = "modern", output_dir: Optional[str] = None, title: Optional[str] = None) -> ConversionResult:
        """
        Converts in-memory Markdown text into a .docx file.
        Detects document title for naming and outputs into output_dir (or Desktop).
        """
        t0 = time.time()
        if not output_dir or not os.path.exists(output_dir):
            output_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(output_dir):
                output_dir = os.getcwd()

        if not title:
            title = self.cleaner.extract_title_or_first_line(markdown_text, default_name="剪贴板转换文档")
        
        target_docx = os.path.join(output_dir, f"{title}.docx")
        target_docx = self._resolve_output_path(target_docx)

        try:
            cleaned_text = self.cleaner.process(markdown_text)
            ref_template = self.template_mgr.get_template_path(preset)

            markdown_format = (
                'markdown'
                '-raw_tex'
                '+tex_math_dollars'
                '+yaml_metadata_block'
                '+implicit_figures'
                '+pipe_tables'
                '+fenced_code_blocks'
                '+backtick_code_blocks'
                '+strikeout'
                '+task_lists'
            )
            extra_args = [
                '-s',
                '--quiet',
                f'--reference-doc={ref_template}'
            ]

            pypandoc.convert_text(
                cleaned_text,
                'docx',
                format=markdown_format,
                outputfile=target_docx,
                extra_args=extra_args
            )

            post_proc = DocxPostProcessor(target_docx, preset=preset)
            post_proc.run()

            file_size = os.path.getsize(target_docx) if os.path.exists(target_docx) else 0
            elapsed = time.time() - t0

            return ConversionResult(
                success=True,
                input_source=f"文本内容 ({title})",
                output_path=target_docx,
                elapsed_time=round(elapsed, 2),
                file_size_bytes=file_size,
                is_text_source=True
            )

        except Exception as e:
            logger.exception("Text conversion failed")
            return ConversionResult(
                success=False,
                input_source="剪贴板文本",
                output_path=target_docx if 'target_docx' in locals() else "",
                elapsed_time=round(time.time() - t0, 2),
                file_size_bytes=0,
                error_message=str(e),
                is_text_source=True
            )
