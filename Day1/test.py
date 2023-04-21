import time
import subprocess

adb_path = "/Users/helinglin/MyCode/platform-tools/adb"

# subprocess.getoutput(f"{adb_path} kill-server)")
subprocess.getoutput(f"{adb_path} start-server")

res = subprocess.getoutput(f"{adb_path} devices")
print(res)

# emulator-5554   device

# subprocess.getoutput(f"{adb_path} -s emulator-5554 shell input tap 纵坐标 横坐标" )

# subprocess.getoutput(f"{adb_path} -s emulator-5554 shell input swipe 纵坐标 横坐标 纵坐标 横坐标 400 " )

while True:
    subprocess.getoutput(f"{adb_path} -s emulator-5554 shell input swipe 336 1088 653 294 400 " )
    time.sleep(3)

