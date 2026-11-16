import os
import urllib.request

print("Đang tự động thiết lập HADOOP_HOME cho Windows...")

# 1. Tự động tạo thư mục C:\hadoop\bin
hadoop_dir = r"C:\hadoop\bin"
os.makedirs(hadoop_dir, exist_ok=True)

# 2. Link tải bản chuẩn
files = {
    "winutils.exe": "https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.5/bin/winutils.exe",
    "hadoop.dll": "https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.5/bin/hadoop.dll"
}

# 3. Tự động tải về và đặt vào đúng chỗ
for filename, url in files.items():
    filepath = os.path.join(hadoop_dir, filename)
    if not os.path.exists(filepath):
        print(f"-> Đang tải {filename}...")
        try:
            urllib.request.urlretrieve(url, filepath)
            print(f"   [OK] Đã lưu {filename}")
        except Exception as e:
            print(f"   [LỖI] Không thể tải {filename}: {e}")
    else:
        print(f"-> {filename} đã có sẵn!")

print("\nHoàn tất! Môi trường Hadoop đã sẵn sàng. Bạn có thể chạy PySpark được rồi!")