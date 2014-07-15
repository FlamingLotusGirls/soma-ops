// vim:set ts=4 sw=4 ai et:

#include <SPI.h>

// Pins for the Teensy 2.0:
//      http://www.pjrc.com/teensy/td_libs_SPI.html
//      https://www.pjrc.com/teensy/pinout.html


//#define INTERNAL_LED_PIN  11    // Unused; shares pin with TEMP_4
//#define POWER_SENSOR_PIN  A0  // Unused; backlow allowed Teensy to power on from this pin

#define RTC_SELECT_PIN       0
#define CURRENT_SENSOR_PIN  A1

#define ACC_Z_PIN           A2
#define ACC_Y_PIN           A3
#define ACC_X_PIN           A4

#define TEMP_1_PIN          A7
#define TEMP_2_PIN          A8
#define TEMP_3_PIN          A9
#define TEMP_4_PIN          A10

#define BUTTON_1_PIN        16
#define BUTTON_2_PIN        15

#define UART Serial1

float read_ac_current()
{
    // - A single operation seems to take about 0.112ms
    // - A 60Hz signal has a period of 1000/60 == 16.667ms
    // - So, it takes 16.667/0.112 == 148.8125 samples to see one sin wave
    // - Let's sample at least 3 waveforms to find a good average.
    #define CURRENT_SENSOR_ITERATIONS  (1000.0 / 60.0 / 0.112 * 3)
    #define SQRT_2 1.41421356237

    int maxVal = 0;
    int minVal = 1024;
    
    for (int i = 0; i < CURRENT_SENSOR_ITERATIONS; i++) {
          int x = analogRead(CURRENT_SENSOR_PIN);
          maxVal  = max(maxVal, x);
          minVal  = min(minVal, x);
    }

    float peakVoltage = (maxVal-minVal) * 5.0/1024 / 2;
    float rms = peakVoltage / SQRT_2;
    float amps = rms * 30;
    return amps;
}

float read_accelerometer()
{
    // 3.3/2/5.0*1024   => 337.92       338 (0g)
    // 0.6/5.0*1024     => 122.88       123 (mv/G)
    float gx = abs(analogRead(ACC_X_PIN) - 337.92) / 122.88;
    float gy = abs(analogRead(ACC_Y_PIN) - 337.92) / 122.88;
    float gz = abs(analogRead(ACC_Z_PIN) - 337.92) / 122.88;
    float sum = gx + gy + gz;
    return abs(1-sum);
}

// RTC code came from
// http://dlnmh9ip6v2uc.cloudfront.net/datasheets/BreakoutBoards/DS3234_Example_Code.pde
int RTC_init()
{
    pinMode(RTC_SELECT_PIN, OUTPUT);
    SPI.begin();
    SPI.setBitOrder(MSBFIRST);
    SPI.setDataMode(SPI_MODE1); // mode1, or mode3
    digitalWrite(RTC_SELECT_PIN, LOW);
    SPI.transfer(0x8E);
    SPI.transfer(0x60); // 0x60= disable Osciallator and Battery SQ wave @1hz, temp compensation, Alarms disabled
    digitalWrite(RTC_SELECT_PIN, HIGH);
    delay(10);
}

int SetTimeDate(int day, int month, int year, int hour, int min, int sec)
{
    int TimeDate[7] = { sec, min, hour, 0, day, month, year };

    for (int i = 0; i <= 6; i++) {
        if (i == 3)
            i++;

        int b = TimeDate[i] / 10;
        int a = TimeDate[i] - b * 10;

        if (i == 2) {
            if (b == 2)
                b = B00000010;
            else if (b == 1)
                b = B00000001;
        }

        TimeDate[i] = a + (b << 4);

        digitalWrite(RTC_SELECT_PIN, LOW);
        SPI.transfer(i + 0x80);
        SPI.transfer(TimeDate[i]);
        digitalWrite(RTC_SELECT_PIN, HIGH);
    }
}

char timebuf[30];
int get_time()
{
    int TimeDate[7]; // second, minute, hour, null, day, month, year

    for (int i = 0; i <= 6; i++) {
        if (i == 3)
            i++;
        digitalWrite(RTC_SELECT_PIN, LOW);
        SPI.transfer(i + 0x00);
        unsigned int n = SPI.transfer(0x00);

        digitalWrite(RTC_SELECT_PIN, HIGH);
        int a = n & B00001111;

        if (i == 2) {
            int b = (n & B00110000) >> 4;       // 24 hour mode

            if (b == B00000010)
                b = 20;
            else if (b == B00000001)
                b = 10;
            TimeDate[i] = a + b;
        }
        else if (i == 4) {
            int b = (n & B00110000) >> 4;

            TimeDate[i] = a + b * 10;
        }
        else if (i == 5) {
            int b = (n & B00010000) >> 4;

            TimeDate[i] = a + b * 10;
        }
        else if (i == 6) {
            int b = (n & B11110000) >> 4;

            TimeDate[i] = a + b * 10;
        }
        else {
            int b = (n & B01110000) >> 4;

            TimeDate[i] = a + b * 10;
        }
    }

    sprintf(timebuf, "@%04d-%02d-%02d %02d:%02d:%02d",
            TimeDate[6]+2000,
            TimeDate[5],
            TimeDate[4],
            TimeDate[2],
            TimeDate[1],
            TimeDate[0]);
    return TimeDate[0];
}

void setup()
{
    pinMode(ACC_Z_PIN, INPUT);
    pinMode(ACC_Y_PIN, INPUT);
    pinMode(ACC_X_PIN, INPUT);

    pinMode(TEMP_1_PIN, INPUT);
    pinMode(TEMP_2_PIN, INPUT);
    pinMode(TEMP_3_PIN, INPUT);
    pinMode(TEMP_4_PIN, INPUT);

    pinMode(BUTTON_1_PIN, INPUT_PULLUP);
    pinMode(BUTTON_2_PIN, INPUT_PULLUP);

    pinMode(CURRENT_SENSOR_PIN, INPUT);
    pinMode(RTC_SELECT_PIN, OUTPUT);

    Serial.begin(9600);
    UART.begin(9600);
    RTC_init();
}

void parse_serial_input(char *buf)
{
    int year, month, day, hour, min, sec;
    int ret;

    ret = sscanf(buf, "@%d-%d-%d %d:%d:%d", &year, &month, &day, &hour, &min, &sec);

    if (ret != 6) {
        Serial.println("# sscanf() failed");
        return;
    }

    year -= 2000;
    if (!(10 <= year   && year   <= 99 &&
           1 <= month  && month  <= 12 &&
           1 <= day    && day    <= 31 &&
           0 <= hour   && hour   <= 23 &&
           0 <= min    && min    <= 59 &&
           0 <= sec    && sec    <= 59))
    {
        Serial.println("# Range error");
        return;
    }

    SetTimeDate(day, month, year, hour, min, sec); 
    Serial.println("# Set");
}

void read_serial()
{
    #define BUF_SIZE 100
    static char buf[BUF_SIZE];
    static int buf_len;

    while (Serial.available()) {
        int c = Serial.read();

        if (c == '\n' || c == '\r') {
            buf[buf_len] = 0;
            if (buf_len > 0)
                parse_serial_input(buf);
            buf_len = 0;
        }

        else if (buf_len < BUF_SIZE-1) {
            buf[buf_len++] = c;
        }
    }
}

void read_temp(int pin, int *raw, float *c, float *f)
{
    *raw = analogRead(pin);
    *c = (5.0 * *raw * 100) / 1024;
    *f = (*c * 9)/ 5 + 32;
}

float max_acc;

void show_output()
{
    int temp_raw1, temp_raw2, temp_raw3, temp_raw4;
    float temp_f1, temp_f2, temp_f3, temp_f4,
          temp_c1, temp_c2, temp_c3, temp_c4,
          amps;

    amps = read_ac_current();

    read_temp(TEMP_1_PIN, &temp_raw1, &temp_c1, &temp_f1);
    read_temp(TEMP_2_PIN, &temp_raw2, &temp_c2, &temp_f2);
    read_temp(TEMP_3_PIN, &temp_raw3, &temp_c3, &temp_f3);
    read_temp(TEMP_4_PIN, &temp_raw4, &temp_c4, &temp_f4);

    //

    Serial.print(timebuf);
    Serial.print("     ");

    Serial.print("Acc: ");
    Serial.print(max_acc, 5);
    Serial.print("     ");

    Serial.print("Amp: ");
    Serial.print(amps);
    Serial.print("     ");

    Serial.print("TempRaw: ");
    Serial.print(temp_raw1); Serial.print(" ");
    Serial.print(temp_raw2); Serial.print(" ");
    Serial.print(temp_raw3); Serial.print(" ");
    Serial.print(temp_raw4); Serial.print(" ");
    Serial.print("  ");

    Serial.print("TempF: ");
    Serial.print(temp_f1); Serial.print("  ");
    Serial.print(temp_f2); Serial.print("  ");
    Serial.print(temp_f3); Serial.print("  ");
    Serial.print(temp_f4); Serial.println();

    //

    UART.print(timebuf);
    UART.print("     ");

    UART.print("Acc: ");
    UART.print(max_acc, 5);
    UART.print("     ");

    UART.print("Amp: ");
    UART.print(amps);
    UART.print("     ");

    UART.print("TempRaw: ");
    UART.print(temp_raw1); UART.print(" ");
    UART.print(temp_raw2); UART.print(" ");
    UART.print(temp_raw3); UART.print(" ");
    UART.print(temp_raw4); UART.print(" ");
    UART.print("  ");

    UART.print("TempF: ");
    UART.print(temp_f1); UART.print("  ");
    UART.print(temp_f2); UART.print("  ");
    UART.print(temp_f3); UART.print("  ");
    UART.print(temp_f4); UART.println();
}

void print_button(int i, int fired)
{
    if (fired) {
        Serial.print("!ON ");
        UART.print("!ON ");
    }
    else {
        Serial.print("!OFF ");
        UART.print("!OFF ");
    }

    Serial.println(i);
    UART.println(i);
}

#define BUTTON_HOLD_TIME 250
void read_buttons()
{
    static uint32_t debounced[2] = { 1, 1 };
    static int button_pin[2] = { BUTTON_1_PIN, BUTTON_2_PIN };
    static int pressed[2];
    static int show_time[2];

    unsigned long now = millis();

    for (int i = 0; i < 2; i++)
    {
        debounced[i] = (debounced[i] << 1) | digitalRead(button_pin[i]);

        // If it was previously pressed
        if (pressed[i]) {

            // if now released
            if (debounced[i] != 0) {
                print_button(i, 0);
                pressed[i] = 0;
            }

            else if (now - show_time[i] > BUTTON_HOLD_TIME) {
                print_button(i, 1);
                show_time[i] = now;
            }
        }

        // If it was not previously pressed
        else {
            // if now pressed
            if (debounced[i] == 0) {
                pressed[i] = 1;
                print_button(i, 1);
                show_time[i] = now;
            }
        }
    }
}

void loop()
{
    int old_secs = 0;

    while (1) {
        int new_secs = get_time();

        if (new_secs != old_secs)
        {
            show_output();
            max_acc = 0;
            old_secs = new_secs;
        }

        max_acc = max(max_acc, read_accelerometer());
        read_buttons();
    }
}
