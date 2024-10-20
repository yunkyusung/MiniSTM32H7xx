from machine import Pin
import utime

def dht_read(DHT11_PIN = 'B10', max_retries=5):
    """
    Function to read temperature and humidity data from DHT11 sensor

    Args:
        pin_name (str): Pin number where the sensor's data pin is connected (default: 'B10')
        max_retries (int): Maximum number of retries for reading data (default: 5)

    Returns:
        tuple: (humidity, temperature) tuple. Returns ('Error message', -1) in case of an error
    """
    Dht = Pin(DHT11_PIN, Pin.IN, Pin.PULL_DOWN)

    for _ in range(max_retries):
        try:
            data = [0b11111111] * 5

            # 0. Check if DHT is in IDLE (pull-up, High) state
            isIDLE = True
            for i in range(10):
#                print(Dht.value())
                if Dht.value() != 1:
                    isIDLE = False
#                    break
                utime.sleep_ms(10)

            if not isIDLE:
                print('Error! Sensor is busy')
                continue  # Retry if not in IDLE state

            # 1. When the line is in IDLE state, MCU sets the line to LOW for 18ms.
            Dht.init(Pin.OUT)
            Dht.low()
            utime.sleep_ms(18)

            # 2. MCU keeps the line HIGH for about 20~40us. => Start call
            Dht.high()
            utime.sleep_us(40)
            Dht.init(Pin.IN)

            # 3. DHTxx detects this as START from MCU and pulls the line LOW for 80us => Ack response
            while not Dht.value():  # Stay until the end of LOW state
                pass

            # 4. Next, DHT pulls the line HIGH for 80us to indicate "ready" for communication => ready response
            while Dht.value():  # Stay until the end of HIGH state
                pass

            # 5. 40-bit (8bit x 5) data transfer
            for i in range(5):
                for b in range(8):
                    # Wait for the start of the data bit High (Rising) signal
                    while not Dht.value():
                        pass

                    prev = utime.ticks_us()

                    while Dht.value():
                        pass

                    if utime.ticks_us() - prev < 40:
                        data[i] &= ~(1 << (7 - b))

            # Checksum verification
            checksum = data[0] + data[1] + data[2] + data[3]
            if (checksum & 0xFF) != data[4]:
                print("Checksum error")
                continue  # Retry if checksum error

            # Calculate humidity and temperature values
            humi = data[0] + data[1] / 10
            temp = data[2] + data[3] / 10

            # Validity check: Check if humidity is in the range of 0~100% and temperature is in the range of -40~80℃
            if not (0 <= humi <= 100 and -40 <= temp <= 80):
                print("Error! invalid sensor data range")
                continue  # Retry if data is invalid

            return humi, temp

        except Exception as e:
            print(f"Error! reading DHT11: {e}")
    
    return "Error! Failed to read data from DHT11 after multiple retries.", -1

if __name__ == '__main__':
    while True:
        humi, temp = dht_read()
        print('humi:', humi, 'temp:', temp)
        utime.sleep_ms(1500)
