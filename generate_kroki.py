import zlib
import base64

def get_kroki_url(diagram_code, type='mermaid', format='png'):
    diagram_bytes = diagram_code.encode('utf-8')
    compressed = zlib.compress(diagram_bytes, 9)
    encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
    return f'https://kroki.io/{type}/{format}/{encoded}'

arch = '''graph LR
    User([HR Manager]) --> WebApp[Our Website]
    WebApp --> Server[Backend Server]
    Server --> Brain[AI Model]
    Server --> Storage[(Database)]
    Brain -.-> Server'''

components = '''graph TD
    System[Resume Assistant System]
    System --> Reader[Document Reader: Reads PDFs/Word]
    System --> Memory[Memory: Remembers Resumes & Chats]
    System --> AI[AI Engine: Answers Questions]'''

activity = '''flowchart TD
    A[Upload Resumes] --> B[System Reads Text]
    B --> C[Ask a Question]
    C --> D[System Finds Best Resumes]
    D --> E[Get Direct Answer]'''

usecase = '''graph LR
    HR([You - HR user]) --> U[Upload Resumes]
    HR --> C[Chat with Documents]
    HR --> M[Find Best Matches]'''

print('UML_ARCH = \"' + get_kroki_url(arch) + '\"')
print('UML_CLASS = \"' + get_kroki_url(components) + '\"')
print('UML_ACTIVITY = \"' + get_kroki_url(activity) + '\"')
print('UML_USECASE = \"' + get_kroki_url(usecase) + '\"')
