"""Test the quality gate against sample titles."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from cleaning_layer import DataCleaner

cleaner = DataCleaner()

test_cases = [
    # Should REJECT
    ("Main下最新版本Windows下编译运行不成功", "", "Should reject: Chinese"),
    ("Как настроить Docker в Ubuntu", "", "Should reject: Cyrillic/Russian"),
    ("كيفية تثبيت Python", "", "Should reject: Arabic"),
    ("ข้อผิดพลาดในการติดตั้ง Node.js", "", "Should reject: Thai"),
    ("", "", "Should reject: empty"),
    ("Hi", "", "Should reject: too short"),
    ("!!!@@@###$$$%%%^^^&&&", "", "Should reject: code dump"),
    ("/usr/local/bin/python3.12", "", "Should reject: file path"),
    ("Ã¢â‚¬â€œ some broken title", "", "Should reject: mojibake"),
    
    # Should PASS
    ("How to handle 1 million requests in a full stack application", "Description of the problem", "Should pass: normal English"),
    ("Docker pull fails with invalid tar header", "Docker error description", "Should pass: Docker issue"),
    ("GRPC DEADLINE_EXCEEDED even that the server is up", "gRPC issue details", "Should pass: technical problem"),
    ("[P] Using residual ML correction on top of a model", "ML paper discussion", "Should pass: ML topic"),
    ("How to remove packages installed with older versions of Python", "Python cleanup", "Should pass: Python question"),
    ("Building a Web Framework from Scratch", "Web dev project", "Should pass: web dev"),
    ("VS Code Debugging - Node TypeScript", "VS Code debugging tips", "Should pass: tools"),
]

print(f"{'Result':8s} | {'Expected':40s} | Title")
print("-" * 100)
for title, desc, expected in test_cases:
    cleaned = {"title": title, "description": desc}
    passes, reason = cleaner.passes_quality_gate(cleaned)
    result = "PASS" if passes else f"REJECT"
    reason_str = f"({reason})" if not passes else ""
    safe_title = title[:50].encode('ascii', errors='replace').decode('ascii') if title else "[empty]"
    
    # Check if result matches expectation
    should_pass = expected.startswith("Should pass")
    match = "✓" if (passes == should_pass) else "✗ WRONG"
    
    print(f"{result:8s} | {expected:40s} | {safe_title} {reason_str} {match}")
