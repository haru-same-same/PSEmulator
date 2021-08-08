import serial
import math
import time
import matplotlib.pyplot as plt

class PSEmulator:
    # Member variables
    conn: serial.serialposix.Serial
    start_time: float = 0 #s
    time_list: list = []
    volt_list: list = []
    curr_list: list = []
    okmsg: bytes = 'OK\n'.encode()
    
    time_delay_on: float = 0 #s
    time_delay_off: float = 0 #s

    output_state: bool = False
    ack_msg_state: bool = True
    
    voltage: float = 0 #V
    target_voltage: float = 0 #V
    volt_nstep: int = 0
    volt_slew_rise: float = 0 #V/s
    volt_slew_fall: float = 0 #V/s

    current: float = 0 #A
    target_current: float = 0 #A
    curr_nstep: int = 0
    curr_slew_rise: float = 0 #A/s
    curr_slew_fall: float = 0 #A/s

    power: float = 0 #W

    # Member functions
    def __init__(self, device_addr: str, bit_rate: int) -> None:
        print('Connecting serial device: ' + device_addr)
        try:
            self.conn = serial.Serial(device_addr, bit_rate, timeout = None)
        except:
            print('Serial connection ERROR!')
        else:
            print('Serial connection: established')

    def update_parameters(self) -> None:
        if self.volt_nstep > 0:
            dv = self.voltage - self.target_voltage
            if dv < 0 and abs(dv) > self.volt_slew_rise:
                self.voltage += self.volt_slew_rise
            elif dv > 0 and abs(dv) > self.volt_slew_fall:
                self.voltage -= self.volt_slew_fall
            else:
                self.voltage = self.target_voltage
            self.volt_nstep -= 1
        elif self.curr_nstep > 0:
            di = self.current - self.target_current
            if di < 0 and abs(di) > self.curr_slew_rise:
                self.current += self.curr_slew_rise
            elif di > 0 and abs(di) > self.curr_slew_fall:
                self.current -= self.curr_slew_fall
            else:
                self.current = self.target_current
            self.curr_nstep -= 1
        else:
            pass

    def set_voltage(self, volt: float) -> None:
        self.target_voltage = volt
        dv = self.voltage - volt
        if dv < 0: #raise voltage
            if math.isclose(self.volt_slew_rise, 0): #slew rate == 0
                self.voltage = volt
            else:
                self.volt_nstep = math.floor(abs(dv) / self.volt_slew_rise) + 1
        else: #lower voltage
            if math.isclose(self.volt_slew_fall, 0): #slew rate == 0
                self.voltage = volt
            else:
                self.volt_nstep = math.floor(abs(dv) / self.volt_slew_fall) + 1

    def set_current(self, curr: float) -> None:
        self.target_current = curr
        di = self.current - curr
        if di < 0: #raise current
            if math.isclose(self.curr_slew_rise, 0): #slew rate == 0
                self.current = curr
            else:
                self.curr_nstep = math.floor(abs(di) / self.curr_slew_rise) + 1
        else: #lower current
            if math.isclose(self.curr_slew_fall, 0): #slew rate == 0
                self.current = curr
            else:
                self.curr_nstep = math.floor(abs(di) / self.curr_slew_fall) + 1

    def set_volt_slew_rise(self, volt_slew_r: float) -> None:
        self.volt_slew_rise = volt_slew_r
    
    def set_volt_slew_fall(self, volt_slew_f: float) -> None:
        self.volt_slew_fall = volt_slew_f

    def set_curr_slew_rise(self, curr_slew_r: float) -> None:
        self.curr_slew_rise = curr_slew_r
    
    def set_curr_slew_fall(self, curr_slew_f: float) -> None:
        self.curr_slew_fall = curr_slew_f

    def update_canvas(self, _ax1, _ax2, p_time: float, volt: float, curr: float) -> None:
        self.time_list.append(p_time)
        self.volt_list.append(volt)
        self.curr_list.append(curr)
        if len(self.time_list) > 100:
            del self.time_list[0:80]
            del self.volt_list[0:80]
            del self.curr_list[0:80]
        
        _ax1.set_xlim(p_time - 30, p_time + 30)
        _ax1.plot(self.time_list, self.volt_list, marker = 'o', color = 'b')
        _ax2.set_xlim(p_time - 30, p_time + 30)
        _ax2.plot(self.time_list, self.curr_list, marker = 'o', color = 'r')
        plt.pause(0.01)

    def stand_by(self) -> None:
        print('Setting up canvas...')
        fig = plt.figure(figsize = (20, 8))
        
        ax1 = fig.add_subplot(1, 2, 1)
        ax1.set_xlabel('time from init [t]')
        ax1.set_ylabel('Voltage [V]')
        ax1.grid()
        
        ax2 = fig.add_subplot(1, 2, 2)
        ax2.set_xlabel('time from init [t]')
        ax2.set_ylabel('Current [A]')
        ax2.grid()
        print('Setting up canvas: done')
        self.start_time = time.time()
        
        while True:
            loop_start_time = time.time()
            
            self.update_parameters()
            passed_time = time.time() - self.start_time
            self.update_canvas(ax1, ax2, passed_time, self.voltage, self.current)
            
            if self.conn.in_waiting > 0:
                line = self.conn.readline().decode()
                print(line)
                
                # read parameters
                comm = line.split()[0]
                if len(line.split()) > 1:
                    par = float(line.split()[1].rstrip(';\r\n'))
                
                # set parameters
                if comm == ':SOURce:VOLTage:SLEW:RISing':
                    self.conn.write(self.okmsg)
                    self.set_volt_slew_rise(par)

                elif comm == ':SOURce:VOLTage:SLEW:FALLing':
                    self.conn.write(self.okmsg)
                    self.set_volt_slew_fall(par)
                    
                elif ':SOURce:VOLTage' in comm:
                    self.conn.write(self.okmsg)
                    self.set_voltage(par)

                elif comm == ':SOURce:CURRent:SLEW:RISing':
                    self.conn.write(self.okmsg)
                    self.set_curr_slew_rise(par)

                elif comm == ':SOURce:CURRent:SLEW:FALLing':
                    self.conn.write(self.okmsg)
                    self.set_curr_slew_fall(par)
                    
                elif ':SOURce:CURRent' in comm:
                    self.conn.write(self.okmsg)
                    self.set_current(par)

                elif comm == ':MEASure:VOLTage?':
                    self.conn.write((str(self.voltage) + '\n').encode())

                elif comm == ':MEASure:CURRent?':
                    self.conn.write((str(self.current) + '\n').encode())
            next_time = 1 - (time.time() - loop_start_time)
            time.sleep(next_time)
