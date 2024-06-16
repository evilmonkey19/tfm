import time

output = """
  -------------------------------------------------------------------------
  SlotID  BoardName  Status          SubType0  SubType1  Online/Offline  
  -------------------------------------------------------------------------
  0       H901TWEDE  Normal                                            
  1                          
  2       H901PILA   Normal                                            
  3       H901MPSCE  Normal          CPCF                              
  4       H901MPSCE  Standby_failed  CPCF                Offline       
  5                                                                    
  -------------------------------------------------------------------------
"""

## REGEX ##
import re
pattern = r"\s+(\d+)\s+(\s*\w*)?(\s*\w*)?(\s*\w*)?(\s*\w*)?(Online|Offline)?$"
start_time = time.time()
for line in output.splitlines():
    match = re.match(pattern, line)
    if match:
        pass
        # print(match.groups())
print(f"Time: {time.time()- start_time}")

## TEXTFSM ##
import textfsm
start_time = time.time()
with open('display_board.textfsm') as f:
    re_table = textfsm.TextFSM(f)
    header = re_table.header
    result = re_table.ParseText(output)
    # print(result)
print(f"Time: {time.time()- start_time}")

## TTP ##
from ttp import ttp
start_time = time.time()
with open("display_board.ttp") as f:
    parser = ttp(data=output, template=f.read())
    parser.parse()
    result = parser.result()
print(f"Time: {time.time()- start_time}")