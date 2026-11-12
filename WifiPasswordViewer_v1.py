'''
Wifi password Viewer
'''
import subprocess

profiles = subprocess.check_output('netsh wlan show profiles', shell=True).decode()
names = [line.split(":")[1].strip() for line in profiles.split('\n') if "All User Profile" in line]

for i, n in enumerate(names, 1):
    print(f"[{i}] {n}")
ch = int(input("Enter the number of the profile to view the password: "))
n = names[ch - 1]
results = subprocess.check_output(f'netsh wlan show profile "{n}" key=clear', shell=True).decode()
print(f"\n{results}\n")
