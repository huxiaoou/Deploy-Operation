$sig_date = Read-Host -Prompt "Please input the sig date, format=[YYYYMMDD]"
python main.py -d $sig_date allocated
python main.py -d $sig_date sync
python main.py -d $sig_date positions
python main.py -d $sig_date trades
python main.py -d $sig_date orders
