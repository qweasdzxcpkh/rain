version = VERSION = '0.0.1'

ascii_logo = ASCII_LOGO = '''
 ██▀███   ▄▄▄       ██▓ ███▄    █ 
▓██ ▒ ██▒▒████▄    ▓██▒ ██ ▀█   █ 
▓██ ░▄█ ▒▒██  ▀█▄  ▒██▒▓██  ▀█ ██▒
▒██▀▀█▄  ░██▄▄▄▄██ ░██░▓██▒  ▐▌██▒
░██▓ ▒██▒ ▓█   ▓██▒░██░▒██░   ▓██░
░ ▒▓ ░▒▓░ ▒▒   ▓▒█░░▓  ░ ▒░   ▒ ▒ 
  ░▒ ░ ▒░  ▒   ▒▒ ░ ▒ ░░ ░░   ░ ▒░
  ░░   ░   ░   ▒    ▒ ░   ░   ░ ░ 
   ░           ░  ░ ░           ░ 
'''.strip()  # http://patorjk.com/software/taag/#p=display&f=Bloody&t=Rain

desc = DESC = "A simple async http api server."

from rain.app import Rain
