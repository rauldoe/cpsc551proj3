import multiprocessing
import subprocess

subprocess.run(["python.exe", "-u", "test.py"], shell=True, tdout = subprocess.STDOUT)

