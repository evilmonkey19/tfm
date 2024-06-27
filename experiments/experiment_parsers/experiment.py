import csv
import os
from dotenv import load_dotenv
import time

load_dotenv()

rounds = int(os.getenv("ROUNDS", 100))

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

results = {
    "regex": [],
    "textfsm": [],
    "ttp": [],
}
for i in range(rounds):
    ## REGEX ##
    import re
    pattern = r"\s+(\d+)\s+(\s*\w*)?(\s*\w*)?(\s*\w*)?(\s*\w*)?(Online|Offline)?$"
    pattern = re.compile(pattern)
    start_time = time.time()
    lines = output.splitlines()
    for line in lines:
        match = pattern.match(line)
        if match:
            pass
    results["regex"].append(time.time() - start_time)

    ## TEXTFSM ##
    import textfsm
    start_time = time.time()
    with open('display_board.textfsm') as f:
        re_table = textfsm.TextFSM(f)
        header = re_table.header
        result = re_table.ParseText(output)
        # print(result)
    results["textfsm"].append(time.time()-start_time)

    ## TTP ##
    from ttp import ttp
    start_time = time.time()
    with open("display_board.ttp") as f:
        parser = ttp(data=output, template=f.read())
        parser.parse()
        result = parser.result()
    results["ttp"].append(time.time()-start_time)

with open(f"results.csv", "w", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(results.keys())
    for i in range(rounds):
        writer.writerow([results[platform][i] for platform in results])
