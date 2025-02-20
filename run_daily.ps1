$sig_date = Read-Host -Prompt "Please input the sig date, format=[YYYYMMDD]"
python main.py -d $sig_date allocated
python main.py -d $sig_date sync
python main.py -d $sig_date positions # translate signals to positions
python main.py -d $sig_date trades # calculate trades from positions

# python main.py -d $sig_date orders --sec opn --type last # type = ["last", "real"]
# python main.py -d $sig_date orders --sec cls --type last # type = ["last", "real"]
# python main.py -d $sig_date orders --sec cls --type real # type = ["last", "real"]
