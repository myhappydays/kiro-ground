from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
import re
import textwrap
import sys
import io
from enum import Enum

# Windows 환경에서 UTF-8 출력 강제 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class MediaType(Enum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    LINK = "link"

@dataclass
class FontConfig:
    class_name: str
    family: str
    url: Optional[str] = None
    google: bool = False

@dataclass
class StyleResult:
    class_list: List[str]
    style_attr: str
    rendered: str

# 폰트 설정: Tailwind 클래스와 매핑
FONT_CONFIG: Dict[str, FontConfig] = {
    "RIDIBatang": FontConfig(
        class_name="font-ridi",
        family="RIDIBatang",
        url="https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_twelve@1.0/RIDIBatang.woff"
    ),
    "GowunDodum": FontConfig(
        class_name="font-gowun",
        family="GowunDodum",
        url="https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_2108@1.1/GowunDodum-Regular.woff"
    ),
    "Monoplex": FontConfig(
        class_name="font-monoplex",
        family="MonoplexKR",
        url="https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_Monoplex-kr@1.0/MonoplexKR-Regular.woff2"
    ),
    "Pretendard": FontConfig(
        class_name="font-pretendard",
        family="Pretendard",
        url="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css"
    ),
    "JetBrains Mono": FontConfig(
        class_name="font-jetbrains",
        family="JetBrains Mono",
        google=True
    ),
    "code": FontConfig(
        class_name="font-jetbrains",
        family="JetBrains Mono",
        google=True
    ),
    "default": FontConfig(
        class_name="font-sans",
        family="Noto Sans KR",
        google=True
    )
}

# 공통 인라인 코드 스타일 상수
INLINE_CODE_STYLE = "font-family: 'JetBrains Mono', monospace"

# 공통 웹폰트 정의 상수
GOOGLE_FONT_LINK = """
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR&family=Roboto&family=JetBrains+Mono&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
"""

CUSTOM_FONT_STYLE = """
<style>
@font-face {
    font-family: 'GowunDodum-Regular';
    src: url('https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_2108@1.1/GowunDodum-Regular.woff') format('woff');
}
@font-face {
    font-family: 'RIDIBatang';
    src: url('https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_twelve@1.0/RIDIBatang.woff') format('woff');
}
@font-face {
    font-family: 'MonoplexKR-Regular';
    src: url('https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_Monoplex-kr@1.0/MonoplexKR-Regular.woff2') format('woff2');
}
pre, code {
    font-family: 'JetBrains Mono', monospace !important;
}
</style>
"""

# 기본 색상 매핑
BASIC_COLORS = {
    "red": "text-red-600",
    "blue": "text-blue-600",
    "green": "text-green-600",
    "yellow": "text-yellow-600",
    "purple": "text-purple-600",
    "pink": "text-pink-600",
    "indigo": "text-indigo-600",
    "teal": "text-teal-600",
    "cyan": "text-cyan-600",
    "orange": "text-orange-600",
    "lime": "text-lime-600",
    "amber": "text-amber-600",
    "gray": "text-gray-600",
    "zinc": "text-zinc-600",
    "slate": "text-slate-600",
    "black": "text-black",
    "white": "text-white"
}

def extract_font_family(classes: List[str]) -> Optional[str]:
    """클래스에서 폰트 패밀리를 추출합니다."""
    for cls in classes:
        for key in FONT_CONFIG:
            if cls.startswith(key):
                return get_font_class(key)
    return None

def extract_color(classes: List[str]) -> Optional[str]:
    """클래스에서 색상을 추출합니다."""
    for cls in classes:
        if cls.startswith("#"):
            color = cls[1:]
            if color.lower() in BASIC_COLORS:
                return BASIC_COLORS[color.lower()]
            return f"style=\"color: #{color}\""
    return None

def apply_inline_styles(text: str) -> str:
    """인라인 스타일을 적용합니다."""
    # 중첩된 마크다운 구문을 처리하기 위해 순서대로 처리
    patterns = [
        (r"~~(.*?)~~", r"<del class='line-through'>\1</del>"),  # 취소선
        (r"==(.*?)==", r"<mark class='bg-yellow-200'>\1</mark>"),  # 하이라이트
        (r"\*\*(.*?)\*\*", r"<strong class='font-bold'>\1</strong>"),  # 굵게
        (r"_(.*?)_", r"<em class='italic'>\1</em>"),  # 기울임
        (r"`(.*?)`", r"<code class='px-1 py-0.5 bg-gray-100 text-sm rounded font-jetbrains'>\1</code>")  # 코드
    ]
    
    # 중첩된 패턴을 처리하기 위해 여러 번 반복
    prev_text = None
    current_text = text
    while prev_text != current_text:
        prev_text = current_text
        for pattern, replacement in patterns:
            current_text = re.sub(pattern, replacement, current_text)
    
    return current_text

def parse_styles(lines: List[str]) -> Dict:
    """스타일 정의를 파싱합니다."""
    styles = {}
    style_mode = False
    current_parent = None
    current_child = None

    for line in lines:
        stripped = line.strip()
        if stripped == "<style>":
            style_mode = True
            continue
        elif stripped == "<>":
            style_mode = False
            continue
            
        if style_mode:
            if "=" in line and not line.strip().startswith(":"):
                key, val = line.split("=", 1)
                key = key.strip("[] ")
                
                classes = []
                md_structure = None
                
                # 마크다운 구조 추출
                structure_match = re.search(r"\{([^}]+)\}", val)
                if structure_match:
                    md_structure = structure_match.group(1)
                    
                # 스타일 속성 파싱
                for pattern, extractor in [
                    (r"\[=([^\]]+)\]", lambda m: classes.append(m.group(1))),  # 폰트
                    (r"\[#([^\]]+)\]", lambda m: classes.append(f"#{m.group(1)}")),  # 색상
                    (r"\[\+([^\]]+)\]", lambda m: classes.append(f"+{m.group(1)}")),  # 아이콘
                    (r"\[\$([^\]]+)\]", lambda m: classes.append(m.group(1)))  # Tailwind
                ]:
                    for match in re.finditer(pattern, val):
                        extractor(match)
                
                styles[key] = {
                    "classes": classes,
                    "md_structure": md_structure,
                    "children": {}
                }
                current_parent = key
                
            elif "=" in line and line.strip().startswith(":") and not line.strip().startswith("::"):
                if current_parent:
                    child_key, val = line.split("=", 1)
                    child_key = child_key.strip(": ")
                    
                    classes = []
                    md_structure = None
                    
                    # 마크다운 구조 추출
                    structure_match = re.search(r"\{([^}]+)\}", val)
                    if structure_match:
                        md_structure = structure_match.group(1)
                    
                    # 스타일 속성 파싱
                    for pattern, extractor in [
                        (r"\[=([^\]]+)\]", lambda m: classes.append(m.group(1))),
                        (r"\[#([^\]]+)\]", lambda m: classes.append(f"#{m.group(1)}")),
                        (r"\[\+([^\]]+)\]", lambda m: classes.append(f"+{m.group(1)}")),
                        (r"\[\$([^\]]+)\]", lambda m: classes.append(m.group(1)))
                    ]:
                        for match in re.finditer(pattern, val):
                            extractor(match)
                    
                    styles[current_parent]["children"][child_key] = {
                        "classes": classes,
                        "md_structure": md_structure
                    }
                    current_child = child_key
                    
            elif "=" in line and line.strip().startswith("::"):
                if current_parent and current_child:
                    child_child_key, val = line.split("=", 1)
                    child_child_key = child_child_key.strip(": ")
                    
                    classes = []
                    md_structure = None
                    
                    # 마크다운 구조 추출
                    structure_match = re.search(r"\{([^}]+)\}", val)
                    if structure_match:
                        md_structure = structure_match.group(1)
                    
                    # 스타일 속성 파싱
                    for pattern, extractor in [
                        (r"\[=([^\]]+)\]", lambda m: classes.append(m.group(1))),
                        (r"\[#([^\]]+)\]", lambda m: classes.append(f"#{m.group(1)}")),
                        (r"\[\+([^\]]+)\]", lambda m: classes.append(f"+{m.group(1)}")),
                        (r"\[\$([^\]]+)\]", lambda m: classes.append(m.group(1)))
                    ]:
                        for match in re.finditer(pattern, val):
                            extractor(match)
                    
                    if "grandchildren" not in styles[current_parent]["children"][current_child]:
                        styles[current_parent]["children"][current_child]["grandchildren"] = {}
                        
                    styles[current_parent]["children"][current_child]["grandchildren"][child_child_key] = {
                        "classes": classes,
                        "md_structure": md_structure
                    }

    return styles

def get_style_classes(style_name: str, styles: Dict) -> Dict:
    """스타일 클래스를 가져옵니다."""
    parts = style_name.split(':')
    base_style = parts[0]
    
    result = {
        "classes": [],
        "md_structure": None
    }
    
    if base_style not in styles:
        return result
    
    # Start with base style
    result["classes"] = styles[base_style]["classes"].copy()
    result["md_structure"] = styles[base_style].get("md_structure")
    
    # Apply child style if specified
    if len(parts) > 1 and parts[1] in styles[base_style]["children"]:
        child_style = styles[base_style]["children"][parts[1]]
        
        # For each class in child classes, check if it should override a parent class
        if "classes" in child_style:
            # Handle font, color, and icon overrides
            for child_class in child_style["classes"]:
                # For fonts ([=Font])
                if any(child_class == font_name for font_name in FONT_CONFIG):
                    result["classes"] = [cls for cls in result["classes"] 
                                        if not any(cls == font_name for font_name in FONT_CONFIG)]
                    result["classes"].append(child_class)
                # For colors ([#color])
                elif child_class.startswith('#'):
                    result["classes"] = [cls for cls in result["classes"] if not cls.startswith('#')]
                    result["classes"].append(child_class)
                # For icons ([+icon])
                elif child_class.startswith('+'):
                    result["classes"] = [cls for cls in result["classes"] if not cls.startswith('+')]
                    result["classes"].append(child_class)
                else:
                    # For other Tailwind classes, just add them
                    result["classes"].append(child_class)
        
        # Override markdown structure if defined in child
        if child_style.get("md_structure"):
            result["md_structure"] = child_style["md_structure"]
        
        # Apply grandchild style if specified
        if len(parts) > 2 and "grandchildren" in child_style and parts[2] in child_style["grandchildren"]:
            grandchild_style = child_style["grandchildren"][parts[2]]
            
            # Same logic for grandchild classes
            if "classes" in grandchild_style:
                for gc_class in grandchild_style["classes"]:
                    # For fonts
                    if any(gc_class == font_name for font_name in FONT_CONFIG):
                        result["classes"] = [cls for cls in result["classes"] 
                                           if not any(cls == font_name for font_name in FONT_CONFIG)]
                        result["classes"].append(gc_class)
                    # For colors
                    elif gc_class.startswith('#'):
                        result["classes"] = [cls for cls in result["classes"] if not cls.startswith('#')]
                        result["classes"].append(gc_class)
                    # For icons
                    elif gc_class.startswith('+'):
                        result["classes"] = [cls for cls in result["classes"] if not cls.startswith('+')]
                        result["classes"].append(gc_class)
                    else:
                        # For other classes, just add them
                        result["classes"].append(gc_class)
            
            # Override markdown structure if defined in grandchild
            if grandchild_style.get("md_structure"):
                result["md_structure"] = grandchild_style["md_structure"]
    
    return result

def generate_font_styles() -> Dict[str, str]:
    """폰트 스타일을 생성합니다."""
    google_fonts = []
    custom_fonts_css = []
    processed_fonts = set()  # Track fonts that have already been processed
    
    for font in FONT_CONFIG.values():
        if font.google:
            font_family = font.family.replace(" ", "+")
            if font_family not in google_fonts:
                google_fonts.append(font_family)
        elif font.url and font.family not in processed_fonts:
            processed_fonts.add(font.family)  # Mark this font as processed
            if font.url.endswith(".css"):
                custom_fonts_css.append(f'<link rel="stylesheet" href="{font.url}">')
                continue
                
            font_format = font.url.split('.')[-1]
            font_css = f"""
@font-face {{
    font-family: '{font.family}';
    src: url('{font.url}') format('{font_format}');
    font-display: swap;
}}"""
            custom_fonts_css.append(font_css)
    
    google_fonts_link = ""
    if google_fonts:
        fonts_str = "&family=".join(google_fonts)
        google_fonts_link = f"""
<link href="https://fonts.googleapis.com/css2?family={fonts_str}&display=swap" rel="stylesheet">
"""
    
    tailwind_config = """
<script>
tailwind.config = {
  theme: {
    extend: {
      fontFamily: {
"""
    
    # Track font class names to avoid duplication in Tailwind config
    processed_class_names = set()
    for key, font in FONT_CONFIG.items():
        class_name = font.class_name.replace("font-", "")
        if class_name not in processed_class_names:
            processed_class_names.add(class_name)
            tailwind_config += f"        '{class_name}': ['{font.family}', ...tailwind.defaultTheme.fontFamily.sans],\n"
    
    tailwind_config += """      }
    }
  }
}
</script>
"""
    
    code_style = f"""
pre, code {{
    font-family: '{FONT_CONFIG["code"].family}', monospace !important;
}}
"""
    
    custom_fonts_style = "\n".join([css for css in custom_fonts_css if not css.startswith('<link')])
    custom_fonts_links = "\n".join([css for css in custom_fonts_css if css.startswith('<link')])
    
    return {
        "google_fonts": google_fonts_link,
        "custom_fonts_links": custom_fonts_links,
        "custom_fonts": f"<style>\n{custom_fonts_style}\n{code_style}\n</style>",
        "tailwind_config": tailwind_config
    }

def get_font_class(font_name: str) -> str:
    """폰트 이름에서 Tailwind 클래스를 반환합니다."""
    return FONT_CONFIG.get(font_name, FONT_CONFIG["default"]).class_name

def render_media(line: str) -> Optional[str]:
    """미디어 요소를 렌더링합니다."""
    media_match = re.match(r"@([a-z]+): *([^ ]+) *! *(.*)", line)
    if not media_match:
        return None
        
    media_type, url, desc = media_match.groups()
    url = url.strip()
    desc = desc.strip()
    
    try:
        media_type_enum = MediaType(media_type)
    except ValueError:
        return None
    
    media_templates = {
        MediaType.IMAGE: f'<figure class="my-4"><img src="{url}" alt="{desc}" title="{desc}" class="rounded-md"/><figcaption class="text-center text-sm text-gray-600 mt-1">{desc}</figcaption></figure>',
        MediaType.AUDIO: f'<figure class="my-4"><audio controls src="{url}" title="{desc}" class="mt-1 w-full"></audio><figcaption class="text-center text-sm text-gray-600 mt-1">{desc}</figcaption></figure>',
        MediaType.VIDEO: f'<figure class="my-4"><video controls src="{url}" title="{desc}" class="rounded-md mt-1 w-full"></video><figcaption class="text-center text-sm text-gray-600 mt-1">{desc}</figcaption></figure>',
        MediaType.LINK: f'<a href="{url}" class="text-blue-600 underline" title="{desc}">{desc}</a>'
    }
    
    return media_templates.get(media_type_enum)

def render_inline_kiro(line: str, styles: Dict) -> str:
    """인라인 Kiro 요소를 렌더링합니다."""
    # 인라인 스타일 태그가 있는지 확인
    if "[" in line and "]" in line and not line.startswith("[") and not ("<>" in line):
        # 복합 스타일 태그 처리
        result = ""
        pos = 0
        while pos < len(line):
            bracket_start = line.find("[", pos)
            if bracket_start == -1:
                # 남은 텍스트 처리
                result += apply_inline_styles(line[pos:])
                break
                
            # 태그 이전 텍스트 처리
            if bracket_start > pos:
                result += apply_inline_styles(line[pos:bracket_start])
                
            bracket_end = line.find("]", bracket_start)
            if bracket_end == -1:
                # 닫히지 않은 태그
                result += line[bracket_start:]
                break
                
            style_name = line[bracket_start+1:bracket_end]
            
            # 태그 뒤 컨텐츠 찾기
            content_start = bracket_end + 1
            next_bracket = line.find("[", content_start)
            if next_bracket == -1:
                content = line[content_start:]
                pos = len(line)
            else:
                content = line[content_start:next_bracket]
                pos = next_bracket
                
            # 스타일 적용
            if style_name in styles:
                style_result = process_style_content(style_name, content.strip(), styles)
                result += f'<span class="{" ".join(style_result.class_list)}" {style_result.style_attr}>{style_result.rendered}</span>'
            else:
                result += f'[{style_name}]{apply_inline_styles(content)}'
                
        return result
    
    # 기본 아이콘 접두사 처리
    emoji_prefix = re.match(r"\[\+(.+?)\]\s*(.*)", line)
    if emoji_prefix:
        icon, content = emoji_prefix.groups()
        return f"<span>{icon}</span> {apply_inline_styles(content)}"
            
    return apply_inline_styles(line)

def process_style_content(style_name: str, content: str, styles: Dict) -> StyleResult:
    """스타일 콘텐츠를 처리합니다."""
    style_result = get_style_classes(style_name, styles)
    class_list = []
    md_structure = style_result["md_structure"]
    
    # 먼저 인라인 스타일 적용
    processed_content = render_inline_kiro(content, styles)
    
    if md_structure:
        # 마크다운 구조 파싱
        md_elements = []
        current_element = ""
        
        # 마크다운 구조를 파싱하여 요소 목록 생성
        for char in md_structure:
            if char in ['#', '*', '_', '`', '-', '>', '|', '~', '=', '^', '[', ']', '(', ')']:
                if current_element:
                    md_elements.append(current_element)
                current_element = char
            else:
                current_element += char
        
        if current_element:
            md_elements.append(current_element)
            
        # 중복된 마크다운 요소 제거
        md_elements = list(dict.fromkeys(md_elements))
        
        # 마크다운 요소를 우선순위에 따라 정렬
        priority_order = {
            '#': 1, '##': 2, '###': 3,  # 헤딩
            '>': 4,  # 인용
            '-': 5,  # 리스트
            '|': 6,  # 단락
            '**': 7, '_': 8,  # 강조
            '`': 9,  # 코드
            '~~': 10, '==': 11  # 기타
        }
        md_elements.sort(key=lambda x: priority_order.get(x, 999))
        
        # 마크다운 요소 적용 (순서 중요)
        for element in md_elements:
            if element.startswith('#'):
                level = len(element)
                if level == 1:
                    processed_content = f"<h1 class='mt-6 mb-4 text-4xl font-bold'>{processed_content}</h1>"
                elif level == 2:
                    processed_content = f"<h2 class='mt-5 mb-3 text-3xl font-bold'>{processed_content}</h2>"
                elif level == 3:
                    processed_content = f"<h3 class='mt-4 mb-2 text-2xl font-bold'>{processed_content}</h3>"
            elif element == '**':
                # 기존 strong 태그가 있는지 확인하고 중복 방지
                if '<strong' not in processed_content:
                    processed_content = f"<strong class='font-bold'>{processed_content}</strong>"
            elif element == '_':
                # 기존 em 태그가 있는지 확인하고 중복 방지
                if '<em' not in processed_content:
                    processed_content = f"<em class='italic'>{processed_content}</em>"
            elif element == '`':
                # 기존 code 태그가 있는지 확인하고 중복 방지
                if '<code' not in processed_content:
                    processed_content = f"<code class='px-1 py-0.5 bg-gray-100 text-sm rounded font-jetbrains'>{processed_content}</code>"
            elif element == '-':
                processed_content = f"<li class='ml-6'>{processed_content}</li>"
            elif element == '>':
                processed_content = f"<blockquote class='my-4 border-l-4 pl-4 italic text-gray-600'>{processed_content}</blockquote>"
            elif element == '|':
                processed_content = f"<p class='mb-4'>{processed_content}</p>"
            elif element == '~~':
                processed_content = f"<del class='line-through'>{processed_content}</del>"
            elif element == '==':
                processed_content = f"<mark class='bg-yellow-200'>{processed_content}</mark>"
        
        # 리스트 항목인 경우 리스트 컨테이너 추가
        if any(element == '-' for element in md_elements):
            processed_content = f"<ul class='list-disc ml-6 mb-4'>{processed_content}</ul>"
    
    # 스타일 클래스 처리
    style_elements = style_result["classes"].copy()
    icon_prefix = ""
    style_attr = ""
    
    # 색상 클래스 추출
    color_classes = [cls for cls in style_elements if cls.startswith('text-')]
    
    for style in style_elements:
        if style.startswith('+'):
            icon = style[1:]
            icon_prefix = f"{icon} "
        elif style.startswith('#'):
            color_attr = extract_color([style])
            if color_attr and color_attr.startswith('text-'):
                class_list.append(color_attr)
            elif color_attr:
                style_attr = color_attr
        elif style in FONT_CONFIG:
            font_class = get_font_class(style)
            class_list.append(font_class)
        elif style == "MonoplexKR-Regular":  # 특수 케이스 처리
            class_list.append("font-monoplex")
        else:
            class_list.append(style)
    
    # 기본 마진 추가
    if not any(cls.startswith("m") for cls in class_list):
        class_list.append("mb-4")
    
    # 아이콘 접두사 추가
    if icon_prefix:
        processed_content = icon_prefix + processed_content
    
    # 색상 클래스가 있는 경우 strong 태그에 색상 클래스 추가
    if color_classes:
        processed_content = re.sub(
            r'<strong class=\'font-bold\'>(.*?)</strong>',
            lambda m: f'<strong class=\'font-bold {" ".join(color_classes)}\'>{m.group(1)}</strong>',
            processed_content
        )
    
    return StyleResult(
        class_list=class_list,
        style_attr=style_attr,
        rendered=processed_content
    )

def is_toggle_line(line: str) -> bool:
    """토글 라인인지 확인합니다."""
    return bool(re.match(r"(#{1,6})?\s*(>{1,})\s*(.+)", line))

def get_toggle_depth(line: str) -> int:
    """토글 라인의 깊이를 반환합니다."""
    match = re.match(r"(#{1,6})?\s*(>{1,})\s*(.+)", line)
    return len(match.group(2)) if match else 0

def has_deeper_toggle_next(lines: List[str], i: int, current_depth: int) -> bool:
    """다음 라인이 더 깊은 토글인지 확인합니다."""
    if i + 1 < len(lines):
        next_line = lines[i + 1]
        next_match = is_toggle_line(next_line)
        if next_match:
            next_depth = get_toggle_depth(next_line)
            return next_depth > current_depth
    return False

def process_toggle_content(lines: List[str], start_index: int, depth: int, styles: Dict) -> Tuple[List[str], int]:
    """토글 내부 콘텐츠를 재귀적으로 처리합니다."""
    content_html = []
    i = start_index
    
    while i < len(lines):
        line = lines[i]
        
        if is_toggle_line(line):
            current_depth = get_toggle_depth(line)
            
            if current_depth <= depth:
                return content_html, i
            
            next_content, next_i = process_toggle_content(lines, i + 1, current_depth, styles)
            
            match = re.match(r"(#{1,6})?\s*(>{1,})\s*(.+)", line)
            heading, toggle_markers, content = match.groups()
            rendered_content = render_inline_kiro(content, styles)
            
            if heading:
                heading_level = len(heading)
                content_html.append(f'<details open>')
                content_html.append(f'<summary>{rendered_content}</summary>')
                content_html.append('<div>')
            else:
                content_html.append(f'<details open>')
                content_html.append(f'<summary>{rendered_content}</summary>')
                content_html.append('<div>')
            
            content_html.extend(next_content)
            content_html.append('</div></details>')
            
            i = next_i
            continue
        
        content_html.append(f'<p class="mb-2">{render_inline_kiro(line.strip(), styles)}</p>')
        i += 1
    
    return content_html, i

def render_kiro(text: str) -> Tuple[str, str]:
    """Kiro 텍스트를 HTML로 렌더링합니다."""
    lines = text.split("\n")
    html = []
    in_code_block = False
    code_lines = []
    in_ul = False
    in_ol = False
    in_custom_list = False
    in_quote_block = False
    toggle_stack = []
    quote_lines = []
    styles = parse_styles(lines)
    style_mode = False

    print("🔍 Kiro 문서 렌더링 중...")

    global_classes = []
    if "!global" in styles:
        global_classes = styles["!global"]["classes"]

    def is_font(cls): return cls in FONT_CONFIG
    def is_color(cls): return cls.startswith("#")
    def is_tailwind(cls): return not cls.startswith("+") and not is_font(cls) and not is_color(cls)

    global_class_str = " ".join([
        get_font_class(c) if is_font(c) else
        extract_color([c]).replace('style="', '').replace('"', '') if is_color(c) else
        c
        for c in global_classes if is_tailwind(c) or is_font(c) or is_color(c)
    ])

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if stripped == "<style>":
            style_mode = True
            i += 1
            continue
        elif stripped == "<>":
            style_mode = False
            i += 1
            continue
        elif style_mode:
            i += 1
            continue
        elif stripped.startswith("[") and "=" in stripped and "]" in stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            if not in_code_block:
                code_html = "\n".join(code_lines)
                html.append(f'<pre><code>{code_html}</code></pre>')
                code_lines = []
            i += 1
            continue
        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        toggle_match = is_toggle_line(line)
        
        if toggle_stack and not toggle_match:
            while toggle_stack:
                html.append('</div></details>')
                toggle_stack.pop()
        
        if toggle_match:
            match = re.match(r"(#{1,6})?\s*(>{1,})\s*(.+)", line)
            heading, toggle_markers, content = match.groups()
            current_depth = len(toggle_markers)
            
            is_toggle_node = has_deeper_toggle_next(lines, i, current_depth)
            
            while toggle_stack and toggle_stack[-1][0] >= current_depth:
                html.append('</div></details>')
                toggle_stack.pop()
            
            rendered_content = render_inline_kiro(content, styles)
            
            if is_toggle_node:
                toggle_stack.append((current_depth, content))
                
                if heading:
                    heading_level = len(heading)
                    html.append(f'<details open>')
                    html.append(f'<summary>{rendered_content}</summary>')
                    html.append('<div>')
                else:
                    html.append(f'<details open>')
                    html.append(f'<summary>{rendered_content}</summary>')
                    html.append('<div>')
            else:
                if heading:
                    heading_level = len(heading)
                    html.append(f'<h{heading_level} class="text-{heading_level}xl font-bold mt-{heading_level + 2} mb-2">{rendered_content}</h{heading_level}>')
                else:
                    html.append(f'<p class="mb-4">{rendered_content}</p>')
            
            i += 1
            continue

        if line.startswith("| "):
            quote_lines.append(render_inline_kiro(line[2:], styles))
            in_quote_block = True
            i += 1
            continue
        elif in_quote_block and not line.startswith("| "):
            quote_html = "<br>".join(quote_lines)
            html.append(f'<blockquote>{quote_html}</blockquote>')
            quote_lines = []
            in_quote_block = False

        if "[" in line and "]" in line:
            if "<>" in line:
                processed_html = process_styled_line(line, styles)
                html.append(processed_html)
                i += 1
                continue

        media_html = render_media(line)
        if media_html:
            html.append(media_html)
            i += 1
            continue

        custom_list_match = re.match(r"^-([0-9A-Za-z\.]+)\s+(.*)", line)
        if custom_list_match:
            if not in_custom_list:
                html.append('<ul class="custom-list pl-0 -ml-20">')
                in_custom_list = True
            list_key, content = custom_list_match.groups()
            styled_key = f'<span class="inline-block w-[6em] text-right text-gray-500 font-mono">{list_key}</span>'
            html.append(f'<li>{styled_key} {render_inline_kiro(content, styles)}</li>')
            i += 1
            continue
        elif in_custom_list:
            html.append('</ul>')
            in_custom_list = False

        if re.match(r"^\d+\. ", line):
            if not in_ol:
                html.append("<ol>")
                in_ol = True
            cleaned = re.sub(r'^\d+\. ', '', line)
            html.append(f"<li>{render_inline_kiro(cleaned, styles)}</li>")
            i += 1
            continue
        elif in_ol:
            html.append("</ol>")
            in_ol = False

        list_match = re.match(r"^(\s*)- (.*)", line)
        if list_match:
            indent, content = list_match.groups()
            indent_level = len(indent) // 2
            
            if indent_level > 0:
                if not in_ul:
                    html.append("<ul>")
                    in_ul = True
                
                content_html = render_inline_kiro(content, styles)
                html.append(f"<li class=\"ml-{indent_level * 4}\">{content_html}</li>")
            else:
                if not in_ul:
                    html.append("<ul>")
                    in_ul = True
                html.append(f"<li>{render_inline_kiro(content, styles)}</li>")
            i += 1
            continue
        
        # 대시 중첩 리스트 처리 (-- 또는 --- 형식)
        dash_list_match = re.match(r"^(-+)\s+(.*)", line)
        if dash_list_match and not list_match:
            dashes, content = dash_list_match.groups()
            indent_level = len(dashes) - 1  # 첫 번째 대시를 뺀 개수가 들여쓰기 레벨
            
            if indent_level >= 0:
                if not in_ul:
                    html.append("<ul>")
                    in_ul = True
                
                content_html = render_inline_kiro(content, styles)
                if indent_level > 0:
                    html.append(f"<li class=\"ml-{indent_level * 4}\">{content_html}</li>")
                else:
                    html.append(f"<li>{content_html}</li>")
                i += 1
                continue
            
        elif in_ul:
            html.append("</ul>")
            in_ul = False

        if line.startswith("### "):
            html.append(f'<h3>{render_inline_kiro(line[4:], styles)}</h3>')
            i += 1
            continue
        elif line.startswith("## "):
            html.append(f'<h2>{render_inline_kiro(line[3:], styles)}</h2>')
            i += 1
            continue
        elif line.startswith("# "):
            html.append(f'<h1>{render_inline_kiro(line[2:], styles)}</h1>')
            i += 1
            continue

        if stripped == "---":
            html.append("<hr>")
        elif not stripped:
            html.append("<p></p>")
        else:
            html.append(f"<p>{render_inline_kiro(line, styles)}</p>")

        i += 1

    if in_quote_block:
        quote_html = "<br>".join(quote_lines)
        html.append(f'<blockquote>{quote_html}</blockquote>')
    if in_ul:
        html.append("</ul>")
    if in_ol:
        html.append("</ol>")
    if in_custom_list:
        html.append("</ul>")
        
    while toggle_stack:
        html.append('</div></details>')
        toggle_stack.pop()

    print("✅ HTML 생성 완료")
    return "\n".join(html), global_class_str

def convert_file(input_path: str, output_path: str) -> None:
    """Kiro 파일을 HTML로 변환합니다."""
    print(f"📂 입력 파일: {input_path}")
    try:
        text = Path(input_path).read_text(encoding="utf-8")
        html_body, global_class_str = render_kiro(text)
        
        font_styles = generate_font_styles()

        html = textwrap.dedent(f"""
        <html>
        <head>
            <meta charset=\"UTF-8\">
            <title>Kiro Rendered Document</title>
            <script src=\"https://cdn.tailwindcss.com?plugins=typography\"></script>
            {font_styles["google_fonts"]}
            {font_styles["custom_fonts_links"]}
            {font_styles["custom_fonts"]}
            {font_styles["tailwind_config"]}
            <style type="text/css">
                /* 커스텀 리스트 스타일 */
                .prose :where(ul.custom-list):not(:where([class~="not-prose"] *)) {{
                    list-style-type: none;
                    padding-left: 0em;
                }}
                .prose :where(ul.custom-list li):not(:where([class~="not-prose"] *)) {{
                    display: flex;
                    align-items: baseline;
                    margin-top: 0.5em;
                    margin-bottom: 0.5em;
                }}
                .prose :where(ul.custom-list li span):not(:where([class~="not-prose"] *)) {{
                    font-family: 'JetBrains Mono', monospace;
                    color: #6b7280;
                    margin-right: 0.5em;
                    min-width: 3em;
                    display: inline-block;
                    text-align: right;
                }}

                /* 토글 스타일 개선 */
                details {{
                    position: relative;
                    margin: 0em 0;
                    padding-left: 1em;
                }}

                details::before {{
                    content: none;
                }}

                details > div {{
                    position: relative;
                    margin-left: 1em;
                    padding-left: 1em;
                }}

                details > div::before {{
                    content: '';
                    position: absolute;
                    left: -1em;
                    top: 0;
                    bottom: 0;
                    width: 2px;
                    background-color: #e5e7eb;
                    border-radius: 1px;
                }}

                details summary {{
                    margin-bottom: 0.5em;
                }}

                /* 헤딩 마진 조정 */
                .prose :where(h1, h2, h3, h4, h5, h6):not(:where([class~="not-prose"] *)) {{
                    margin-bottom: 0.3em;
                }}
            </style>
        </head>
        <body class=\"min-h-screen bg-gray-50 text-gray-800 font-sans\">
            <div class=\"max-w-3xl mx-auto py-10 px-4 sm:px-6\">
                <article class="prose prose-slate max-w-none {global_class_str}">
                    {html_body}
                </article>
            </div>
        </body>
        </html>
        """)

        Path(output_path).write_text(html, encoding="utf-8")
        print(f"💾 저장 완료: {output_path}")
    except Exception as e:
        import traceback
        print(f"❌ 오류 발생: {e}")
        traceback.print_exc()
        sys.exit(1)

def process_styled_line(line: str, styles: Dict) -> str:
    """스타일 태그가 포함된 줄을 처리합니다."""
    if "<>" not in line:
        return render_inline_kiro(line, styles)
        
    style_tags = re.findall(r"\[([^\]]+)\]", line)
    if len(style_tags) > 1:
        processed_parts = []
        
        style_pattern = r"\[([^\]]+)\](.*?)(?=\[|\s*<>|$)"
        for match in re.finditer(style_pattern, line):
            style_name = match.group(1)
            content = match.group(2).strip()
            
            if content:
                if style_name in styles:
                    result = process_style_content(style_name, content, styles)
                    processed_parts.append(
                        f'<span class="{" ".join(result.class_list)}" {result.style_attr}>{result.rendered}</span>'
                    )
                else:
                    content_rendered = render_inline_kiro(content, styles)
                    processed_parts.append(
                        f'<span>[{style_name}]{content_rendered}</span>'
                    )
        
        close_pos = line.find("<>")
        if close_pos > 0 and close_pos + 2 < len(line):
            tail = line[close_pos + 2:].strip()
            if tail:
                tail_rendered = render_inline_kiro(tail, styles)
                processed_parts.append(f'{tail_rendered}')
        
        return f'<div class="mb-4">{"".join(processed_parts)}</div>'
    else:
        style_match = re.match(r"\[(.+?)\](.*?)<>(.*)?", line)
        if style_match:
            style_name, content, tail = style_match.groups()
            content = content.strip()
            
            if style_name in styles:
                result = process_style_content(style_name, content, styles)
                tail_rendered = render_inline_kiro(tail.strip(), styles) if tail else ""
                
                return f'<div class="{" ".join(result.class_list)}" {result.style_attr}>{result.rendered} {tail_rendered}</div>'
            else:
                content_rendered = render_inline_kiro(content, styles)
                tail_rendered = render_inline_kiro(tail.strip(), styles) if tail else ""
                return f'<div class="mb-4">[{style_name}]{content_rendered}<> {tail_rendered}</div>'
    
    return render_inline_kiro(line, styles)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("📌 사용법: python kiro_renderer.py input.kiro output.html")
    else:
        try:
            convert_file(sys.argv[1], sys.argv[2])
            print("🎉 렌더링 성공!")
        except Exception as e:
            import traceback
            print(f"❌ 오류 발생: {e}")
            traceback.print_exc()
            sys.exit(1)
