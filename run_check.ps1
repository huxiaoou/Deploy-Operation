$trade_date = Read-Host -Prompt "Please input the signal date to check, format=[YYYYMMDD]"
$sec = Read-Host -Prompt "Please input the signal type to check, options=(cls, opn)"
python main.py -d $trade_date check  --sec $sec
