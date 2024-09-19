
from time import sleep
import lauterbach.trace32.rcl as t32

# print(t32.VERSION)

dbg = t32.connect(node='127.0.0.1', port=20000, protocol='TCP')

dbg.cmd('Winclear')
dbg.cmd('Area.Clear')
dbg.cmd('Area')
dbg.print('Hello from Python API')

sleep(2)

# sleep(2)

# dbg.cmd('Sys.CPU S32G274A-M7')
# dbg.cmd('Sys.up')

#if dbg.fnc.system_up():
#    dbg.print('Up Successfully!')

#dbg.cmd(r'CD ~~\demo\arm\hardware\s32g2\s32g-vnp-evb\s32g-vnp-evb-m7')
#dbg.cmd('data.load.elf sieve_ram_thumb_ii_v7m.elf')

#dbg.cmm('/Users/helinglin/t32_202402/demo/arm/compiler/arm/cortexm.cmm')
dbg.cmd('ChDir.DO /Users/helinglin/t32_202402/demo/arm/compiler/arm/cortexm.cmm')


# 执行下面命令启动T32窗口 /Users/helinglin/t32_202402/bin/macosx64/t32marm-qt -c /Users/helinglin/t32_202402/config_sim.t32


#dbg.cmm('DO /Users/helinglin/t32_202402/demo/arm/compiler/arm/cortexm.cmm', timeout=30)
# dbg.cmm(r'CD ~~\T32_new\demo\arm\flash\s32g274-cm7-qspi.cmm', timeout=30)
#dbg.cmd('List')

# dbg.cmd('Data.Dump ANC:0x80000')
# addr1 = dbg.address(access='ANC', value=0x80000)
# dbg.memory.write_int32(address=addr1, value=-12345678)
# val1 = dbg.memory.read_int32(address=addr1)
# print(val1)


# dbg.cmd('var.watch mstatic1')
# dbg.variable.write("mstatic1", 1234567)
# val2 = dbg.variable.read("mstatic1")
# print(val2.value)

# Set Register - Method 1
# dbg.cmd('Register.Set PC main')
# Set Register - Method 2
# reg_val = dbg.symbol.query_by_name(name='main').address.value
# dbg.register.write_by_name(name="PC", value=reg_val)

# symbol_func2 = dbg.symbol.query_by_name('func2')
# dbg.breakpoint.set(address=symbol_func2.address, impl='ONCHIP')

# dbg.go()

# sleep(3)

# dbg.break_()

if dbg.fnc.state_halt():
    dbg.print("CPU is stopped at breakpoint")
    dbg.cmd("List.auto")



# addr = dbg.address(access='P', value=0x34042df8)
# symbol_main = dbg.symbol.query_by_address(address=addr)
# print(symbol_main.name)

# dbg.breakpoint.set(address=symbol_main.address, impl='SOFT')


# bp_list = dbg.breakpoint.list()