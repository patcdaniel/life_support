'''
This the script that will run the lifesupport code. There are three classes that will be used for this,
LifeSupport, Timer, and WebReport
'''

import lifesupport

### Start Program
ls = lifesupport.LifeSupport()
ls.open_com()
wr = lifesupport.WebReport()
wr.start_web_report()

while ls.is_open():
    ls.get_case()
    wr.update_plot(ls.get_status()[4]) # Plot the state of the float switches

