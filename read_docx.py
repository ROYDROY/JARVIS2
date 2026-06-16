import zipfile
import xml.etree.ElementTree as ET
import sys
import os

def read_docx(filename):
    if not os.path.exists(filename):
        return f"File not found: {filename}"
    text = []
    try:
        with zipfile.ZipFile(filename) as docx:
            xml_content = docx.read('word/document.xml')
            tree = ET.XML(xml_content)
            # XML namespace for Word
            WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
            PARA = WORD_NAMESPACE + 'p'
            TEXT = WORD_NAMESPACE + 't'
            for paragraph in tree.iter(PARA):
                texts = [node.text for node in paragraph.iter(TEXT) if node.text]
                if texts:
                    text.append(''.join(texts))
        return '\n'.join(text)
    except Exception as e:
        return f"Error reading {filename}: {e}"

if __name__ == '__main__':
    if len(sys.argv) > 2:
        out_file = sys.argv[2]
        content = read_docx(sys.argv[1])
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(content)
