$trade_date = Read-Host -Prompt "Please input the signal date, format=[YYYYMMDD]"
$sec = Read-Host -Prompt "Please input the signal type, options=(cls, opn), default = 'cls', no quotes"
if ($sec -eq "")
{
    $sec = "cls"
}
python main.py -d $trade_date orders --sec $sec --rt --send
