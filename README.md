# PSEmulator

## requirements
- pyserial
- matplotlib
- Python > 3.7

## usage
``` bash
$ python3 -m venv myenv
$ source /myenv/bin/activate
myenv> pip install pyserial matplotlib jupyterlab
```
ex: exec.py
``` python
import PSEmulator

Emu1 = PSEmulator.PSEmulator('/path/to/serial_device', bit_rate)
Emu1.stand_by()
```
and, please refer to exec.ipynb
