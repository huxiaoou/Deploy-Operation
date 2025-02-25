$sig_date = Read-Host -Prompt "Please input the sig date, format=[YYYYMMDD]"
python main.py -d $sig_date allocated
python main.py -d $sig_date sync
python main.py -d $sig_date positions # translate signals to positions
python main.py -d $sig_date trades # calculate trades from positions

python main.py -d $sig_date orders --sec opn --send # use "--rt" to call real time data
#python main.py -d $sig_date orders --sec cls --send # use "--rt" to call real time data
